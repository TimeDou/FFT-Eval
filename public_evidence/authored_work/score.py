"""Public architecture-profile score (same formulas as fft64_benchmark/tools/scoring.py)."""
import math
import sys


def score(A, P, L, II=64):
    sa = min(1.0, 3500.0 / (A + 3000.0)) if A > 500 else 1.0
    t = 1e9 / (II * P)
    st = min(1.0, max(0.0, math.log(t / (1e9 / 3840.0)) / math.log(240.0)))
    sl = min(1.0, max(0.0, (300.0 - L) / 237.0))
    return dict(S=0.6 * sa + 0.3 * st + 0.1 * sl, SA=sa, ST=st, SL=sl,
                wA=0.6 * sa, wT=0.3 * st, wL=0.1 * sl)


if __name__ == '__main__':
    A, P, L = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
    II = int(sys.argv[4]) if len(sys.argv) > 4 else 64
    r = score(A, P, L, II)
    print(' '.join(f'{k}={v:.4f}' for k, v in r.items()))
