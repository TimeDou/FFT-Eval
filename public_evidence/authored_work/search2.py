"""Precision search on the bit-exact generator model (flop count vs worst SQNR)."""
import itertools
import json
import sys
import numpy as np
sys.path.insert(0, '/mnt/DATA1/sj/FFT/Claude-Opus-5.5/FFT-Bench/work')
import gen
from fxmodel import frame_sqnr, test_frames

THRESH = float(sys.argv[1]) if len(sys.argv) > 1 else 53.0
x, _ = test_frames([20261118, 7, 11, 13])
base = dict(gen.DEFAULT, altpol=1, exact_widths=1, clamp15=1)

cands = []
for m0 in (0, 1):
    for steps in itertools.product((0, 1), repeat=5):
        m = [m0]
        for st in steps:
            m.append(m[-1] + st)
        for m6 in (m[5] + 1, m[5] + 2, m[5] + 3):
            mm = m + [m6]
            for a, b, c in itertools.product((0, 1), repeat=3):
                for r6 in (0, 1):
                    cfg = dict(base, m=mm, mA=mm[2] + a, mB=mm[3] + b, mC=mm[5] + c,
                               bf_round=[0, 0, 0, 0, 0, r6])
                    if cfg['mA'] > mm[3] or cfg['mB'] > mm[4] or cfg['mC'] > mm[6]:
                        continue
                    cands.append(cfg)
print('candidates', len(cands), flush=True)
scored = []
for cfg in cands:
    try:
        scored.append((gen.storage_bits(cfg), cfg))
    except AssertionError:
        pass
scored.sort(key=lambda t: t[0])
good = []
for bits, cfg in scored:
    y = gen.model(x, cfg)
    q, zok = frame_sqnr(x, y)
    if q.min() >= THRESH and zok:
        good.append(dict(bits=bits, sqnr=round(float(q.min()), 3), m=cfg['m'], mA=cfg['mA'], mB=cfg['mB'],
                         mC=cfg['mC'], r6=cfg['bf_round'][5]))
        print(good[-1], flush=True)
        if len(good) >= 20:
            break
json.dump(good, open(f'search2_{THRESH}.json', 'w'), indent=1)
