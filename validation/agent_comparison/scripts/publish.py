"""Collect compact real evidence into private result worktrees after validation."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent
WORKSPACE = Path('/mnt/DATA1/sj/ALS/DP2.0/DSBench')
COMPARISON = WORKSPACE/'FFT-Eval-agent-comparison/validation/agent_comparison'


def copy(source, target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def measurement(source, target):
    ignored_dirs = {'__pycache__','csrc','simv.daidir','dc_work','obj'}
    ignored_names = {'mapped.ddc','simv','vectors.txt','output.txt','source.sv','staged.sv','tb.sv','lock'}
    for p in source.rglob('*'):
        if not p.is_file() or any(x in ignored_dirs for x in p.parts) or p.name in ignored_names:
            continue
        if p.name == 'mapped.v' and 'frequency_certificates' in p.parts:
            continue
        if p.suffix in {'.json','.csv','.rpt','.log','.sdc','.tcl','.npz'} or p.name in {'mapped.v','input_mapped.v'}:
            copy(p, target/p.relative_to(source))


def manifest(root):
    files = {str(p.relative_to(root)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
             for p in sorted(root.rglob('*')) if p.is_file() and p.name not in {'FILE_MANIFEST.json','verification.json'}
             and '__pycache__' not in p.parts}
    record = dict(files=files,excluded_metadata=['FILE_MANIFEST.json','verification.json'],
         scope='Actual submission, raw metrics, reports, mapped netlists and compact observed numerical outputs. '
               'Large per-cycle text and simulator builds remain at original_campaign_directory.',
         original_campaign_directory=str(ROOT),source_commit=json.loads((ROOT/'campaign.json').read_text())['source_commit'])
    (root/'FILE_MANIFEST.json').write_text(json.dumps(record,indent=2)+'\n')


def main():
    status = json.loads((ROOT/'status.json').read_text())
    assert status['status'] == 'COMPLETE'
    campaign = json.loads((ROOT/'campaign.json').read_text())
    COMPARISON.mkdir(parents=True,exist_ok=True)
    for name in ['campaign.json','calibration.json','status.json','summary.json','scores.csv','RESULTS.md',
                 'execution_source_manifest.json','frequency_prefetch.json','architecture_claim_check.json','new_agent_environment.json','source_preservation.json']:
        copy(ROOT/name, COMPARISON/name)
    for folder in ['analysis','numeric_evidence','calibration_baselines']:
        shutil.copytree(ROOT/folder,COMPARISON/folder,dirs_exist_ok=True)
    for name in ['driver.py','worker.py','collect_numeric.py','prefetch_frequency.py','analyze.py','publish.py','check_architecture_claims.py','verify_archive.py','write_branch_docs.py']:
        copy(ROOT/name,COMPARISON/'scripts'/name)
    for case in campaign['cases']:
        name = case['id']
        result = json.loads((ROOT/'measurements'/name/'result.json').read_text())
        assert result['grade']['score_valid'] and result['grade']['resolved'], name
        branch = WORKSPACE/('FFT-Eval-agent-'+name)
        assert (branch/'.git').is_file()
        shutil.copytree(ROOT/'submissions'/name,branch/'submission',dirs_exist_ok=True)
        ev = branch/'agent_evaluation'
        ev.mkdir(exist_ok=True)
        measurement(ROOT/'measurements'/name,ev/'measurement')
        shutil.copytree(ROOT/'public_evidence'/name,ev/'public_evidence',dirs_exist_ok=True)
        copy(ROOT/'calibration.json',ev/'calibration.json')
        copy(ROOT/'numeric_evidence/inputs.npz',ev/'numeric_evidence/inputs.npz')
        copy(ROOT/'numeric_evidence/format.json',ev/'numeric_evidence/format.json')
        for suffix in ['.npz','.json']:
            copy(ROOT/'numeric_evidence'/(name+suffix),ev/'numeric_evidence'/(name+suffix))
        record = dict(case,source_commit=campaign['source_commit'],policy_sha256=campaign['policy_sha256'],
                      seed=campaign['seed'],audience='hidden',profile='architecture',original_campaign_directory=str(ROOT))
        (ev/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
        grade = result['grade']
        (ev/'grade.json').write_text(json.dumps(grade,indent=2)+'\n')
        (ev/'code_result.json').write_text(json.dumps({k:grade[k]for k in ['resolved','score','reason']},indent=2)+'\n')
        copy(ROOT/'verify_archive.py',ev/'verify_archive.py')
        target = COMPARISON/'cases'/name
        shutil.copytree(branch/'submission',target/'submission',dirs_exist_ok=True)
        shutil.copytree(ev,target/'agent_evaluation',dirs_exist_ok=True)
    print('Collected all three valid result branches and comparison evidence; write reports then refresh manifests.')


if __name__ == '__main__':
    main()
