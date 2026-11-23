"""Search per-stage LSB schedules: storage bits vs minimum frame SQNR."""
import itertools, sys, json
import numpy as np
import fxmodel as fm
from fxmodel import Cfg, frame_sqnr, test_frames, bf, rot_trivial, BIT, P, rshift, BITREV

BOUND = dict(inp=16384, s1=32768, s2=65536, w8a=79109, s3=158218, w64=166350,
             s4=332700, s5=665399, w8b=667008, s6=1334016)


def bits(name, m, guard=1.002):
    b = BOUND[name] * guard / (1 << m)
    n = 1
    while not (-(1 << (n - 1)) <= -np.ceil(b) and np.floor(b) <= (1 << (n - 1)) - 1):
        n += 1
    return n


def fft64(x, m, mA, mB, mC, k8=8, tb=10, bf_mode='floor', tw_mode='round', w8_mode='round'):
    re = x[..., 0].astype(np.int64); im = x[..., 1].astype(np.int64)
    re, im = rshift(re, m[0], bf_mode), rshift(im, m[0], bf_mode)
    cur = m[0]
    K8 = int(round((1 << k8) / np.sqrt(2)))
    C = np.rint(np.cos(-2 * np.pi * np.arange(64) / 64) * (1 << tb)).astype(np.int64)
    S = np.rint(np.sin(-2 * np.pi * np.arange(64) / 64) * (1 << tb)).astype(np.int64)
    for s in range(1, 7):
        re, im = bf(re, im, 6 - s)
        re, im = rshift(re, m[s] - cur, bf_mode), rshift(im, m[s] - cur, bf_mode)
        cur = m[s]
        if s in (1, 4):
            q = BIT(4) * BIT(5) if s == 1 else BIT(1) * BIT(2)
            re, im = rot_trivial(re, im, q)
        elif s in (2, 5):
            sel = BIT(3) * (BIT(5) + 2 * BIT(4)) if s == 2 else BIT(0) * (BIT(2) + 2 * BIT(1))
            mo = mA if s == 2 else mC
            d = mo - cur
            u = re + im; v = im - re
            us = rshift(u * K8, k8 + d, w8_mode); vs = rshift(v * K8, k8 + d, w8_mode)
            tr, ti = rshift(re, d, bf_mode), rshift(im, d, bf_mode)
            nre = np.where(sel == 0, tr, np.where(sel == 1, us, np.where(sel == 2, ti, vs)))
            nim = np.where(sel == 0, ti, np.where(sel == 1, vs, np.where(sel == 2, -tr, -us)))
            re, im = nre, nim
            cur = mo
        elif s == 3:
            e = (P & 7) * (BIT(5) + 2 * BIT(4) + 4 * BIT(3))
            d = mB - cur
            c, sn = C[e], S[e]
            pr = re * c - im * sn; pi = re * sn + im * c
            triv = (e % 16) == 0
            tr, ti = rot_trivial(rshift(re, d, bf_mode), rshift(im, d, bf_mode), e // 16)
            re = np.where(triv, tr, rshift(pr, tb + d, tw_mode))
            im = np.where(triv, ti, rshift(pi, tb + d, tw_mode))
            cur = mB
    out = np.empty(x.shape, dtype=np.int64)
    out[:, BITREV, 0] = re << cur
    out[:, BITREV, 1] = im << cur
    return out


def storage(m, mA, mB, mC):
    s = 0
    s += 32 * max(bits('inp', m[0]), bits('s1', m[1]))
    s += 16 * max(bits('s1', m[1]), bits('s2', m[2]))
    s += 8 * max(bits('w8a', mA), bits('s3', m[3]))
    s += 4 * max(bits('w64', mB), bits('s4', m[4]))
    s += 2 * max(bits('s4', m[4]), bits('s5', m[5]))
    s += 1 * max(bits('w8b', mC), bits('s6', m[6]))
    s += 49 * bits('s6', m[6])
    return s


def widths(m, mA, mB, mC):
    return dict(inp=bits('inp', m[0]), s1=bits('s1', m[1]), s2=bits('s2', m[2]), w8a=bits('w8a', mA),
                s3=bits('s3', m[3]), w64=bits('w64', mB), s4=bits('s4', m[4]), s5=bits('s5', m[5]),
                w8b=bits('w8b', mC), s6=bits('s6', m[6]))


def evaluate(x, cand, **kw):
    y = fft64(x, *cand, **kw)
    q, zok = frame_sqnr(x, y)
    return q.min(), zok


if __name__ == '__main__':
    xq, _ = test_frames([20261118, 7])
    cands = []
    for m0 in (0, 1):
        for steps in itertools.product((0, 1, 2), repeat=6):
            m = [m0]
            for st in steps:
                m.append(m[-1] + st)
            if m[6] > 5:
                continue
            for a, b, c in itertools.product((0, 1), repeat=3):
                cand = (m, m[2] + a, m[3] + b, m[5] + c)
                cands.append((storage(*cand), cand))
    cands.sort(key=lambda t: t[0])
    print('candidates', len(cands))
    good = []
    for st, cand in cands:
        mn, zok = evaluate(xq, cand)
        if mn >= 52.5 and zok:
            good.append((st, cand, mn))
            print(st, cand, round(mn, 2), widths(*cand), flush=True)
        if len(good) >= 25:
            break
    json.dump([(s, c, mn) for s, c, mn in good], open('good.json', 'w'))
