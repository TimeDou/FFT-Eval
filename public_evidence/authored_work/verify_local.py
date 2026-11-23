"""Local cycle-accurate verification with the benchmark's own scheduler/decoder.

Usage: python3 verify_local.py RTL.v CFG.json [backend] [intervals...]
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path
import numpy as np

sys.path.insert(0, '/mnt/DATA1/sj/FFT/Claude-Opus-5.5/FFT-Bench/fft64_benchmark/tools')
sys.path.insert(0, '/mnt/DATA1/sj/FFT/Claude-Opus-5.5/FFT-Bench/work')
import model as bench  # noqa
from simulate import schedule, simulate, decode  # noqa
from throughput import stream_schedule  # noqa
import gen  # noqa


def main():
    rtl = Path(sys.argv[1]).read_text()
    cfg = dict(gen.DEFAULT)
    cfg.update(json.loads(Path(sys.argv[2]).read_text()))
    backend = sys.argv[3] if len(sys.argv) > 3 else 'verilator'
    intervals = [int(v) for v in sys.argv[4:]] or [64, 65, 71, 100, 383, 384]
    frames, labels = bench.evaluation_frames(20261118, 1024)
    work = Path(tempfile.mkdtemp(prefix='fftv_', dir='/mnt/DATA1/sj/FFT/Claude-Opus-5.5/FFT-Bench/work'))
    ok = True
    try:
        # 1) the numerical schedule with reset probes and long gaps
        ev, meta = schedule(frames, 20261118 + 17)
        raw = simulate(rtl, ev, work / 'num', backend)
        out, lat = decode(raw, ev, meta)
        exp = gen.model(frames, cfg)
        same = np.array_equal(out, exp)
        q = bench.quality(frames, out)
        print(f'numerical: frames={len(frames)} bitexact={same} minSQNR={q["minimum_frame_sqnr_db"]:.3f} '
              f'feasible={q["feasible"]} zero_exact={q["zero_frame_exact"]} maxlat={lat["maximum_first_output_latency_cycles"]} '
              f'maxcomp={lat["maximum_frame_completion_cycles"]}')
        if not same:
            bad = np.argwhere(np.any(out != exp, axis=(1, 2)))[:5].ravel()
            print('  mismatching frames', bad, [labels[i] for i in bad])
            ok = False
        # 1b) extreme-corner stress frames (overflow hunting), bit-exact vs model
        rng = np.random.default_rng(7)
        vals = np.array([-16384, 16384, -16383, 16383, 0])
        stress = [rng.choice(vals[:4], size=(64, 2)) for _ in range(96)]
        for k in range(32):
            a = np.zeros((64, 2), dtype=np.int64)
            a[:, 0] = np.where(rng.random(64) < 0.5, -16384, 16384)
            a[:, 1] = np.where(rng.random(64) < 0.5, -16384, 16384)
            a[k::32] = [[-16384, -16384]] if k % 2 else [[16384, 16384]]
            stress.append(a)
        t = np.arange(64)
        for k in range(64):
            for ph in (0.0, 0.25, 0.5):
                z = 0.5 * np.exp(2j * np.pi * (k * t / 64 + ph))
                stress.append(np.clip(np.rint(np.column_stack([z.real, z.imag]) * 32768), -16384, 16384).astype(np.int64))
        stress = np.asarray(stress, dtype=np.int64)
        ev, meta, inputs = stream_schedule(stress, 64, 99, tail=False, reset_probes=False)
        raw = simulate(rtl, ev, work / 'stress', backend)
        out, lat = decode(raw, ev, meta)
        exp = gen.model(inputs, cfg)
        same = np.array_equal(out, exp)
        qs = bench.quality(inputs, out)
        print(f'stress: frames={len(inputs)} bitexact={same} minSQNR={qs["minimum_frame_sqnr_db"]:.2f}')
        ok &= same
        # 2) dense streams at several intervals, with reset probes + mixed gap tail
        for ii in intervals:
            sub = frames[:256]
            ev, meta, inputs = stream_schedule(sub, ii, 20261118 + 31)
            raw = simulate(rtl, ev, work / f'ii{ii}', backend)
            try:
                out, lat = decode(raw, ev, meta)
            except AssertionError as exc:
                print(f'II={ii}: PROTOCOL FAIL {exc}')
                ok = False
                continue
            exp = gen.model(inputs, cfg)
            same = np.array_equal(out, exp)
            print(f'II={ii}: frames={len(inputs)} bitexact={same} lat={lat["first_output_latency_cycles"]} '
                  f'comp_max={lat["maximum_frame_completion_cycles"]}')
            ok &= same
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print('ALL_OK' if ok else 'FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
