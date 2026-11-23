"""Evaluate gen.model precision configs over many seeds (worst-frame SQNR).

python3 prec_eval.py NSEEDS  (configs defined below)
"""
import json
import sys
import numpy as np
sys.path.insert(0, '/mnt/DATA1/sj/FFT/Claude-Opus-5.5/FFT-Bench/work')
import gen
from fxmodel import frame_sqnr, test_frames

nseeds = int(sys.argv[1]) if len(sys.argv) > 1 else 8
seeds = [20261118] + [5000 + i for i in range(nseeds - 1)]
x, labels = test_frames(seeds)
labels = np.array(labels)
base = dict(gen.DEFAULT, altpol=1, exact_widths=1, clamp15=1)


def ev(name, **kw):
    cfg = dict(base)
    cfg.update(kw)
    y = gen.model(x, cfg)
    q, zok = frame_sqnr(x, y)
    f = gen.formats(cfg)
    worst_fam = sorted(((q[labels == l].min(), l) for l in np.unique(labels)))[:2]
    print(f'{name:34s} min={q.min():6.2f} p0.1={np.percentile(q, 0.1):6.2f} zero={zok} '
          f'bits={gen.storage_bits(cfg)} s6={f["s6"]} worst={[(round(a, 2), b[:24]) for a, b in worst_fam]}', flush=True)
    return q.min()


if __name__ == '__main__':
    print('frames', len(x))
    ev('A current')
    ev('B r6', bf_round=[0, 0, 0, 0, 0, 1])
    ev('C r6 m6=5', bf_round=[0, 0, 0, 0, 0, 1], m=[0, 1, 1, 1, 2, 2, 5])
    ev('D r6 m6=5 m0=1', bf_round=[0, 0, 0, 0, 0, 1], m=[1, 1, 1, 1, 2, 2, 5])
    ev('E r6 m6=5 m1=2', bf_round=[0, 0, 0, 0, 0, 1], m=[0, 2, 2, 2, 2, 2, 5], mA=2)
    ev('F r6 m6=5 tb=9', bf_round=[0, 0, 0, 0, 0, 1], m=[0, 1, 1, 1, 2, 2, 5], tb=9)
    ev('G r6 m6=5 mC=3', bf_round=[0, 0, 0, 0, 0, 1], m=[0, 1, 1, 1, 2, 2, 5], mC=3)
    ev('H r6 m6=5 m5=3,mC=3', bf_round=[0, 0, 0, 0, 0, 1], m=[0, 1, 1, 1, 2, 3, 5], mC=3)
    ev('I r all, m6=5', bf_round=[1, 1, 1, 1, 1, 1], m=[0, 1, 1, 1, 2, 2, 5])
    ev('J r6 m6=5 m3=2', bf_round=[0, 0, 0, 0, 0, 1], m=[0, 1, 1, 2, 2, 2, 5])
