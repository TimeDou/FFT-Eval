"""Shared file, process and environment helpers for the FFT64 evaluator."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import shutil
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
TECH = Path(os.environ.get('FFT_TECH_DIR', ROOT / 'tech')).resolve()
COMB = TECH / 'ASAP7_RVT_TT_nldm_NO_FAHA.lib'
SEQ = TECH / 'ASAP7_SEQ_RVT_TT_nldm_220123.lib'

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
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                                stdout=stream, stderr=subprocess.STDOUT,
                                cwd=cwd or ROOT, start_new_session=True)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            save(str(log) + '.json', dict(argv=list(map(str, argv)),
                 seconds=time.monotonic()-start, status='TIMEOUT'))
            raise
    receipt = dict(argv=list(map(str, argv)), seconds=time.monotonic()-start,
                   returncode=proc.returncode)
    save(str(log) + '.json', receipt)
    if proc.returncode:
        raise RuntimeError(str(log) + '\n' + log.read_text()[-1600:])
    return receipt

def lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open('a')
    fcntl.flock(stream, fcntl.LOCK_EX)
    return stream

def flow_identity(backend):
    """Identify the setup so an area denominator stays comparable."""
    files = ['SPEC.json', 'tools/local_asic.py'] if backend == 'local' else [
        'SPEC.json', 'tools/commercial.py', 'flow/synth_dc.tcl',
        'flow/constraints.sdc', 'flow/timing_pt.tcl', 'flow/paths.tcl']
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
