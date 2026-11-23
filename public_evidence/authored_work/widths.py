"""Exact signed-width analysis for the generated R2^3 SDF datapath.

Range at a point = extremes of the (quantized-coefficient) linear map over the
input box + a bound on all upstream quantization errors propagated with the
L1 gain of the downstream linear map.  Returns per-point (width, lsb).
"""
import math
import numpy as np

P = np.arange(64)
BIT = lambda p, b: (p >> b) & 1

POINTS = ['inp', 's1', 's2', 'w8a', 's3', 'w64', 's4', 's5', 'w8b', 's6']


def _tw_index(p):
    return (p & 7) * (BIT(p, 5) + 2 * BIT(p, 4) + 4 * BIT(p, 3))


def _ops(cfg, twc):
    """List of (point_name_or_None, function(z)->z) on complex arrays (...,64)."""
    K = twc['K8']
    w8f = K * (1 - 1j)

    def bf(b):
        D = 1 << b
        lo = P[(P >> b) & 1 == 0]
        hi = lo + D

        def f(z):
            n = z.copy()
            n[..., lo] = z[..., lo] + z[..., hi]
            n[..., hi] = z[..., lo] - z[..., hi]
            return n
        return f

    def jrot(cond):
        c = cond.astype(bool)

        def f(z):
            return np.where(c, -1j * z, z)
        return f

    def w8(sel):
        mult = np.select([sel == 0, sel == 1, sel == 2, sel == 3], [1.0 + 0j, w8f, -1j, -1j * w8f])

        def f(z):
            return z * mult
        return f

    e = _tw_index(P)
    tw = np.array([twc['W'][int(k)] for k in e])

    def w64(z):
        return z * tw

    return [
        ('s1', bf(5)),
        (None, jrot(BIT(P, 5) & BIT(P, 4))),
        ('s2', bf(4)),
        ('w8a', w8(BIT(P, 3) * (BIT(P, 5) + 2 * BIT(P, 4)))),
        ('s3', bf(3)),
        ('w64', w64),
        ('s4', bf(2)),
        (None, jrot(BIT(P, 1) & BIT(P, 2))),
        ('s5', bf(1)),
        ('w8b', w8(BIT(P, 0) * (BIT(P, 2) + 2 * BIT(P, 1)))),
        ('s6', bf(0)),
    ]


def _maps(ops, start_after=None):
    """Complex 64x64 maps from point start_after (or input) to each later point."""
    z = np.eye(64, dtype=complex)  # row r = unit impulse at position r
    started = start_after is None
    out = {}
    if started:
        out['inp'] = z.T.copy()
    for name, f in ops:
        if not started:
            if name == start_after:
                started = True
            continue
        z = f(z)
        if name:
            out[name] = z.T.copy()   # A[p, n]
    return out


def _skip_until(ops, name):
    idx = [i for i, (n, _) in enumerate(ops) if n == name][0]
    return ops[idx + 1:]


