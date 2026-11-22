"""Native public/private contract validation on immutable source snapshots."""
from pathlib import Path
import fcntl
import json
import os
import subprocess
import sys
import time
import traceback
import zipfile

ROOT = Path(__file__).resolve().parent
os.environ.update(FFT_TECH_DIR='/mnt/mydata/.fft64/tech/99619e6e51b75f151556',
                  FFT_TOOLS_PREFIX='/mnt/mydata/.fft64/runtime',
                  FFT_PHYSICAL_CACHE_DIR=str(ROOT/'physical_cache'))
sys.path.insert(0, str(ROOT/'engine_private/fft64_benchmark/tools'))
from common import read, save, sha
from scoring import make_calibration, score_result, hardware_feasible, POLICY_SHA256
from toolchain import prepare


def main():
    lock = (ROOT/'driver.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    started = time.monotonic()
    config = read(ROOT/'config.json')
    environment = prepare('commercial', allow_build=False)
    save(ROOT/'environment.json', environment)
    assert environment['ready']
    for rel in ['tools/scoring.py', 'profiles/policy.json', 'SPEC.json']:
        assert sha(ROOT/'engine_private/fft64_benchmark'/rel) == sha(ROOT/'engine_public/fft64_benchmark'/rel)
    cases = [('sdf_hidden', 'sdf'), ('folded_hidden', 'iterative')]
    jobs = []
    for name, source in cases:
        command = [sys.executable, ROOT/'engine_private/fft64_benchmark/tools/evaluate.py',
                   '--submission', ROOT/'engine_private/operator/baselines'/source,
                   '--out', ROOT/'measurements'/name, '--backend', 'commercial',
                   '--profile', 'architecture', '--audience', 'hidden',
                   '--seed', str(config['hidden_seed']), '--auto-ii']
        jobs.append((name, command))
    jobs.append(('public_preview', [sys.executable, ROOT/'public_worker.py']))
    running, finished, streams = {}, [], []
    (ROOT/'logs').mkdir(exist_ok=True)
    for name, command in jobs:
        previous = ROOT/'measurements'/name/'result.json'
        if previous.exists() and hardware_feasible(read(previous)):
            finished.append(dict(id=name, returncode=0, reused=True))
            continue
        stream = (ROOT/'logs'/(name+'.log')).open('a')
        streams.append(stream)
        save(ROOT/'logs'/(name+'_command.json'), list(map(str, command)))
        process = subprocess.Popen(list(map(str, command)), stdout=stream, stderr=subprocess.STDOUT)
        running[name] = dict(process=process, started=time.monotonic())
    while running:
        for name, state in list(running.items()):
            code = state['process'].poll()
            if code is not None:
                finished.append(dict(id=name, returncode=code, seconds=time.monotonic()-state['started']))
                del running[name]
                print('FINISHED', name, code, flush=True)
        save(ROOT/'status.json', dict(status='RUNNING', elapsed_seconds=time.monotonic()-started,
             finished=finished, running={name:dict(pid=s['process'].pid, seconds=time.monotonic()-s['started'])
                                        for name,s in running.items()}))
        if running:
            time.sleep(5)
    for stream in streams:
        stream.close()
    results = {name:read(ROOT/'measurements'/name/'result.json') for name,_ in jobs}
    assert all(hardware_feasible(value) for value in results.values())
    assert results['public_preview']['grade']['score_valid']
    assert results['public_preview']['grade']['scoring_scope'] == 'public_preview'
    assert not results['public_preview']['grade']['official_score']
    controls = {source:results[name] for name,source in cases}
    sys.path.insert(0, str(ROOT/'engine_private/operator'))
    import evaluate_synopsys as runner
    settings = dict(benchmark_id=read(ROOT/'engine_private/fft64_benchmark/SPEC.json')['benchmark_id'],
                    specification_sha256=sha(ROOT/'engine_private/fft64_benchmark/SPEC.json'),
                    data_generator_sha256=sha(ROOT/'engine_private/fft64_benchmark/tools/model.py'),
                    seed=config['hidden_seed'], scale=1, measurement_backend='commercial')
    identity = runner.platform_identity(environment)
    save(ROOT/'platform_identity.json', identity)
    calibration = make_calibration(controls, 'architecture', platform_fingerprint=runner.digest(identity),
        protocol_fingerprint=runner.digest(settings), baseline_results=controls,
        evaluation_protocol=dict(seed=config['hidden_seed'], scale=1))
    save(ROOT/'calibration.json', calibration)
    old_calibration = read(ROOT/'prior_calibration.json')
    old_grade = score_result(results['sdf_hidden'], old_calibration)
    assert old_grade['resolved'] and not old_grade['score_valid']
    save(ROOT/'prior_calibration_rejection.json', dict(status='PASS', old_score_valid=False,
         hardware_feasible=True, reason=old_grade['reason'], old_calibration_sha256=sha(ROOT/'prior_calibration.json'),
         specification_sha256=settings['specification_sha256'], policy_unchanged=calibration['policy_sha256']==old_calibration['policy_sha256']))
    rows, cached_checks = [], []
    for name,source in cases:
        directory = ROOT/'measurements'/name
        save(directory/'result_before_calibration.json', results[name])
        calibrated,reused = runner.cached_evaluate(ROOT/'engine_private/operator/baselines'/source,
            directory, settings, calibration=calibration, profile='architecture', auto_ii=True)
        assert reused and calibrated['grade']['score_valid'] and calibrated['grade']['official_score']
        assert calibrated['grade']['resolved']
        save(directory/'result.json', calibrated)
        results[name] = calibrated
        cached_checks.append(dict(id=name, status='PASS', matching_native_measurements_reused=True,
                                  score=calibrated['grade']['score']))
    save(ROOT/'calibrated_operator_check.json', dict(status='PASS', cases=cached_checks,
         scope='Actual private operator cached_evaluate with matching native source/platform/protocol evidence; no claim of a second independent dataset'))
    for name,value in results.items():
        grade = value['grade']
        assert grade['resolved'] and grade['score_valid']
        save(ROOT/'measurements'/name/'validated_grade.json', grade)
        rows.append(dict(id=name, grade=grade, minimum_sqnr_db=value['quality']['minimum_frame_sqnr_db']))
    compact = dict(calibration)
    compact.pop('baseline_results')
    save(ROOT/'calibration_for_grader.json', compact)
    command = [sys.executable, ROOT/'engine_private/fft64_benchmark/grading/make_grader.py',
               '--profile', 'architecture', '--calibration', ROOT/'calibration_for_grader.json',
               '--out', ROOT/'grader']
    receipt = subprocess.run(list(map(str, command)), check=True, capture_output=True, text=True)
    (ROOT/'logs/grader_build.log').write_text(receipt.stdout+receipt.stderr)
    with zipfile.ZipFile(ROOT/'grader/fft64_grader.zip') as archive:
        for item in ['tools/scoring.py', 'profiles/policy.json', 'SPEC.json']:
            assert archive.read('fft64_grader/'+item) == (ROOT/'engine_public/fft64_benchmark'/item).read_bytes()
    save(ROOT/'contract_check.json', dict(status='PASS', policy_sha256=POLICY_SHA256,
         specification_sha256=settings['specification_sha256'],
         scoring_source_sha256=sha(ROOT/'engine_private/fft64_benchmark/tools/scoring.py'),
         public_private_source_identical=True, grader_source_identical=True,
         public_valid_without_calibration=True, public_official_score=False,
         hidden_valid_with_matching_calibration=True, previous_calibration_rejected=True,
         scoring_policy_unchanged=True))
    save(ROOT/'summary.json', dict(status='COMPLETE', cases=rows))
    save(ROOT/'status.json', dict(status='COMPLETE', elapsed_seconds=time.monotonic()-started, finished=finished))
    print(json.dumps(read(ROOT/'contract_check.json'), indent=2), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        failure = traceback.format_exc()
        save(ROOT/'status.json', dict(status='INCOMPLETE', traceback=failure))
        raise
