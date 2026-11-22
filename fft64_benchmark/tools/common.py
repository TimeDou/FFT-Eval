"""Shared file, process and environment helpers for the FFT64 evaluator."""
from pathlib import Path
import fcntl
import errno
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
TECH = Path(os.environ.get('FFT_TECH_DIR', ROOT / 'tech')).resolve()
COMB = TECH / 'ASAP7_RVT_TT_nldm_NO_FAHA.lib'
SEQ = TECH / 'ASAP7_SEQ_RVT_TT_nldm_220123.lib'

class InfrastructureError(RuntimeError):
    """An evaluation could not be measured; this is not a design score."""

class CacheIdentityError(InfrastructureError):
    """A result directory belongs to another measurement."""

class DesignInvalidError(ValueError):
    """An observed violation attributable to the submitted design."""

class ToolExecutionError(InfrastructureError):
    """A tool failed without an established design violation."""

def tool_failure(message):
    """Classify explicit HDL/checker diagnostics; unknown tool errors stay unscored."""
    infrastructure = (r'license\s+(?:checkout|check.?out|server|manager|error|unavailable|failed|failure|denied)|'
                      r'no\s+valid\s+license|no\s+licenses?\s+available|licensing error|'
                      r'(?:unable|failed|cannot)\s+to\s+(?:obtain|check\s*out).*license|'
                      r'FLEXnet|SNPSLMD|DCSH-1|segmentation|internal error|out of memory|'
                      r'No space left|file open|cannot open.*(?:lib|db)')
    design = (r'X (?:control|data) cycle\d+|TASK_DESIGN_INVALID:|'
              r'Error-\[(?:SE|IPD|XMRE|URMI|ICPD|PCWM)\]|'
              r'source\.sv:\d+:.*(?:syntax error|Unknown module|error:)|'
              r'syntax error.*source\.sv|%Error.*source\.sv|'
              r'Error:.*\((?:VER|ELAB)-\d+\)')
    if not re.search(infrastructure, message, re.I) and re.search(design, message, re.I):
        return DesignInvalidError(message)
    return ToolExecutionError(message)

def failure_status(exc):
    """Only identified design violations may enter a ranking as a valid zero."""
    if isinstance(exc, (DesignInvalidError, AssertionError)):
        return 'DESIGN_INVALID'
    return 'UNSCORED_INFRASTRUCTURE'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False,
                             default=lambda x: x.item() if hasattr(x, 'item') else str(x)) + '\n')
    tmp.replace(path)

def read(path):
    return json.loads(Path(path).read_text())

def run(argv, log, timeout=600, cwd=None):
    argv = list(map(str, argv))
    from toolchain import TOOLS, find_tool
    if argv[0] in TOOLS:
        argv[0] = find_tool(argv[0]) or argv[0]
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    if log.exists():
        previous = log.parent / 'attempts'
        previous.mkdir(exist_ok=True)
        log.rename(previous / (log.name + '.' + str(time.time_ns())))
    start = time.monotonic()
    with log.open('w') as stream:
        options=dict(stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
                     cwd=cwd or ROOT, start_new_session=True)
        try:
            proc = subprocess.Popen(argv, **options)
        except OSError as exc:
            # Some Synopsys launchers are executable shell text without
            # a shebang. Interactive bash handles ENOEXEC automatically; Python
            # execve does not. Keep the product alias as the script's $0.
            if exc.errno != errno.ENOEXEC:
                raise
            header=Path(argv[0]).read_bytes()[:4096]
            if not header or b'\0' in header or header.startswith(b'\x7fELF'):
                raise
            argv=['bash',*argv]
            proc = subprocess.Popen(argv, **options)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            save(str(log) + '.json', dict(argv=list(map(str, argv)),
                 seconds=time.monotonic()-start, status='TIMEOUT'))
            raise InfrastructureError('Tool timeout: '+str(log)) from exc
    receipt = dict(argv=list(map(str, argv)), seconds=time.monotonic()-start,
                   returncode=proc.returncode)
    save(str(log) + '.json', receipt)
    if proc.returncode:
        raise tool_failure(str(log) + '\n' + log.read_text()[-4000:])
    return receipt

def lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open('a')
    fcntl.flock(stream, fcntl.LOCK_EX)
    return stream

def flow_identity(backend):
    """Identify the setup so an area denominator stays comparable."""
    files = ['SPEC.json', 'tools/local_asic.py', 'tools/scoring.py','tools/local_frequency.py','tools/implementation.py'] if backend == 'local' else [
        'SPEC.json', 'tools/commercial.py', 'flow/synth_dc.tcl',
        'flow/constraints.sdc', 'flow/timing_pt.tcl', 'flow/paths.tcl', 'tools/scoring.py',
        'flow/fmax_pt.tcl', 'tools/frequency.py', 'tools/throughput.py','tools/implementation.py','flow/templates/dc_opt.tcl']
    files += ['profiles/policy.json']
    libraries = [COMB, SEQ]
    if backend == 'commercial':
        libraries += [TECH/'db/comb_rvt_tt.db', TECH/'db/seq_rvt_tt.db']
    data = dict(backend=backend, files={p: sha(ROOT/p) for p in files},
                libraries={p.name: sha(p) for p in libraries})
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def executable(variable, candidates):
    if os.environ.get(variable):
        value = os.environ[variable]
        return Path(os.path.abspath(shutil.which(value) or value))
    for name in candidates:
        found = shutil.which(name)
        if found:
            return Path(os.path.abspath(found))
    return Path(candidates[0])
