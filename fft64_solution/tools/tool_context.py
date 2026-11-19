"""Local measurement identity used for cross-machine checkpoint reuse."""
from pathlib import Path
import shutil
import sys

SOLUTION=Path(__file__).resolve().parents[1]
BENCHMARK=SOLUTION.with_name('fft64_benchmark')
sys.path.insert(0,str(BENCHMARK/'tools'))
from common import TECH,sha
from toolchain import activate


def current():
    import numpy
    found=activate()
    tools={name:found[name]for name in ['yosys','abc','sta','iverilog','vvp','verilator']}
    tools.update({name:shutil.which(name)for name in ['g++','make']})
    if not all(tools.values()):
        raise EnvironmentError('Prepare the local toolchain before running the reference search')
    return dict(tools={name:dict(path=str(Path(path).resolve()),sha256=sha(path))for name,path in tools.items()},
                libraries={p.name:sha(p)for p in [TECH/'ASAP7_RVT_TT_nldm_NO_FAHA.lib',TECH/'ASAP7_SEQ_RVT_TT_nldm_220123.lib',TECH/'cells_sim.v']},
                python=sys.version,numpy=numpy.__version__)
