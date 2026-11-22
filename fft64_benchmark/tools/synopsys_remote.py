"""Public SSH bridge for a sibling Synopsys mount and port.txt; host stdlib only."""
from pathlib import Path
import argparse
import contextlib
import datetime
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

REPO = Path(__file__).resolve().parents[2]
LIBRARIES = ['ASAP7_RVT_TT_nldm_NO_FAHA.lib', 'ASAP7_SEQ_RVT_TT_nldm_220123.lib', 'cells_sim.v']
PUBLIC_FILES = ['SPEC.json', 'requirements.txt', 'runtime.sh', 'setup.sh', 'run_preview.sh']
PUBLIC_DIRS = ['tools', 'flow', 'profiles']
IGNORE = shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'runs', '.eval_state',
                               'obj', 'csrc', 'simv', 'simv.daidir', '*.log', '*.log.json', 'attempts')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n'); temporary.replace(path)


def file_hashes(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(directory).rglob('*')) if p.is_file() and not any(IGNORE(str(directory), [part]) for part in p.relative_to(directory).parts)}


class Layout:
    def __init__(self, repo=REPO, port_file=None, shared=None, port=None, mount='/mnt/mydata', host='root@localhost'):
        self.repo = Path(repo).resolve()
        self.port_file = Path(port_file).resolve() if port_file else self.repo.parent/'port.txt'
        self.shared = Path(shared).resolve() if shared else self.repo.parent/'Synopsys'
        self.mount = str(Path(mount))
        self.host = host
        if not self.mount.startswith('/'):
            raise ValueError('The container mount must be an absolute path')
        if port is None:
            try: text = self.port_file.read_text().strip()
            except OSError as exc:
                raise ValueError('Cannot read '+str(self.port_file)+'; create it with the container SSH port.') from exc
            if not re.fullmatch(r'[0-9]+', text):
                raise ValueError('port.txt must contain one integer SSH port')
            port = int(text)
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError('SSH port must be between 1 and 65535')
        self.port = port

    def remote(self, path):
        path = Path(path).resolve()
        try: relative = path.relative_to(self.shared)
        except ValueError as exc: raise ValueError('Path is outside the shared mount: '+str(path)) from exc
        return str(Path(self.mount)/relative)

    def metadata(self):
        return dict(ssh_host=self.host, ssh_port=self.port, port_file=str(self.port_file),
                    shared_directory=str(self.shared), container_mount=self.mount)


