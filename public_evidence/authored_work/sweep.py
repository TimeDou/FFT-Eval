import sys, itertools
import numpy as np
from fxmodel import Cfg, fft64, frame_sqnr, test_frames

seeds = [int(s) for s in sys.argv[1].split(',')] if len(sys.argv) > 1 else [20261118, 1, 2, 3]
x, labels = test_frames(seeds)
labels = np.array(labels)
print('frames', len(x))


def run(name, **kw):
    cfg = Cfg(**kw)
    y = fft64(x, cfg)
    q, zok = frame_sqnr(x, y)
    i = np.argmin(q)
    fam = {}
    for lab in set(labels):
        sel = labels == lab
        fam[lab] = q[sel].min()
    worst = sorted(fam.items(), key=lambda t: t[1])[:3]
    print(f'{name:40s} min={q.min():6.2f} p01={np.percentile(q,1):6.2f} med={np.median(q[np.isfinite(q)]):6.2f} zero_ok={zok} worst={[(a[:28], round(b,2)) for a,b in worst]}')
    return q


if __name__ == '__main__':
    run('ideal-ish tb16 k8=16', m=[0]*7, tb=16, k8=16)
    for tb in [8, 9, 10, 11, 12]:
        run(f'm=0 tb={tb}', m=[0]*7, tb=tb, k8=16)
    for k8 in [7, 8, 9, 10, 11]:
        run(f'm=0 k8={k8}', m=[0]*7, tb=16, k8=k8)
    for m in [[0,1,1,2,2,3,4],[0,1,2,2,3,3,4],[0,1,1,2,3,3,4],[0,1,2,3,3,4,4],[0,0,1,1,2,2,3],[1,1,2,2,3,3,4],[0,1,2,3,4,4,4]]:
        for mode in ['floor', 'round']:
            run(f'm={m} {mode}', m=m, mode=[mode]*7, tb=16, k8=16)
