import json, sys, shutil, tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0, '/mnt/DATA1/sj/FFT/Claude-Opus-5.5/FFT-Bench/fft64_benchmark/tools')
sys.path.insert(0, '/mnt/DATA1/sj/FFT/Claude-Opus-5.5/FFT-Bench/work')
import model as bench
from simulate import simulate, decode
from throughput import stream_schedule
import gen

rtl = Path(sys.argv[1]).read_text()
cfg = dict(gen.DEFAULT); cfg.update(json.loads(Path(sys.argv[2]).read_text()))
iis = [int(v) for v in sys.argv[3:]]
frames, _ = bench.evaluation_frames(20261118, 1024)
work = Path(tempfile.mkdtemp(prefix='dbg_', dir='.'))
try:
    for ii in iis:
        sub = frames[:24]
        ev, meta, inputs = stream_schedule(sub, ii, 5, tail=False, reset_probes=False)
        raw = simulate(rtl, ev, work / f'ii{ii}', 'verilator')
        out, lat = decode(raw, ev, meta)
        exp = gen.model(inputs, cfg)
        badf = np.flatnonzero(np.any(out != exp, axis=(1, 2)))
        bins = sorted(set(np.argwhere(np.any(out != exp, axis=2))[:, 1].tolist()))
        print(f'II={ii} bad_frames={badf.tolist()[:12]} bad_bins={bins}')
finally:
    shutil.rmtree(work, ignore_errors=True)
