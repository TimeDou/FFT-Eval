"""Archive compact, actually observed FFT outputs for independent QoR checks."""
from pathlib import Path
import json,sys
import worker
import numpy as np
from common import read,save,sha
from model import evaluation_frames,quality
from simulate import schedule,decode

ROOT=Path(__file__).resolve().parent


if __name__=='__main__':
    protocol=read(ROOT/'campaign.json');frames,labels=evaluation_frames(protocol['seed'],8192)
    events,meta=schedule(frames,protocol['seed']+17)
    out=ROOT/'numeric_evidence';out.mkdir(exist_ok=True)
    if not(out/'inputs.npz').exists():np.savez_compressed(out/'inputs.npz',inputs=frames.astype(np.int16),labels=np.asarray(labels),frame_starts=np.asarray(meta['frame_starts'],dtype=np.int64))
    save(out/'format.json',dict(fft_length=64,fractional_bits=15,input_dtype='int16',output_dtype='int32',
        components='last axis: real, imaginary',reference='float64 FFT of the same quantized input',
        random_nonzero_frames=8192,directed_frames=192,inputs_sha256=sha(out/'inputs.npz'),
        scope='Actual numerical RTL observations; mapped and capacity proof are stored separately'))
    paths=[(c['id'],ROOT/'measurements'/c['id'])for c in protocol['cases']]
    paths.extend((c['id'],ROOT/'supplementary'/c['id']/'measurement')for c in read(ROOT/'supplementary_cases.json')['cases'])
    for name,path in paths:
        target=out/(name+'.npz')
        if target.exists():continue
        receipt=path/'rtl_sim/receipt.json'
        if not receipt.exists()or not(path/'per_frame_quality.json').exists():continue
        record=read(receipt);rawfile=path/'rtl_sim/output.txt'
        if sha(rawfile)!=record['output_sha256']:raise RuntimeError('Observation changed: '+name)
        raw=np.loadtxt(rawfile,dtype=np.int64,ndmin=2)
        outputs,latency=decode(raw,events,meta);q=quality(frames,outputs)
        stored=read(path/'per_frame_quality.json')
        reference_min=min(row['sqnr_db']for row in stored if row['sqnr_db']is not None)
        if abs(q['minimum_frame_sqnr_db']-reference_min)>1e-8:raise RuntimeError('QoR replay mismatch: '+name)
        np.savez_compressed(target,outputs=outputs.astype(np.int32),
            first_latency_cycles=np.asarray(latency['per_frame_first_output_latency_cycles'],dtype=np.int32),
            completion_cycles=np.asarray(latency['per_frame_completion_cycles'],dtype=np.int32))
        save(out/(name+'.json'),dict(quality=q,source_sha256=record['signature']['source_sha256'],
            original_observation_sha256=record['output_sha256'],original_vectors_sha256=record['input_sha256'],
            compact_archive_sha256=sha(target),independent_qor_replay='PASS'))
        print(name,q['minimum_frame_sqnr_db'],q['feasible'],flush=True)
        del raw,outputs
