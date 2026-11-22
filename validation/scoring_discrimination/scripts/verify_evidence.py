"""Check archived observations and recompute scores without running EDA tools."""
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
    parser.add_argument('--evidence', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    root = args.evidence.resolve()
    repo = next(p for p in root.parents if (p/'fft64_benchmark/tools/scoring.py').is_file())
    sys.path.insert(0, str(repo/'fft64_benchmark/tools'))
    from scoring import POLICY_SHA256, score_result
    from model import quality

    manifest = read(root/'FILE_MANIFEST.json')
    assert POLICY_SHA256 == manifest['policy_sha256'], 'Use the recorded evaluator and policy'
    for name, record in manifest['files'].items():
        path = root/name
        assert path.is_file() and path.stat().st_size == record['bytes'], name
        assert sha(path) == record['sha256'], name

    summary = read(root/'analysis/summary.json')
    calibration = read(root/'calibration.json')
    frames = np.load(root/'numeric_evidence/inputs.npz', allow_pickle=False)['inputs']
    assert frames.shape == (8384, 64, 2)
    assert frames.min() >= -16384 and frames.max() <= 16384
    zero = np.all(frames == 0, axis=(1, 2))
    rms = np.sqrt(np.mean(np.sum((frames.astype(np.float64)/32768)**2, axis=-1), axis=-1))
    assert np.all(rms[~zero] >= 1/32)

    records = []
    accurate_outputs = np.load(root/'numeric_evidence/exact_folded.npz', allow_pickle=False)['outputs']
    exact_family = {'exact_sdf', 'pipelined_folded', 'timing2ns_folded', 'abc_default', 'abc_resyn2'}
    for row in summary['measured_cases']:
        name = row['id']
        case = root/'cases'/name
        measured_path = case/'measurement/result.json'
        measured = read(measured_path)
        assert sha(measured_path) == row['result_sha256'], name
        grade = score_result(measured, calibration)
        assert grade['score_valid'] and grade['resolved'] == row['resolved'], name
        assert math.isclose(grade['score'], row['score'], rel_tol=0, abs_tol=1e-14), name
        saved_grade = read(root/'analysis'/(name+'_grade.json'))
        assert grade == saved_grade, name

        archive = root/'numeric_evidence'/(name+'.npz')
        observation = read(root/'numeric_evidence'/(name+'.json'))
        assert sha(archive) == observation['compact_archive_sha256'], name
        output = np.load(archive, allow_pickle=False)['outputs']
        assert output.shape == frames.shape, name
        q = quality(frames, output)
        assert q['feasible'] == observation['quality']['feasible'], name
        assert q['failed_frames'] == observation['quality']['failed_frames'], name
        assert math.isclose(q['minimum_frame_sqnr_db'], observation['quality']['minimum_frame_sqnr_db'],
                            rel_tol=0, abs_tol=1e-8), name
        if name in exact_family:
            assert np.array_equal(output, accurate_outputs), name
        if row['resolved']:
            mapped = case/'measurement/asic/mapped.v'
            assert sha(mapped) == measured['ppa']['mapped_sha256'], name
            assert measured['mapped_simulation_pass'] and measured['throughput_check']['mapped_pass'], name
            assert measured['mapped_initial_state_modes'] == [0, 1, 20261121], name
            assert measured['ppa']['fmax_certificate']['mapped_sha256'] == sha(mapped), name
        records.append(dict(id=name, score=grade['score'], resolved=grade['resolved'],
                            score_valid=grade['score_valid'], observed_qor_replay='PASS'))

    capacities = []
    for path in sorted((root/'capacity').glob('*/probe_results.json')):
        rows = read(path)
        assert [r['frame_ii_cycles'] for r in rows] == list(range(64, 385)), str(path)
        assert all(r['tested_frames'] == 1024 for r in rows), str(path)
        passed = [r['frame_ii_cycles'] for r in rows if r['pass_rtl']]
        assert passed
        capacities.append(dict(identity=path.parent.name, intervals=len(rows),
                               frames_per_interval=1024, minimum_passing_ii=min(passed)))
    assert len(capacities) == 5
    with (root/'analysis/scorer_controls.csv').open(newline='') as stream:
        controls = list(csv.DictReader(stream))
    assert len(controls) == 11 and all(c['pass_check'] == 'True' for c in controls)
    feasible = [r for r in records if r['resolved']]
    assert len(feasible) == 8 and len({round(r['score'], 6) for r in feasible}) == 8
    assert sum(not r['resolved'] and r['score_valid'] for r in records) == 1
    receipt = dict(status='PASS', scope='Archive hashes, score replay, observed numerical outputs, '
                   'mapped-netlist hash binding and full capacity summaries; no new EDA execution',
                   files_checked=len(manifest['files']), observed_frames_per_design=len(frames),
                   complex_samples_per_design=len(frames)*64, cases=records,
                   capacities=capacities, scorer_replay_controls=11, policy_sha256=POLICY_SHA256)
    if args.receipt:
        args.receipt.write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
