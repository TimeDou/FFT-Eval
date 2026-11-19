"""Prefer the installed EDA environment; prepare only missing dependencies."""
from pathlib import Path
import importlib.util
import os
import shlex
import shutil
import subprocess
import sys
from common import ROOT, TECH, COMB, SEQ, lock, run

TOOLS = {
    'vcs': ('FFT_VCS', ['vcs'], ['VCS_HOME']),
    'dc_shell': ('FFT_DC', ['dc_shell'], ['DC_HOME']),
    'pt_shell': ('FFT_PT', ['pt_shell'], ['PT_HOME']),
    'lc_shell': ('FFT_LC_BIN', ['lc_shell'], ['LC_HOME', 'DC_HOME']),
    'yosys': ('FFT_YOSYS', ['yosys'], ['YOSYS_HOME']),
    'abc': ('FFT_ABC', ['yosys-abc', 'berkeley-abc', 'abc'], ['YOSYS_HOME', 'ABC_HOME']),
    'sta': ('FFT_STA', ['sta', 'opensta'], ['OPENSTA_HOME']),
    'iverilog': ('FFT_IVERILOG', ['iverilog'], ['IVERILOG_HOME']),
    'vvp': ('FFT_VVP', ['vvp'], ['IVERILOG_HOME']),
    'verilator': ('FFT_VERILATOR', ['verilator'], ['VERILATOR_ROOT']),
}
COMMERCIAL = ['vcs', 'dc_shell', 'pt_shell']
LOCAL = ['yosys', 'abc', 'sta', 'iverilog', 'vvp', 'verilator']
_PROFILE_LOADED = False


def load_platform_profile():
    """Also support a Python grader launched without a login shell."""
    global _PROFILE_LOADED
    if _PROFILE_LOADED or os.environ.get('FFT_EDA_PROFILE_LOADED') == '1':
        return
    _PROFILE_LOADED = True
    profile = Path(os.environ.get('FFT_EDA_PROFILE', '/etc/profile.d/eda-env.sh'))
    if not profile.is_file():
        return
    completed = subprocess.run(['bash','-c','source "$1" >/dev/null && env -0','fft64',str(profile)],
                               capture_output=True, timeout=20)
    if completed.returncode:
        raise EnvironmentError('Cannot load the platform EDA profile: '+str(profile))
    for entry in completed.stdout.split(b'\0'):
        if b'=' not in entry:continue
        key, value = map(os.fsdecode, entry.split(b'=',1))
        if key not in {'HOME','CODEX_HOME','PWD','OLDPWD','SHLVL','_'}:
            os.environ[key] = value
    os.environ['FFT_EDA_PROFILE_LOADED'] = '1'


def prefix():
    default = Path('/workspace/.fft64-tools') if Path('/workspace').is_dir() else ROOT.parent/'.fft64-tools'
    return Path(os.environ.get('FFT_TOOLS_PREFIX', default)).resolve()


def executable_path(path):
    # Synopsys product commands may be links to a shared snps_shell launcher.
    # Keep the invoked name (argv[0]); realpath is suitable for fingerprints,
    # not for choosing which executable entrypoint to run.
    return os.path.abspath(os.fspath(path))


def databases_ready():
    return all(path.is_file() and path.stat().st_size > 0 for path in
               [TECH/'db/comb_rvt_tt.db', TECH/'db/seq_rvt_tt.db'])


def find_tool(name):
    variable, names, homes = TOOLS[name]
    if os.environ.get(variable):
        value = os.environ[variable]
        path = shutil.which(value)
        return executable_path(path) if path else None
    for candidate in names:
        path = shutil.which(candidate)
        if path:
            return executable_path(path)
    directories = []
    for home in homes:
        if os.environ.get(home):
            base = Path(os.environ[home])
            directories.extend([base/'bin', base/'syn/bin', base/'linux64/bin', base])
    directories.append(prefix()/'bin')
    if name == 'lc_shell':
        for pattern in ['*/bin/lc_shell','*/*/bin/lc_shell','*/*/linux64/bin/lc_shell']:
            directories.extend(path.parent for path in Path('/opt/eda/Synopsys').glob(pattern))
    for directory in directories:
        for candidate in names:
            path = directory/candidate
            if path.is_file() and os.access(path, os.X_OK):
                return executable_path(path)
    return None


def activate():
    """Expose discovered installed tools to the existing measurement scripts."""
    load_platform_profile()
    found = {name: find_tool(name) for name in TOOLS}
    directories = os.environ.get('PATH', '').split(os.pathsep)
    for name, path in found.items():
        if not path:
            continue
        directory = str(Path(path).parent)
        if directory not in directories:
            directories.append(directory)
        if name in {'abc', 'sta'}:
            os.environ.setdefault(TOOLS[name][0], path)
    os.environ['PATH'] = os.pathsep.join(directories)
    return found