class Connection:
    def __init__(self, layout):
        self.layout = layout
        key = digest(dict(host=layout.host, port=layout.port, shared=str(layout.shared)))[:12]
        self.state = Path(tempfile.gettempdir())/('f64_'+str(os.getuid())+'_'+key)
        self.state.mkdir(mode=0o700, exist_ok=True)
        self.state.chmod(0o700)

    def run(self, script, capture=False, log=None):
        if not shutil.which('ssh'): raise RuntimeError('OpenSSH client is required on the host')
        with tempfile.TemporaryDirectory(prefix='askpass_', dir=self.state) as temporary:
            helper = Path(temporary)/'askpass.sh'
            helper.write_text('#!/bin/sh\nprintf \'%s\\n\' "$FFT_SSH_PASSWORD"\n'); helper.chmod(0o700)
            env = dict(os.environ)
            env.update(SSH_ASKPASS=str(helper), SSH_ASKPASS_REQUIRE='force',
                       DISPLAY=env.get('DISPLAY') or ':0',
                       FFT_SSH_PASSWORD=env.get('FFT_SSH_PASSWORD', 'passwd'))
            argv = ['ssh', '-o', 'StrictHostKeyChecking=accept-new', '-o',
                    'UserKnownHostsFile='+str(self.state/'known_hosts'), '-o', 'ConnectTimeout=10',
                    '-o', 'NumberOfPasswordPrompts=1', '-o', 'ControlMaster=auto',
                    '-o', 'ControlPersist=10m', '-o', 'ControlPath='+str(self.state/'socket'),
                    '-o', 'ServerAliveInterval=30', '-o', 'ServerAliveCountMax=2',
                    '-p', str(self.layout.port), self.layout.host, 'bash -lc '+shlex.quote(script)]
            if log is None:
                return subprocess.run(argv, stdin=subprocess.DEVNULL, env=env, start_new_session=True,
                                      text=True, capture_output=capture)
            with Path(log).open('w') as stream:
                process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,env=env,start_new_session=True,
                                         text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                for line in process.stdout:
                    stream.write(line);stream.flush();print(line,end='',flush=True)
                return subprocess.CompletedProcess(argv,process.wait())

    def handshake(self):
        if not self.layout.shared.is_dir():
            raise ValueError('Shared directory does not exist: '+str(self.layout.shared))
        directory = self.layout.shared/'.fft64/handshakes'/uuid.uuid4().hex
        directory.mkdir(parents=True)
        token = uuid.uuid4().hex
        (directory/'host.txt').write_text(token)
        host_file = shlex.quote(self.layout.remote(directory/'host.txt'))
        reply = shlex.quote(self.layout.remote(directory/'container.txt'))
        script = ('set -e; test "$(cat '+host_file+')" = '+shlex.quote(token)+'; '
                  'printf %s '+shlex.quote(token)+' > '+reply+'; '
                  'if [ "$(id -u)" = 0 ]; then chown '+str(os.getuid())+':'+str(os.getgid())+' '+reply+'; fi')
        result = self.run(script, capture=True)
        if result.returncode:
            raise RuntimeError('SSH/shared-mount check failed:\n'+result.stdout+result.stderr+
                               '\nExpected '+str(self.layout.shared)+' mounted at '+self.layout.mount)
        if not (directory/'container.txt').is_file() or (directory/'container.txt').read_text() != token:
            raise RuntimeError('The SSH container is not using the expected writable shared mount')
        return dict(ssh=True, shared_read=True, shared_write=True)


def environment_script(layout, python=None, profile=None, need_python=True):
    lines = ['set -e', 'export FFT_CONTAINER_SHARE='+shlex.quote(layout.mount)]
    if profile:
        lines += ['source '+shlex.quote(profile)]
    else:
        lines += ['if [ -r /etc/profile.d/eda-env.sh ]; then source /etc/profile.d/eda-env.sh; fi']
    # Discover product aliases, retaining their names for Synopsys launchers.
    lines += [r'''for d in /usr/synopsys/vcs*/bin /usr/synopsys/dc*/bin /usr/synopsys/pt*/bin /usr/synopsys/lc*/bin /opt/eda/Synopsys/vcs/*/bin /opt/eda/Synopsys/syn/*/bin /opt/eda/Synopsys/prime/*/bin /opt/eda/Synopsys/lc/*/bin; do
if [ -d "$d" ]; then export PATH="${PATH:-}:$d"; fi
done''',
              r'''if [ -z "${VCS_HOME:-}" ]; then p="$(command -v vcs || true)"; if [ -n "$p" ]; then export VCS_HOME="$(dirname "$(dirname "$p")")"; fi; fi
if [ -z "${DC_HOME:-}" ]; then p="$(command -v dc_shell || true)"; if [ -n "$p" ]; then export DC_HOME="$(dirname "$(dirname "$p")")"; fi; fi
if [ -z "${PT_HOME:-}" ]; then p="$(command -v pt_shell || true)"; if [ -n "$p" ]; then export PT_HOME="$(dirname "$(dirname "$p")")"; fi; fi
if [ -z "${LC_HOME:-}" ]; then p="$(command -v lc_shell || true)"; if [ -n "$p" ]; then export LC_HOME="$(dirname "$(dirname "$p")")"; fi; fi''',
              'export LM_LICENSE_FILE="${LM_LICENSE_FILE:-27000@localhost}"',
              'export SNPSLMD_LICENSE_FILE="${SNPSLMD_LICENSE_FILE:-$LM_LICENSE_FILE}"',
              'export FFT_EDA_PROFILE_LOADED=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 FFT_NO_BUILD=1']
    if need_python:
        fixed = shlex.quote(python) if python else '"${FFT_PYTHON:-}"'
        candidates = [fixed] if python else [fixed, '/opt/dsbench/bin/python3', shlex.quote(layout.mount+'/.fft64/runtime/python/bin/python3'), shlex.quote(layout.mount+'/runtime/python/bin/python3'), '"$(command -v python3 || true)"']
        lines += ['task_python=""; task_python_without_numpy=""',
                  'for p in '+' '.join(candidates)+'; do',
                  'if [ -n "$p" ] && [ -x "$p" ] && "$p" -c "import sys; assert sys.version_info >= (3,10)" >/dev/null 2>&1; then',
                  'if [ -z "$task_python_without_numpy" ]; then task_python_without_numpy="$p"; fi',
                  'if "$p" -c "import numpy" >/dev/null 2>&1; then task_python="$p"; break; fi',
                  'fi; done',
                  'task_python="${task_python:-$task_python_without_numpy}"',
                  'if [ -z "$task_python" ]; then echo "Python 3.10+ is required inside the container; use --prepare-python or provide --remote-python." >&2; exit 2; fi',
                  'export FFT_PYTHON="$task_python"']
    return '\n'.join(lines)+'\n'


