"""Independent hidden evaluation of immutable completed Agent submissions."""
from pathlib import Path
import hashlib
import json
import os
import resource
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent
os.environ.update(FFT_TECH_DIR='/mnt/mydata/.fft64/tech/99619e6e51b75f151556',
                  FFT_TOOLS_PREFIX='/mnt/mydata/.fft64/runtime',
                  FFT_PHYSICAL_CACHE_DIR='/mnt/mydata/.fft64/physical_cache')
sys.path.insert(0, str(ROOT/'engine/fft64_benchmark/tools'))
from common import read, save, lock
from evaluate import assemble, evaluate
from scoring import measurement_context, hardware_feasible, score_result, POLICY_SHA256
from toolchain import activate


def main():
    name = sys.argv[1]
    campaign = read(ROOT/'campaign.json')
    case = next(c for c in campaign['cases'] if c['id'] == name)
    calibration = read(ROOT/'calibration.json')
    submission = ROOT/'submissions'/name
    out = ROOT/'measurements'/name
    with lock(ROOT/'locks'/(name+'.lock')):
        for relative, expected in case['files_sha256'].items():
            if hashlib.sha256((submission/relative).read_bytes()).hexdigest() != expected:
                raise RuntimeError('Frozen submission changed: '+relative)
        source, info = assemble(submission)
        assert info['source_sha256'] == case['source_sha256']
        assert POLICY_SHA256 == campaign['policy_sha256']
        activate()
        actual = measurement_context(dict(backend='commercial', seed=campaign['seed'], scale=1, audience='hidden'))
        if actual != calibration['measurement_context']:
            save(out/'context_mismatch.json', dict(actual=actual, expected=calibration['measurement_context']))
            raise RuntimeError('Existing accurate calibration does not match this runtime/protocol')
        prior = out/'result.json'
        if prior.exists():
            result = read(prior)
            if result.get('status') in {'COMPLETE', 'QUALITY_FAILED', 'DESIGN_INVALID', 'THROUGHPUT_FAILED'}:
                grade = score_result(result, calibration)
                if grade['score_valid']:
                    save(out/'final_grade.json', grade)
                    print('REUSED', name, result['status'], grade['score'], flush=True)
                    return
        started = time.monotonic()
        try:
            result = evaluate(submission, out, 'commercial', seed=campaign['seed'], scale=1,
                              calibration=calibration, profile='architecture', auto_ii=True, audience='hidden')
            save(out/'final_grade.json', result['grade'])
            print('FINISHED', name, result['status'], result['grade']['score'], result['grade']['score_valid'], flush=True)
        finally:
            own = resource.getrusage(resource.RUSAGE_SELF)
            children = resource.getrusage(resource.RUSAGE_CHILDREN)
            save(out/'resources.json', dict(wall_seconds=time.monotonic()-started,
                 python_peak_rss_kib=own.ru_maxrss, largest_child_peak_rss_kib=children.ru_maxrss,
                 cpu_user_seconds=own.ru_utime+children.ru_utime,
                 cpu_system_seconds=own.ru_stime+children.ru_stime,
                 scope='Process lifetime Python peak and maximum child peak, not summed concurrent RSS'))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        save(ROOT/'measurements'/sys.argv[1]/'worker_failure.json',
             dict(status='UNSCORED_INFRASTRUCTURE', failure=str(exc), traceback=traceback.format_exc()))
        raise