def probe(quick=False):
    tools = {name: find_tool(name) for name in TOOLS}
    library_files = [COMB, SEQ, TECH/'cells_sim.v']
    db_files = [TECH/'db/comb_rvt_tt.db', TECH/'db/seq_rvt_tt.db']
    numerical = importlib.util.find_spec('numpy') is not None
    commercial_missing = [name for name in (['vcs'] if quick else COMMERCIAL) if not tools[name]]
    local_missing = [name for name in (['iverilog', 'vvp'] if quick else LOCAL) if not tools[name]]
    if not quick:
        local_missing += [name for name in ['g++', 'make'] if not shutil.which(name)]
    common_missing = ([] if numerical else ['numpy']) + ([] if quick else [str(p) for p in library_files if not p.is_file()])
    return dict(tools=tools, python=sys.executable, numpy_available=numerical,
                commercial=dict(tools_present=not commercial_missing,
                    missing=commercial_missing+common_missing+([] if quick else [str(p) for p in db_files if not p.is_file() or p.stat().st_size == 0]),
                    ready=not commercial_missing and not common_missing and (quick or databases_ready())),
                local=dict(tools_present=not local_missing, missing=local_missing+common_missing,
                           ready=not local_missing and not common_missing), quick=quick)


def select_backend(report, requested='auto', calibration=None):
    if requested not in {'auto', 'commercial', 'local'}:
        raise ValueError('Backend must be auto, commercial or local')
    if calibration and requested == 'auto':
        return calibration['backend'], 'Use the calibrated backend.'
    if requested != 'auto':
        return requested, 'Explicit backend selection.'
    if report['commercial']['tools_present']:
        return 'commercial', 'Use installed Synopsys tools; prepare libraries if needed.'
    if report['tools']['yosys'] or (report['quick'] and report['local']['tools_present']):
        return 'local', 'Use installed open-source tools; fill missing dependencies only.'
    return 'local', 'No complete Synopsys chain or installed Yosys; open-source setup is the last fallback.'


def prepare(requested='auto', quick=False, check_only=False, allow_build=True, calibration=None):
    activate()
    initial = probe(quick)
    backend, reason = select_backend(initial, requested, calibration)
    actions, failures = [], []
    if not check_only:
        if not initial['numpy_available']:
            try:
                wheel_options = ['--no-index', '--find-links', ROOT/'vendor/wheels'] if sys.version_info[:2] == (3, 12) else []
                run([sys.executable, '-m', 'pip', 'install', *wheel_options, '-r', ROOT/'requirements.txt'],
                    prefix()/'logs/numpy.log', 600)
                importlib.invalidate_caches()
                actions.append('Installed the missing NumPy dependency.')
            except Exception as exc:
                failures.append(str(exc))
        if backend == 'commercial' and not quick:
            if initial['commercial']['tools_present'] and not databases_ready():
                compiler = find_tool('lc_shell')
                if compiler:
                    try:
                        with lock(TECH/'db/compile.lock'):
                            if not databases_ready():
                                run([compiler, '-f', ROOT/'flow/compile_libraries.tcl'], TECH/'library_compile.log', 300)
                            if not databases_ready():
                                raise EnvironmentError('Library Compiler did not produce both nonempty ASAP7 DB files; see '+str(TECH/'library_compile.log'))
                        actions.append('Compiled the supplied Liberty files into DB; no open-source EDA build.')
                    except Exception as exc:
                        failures.append(str(exc))
                else:
                    failures.append('Synopsys is installed but the ASAP7 DBs are missing. Set FFT_LC_BIN or provide tech/db/comb_rvt_tt.db and seq_rvt_tt.db; installing Yosys does not fix this library setup.')
        elif backend == 'local' and not probe(quick)['local']['tools_present']:
            missing = [name for name in (['iverilog', 'vvp'] if quick else LOCAL) if not find_tool(name)]
            if allow_build:
                try:
                    from bootstrap_oss import build_missing
                    built = build_missing(missing)
                    actions.extend('Built missing component: '+name for name in built)
                    activate()
                except Exception as exc:
                    failures.append(str(exc))
            else:
                failures.append('Missing open-source tools; automatic build is disabled.')
    final = probe(quick)
    notices = []
    if (backend == 'commercial' and requested == 'auto' and not calibration and not check_only
            and not final['commercial']['ready'] and final['local']['ready']):
        backend = 'local'
        reason = 'Commercial library setup is incomplete; reuse the already complete open-source chain.'
        notices, failures = failures, []
        actions.append('Reused existing open-source tools; no EDA build.')
    return dict(requested_backend=requested, selected_backend=backend, selection_reason=reason,
                ready=final[backend]['ready'], missing=final[backend]['missing'], tools=final['tools'],
                python=final['python'], actions=actions, failures=failures, notices=notices, check_only=check_only,
                quick=quick, tools_prefix=str(prefix()))


def write_environment(path, report):
    """A small shell handoff for tools already resolved by setup.sh."""
    lines = ['export FFT_SELECTED_BACKEND='+shlex.quote(report['selected_backend']),
             'export PATH='+shlex.quote(os.environ.get('PATH', ''))]
    for name, value in report['tools'].items():
        if value:
            lines.append('export '+TOOLS[name][0]+'='+shlex.quote(value))
    Path(path).write_text('\n'.join(lines)+'\n')
