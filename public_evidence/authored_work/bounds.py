"""Worst-case component magnitudes at each pipeline point (exact arithmetic)."""
import numpy as np
from fxmodel import Cfg, bf, rot_trivial, w8_mult, w64_mult, BIT, P

B = 16384.0


def stage_points():
    """Return dict name -> (64x64 complex coefficient matrix)."""
    cfg = Cfg(exact=True)
    eye = np.eye(64)
    re = eye.copy(); im = np.zeros((64, 64))
    pts = {}
    pts['in'] = (re + 1j * im).T
    for s in range(1, 7):
        re, im = bf(re, im, 6 - s)
        pts[f's{s}'] = (re + 1j * im).T
        if s == 1:
            re, im = rot_trivial(re, im, BIT(4) * BIT(5))
        elif s == 2:
            re, im = w8_mult(re, im, BIT(3) * (BIT(5) + 2 * BIT(4)), cfg)
            pts['w8a'] = (re + 1j * im).T
        elif s == 3:
            re, im = w64_mult(re, im, (P & 7) * (BIT(5) + 2 * BIT(4) + 4 * BIT(3)), cfg)
            pts['w64'] = (re + 1j * im).T
        elif s == 4:
            re, im = rot_trivial(re, im, BIT(1) * BIT(2))
        elif s == 5:
            re, im = w8_mult(re, im, BIT(0) * (BIT(2) + 2 * BIT(1)), cfg)
            pts['w8b'] = (re + 1j * im).T
    return pts


if __name__ == '__main__':
    pts = stage_points()
    for name, A in pts.items():
        # rows: positions p, cols: input n ; A[p, n]
        A = A.T if name != 'in' else A
        bound = B * np.max(np.sum(np.abs(A.real) + np.abs(A.imag), axis=1))
        bits = int(np.ceil(np.log2(bound + 1))) + 1
        print(f'{name:5s} max|comp| = {bound:12.1f}  log2={np.log2(bound):6.3f}  signed bits @LSB0 = {bits}')
