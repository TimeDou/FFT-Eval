import sys, json
import numpy as np
from search import fft64, storage, widths
from fxmodel import frame_sqnr, test_frames

nseeds = int(sys.argv[1]) if len(sys.argv) > 1 else 16
seeds = [20261118] + [1000 + i for i in range(nseeds - 1)]
x, labels = test_frames(seeds)
labels = np.array(labels)
print('frames', len(x), 'seeds', nseeds)
cands = [
    (([0, 1, 2, 2, 2, 2, 4], 2, 2, 2), 10),
    (([0, 1, 1, 2, 2, 2, 4], 1, 2, 2), 10),
    (([0, 1, 1, 2, 2, 2, 4], 1, 2, 2), 9),
    (([0, 1, 1, 1, 2, 3, 4], 1, 1, 3), 10),
    (([0, 1, 1, 1, 2, 3, 4], 1, 2, 3), 10),
    (([0, 1, 1, 2, 2, 3, 4], 1, 2, 3), 10),
    (([0, 1, 1, 1, 2, 2, 4], 1, 2, 2), 10),
    (([0, 1, 1, 1, 2, 2, 4], 1, 2, 2), 9),
    (([0, 0, 1, 1, 2, 2, 4], 1, 2, 2), 10),
    (([0, 1, 1, 1, 2, 2, 3], 1, 2, 2), 10),
]
for cand, tb in cands:
    y = fft64(x, *cand, tb=tb)
    q, zok = frame_sqnr(x, y)
    fam = {}
    for lab in np.unique(labels):
        fam[lab] = q[labels == lab].min()
    worst = sorted(fam.items(), key=lambda t: t[1])[:2]
    print(storage(*cand), cand, 'tb', tb, f'min={q.min():.2f} p0.1={np.percentile(q,0.1):.2f} p1={np.percentile(q,1):.2f}', zok, [(a[:26], round(b, 2)) for a, b in worst])
