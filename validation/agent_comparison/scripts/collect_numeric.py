"""Preserve actual hidden RTL observations and independently replay numerical QoR."""
from pathlib import Path
import numpy as np
import worker
from common import read, save, sha
from model import evaluation_frames, quality
from simulate import schedule, decode

ROOT = Path(__file__).resolve().parent


if __name__ == '__main__':
    campaign = read(ROOT/'campaign.json')
    frames, labels = evaluation_frames(campaign['seed'], 8192)
    events, meta = schedule(frames, campaign['seed']+17)
    out = ROOT/'numeric_evidence'
    out.mkdir(exist_ok=True)
    if not (out/'inputs.npz').exists():
        np.savez_compressed(out/'inputs.npz', inputs=frames.astype(np.int16), labels=np.asarray(labels))
    save(out/'format.json', dict(fft_length=64, fractional_bits=15, components='real, imaginary',
         independent_random_nonzero_frames=8192, directed_frames=192,
         reference='float64 FFT of the same quantized input', inputs_sha256=sha(out/'inputs.npz'),
         scope='Actual numerical RTL observations; capacity and mapped checks are separate'))
    for case in campaign['cases']:
        name = case['id']
        directory = ROOT/'measurements'/name
        archive = out/(name+'.npz')
        if archive.exists():
            continue
        receipt = read(directory/'rtl_sim/receipt.json')
        rawpath = directory/'rtl_sim/output.txt'
        assert sha(rawpath) == receipt['output_sha256'], name
        raw = np.loadtxt(rawpath, dtype=np.int64, ndmin=2)
        outputs, latency = decode(raw, events, meta)
        q = quality(frames, outputs)
        rows = read(directory/'per_frame_quality.json')
        minimum = min(r['sqnr_db'] for r in rows if r['sqnr_db'] is not None)
        assert abs(q['minimum_frame_sqnr_db']-minimum) < 1e-8, name
        np.savez_compressed(archive, outputs=outputs.astype(np.int32),
            first_latency_cycles=np.asarray(latency['per_frame_first_output_latency_cycles'], dtype=np.int32),
            completion_cycles=np.asarray(latency['per_frame_completion_cycles'], dtype=np.int32))
        save(out/(name+'.json'), dict(quality=q, independent_qor_replay='PASS',
            compact_archive_sha256=sha(archive), original_vectors_sha256=receipt['input_sha256'],
            original_observation_sha256=receipt['output_sha256'], source_sha256=case['source_sha256']))
        print(name, q['minimum_frame_sqnr_db'], 'PASS', flush=True)
        del raw, outputs