def prepare_library_cache(layout):
    source = layout.repo/'fft64_benchmark/tech'
    content = {name:(source/name).read_bytes() for name in LIBRARIES}
    key = hashlib.sha256(b''.join(content.values())).hexdigest()[:20]
    cache = layout.shared/'.fft64/tech'/key
    cache.mkdir(parents=True, exist_ok=True)
    for name, data in content.items():
        target = cache/name
        if target.exists():
            if target.read_bytes() != data: raise RuntimeError('Shared library cache content mismatch: '+str(target))
        else:
            temporary=target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
            temporary.write_bytes(data);temporary.replace(target)
    return cache


def public_hashes(task):
    hashes={name:hashlib.sha256((task/name).read_bytes()).hexdigest() for name in PUBLIC_FILES}
    for name in PUBLIC_DIRS:
        hashes.update({name+'/'+rel:value for rel,value in file_hashes(task/name).items()})
    return hashes


def stage(layout, submission=None, options=None, out=None, resume=False):
    options = options or {}
    task = layout.repo/'fft64_benchmark'
    public = public_hashes(task)
    source_files = {}
    if submission:
        submission = Path(submission).resolve()
        if not (submission/'rtl').is_dir() and not (submission/'design_config.json').is_file():
            raise ValueError('Submission must contain rtl/ or design_config.json')
        # Hash only what is staged; omit simulations, previous runs and VCS caches.
        with tempfile.TemporaryDirectory() as temporary:
            shutil.copytree(submission, Path(temporary)/'submission', ignore=IGNORE)
            source_files = file_hashes(Path(temporary)/'submission')
    identity = dict(benchmark_files=public, submission_files=source_files, options=options,
                    libraries={n:hashlib.sha256((task/'tech'/n).read_bytes()).hexdigest()for n in LIBRARIES},
                    connection=layout.metadata())
    output = Path(out).absolute() if out else layout.repo/'runs'/('synopsys_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6])
    if output.exists() or output.is_symlink():
        if not resume: raise ValueError('Output already exists; use a new --out or --resume: '+str(output))
        if not output.is_symlink(): raise ValueError('--resume requires an output link created by this launcher')
        job = output.resolve().parent
        if not job.is_relative_to(layout.shared/'.fft64/jobs'):
            raise ValueError('Resume output is outside this shared job directory')
        metadata = json.loads((job/'snapshot.json').read_text())
        if metadata['identity'] != identity: raise ValueError('Resume inputs changed; choose a new --out')
        if public_hashes(job/'fft64_benchmark')!=public or (submission and file_hashes(job/'submission')!=source_files):
            raise ValueError('Staged inputs changed; choose a new --out')
        return job, output
    job = layout.shared/'.fft64/jobs'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:10])
    job.mkdir(parents=True)
    destination = job/'fft64_benchmark'; destination.mkdir()
    for name in PUBLIC_FILES: shutil.copy2(task/name, destination/name)
    for name in PUBLIC_DIRS: shutil.copytree(task/name, destination/name, ignore=IGNORE)
    if submission: shutil.copytree(submission, job/'submission', ignore=IGNORE)
    (job/'output').mkdir()
    save(job/'snapshot.json', dict(identity=identity, host_job=str(job), container_job=layout.remote(job)))
    output.parent.mkdir(parents=True, exist_ok=True);output.symlink_to(job/'output', target_is_directory=True)
    return job, output


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['check','run','build','exec'])
    parser.add_argument('--port', type=int)
    parser.add_argument('--port-file')
    parser.add_argument('--shared-dir')
    parser.add_argument('--mount', default='/mnt/mydata')
    parser.add_argument('--ssh-host', default='root@localhost')
    parser.add_argument('--remote-python')
    parser.add_argument('--prepare-python',action='store_true',help='If no suitable container Python exists, unpack a pinned standalone runtime in the shared directory')
    parser.add_argument('--python-archive',help='Optional host-side offline standalone-Python archive')
    parser.add_argument('--remote-profile', help='Optional container-side shell profile')
    parser.add_argument('--out')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--inspect-only', action='store_true')
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--profile', choices=['area','architecture'], default='architecture')
    parser.add_argument('--seed', type=int, default=20261118)
    parser.add_argument('--scale', type=int, default=1)
    parser.add_argument('--formal', action='store_true')
    parser.add_argument('--backend',choices=['commercial','local'],default='commercial')
    parser.add_argument('--export',action='store_true',help='Copy a successful build into submission/implementation')
    parser.add_argument('--abc-delay-ps',type=float,default=10000)
    parser.add_argument('--tool-timeout',type=int,default=1800)
    parser.add_argument('--cwd', default='/mnt/mydata', help='Container working directory for exec')
    parser.add_argument('arguments', nargs='*')
    values=list(sys.argv[1:] if argv is None else argv)
    if '--' in values:
        split=values.index('--')
        args=parser.parse_args(values[:split]);args.arguments.extend(values[split+1:])
    else:
        args=parser.parse_intermixed_args(values)
    if args.scale<1 or args.abc_delay_ps<=0 or args.tool_timeout<1: parser.error('Frame scale, delay and timeout must be positive')
    layout=None;output=None
    try:
        layout=Layout(port_file=args.port_file, shared=args.shared_dir, port=args.port, mount=args.mount, host=args.ssh_host)
        connection=Connection(layout)
        if args.mode=='exec':
            if not args.arguments:raise ValueError('exec requires a command after --')
            script=environment_script(layout,args.remote_python,args.remote_profile,need_python=False)
            return connection.run(script+'cd '+shlex.quote(args.cwd)+'\nexec '+shlex.join(args.arguments)).returncode
        if args.mode=='check' and args.arguments:raise ValueError('check does not accept a submission')
        if args.mode in {'run','build'} and len(args.arguments)!=1:raise ValueError(args.mode+' requires one submission directory')
        if args.mode=='run'and args.backend!='commercial':raise ValueError('Remote preview uses Synopsys; use run_preview.sh for local evaluation')
        handshake=connection.handshake()
        if args.prepare_python or args.python_archive:
            probe=connection.run(environment_script(layout,args.remote_python,args.remote_profile)+'true\n',capture=True)
            if probe.returncode:
                if args.remote_python or 'Python 3.10+ is required' not in probe.stderr:
                    raise RuntimeError('Container profile/Python selection failed:\n'+probe.stdout+probe.stderr)
                machine=connection.run('uname -sm',capture=True)
                if machine.returncode or machine.stdout.strip()!='Linux x86_64':
                    raise RuntimeError('Automatic standalone runtime supports Linux x86_64; provide --remote-python for this container')
                from prepare_remote_python import prepare as prepare_python
                prepare_python(layout.shared/'.fft64/runtime',args.python_archive)
        cache=prepare_library_cache(layout)
        options=dict(mode=args.mode,inspect_only=args.inspect_only,quick=args.quick,
                     profile=args.profile,seed=args.seed,scale=args.scale,formal=args.formal,
                     remote_python=args.remote_python,remote_profile=args.remote_profile,backend=args.backend,abc_delay_ps=args.abc_delay_ps,tool_timeout=args.tool_timeout)
        job,output=stage(layout,args.arguments[0] if args.mode in {'run','build'} else None,options,args.out,args.resume)
        save(job/'connection.json',dict(**layout.metadata(),checks=handshake))
        remote_job=layout.remote(job)
        command=['"$FFT_PYTHON"',shlex.quote(remote_job+'/fft64_benchmark/tools/synopsys_environment.py'),args.mode,
                 '--out',shlex.quote(remote_job+'/output')]
        if args.mode=='check' and args.inspect_only:command+=['--inspect-only']
        if args.mode in {'run','build'}:
            command+=['--submission',shlex.quote(remote_job+'/submission'),'--profile',args.profile,
                      '--seed',str(args.seed),'--scale',str(args.scale)]
            if args.quick:command+=['--quick']
            if args.formal:command+=['--formal']
            if args.mode=='build':command+=['--backend',args.backend,'--abc-delay-ps',str(args.abc_delay_ps),'--tool-timeout',str(args.tool_timeout)]
        script=environment_script(layout,args.remote_python,args.remote_profile)
        script+='export FFT_TECH_DIR='+shlex.quote(layout.remote(cache))+'\n'
        script+='export FFT_TOOLS_PREFIX='+shlex.quote(layout.mount+'/.fft64/runtime')+'\n'
        script+='export FFT_PHYSICAL_CACHE_DIR='+shlex.quote(layout.mount+'/.fft64/physical_cache')+'\n'
        script+='cd '+shlex.quote(remote_job)+'\n'
        script+='if '+' '.join(command)+'; then task_status=0; else task_status=$?; fi\n'
        script+='if [ "$(id -u)" = 0 ]; then chown -R '+str(os.getuid())+':'+str(os.getgid())+' '+shlex.quote(remote_job)+'; fi\n'
        script+='exit "$task_status"\n'
        print('SSH: '+layout.host+':'+str(layout.port),flush=True)
        print('Host results: '+str(output),flush=True)
        print('Container job: '+remote_job,flush=True)
        result=connection.run(script,log=Path(output)/'ssh.log')
        if result.returncode==0 and args.mode=='build'and args.export:
            submission=Path(args.arguments[0]).resolve()
            if file_hashes(submission)!=json.loads((job/'snapshot.json').read_text())['identity']['submission_files']:
                raise ValueError('Submission changed during build; keep the result and export to a matching source snapshot')
            from implementation import export_artifacts
            destination=export_artifacts(Path(output)/'implementation',submission,Path(output)/'export_backup')
            print('Exported implementation: '+str(destination),flush=True)
        if result.returncode:
            if not (Path(output)/'environment.json').exists():
                save(Path(output)/'environment.json',dict(status='NOT_READY',ready=False,
                    failure='Remote launch did not complete; inspect ssh.log',returncode=result.returncode))
            print('Check failed; inspect '+str(output)+' for environment/tool logs.',file=sys.stderr)
        return result.returncode
    except (OSError,ValueError,RuntimeError) as exc:
        print('Environment/launch error: '+str(exc), file=sys.stderr)
        if output is not None:
            save(Path(output)/'launch_error.json',dict(status='UNSCORED_INFRASTRUCTURE',failure=str(exc)))
        return 2


if __name__=='__main__':sys.exit(main())
