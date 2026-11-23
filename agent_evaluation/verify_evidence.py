"""Verify archived files and scoring arithmetic; does not rerun EDA."""
from pathlib import Path
import hashlib
import json
import sys
import math
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def main():
    record=json.loads((ROOT/'CURRENT_RUN_MANIFEST.json').read_text())
    for relative,item in record['files'].items():
        path=ROOT/relative
        assert path.is_file(),relative
        assert path.stat().st_size==item['bytes'],relative
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],relative
    evaluator=next(p for p in [ROOT,*ROOT.parents]if(p/'fft64_benchmark/tools/scoring.py').is_file())
    sys.path.insert(0,str(evaluator/'fft64_benchmark/tools'))
    from scoring import score_result
    from model import evaluation_frames,quality
    from evaluate import assemble
    result=json.loads((ROOT/'agent_evaluation/measurement/result.json').read_text())
    calibration=json.loads((ROOT/'agent_evaluation/calibration.json').read_text())
    grade=score_result(result,calibration)
    assert grade['resolved']and grade['score_valid']and grade['official_score']
    assert abs(grade['score']-result['grade']['score'])<1e-12
    metadata=json.loads((ROOT/'run_metadata.json').read_text())
    assert result['source']['source_sha256']==metadata['source_sha256']
    assert result['source']['implementation']['mapped_sha256']==metadata['exported_mapped_sha256']
    manifest=json.loads((ROOT/'submission/implementation/manifest.json').read_text())
    actual=hashlib.sha256((ROOT/'submission/implementation/mapped.v').read_bytes()).hexdigest()
    assert actual==manifest['mapped_sha256']==metadata['exported_mapped_sha256']
    for relative,file_info in metadata['files'].items():
        assert hashlib.sha256((ROOT/'submission'/relative).read_bytes()).hexdigest()==file_info['sha256']
    source,info=assemble(ROOT/'submission')
    canonical_hash=hashlib.sha256(source.encode()).hexdigest()
    for relative,expected in result['source']['files'].items():
        original=ROOT/'submission'/relative
        if original.is_file():
            assert hashlib.sha256(original.read_bytes()).hexdigest()==expected
        else:
            # The official batch operator stages expanded sources as a single
            # canonical rtl/fft64_top.sv; original submissions may use .v.
            assert len(result['source']['files'])==1 and expected==canonical_hash
    assert info['source_sha256']==metadata['source_sha256']
    generated,labels=evaluation_frames(result['seed'],8192)
    stored=np.load(ROOT/'agent_evaluation/numeric_evidence/inputs.npz',allow_pickle=False)
    assert np.array_equal(stored['inputs'],generated) and stored['labels'].tolist()==labels
    outputs=np.load(ROOT/'agent_evaluation/numeric_evidence/outputs.npz',allow_pickle=False)['outputs']
    observed=json.loads((ROOT/'agent_evaluation/numeric_evidence/observation.json').read_text())
    q=quality(generated,outputs)
    assert q['feasible'] and q['zero_frame_exact']
    assert math.isclose(q['minimum_frame_sqnr_db'],observed['quality']['minimum_frame_sqnr_db'],abs_tol=1e-8,rel_tol=0)
    assert result['quality']['minimum_frame_sqnr_db']<=q['minimum_frame_sqnr_db']+1e-8
    assert observed['original_receipt']['signature']['source_sha256']==metadata['source_sha256']
    ppa=result['ppa']
    assert hashlib.sha256((ROOT/'agent_evaluation/measurement/asic/mapped.v').read_bytes()).hexdigest()==ppa['mapped_sha256']
    assert ppa['fmax_certificate']['mapped_sha256']==ppa['mapped_sha256']
    protocol=json.loads((ROOT/'agent_evaluation/measurement/throughput/long_intervals/probe_results.json').read_text())
    assert len(protocol)==321 and {x['frame_ii_cycles']for x in protocol}==set(range(64,385))
    assert all(x['tested_frames']>=1024 for x in protocol)
    chat=json.loads((ROOT/'conversation/conversation.json').read_text())
    assert chat['provenance']['agent']==metadata['agent']
    assert chat['provenance']['user_reported_duration_seconds']==metadata['user_reported_dialogue_seconds']
    print(json.dumps(dict(status='PASS',files=len(record['files']),score=grade['score'],
        scope='Archive hashes, regenerated hidden inputs, actual output numerical replay, recorded source/implementation, transcript identity and score arithmetic; no new EDA execution'),indent=2))


if __name__=='__main__':main()
