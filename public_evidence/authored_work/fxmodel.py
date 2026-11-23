"""Bit-accurate fixed-point model of a radix-2^3 DIF FFT64 (R2^3SDF ordering).

Values are integers in units of 2^m (m = current LSB exponent relative to
2^-15).  Position p of the in-place array follows the SDF stream order.
"""
import sys
import numpy as np

sys.path.insert(0, '/mnt/DATA1/sj/FFT/Claude-Opus-5.5/FFT-Bench/fft64_benchmark/tools')
import model as bench  # noqa: E402

P = np.arange(64)
BIT = lambda b: (P >> b) & 1
BITREV = np.array([int(f'{p:06b}'[::-1], 2) for p in range(64)])


def rshift(v, k, mode):
    """Drop k LSBs: 'floor' (truncate) or 'round' (half up) or 'rne'."""
    if k <= 0:
        return v << (-k)
    if mode == 'floor':
        return v >> k
    if mode == 'round':
        return (v + (1 << (k - 1))) >> k
    if mode == 'rne':
        q = v >> k
        r = v - (q << k)
        half = 1 << (k - 1)
        up = (r > half) | ((r == half) & ((q & 1) == 1))
        return q + up
    raise ValueError(mode)


def rot_trivial(re, im, q):
    """Multiply by (-j)^q, q in 0..3 (array)."""
    q = q & 3
    r0, i0 = re, im
    out_re = np.where(q == 0, r0, np.where(q == 1, i0, np.where(q == 2, -r0, -i0)))
    out_im = np.where(q == 0, i0, np.where(q == 1, -r0, np.where(q == 2, -i0, r0)))
    return out_re, out_im


class Cfg:
    def __init__(self, **kw):
        # LSB exponent after input (m[0]) and after each BF stage 1..6
        self.m = kw.get('m', [0, 0, 0, 0, 0, 0, 0])
        self.mode = kw.get('mode', ['round'] * 7)
        # W8 rotators (after stage 2 and 5): constant K/2^F ~ 1/sqrt2; output LSB delta
        self.k8 = kw.get('k8', 12)          # fractional bits of 1/sqrt(2)
        self.w8_mode = kw.get('w8_mode', 'round')
        # W64 twiddle multiplier after stage 3
        self.tb = kw.get('tb', 12)          # twiddle fractional bits
        self.tw_mode = kw.get('tw_mode', 'round')
        self.tw_round = kw.get('tw_round', 'round')  # how twiddles are quantized
        self.out_mode = kw.get('out_mode', 'round')
        self.exact = kw.get('exact', False)


def w8_mult(re, im, sel, cfg):
    """Multiply by W8^sel (sel 0..3 as stage-2 twiddle) with fixed point.

    W8^1 = (1-j)/sqrt2 : ((a+b) + j(b-a))/sqrt2
    W8^3 = (-1-j)/sqrt2: ((b-a) - j(a+b))/sqrt2
    W8^2 = -j
    """
    if cfg.exact:
        w = np.exp(-2j * np.pi * sel / 8)
        z = (re + 1j * im) * w
        return z.real, z.imag
    K = int(round((1 / np.sqrt(2)) * (1 << cfg.k8)))
    u = re + im      # a+b
    v = im - re      # b-a
    us = rshift(u * K, cfg.k8, cfg.w8_mode)
    vs = rshift(v * K, cfg.k8, cfg.w8_mode)
    out_re = np.where(sel == 0, re, np.where(sel == 1, us, np.where(sel == 2, im, vs)))
    out_im = np.where(sel == 0, im, np.where(sel == 1, vs, np.where(sel == 2, -re, -us)))
    return out_re, out_im


def twiddle_table(tb, how='round'):
    ang = -2 * np.pi * np.arange(64) / 64
    c, s = np.cos(ang), np.sin(ang)
    if how == 'round':
        return np.rint(c * (1 << tb)).astype(np.int64), np.rint(s * (1 << tb)).astype(np.int64)
    raise ValueError(how)


