"""Snapshot a design in the shared mount and run the fixed native Synopsys flow."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from bootstrap_docker_runtime import prepare

ROOT = Path(__file__).resolve().parents[1]
LIBRARIES = ['ASAP7_RVT_TT_nldm_NO_FAHA.lib', 'ASAP7_SEQ_RVT_TT_nldm_220123.lib', 'cells_sim.v']
IGNORED = shutil.ignore_patterns('.git', '__pycache__', '.eval_state', 'synopsys_results',
                                '*_feedback.tar.gz', '*.log', '*.log.json', 'obj', 'csrc',
                                'simv', 'simv.daidir', 'dc_work', 'runs', 'attempts', 'db')


def remote_path(path, shared, mount):
    return mount+'/'+str(Path(path).resolve().relative_to(shared))


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    submission = args.pop(0) if args and not args[0].startswith('-') else None
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ssh-host', default=os.environ.get('FFT_DOCKER_HOST', 'root@localhost'))
    parser.add_argument('--ssh-port', type=int, default=int(os.environ.get('FFT_DOCKER_PORT', '1234')))
    parser.add_argument('--shared-dir', default=os.environ.get('FFT_DOCKER_SHARED_DIR', '/home/sj/ALS/DP2.0/DSBench/Synopsys'))
    parser.add_argument('--container-share', default=os.environ.get('FFT_CONTAINER_SHARE', '/mnt/mydata'))
    parser.add_argument('--wheelhouse', help='External offline wheel directory on the host, inside the shared mount')
    options, native = parser.parse_known_args(args)
    normalized=[]
    for token in native:
        if any(token.startswith(flag+'=')for flag in ['--out','--state-dir','--id']):
            normalized.extend(token.split('=',1))
        else:normalized.append(token)
    native=normalized
    if not submission and '--check-only' not in native:
        parser.error('Provide one local submission directory, or --check-only; native batch mode remains available via run_synopsys.sh')
    shared = Path(options.shared_dir).resolve(); shared.mkdir(parents=True, exist_ok=True)
    wheelhouse = None
    if options.wheelhouse:
        path = Path(options.wheelhouse).resolve()
        if not path.is_dir() or not path.is_relative_to(shared):
            parser.error('--wheelhouse must be an existing directory inside --shared-dir')
        wheelhouse = remote_path(path, shared, options.container_share.rstrip('/'))
    prepare(shared/'runtime')
    (shared/'eval').mkdir(exist_ok=True)
    (shared/'eval_state').mkdir(exist_ok=True)
    (shared/'jobs').mkdir(exist_ok=True)
    snapshot = Path(tempfile.mkdtemp(prefix=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_'), dir=shared/'jobs'))
    for name in ['fft64_benchmark', 'operator']:
        shutil.copytree(ROOT/name, snapshot/name, ignore=IGNORED)
    shutil.copy2(ROOT/'run_synopsys.sh', snapshot/'run_synopsys.sh')
    if submission:
        directory = Path(submission).resolve()
        if not (directory/'rtl').is_dir() and not (directory/'design_config.json').exists():
            parser.error('Submission must contain rtl/ or design_config.json')
        shutil.copytree(directory, snapshot/'submission', ignore=IGNORED)
        if '--id' not in native:
            native += ['--id', directory.name]
    # Keep compiled DBs outside snapshots so identical libraries/compiler outputs
    # retain the same calibration fingerprint across repeated wrapper invocations.
    tech = ROOT/'fft64_benchmark/tech'
    library_id = hashlib.sha256(b''.join((tech/name).read_bytes() for name in LIBRARIES)).hexdigest()[:20]
    cache = shared/'runtime/tech'/library_id; cache.mkdir(parents=True, exist_ok=True)
    for name in LIBRARIES:
        target = cache/name
        if not target.exists(): shutil.copy2(tech/name, target)
        if target.read_bytes() != (tech/name).read_bytes(): raise ValueError('Library cache mismatch: '+str(target))
    receipt = dict(source_directory=str(ROOT), submission=str(Path(submission).resolve()) if submission else None,
                   shared_directory=str(shared), container_share=options.container_share,
                   snapshot=str(snapshot), library_id=library_id,
                   source_hashes={str(p.relative_to(snapshot)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for folder in ['fft64_benchmark/tools', 'fft64_benchmark/flow', 'operator']
                                  for p in (snapshot/folder).rglob('*') if p.is_file() and p.suffix in {'.py', '.tcl', '.sdc', '.sh'}})
    (snapshot/'snapshot.json').write_text(json.dumps(receipt, indent=2)+'\n')
    mount = options.container_share.rstrip('/')
    remote = remote_path(snapshot, shared, mount)
    if '--out' not in native:
        native += ['--out', mount+'/eval/'+snapshot.name]
    if '--state-dir' not in native:
        native += ['--state-dir', mount+'/eval_state']
    native_command=shlex.join(['bash', 'run_synopsys.sh']+(['submission'] if submission else [])+native)
    output=native[native.index('--out')+1]
    ownership=' '.join(shlex.quote(x)for x in [remote,output,remote_path(cache,shared,mount),native[native.index('--state-dir')+1]])
    dependency_env = ('export PIP_NO_INDEX=1 PIP_FIND_LINKS='+shlex.quote(Path(wheelhouse).as_uri())+'; ') if wheelhouse else ''
    command = ('set -e; '+dependency_env+'export FFT_CONTAINER_SHARE='+shlex.quote(mount)+
               ' FFT_EDA_PROFILE='+shlex.quote(remote+'/operator/docker_env.sh')+
               ' FFT_TECH_DIR='+shlex.quote(remote_path(cache, shared, mount))+'; '+
               'source "$FFT_EDA_PROFILE"; cd '+shlex.quote(remote)+'; '+
               'if '+native_command+'; then result=0; else result=$?; fi; '+
               'if [ "$(id -u)" = 0 ]; then chown -R '+str(os.getuid())+':'+str(os.getgid())+' '+ownership+'; fi; exit "$result"')
    ssh = ['ssh', '-o', 'StrictHostKeyChecking=accept-new', '-o', 'ConnectTimeout=10',
           '-o', 'ControlMaster=auto', '-o', 'ControlPersist=1h', '-o',
           'ControlPath='+os.environ.get('FFT_DOCKER_SSH_CONTROL', '/tmp/fft64_docker_%C'),
           '-p', str(options.ssh_port), options.ssh_host, command]
    print('Native Synopsys source snapshot: '+str(snapshot), flush=True)
    return subprocess.run(ssh).returncode


if __name__ == '__main__':
    sys.exit(main())
