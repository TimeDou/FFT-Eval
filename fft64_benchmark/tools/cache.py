"""Content identities for resumable measurements and complete cached records."""
from pathlib import Path
import hashlib
import json
import os
import sys
import shutil
import time
import numpy as np
from common import ROOT, TECH, COMB, SEQ, CacheIdentityError, read, save, sha
from toolchain import find_tool


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def array_identity(frames):
    data = np.ascontiguousarray(frames, dtype='<i8')
    return dict(sha256=hashlib.sha256(data.tobytes()).hexdigest(),
                shape=list(data.shape), dtype=data.dtype.str)


def runtime_identity(backend):
    names = {'vcs':['vcs'], 'iverilog':['iverilog','vvp'], 'verilator':['verilator'],
             'commercial':['vcs','dc_shell','pt_shell'],
             'local':['iverilog','vvp','verilator','yosys','abc','sta']}[backend]
    tools = {}
    for name in names:
        path = find_tool(name)
        tools[name] = dict(path=path, sha256=sha(path) if path and Path(path).is_file() else None)
    drivers = ['cache.py','common.py','throughput.py','simulate.py','model.py','numeric_io.py',
               'toolchain.py','scoring.py','evaluate.py','commercial.py','local_asic.py',
               'frequency.py','local_frequency.py','implementation.py']
    libraries = [COMB, SEQ, TECH/'cells_sim.v']
    if backend in {'vcs','commercial'}:
        libraries += [TECH/'db/comb_rvt_tt.db', TECH/'db/seq_rvt_tt.db']
    return dict(backend=backend, tools=tools, python_version=sys.version,
                python_sha256=sha(sys.executable), numpy_version=np.__version__,
                drivers={name:sha(ROOT/'tools'/name) for name in drivers},
                flow_scripts={str(p.relative_to(ROOT/'flow')):sha(p) for p in sorted((ROOT/'flow').rglob('*')) if p.is_file()},
                policy_sha256=sha(ROOT/'profiles/policy.json'),
                specification_sha256=sha(ROOT/'SPEC.json'),
                libraries={p.name:sha(p) if p.is_file() else None for p in libraries},
                environment={k:os.environ.get(k) for k in ['FFT_TECH_DIR','FFT_TOOLS_PREFIX',
                    'VCS_HOME','SYNOPSYS','FFT_VCS','FFT_IVL','FFT_ABC','FFT_STA']})


def bind_directory(directory, identity, artifacts=None):
    """Refuse mismatched or unbound checkpoints without altering their contents."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory/'identity.json'
    if path.exists():
        try:
            matching = read(path) == identity
        except (OSError, ValueError):
            matching = False
        if not matching:
            raise CacheIdentityError('Measurement identity mismatch; choose a new output directory: '+str(directory))
    else:
        existing = (any((directory/name).exists() for name in artifacts) if artifacts is not None
                    else any(p.name != 'lock' for p in directory.iterdir()))
        if existing:
            raise CacheIdentityError('Unbound measurement cache; choose a new output directory: '+str(directory))
        save(path, identity)


def load_cached(path, identity):
    path = Path(path)
    receipt = path.with_name(path.name+'.cache.json')
    try:
        record = read(receipt)
        if (not isinstance(record,dict) or record.get('status') != 'COMPLETE' or record.get('identity') != identity
                or record.get('payload_sha256') != sha(path)):
            return None
        return read(path)
    except (OSError, ValueError, TypeError):
        return None


def save_cached(path, value, identity):
    path = Path(path)
    if path.exists():
        attempt=path.parent/'cache_attempts'/str(time.time_ns())
        attempt.mkdir(parents=True,exist_ok=True)
        for previous in [path,path.with_name(path.name+'.cache.json')]:
            if previous.is_file():shutil.copy2(previous,attempt/previous.name)
    save(path, value)
    save(path.with_name(path.name+'.cache.json'),
         dict(status='COMPLETE', identity=identity, payload_sha256=sha(path)))
