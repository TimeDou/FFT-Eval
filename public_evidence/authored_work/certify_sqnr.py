"""SQNR certification for a generator config: many seeds + min-RMS directed stress.

python3 certify_sqnr.py CFG.json [NSEEDS]
"""
import json
import sys
import numpy as np
sys.path.insert(0, '/mnt/DATA1/sj/FFT/Claude-Opus-5.5/FFT-Bench/work')
import gen
from fxmodel import frame_sqnr, test_frames


def directed_min_rms():
    t = np.arange(64)
    frames, labels = [], []

    def add(z, lab):
        a = np.clip(np.rint(np.column_stack([z.real, z.imag]) * 32768), -16384, 16384).astype(np.int64)
        rms = np.sqrt(np.mean(np.sum((a / 32768.0) ** 2, axis=-1)))
        if rms >= 1 / 32:
            frames.append(a)
            labels.append(lab)

    phases = np.linspace(0, 2 * np.pi, 16, endpoint=False) + 0.0123
    for p in range(64):
        for ph in phases[::2]:
            z = np.zeros(64, complex)
            z[p] = 0.2501 * np.exp(1j * ph)
            add(z, 'impulse_minrms')
    for k in range(64):
        for ph in phases[::2]:
            add(0.03130 * np.exp(1j * (2 * np.pi * k * t / 64 + ph)), 'tone_minrms')
    for ph in phases:
        add(np.full(64, 0.03130 * np.exp(1j * ph)), 'dc_minrms')
        add(0.03130 * np.exp(1j * ph) * (-1.0) ** t, 'nyq_minrms')
    rng = np.random.default_rng(99)
    for _ in range(256):
        raw = rng.choice([725, 726, 727, 730])
        a = rng.choice([-raw, raw], (64, 2)).astype(np.int64)
        frames.append(a)
        labels.append('sign_minrms')
    return np.asarray(frames), labels


if __name__ == '__main__':
    cfg = dict(gen.DEFAULT)
    cfg.update(json.load(open(sys.argv[1])))
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 16
    seeds = [20261118] + [9000 + i for i in range(n - 1)]
    x, labels = test_frames(seeds)
    d, dl = directed_min_rms()
    x = np.concatenate([x, d])
    labels = np.array(list(labels) + dl)
    y = gen.model(x, cfg)
    q, zok = frame_sqnr(x, y)
    fam = sorted(((q[labels == l].min(), l) for l in np.unique(labels)))[:4]
    print(f'frames={len(x)} min={q.min():.3f} zero_ok={zok} worst families={[(round(a, 2), b) for a, b in fam]}')
