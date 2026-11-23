"""Worst-frame SQNR (extended certification set) for precision variants of v2c."""
import json
import sys
import numpy as np
sys.path.insert(0, '/mnt/DATA1/sj/FFT/Claude-Opus-5.5/FFT-Bench/work')
import gen
from fxmodel import frame_sqnr, test_frames
from certify_sqnr import directed_min_rms

n = int(sys.argv[1]) if len(sys.argv) > 1 else 16
seeds = [20261118] + [9000 + i for i in range(n - 1)]
x, labels = test_frames(seeds)
d, dl = directed_min_rms()
x = np.concatenate([x, d])
base = json.load(open('cfg_v2c.json'))

variants = {
    'v4a': dict(m=[0, 1, 1, 2, 2, 3, 5], mA=1, mB=2, mC=3),
    'r3 m3=3 mB=3': dict(m=[0, 1, 1, 3, 3, 3, 5], mA=1, mB=3, mC=3, bf_round=[0, 0, 1, 0, 0, 1]),
    'r3 m3=3 mB=3 mA=2': dict(m=[0, 1, 1, 3, 3, 3, 5], mA=2, mB=3, mC=3, bf_round=[0, 0, 1, 0, 0, 1]),
    'r3 m3=3 mB=3 tb10': dict(m=[0, 1, 1, 3, 3, 3, 5], mA=1, mB=3, mC=3, bf_round=[0, 0, 1, 0, 0, 1], tb=10),
    'r3r1 m3=3 mB=3': dict(m=[0, 1, 1, 3, 3, 3, 5], mA=1, mB=3, mC=3, bf_round=[1, 0, 1, 0, 0, 1]),
    'r35 m3=3,m5=3': dict(m=[0, 1, 1, 3, 3, 3, 5], mA=1, mB=3, mC=3, bf_round=[0, 0, 1, 0, 1, 1]),
    'r3 m3=3 mB=2': dict(m=[0, 1, 1, 3, 3, 3, 5], mA=1, mB=2, mC=3, bf_round=[0, 0, 1, 0, 0, 1]),
}
for name, upd in variants.items():
    cfg = dict(gen.DEFAULT)
    cfg.update(base)
    cfg.update(upd)
    try:
        f = gen.formats(cfg)
    except AssertionError as exc:
        print(name, 'invalid', exc)
        continue
    y = gen.model(x, cfg)
    q, zok = frame_sqnr(x, y)
    print(f'{name:22s} min={q.min():6.2f} p0.1={np.percentile(q, 0.1):6.2f} zero={zok} bits={gen.storage_bits(cfg)} '
          f's3={f["s3"][0]} w64={f["w64"][0]} s4={f["s4"][0]} s5={f["s5"][0]} w8b={f["w8b"][0]} s6={f["s6"][0]}', flush=True)