def analyze(cfg, lsb, modes, twc, in_lo=-16384, in_hi=16384):
    """lsb: dict point->m ; modes: dict point->('floor'|'round'|'mult')."""
    ops = _ops(cfg, twc)
    A = _maps(ops)
    # quantization error magnitude bound at each point (absolute units of 2^-15)
    E = {}
    prev = {'s1': 'inp', 's2': 's1', 'w8a': 's2', 's3': 'w8a', 'w64': 's3',
            's4': 'w64', 's5': 's4', 'w8b': 's5', 's6': 'w8b'}
    E['inp'] = (2 ** lsb['inp'] - 1) if lsb['inp'] > 0 else 0.0
    for p in POINTS[1:]:
        m_in, m_out = lsb[prev[p]], lsb[p]
        if modes[p] == 'floor':
            E[p] = 2.0 ** m_out - 2.0 ** m_in if m_out > m_in else 0.0
        elif modes[p] == 'round':
            E[p] = 2.0 ** (m_out - 1) if m_out > m_in else 0.0
        else:  # rounded product (and floor-shifted trivial path)
            E[p] = max(2.0 ** (m_out - 1), 2.0 ** m_out - 2.0 ** m_in)
    # L1 gains between points
    G = {}
    for q in POINTS:
        rest = ops if q == 'inp' else _skip_until(ops, q)
        Bq = _maps(rest, None)
        for p, B in Bq.items():
            if p == 'inp':
                continue
            G[(q, p)] = float(np.max(np.sum(np.abs(B.real) + np.abs(B.imag), axis=1)))
    # Exact integer intervals for the pre-rotation stages (disjoint input sets,
    # no re/im mixing): inp -> s1 -> (-j) -> s2.
    def q_int(lo, hi, k, mode):
        if k <= 0:
            return lo << (-k) if k < 0 else lo, hi << (-k) if k < 0 else hi
        if mode == 'round':
            h = 1 << (k - 1)
            return (lo + h) >> k, (hi + h) >> k
        return lo >> k, hi >> k
    exact = {}
    ilo, ihi = q_int(in_lo, in_hi, lsb['inp'], 'floor')
    exact['inp'] = (ilo, ihi)
    k1 = lsb['s1'] - lsb['inp']
    s1lo, s1hi = q_int(2 * ilo, 2 * ihi, k1, modes['s1'])           # sum
    d1lo, d1hi = q_int(ilo - ihi, ihi - ilo, k1, modes['s1'])        # difference
    s1 = (min(s1lo, d1lo), max(s1hi, d1hi))
    exact['s1'] = s1
    j2 = (min(s1[0], -s1[1]), max(s1[1], -s1[0]))                     # after optional -j
    exact['j2'] = j2
    k2 = lsb['s2'] - lsb['s1']
    a2lo, a2hi = q_int(s1[0] + j2[0], s1[1] + j2[1], k2, modes['s2'])
    b2lo, b2hi = q_int(s1[0] - j2[1], s1[1] - j2[0], k2, modes['s2'])
    exact['s2'] = (min(a2lo, b2lo), max(a2hi, b2hi))

    def wfor(qlo, qhi):
        w = 1
        while not (-(1 << (w - 1)) <= qlo and qhi <= (1 << (w - 1)) - 1):
            w += 1
        return w
    res = {}
    for p in POINTS:
        Ap = A[p]
        # real component coefficients over (re_n, im_n): (Re A, -Im A); imag: (Im A, Re A)
        rows = []
        for cr, ci in [(Ap.real, -Ap.imag), (Ap.imag, Ap.real)]:
            c = np.concatenate([cr, ci], axis=1)
            hi = np.sum(np.where(c > 0, c * in_hi, c * in_lo), axis=1)
            lo = np.sum(np.where(c > 0, c * in_lo, c * in_hi), axis=1)
            rows.append((lo.min(), hi.max()))
        lin_lo = min(r[0] for r in rows)
        lin_hi = max(r[1] for r in rows)
        err = sum(E[q] * G[(q, p)] for q in POINTS if (q, p) in G and POINTS.index(q) < POINTS.index(p))
        lo, hi = lin_lo - err, lin_hi + err
        m = lsb[p]
        scale = 2.0 ** m
        if modes.get(p) == 'round' or modes.get(p) == 'mult':
            qlo, qhi = math.floor(lo / scale + 0.5), math.floor(hi / scale + 0.5)
        else:
            qlo, qhi = math.floor(lo / scale), math.floor(hi / scale)
        w = 1
        while not (-(1 << (w - 1)) <= qlo and qhi <= (1 << (w - 1)) - 1):
            w += 1
        if p in exact:
            qlo, qhi = exact[p]
            w = wfor(qlo, qhi)
        res[p] = dict(width=w, lsb=m, lin=(lin_lo, lin_hi), err=err, q=(qlo, qhi))
    res['j2'] = dict(width=wfor(*exact['j2']), lsb=lsb['s1'], q=exact['j2'])
    s4q = res['s4']['q']
    j5 = (min(s4q[0], -s4q[1]), max(s4q[1], -s4q[0]))
    res['j5'] = dict(width=wfor(*j5), lsb=lsb['s4'], q=j5)
    return res
