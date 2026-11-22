"""Preserve compact native validation and reset evidence in the private repo."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def copy(source, target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def compact_measurement(source, target):
    excluded_dirs = {'__pycache__', 'csrc', 'simv.daidir', 'dc_work', 'obj'}
    excluded_names = {'simv', 'vectors.txt', 'output.txt', 'source.sv',
                      'staged.sv', 'tb.sv', 'lock', 'mapped.ddc'}
    for path in sorted(source.rglob('*')):
        if not path.is_file() or any(x in excluded_dirs for x in path.parts):
            continue
        if path.name in excluded_names:
            continue
        if path.name == 'mapped.v' and 'frequency_certificates' in path.parts:
            continue
        if path.suffix in {'.json', '.csv', '.rpt', '.log', '.sdc', '.tcl', '.npz'} or path.name in {'mapped.v', 'input_mapped.v'}:
            copy(path, target/path.relative_to(source))


def reset_evidence(target):
    records = []
    for name in ['Claude-DS-Flash', 'Codex-GPT-6.1-Sol-Max',
                 'Codex-GPT-6.2-Sol-Max', 'Claude-Fable-5.2']:
        base = Path('/home/sj/FFT')/name
        repo = base/'FFT-Bench'
        git = lambda *args: subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()
        environment = read(repo/'runs/environment/environment.json')
        assert environment['ready'] and environment['smoke']['status'] == 'PASS', name
        count = int(git('rev-list', '--count', 'HEAD'))
        if name != 'Claude-Fable-5.2':
            assert count == 1, (name, count)
        assert not git('status', '--porcelain'), name
        assert not any((repo/x).exists() for x in ['submission', 'experiments', 'tools_agent', 'work']), name
        compact_measurement((repo/'runs/environment').resolve(), target/name/'smoke_evidence')
        copy(repo/'runs/environment/environment.json', target/name/'environment.json')
        records.append(dict(agent=name, public_commit=git('rev-parse', 'HEAD'),
                            port=(base/'port.txt').read_text().strip(),
                            git_clean=True, local_commit_count=count,
                            old_candidates_absent=True, environment_ready=True,
                            scope='fresh workspace and recreated container' if name != 'Claude-Fable-5.2'
                                  else 'unused workspace synchronized; environment checked'))
    assert len({r['public_commit'] for r in records}) == 1
    save(target/'verification.json', dict(status='PASS', workspaces=records))
    for name in ['workspace_reset_status.json', 'workspace_reset_plan.json',
                 'capture_pilot.py', 'reset_workspaces.py', 'collect_validation.py']:
        copy(Path(__file__).parent/name, target/name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root, target = args.run.resolve(), args.out.resolve()
    assert read(root/'status.json')['status'] == 'COMPLETE'
    assert read(root/'calibrated_replay.json')['status'] == 'PASS'
    for name in ['status.json', 'summary.json', 'config.json', 'environment.json',
                 'platform_identity.json', 'evaluation_protocol.json',
                 'calibration.json', 'published_source_commits.json',
                 'frequency_prefetch.json', 'calibrated_replay.json']:
        copy(root/name, target/'validation'/name)
    for name in ['driver.py', 'prefetch_frequency.py', 'calibrated_replay.py']:
        copy(root/name, target/'scripts'/name)
    copy(Path(__file__).parent/'write_validation_report.py', target/'scripts/write_validation_report.py')
    if (root/'grader').is_dir():
        shutil.copytree(root/'grader', target/'validation/grader', dirs_exist_ok=True)
    for case in ['sdf_hidden', 'folded_hidden', 'public_preview']:
        grade = read(root/'measurements'/case/'validated_grade.json')
        assert grade['score_valid'] and grade['resolved'], case
        compact_measurement(root/'measurements'/case, target/'validation/measurements'/case)
    shutil.copytree(root/'public_submission', target/'validation/public_submission', dirs_exist_ok=True)
    for name in ['sdf', 'iterative']:
        shutil.copytree(root/'engine_private/operator/baselines'/name,
                        target/'validation/accurate_controls'/name, dirs_exist_ok=True)
    copy('/tmp/fft_score_aware_tests_final.log', target/'validation/regression_135_tests.log')
    reset_evidence(target/'reset_receipts')
    files = {str(p.relative_to(target)):dict(bytes=p.stat().st_size,
             sha256=hashlib.sha256(p.read_bytes()).hexdigest())
             for p in sorted(target.rglob('*')) if p.is_file() and p.name != 'FILE_MANIFEST.json'
             and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    save(target/'FILE_MANIFEST.json', dict(files=files, original_campaign_directory=str(root),
         scope='Native measurements, mapped netlists, reports, compact results, source hashes and reset receipts. '
               'Reconstructible simulator builds and large per-cycle text remain at the original private run directory. '
               'The old-hardware diagnostic is not an official reranking of historical Agent results.'))
    print(json.dumps(dict(files=len(files), bytes=sum(r['bytes'] for r in files.values())), indent=2))


if __name__ == '__main__':
    main()
