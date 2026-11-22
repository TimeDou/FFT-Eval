"""Verify archived measurements and observed numerical outputs without EDA execution."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import sys
import numpy as np


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    root = args.directory.resolve()
    repo = next(p for p in [root, *root.parents] if (p/'fft64_benchmark/tools/scoring.py').is_file())
    sys.path.insert(0,str(repo/'fft64_benchmark/tools'))
    from scoring import score_result, make_calibration, POLICY_SHA256, profile_policy
    from evaluate import assemble
    from model import quality, evaluation_frames
    from frequency import validate_trials

    manifest = read(root/'FILE_MANIFEST.json')
    for name, record in manifest['files'].items():
        path = root/name
        assert path.stat().st_size == record['bytes'] and sha(path) == record['sha256'], name
    calibration = read(root/'calibration.json')
    assert calibration['policy_sha256'] == POLICY_SHA256
    if (root/'campaign.json').exists():
        campaign = read(root/'campaign.json')
        seed = campaign['seed']
        cases = [(c['id'],root/'cases'/c['id']/'submission',root/'cases'/c['id']/'agent_evaluation')for c in campaign['cases']]
        accurate = {name:read(root/'calibration_baselines'/name/'result.json')for name in ['exact_folded','exact_sdf']}
        reproduced = make_calibration(accurate,'architecture')
        for key in ['references','targets','weights','measurement_context','backend','flow_id','profile']:
            assert reproduced[key] == calibration[key], key
        assert read(root/'architecture_claim_check.json')['claim_supported'] is False
    else:
        provenance = read(root/'provenance.json')
        seed = provenance['seed']
        cases = [(provenance['id'],root.parent/'submission',root)]
    generated, labels = evaluation_frames(seed,8192)
    results = []
    for name, submission, evidence in cases:
        provenance = read(evidence/'provenance.json')
        for relative, expected in provenance['files_sha256'].items():
            assert sha(submission/relative) == expected, (name, relative)
        result = read(evidence/'measurement/result.json')
        grade = score_result(result,calibration)
        saved_grade = read(evidence/'grade.json')
        assert saved_grade == result['grade']
        assert math.isclose(grade['score'],saved_grade['score'],rel_tol=0,abs_tol=1e-14)
        assert {k:v for k,v in grade.items()if k!='score'} == {k:v for k,v in saved_grade.items()if k!='score'}
        grade = saved_grade
        assert grade['score_valid'] and grade['resolved'] and result['status'] == 'COMPLETE'
        source, info = assemble(submission)
        assert info['source_sha256'] == result['source']['source_sha256'], name
        assert result['measurement_context'] == calibration['measurement_context']
        assert result['dataset_frames'] == 8384 and result['audience'] == 'hidden'
        actual = np.load(evidence/'numeric_evidence/inputs.npz',allow_pickle=False)
        assert np.array_equal(actual['inputs'],generated)
        assert actual['labels'].tolist() == labels
        archive = evidence/'numeric_evidence'/(name+'.npz')
        observation = read(evidence/'numeric_evidence'/(name+'.json'))
        assert sha(archive) == observation['compact_archive_sha256']
        output = np.load(archive,allow_pickle=False)['outputs']
        q = quality(generated,output)
        assert q['feasible'] and q['zero_frame_exact']
        assert math.isclose(q['minimum_frame_sqnr_db'],observation['quality']['minimum_frame_sqnr_db'],rel_tol=0,abs_tol=1e-8)
        assert result['quality']['minimum_frame_sqnr_db'] <= q['minimum_frame_sqnr_db']+1e-8

        asic = evidence/'measurement/asic'
        assert sha(asic/'mapped.v') == result['ppa']['mapped_sha256']
        if info.get('implementation'):
            assert sha(asic/'input_mapped.v') == info['implementation']['mapped_sha256']
        assert result['mapped_initial_state_modes'] == [0,1,20261121]
        assert result['mapped_simulation_pass'] and result['throughput_check']['mapped_pass']
        assert result['ppa']['timing_pass']
        certificate = result['ppa']['fmax_certificate']
        assert certificate['mapped_sha256'] == result['ppa']['mapped_sha256']
        certificates = list((asic/'frequency_certificates').glob('*/certificate.json'))
        assert len(certificates) == 1
        certdir = certificates[0].parent
        assert read(certificates[0]) == certificate
        assert sha(certdir/'fmax_scan/trials.csv') == certificate['trial_trace_sha256']
        with (certdir/'fmax_scan/trials.csv').open(newline='')as stream:
            trials=[dict(trial=int(r['trial']),period_ns=float(r['period_ns']),
                         actual_clock_period_ns=float(r['actual_clock_period_ns']),
                         setup_slack_ns=float(r['setup_slack_ns']),hold_slack_ns=float(r['hold_slack_ns']),
                         **{'pass':r['pass']=='1'})for r in csv.DictReader(stream)]
        validate_trials(certificate,trials,profile_policy('architecture')['fmax_scan'])
        capacity=read(evidence/'measurement/throughput/long_intervals/probe_results.json')
        assert [r['frame_ii_cycles']for r in capacity] == list(range(64,385))
        assert all(r['tested_frames']==1024 for r in capacity)
        passed=[r['frame_ii_cycles']for r in capacity if r['pass_rtl']]
        selected=result['throughput_check']['verified_frame_ii_cycles']
        assert selected in passed
        assert min(passed)==selected, 'Review any mapped rejection of an earlier RTL-passing II'
        results.append(dict(agent=name,resolved=True,score_valid=True,score=grade['score'],
                            numerical_frames=len(generated),intervals=len(capacity),verified_ii=selected))
    receipt=dict(status='PASS',files_checked=len(manifest['files']),cases=results,
                 policy_sha256=POLICY_SHA256,
                 scope='Archive hashes, regenerated input identity, observed numerical replay, original source '
                       'and mapped hash binding, clock trace validation, capacity summaries and score replay; no new EDA execution')
    if args.receipt:
        args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__':
    main()
