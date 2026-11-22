"""Preserve and independently decode actual hidden numerical observations."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

ROOT=Path(Path('/tmp/fft_final_agent_review_path.txt').read_text().strip())
sys.path.insert(0,str(ROOT/'engine_private/fft64_benchmark/tools'))
from model import evaluation_frames,quality
from simulate import schedule,decode


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    campaign=json.loads((ROOT/'campaign.json').read_text())
    protocol=json.loads((ROOT/'private_protocol.json').read_text())
    frames,labels=evaluation_frames(protocol['seed'],8192)
    events,metadata=schedule(frames,protocol['seed']+17)
    out=ROOT/'numerical_replay';out.mkdir(exist_ok=True)
    np.savez_compressed(out/'inputs.npz',inputs=frames,labels=labels)
    records=[]
    for case in campaign['cases']:
        source=next((ROOT/'evaluation/candidates'/case['id']/'runs').glob('*/rtl_sim/output.txt'))
        raw=np.loadtxt(source,dtype=np.int64,ndmin=2)
        assert raw.shape==(len(events),5)
        assert np.array_equal(raw[:,0],np.arange(len(events)))
        outputs,latency=decode(raw,events,metadata)
        q=quality(frames,outputs)
        assert q['feasible'] and q['zero_frame_exact']
        receipt=json.loads((source.parent/'receipt.json').read_text())
        assert sha(source)==receipt['output_sha256']
        assert receipt['signature']['source_sha256']==case['source_sha256']
        archive=out/(case['id']+'.npz')
        np.savez_compressed(archive,outputs=outputs)
        observed=dict(agent=case['id'],quality=q,latency=latency,
            compact_archive_sha256=sha(archive),original_receipt=receipt,
            original_output_path=str(source),source_sha256=case['source_sha256'],
            independent_frames=8192,directed_frames=192,
            scope='Decoded actual VCS output; original byte hash matches native simulator receipt; numerical/protocol replay without additional EDA execution')
        (out/(case['id']+'.json')).write_text(json.dumps(observed,indent=2)+'\n')
        records.append(dict(agent=case['id'],minimum_sqnr_db=q['minimum_frame_sqnr_db'],
                            output_archive_sha256=sha(archive),status='PASS'))
        del raw,outputs
    (out/'summary.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(records,indent=2))


if __name__=='__main__':main()
