"""Cross-check public records without accepting their PPA as private grades."""
from pathlib import Path
import csv
import hashlib
import json
import sys

BASE=Path('/mnt/DATA1/sj/ALS/DP2.0')
sys.path.insert(0,str(BASE/'DSBench/FFT-Eval/fft64_benchmark/tools'))
from scoring import score_result


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=Path(Path('/tmp/fft_final_agent_review_path.txt').read_text().strip())
    config=json.loads((root/'campaign.json').read_text())
    rows=[]
    for case in config['cases']:
        repo=Path(case['original_workspace'])
        final_manifest=json.loads((root/'submissions'/case['id']/'implementation/manifest.json').read_text())
        candidates=[]
        for directory in sorted((repo/'runs').iterdir()):
            file=directory/'result.json'
            if not file.exists():continue
            result=json.loads(file.read_text())
            runtime=result.get('evaluation_identity',{}).get('runtime',{})
            errors=[]
            if runtime:
                if runtime.get('specification_sha256')!=sha(repo/'fft64_benchmark/SPEC.json'):errors.append('SPEC identity')
                if runtime.get('policy_sha256')!=sha(repo/'fft64_benchmark/profiles/policy.json'):errors.append('policy identity')
                for filename,expected in runtime.get('drivers',{}).items():
                    if sha(repo/'fft64_benchmark/tools'/filename)!=expected:errors.append('driver '+filename)
                for filename,expected in runtime.get('flow_scripts',{}).items():
                    if sha(repo/'fft64_benchmark/flow'/filename)!=expected:errors.append('flow '+filename)
            grade=result.get('grade',{})
            complete=result.get('status')=='COMPLETE'
            if complete:
                recomputed=score_result(result)
                if not recomputed['score_valid']or abs(recomputed['score']-grade.get('score',-1))>1e-10:errors.append('score arithmetic')
            architecture=complete and result.get('profile')=='architecture'
            final_input=(result.get('source',{}).get('source_sha256')==case['source_sha256']and
                result.get('source',{}).get('implementation',{}).get('mapped_sha256')==case['exported_mapped_sha256'])
            probes=directory/'throughput/long_intervals/probe_results.json'
            intervals=None
            if architecture:
                observations=json.loads(probes.read_text())
                intervals=len(observations)
                if intervals!=321 or {x['frame_ii_cycles']for x in observations}!=set(range(64,385)):
                    errors.append('II coverage')
                if any(x.get('tested_frames',0)<1024 for x in observations):errors.append('II frame count')
            row=dict(agent=case['id'],run=directory.name,profile=result.get('profile'),status=result['status'],
                grade_score=grade.get('score')if grade.get('score_valid')else None,score_valid=grade.get('score_valid',False),
                independently_checked_public_metadata=not errors,metadata_errors='; '.join(errors),
                matches_final_source_and_input_netlist=final_input,complete_ii_count=intervals,
                source_sha256=result.get('source',{}).get('source_sha256'),
                exported_input_mapped_sha256=result.get('source',{}).get('implementation',{}).get('mapped_sha256'),
                normalized_evaluation_mapped_sha256=result.get('ppa',{}).get('mapped_sha256'),
                original_result=str(file.resolve()))
            rows.append(row)
            if architecture and grade.get('resolved')and grade.get('score_valid'):candidates.append(row)
            if directory.name==case['public_run']:
                assert final_input,case['id']
                assert not errors,(case['id'],errors)
        assert candidates,case['id']
        best=max(candidates,key=lambda r:r['grade_score'])
        selected=next(r for r in rows if r['agent']==case['id']and r['run']==case['public_run'])
        assert abs(selected['grade_score']-best['grade_score'])<1e-10,(case['id'],'selection not best complete public score')
        print(case['id'],len(candidates),'complete architecture runs; final export/RTL match; chosen public score',selected['grade_score'])
    with(root/'public_search_audit.csv').open('w')as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (root/'public_search_audit.json').write_text(json.dumps(rows,indent=2)+'\n')


if __name__=='__main__':main()