def w64_mult(re, im, e, cfg):
    if cfg.exact:
        z = (re + 1j * im) * np.exp(-2j * np.pi * e / 64)
        return z.real, z.imag
    C, S = twiddle_table(cfg.tb, cfg.tw_round)
    c, s = C[e], S[e]
    pr = re * c - im * s
    pi = re * s + im * c
    trivial = (e % 16) == 0
    tr_re, tr_im = rot_trivial(re, im, (e // 16))
    out_re = np.where(trivial, tr_re, rshift(pr, cfg.tb, cfg.tw_mode))
    out_im = np.where(trivial, tr_im, rshift(pi, cfg.tb, cfg.tw_mode))
    return out_re, out_im


def bf(re, im, b):
    D = 1 << b
    lo = (P >> b) & 1 == 0
    il = P[lo]
    ih = il + D
    nre, nim = re.copy(), im.copy()
    nre[:, il] = re[:, il] + re[:, ih]
    nim[:, il] = im[:, il] + im[:, ih]
    nre[:, ih] = re[:, il] - re[:, ih]
    nim[:, ih] = im[:, il] - im[:, ih]
    return nre, nim


def fft64(x, cfg):
    """x: (F,64,2) int input codes. Returns (F,64,2) output in 2^-15 units (float if exact)."""
    if cfg.exact:
        re = x[..., 0].astype(np.float64)
        im = x[..., 1].astype(np.float64)
        rsh = lambda v, k, mode: v
    else:
        re = x[..., 0].astype(np.int64)
        im = x[..., 1].astype(np.int64)
        rsh = rshift
    m = cfg.m
    re, im = rsh(re, m[0], cfg.mode[0]), rsh(im, m[0], cfg.mode[0])
    cur = m[0]
    for s in range(1, 7):
        b = 6 - s
        re, im = bf(re, im, b)
        re, im = rsh(re, m[s] - cur, cfg.mode[s]), rsh(im, m[s] - cur, cfg.mode[s])
        cur = m[s]
        if s == 1:
            re, im = rot_trivial(re, im, BIT(4) * BIT(5))
        elif s == 2:
            re, im = w8_mult(re, im, BIT(3) * (BIT(5) + 2 * BIT(4)), cfg)
        elif s == 3:
            re, im = w64_mult(re, im, (P & 7) * (BIT(5) + 2 * BIT(4) + 4 * BIT(3)), cfg)
        elif s == 4:
            re, im = rot_trivial(re, im, BIT(1) * BIT(2))
        elif s == 5:
            re, im = w8_mult(re, im, BIT(0) * (BIT(2) + 2 * BIT(1)), cfg)
    out = np.empty(x.shape, dtype=np.float64 if cfg.exact else np.int64)
    scale = (1 << cur) if cur >= 0 else 1.0 / (1 << -cur)
    out[:, BITREV, 0] = re * scale
    out[:, BITREV, 1] = im * scale
    return out


def frame_sqnr(x, y):
    ref = bench.reference(x)
    pred = (y[..., 0] + 1j * y[..., 1]) / 32768
    e = np.sum(np.abs(pred - ref) ** 2, -1)
    s = np.sum(np.abs(ref) ** 2, -1)
    nz = s > 0
    q = np.full(len(x), np.inf)
    q[nz & (e > 0)] = -10 * np.log10(e[nz & (e > 0)] / s[nz & (e > 0)])
    zero_ok = bool(np.all(y[~nz] == 0))
    return q, zero_ok


def test_frames(seeds=(20261118,), count=1024):
    xs, labels = [], []
    for sd in seeds:
        f, l = bench.evaluation_frames(sd, count)
        xs.append(f)
        labels += l
        f2, l2 = bench.make_frames(sd ^ 0x5bd1e995, 1)
        xs.append(f2)
        labels += l2
    return np.concatenate(xs), labels


if __name__ == '__main__':
    x, labels = test_frames()
    y = fft64(x, Cfg(exact=True))
    ref = bench.reference(x) * 32768
    err = np.abs((y[..., 0] + 1j * y[..., 1]) - ref).max()
    print('exact-structure max abs error (LSB):', err)
