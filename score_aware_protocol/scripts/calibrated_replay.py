"""Exercise the actual hidden evaluator with matching validation calibration."""
from pathlib import Path
import json
import os
import sys
import time

ROOT = Path(__file__).resolve().parent
os.environ.update(FFT_TECH_DIR='/mnt/mydata/.fft64/tech/99619e6e51b75f151556',
                  FFT_TOOLS_PREFIX='/mnt/mydata/.fft64/runtime',
                  FFT_PHYSICAL_CACHE_DIR=str(ROOT/'physical_cache'))
sys.path.insert(0, str(ROOT/'engine_private/fft64_benchmark/tools'))
from common import read, save
from evaluate import evaluate


def main():
    assert read(ROOT/'status.json')['status'] == 'COMPLETE'
    started = time.monotonic()
    calibration, config = read(ROOT/'calibration.json'), read(ROOT/'config.json')
    checks = []
    for case, source in [('sdf_hidden', 'sdf'), ('folded_hidden', 'iterative')]:
        target = ROOT/'measurements'/case
        original = read(target/'result.json')
        if not (target/'result_before_calibration.json').exists():
            save(target/'result_before_calibration.json', original)
        expected = read(target/'validated_grade.json')
        actual = evaluate(ROOT/'engine_private/operator/baselines'/source, target,
                          backend='commercial', seed=config['hidden_seed'], scale=1,
                          calibration=calibration, profile='architecture',
                          auto_ii=True, audience='hidden')
        grade = actual['grade']
        assert actual['status'] == 'COMPLETE'
        assert grade['resolved'] and grade['score_valid'] and grade['official_score']
        assert grade['scoring_scope'] == 'hidden_evaluation'
        assert grade['performance'] == expected['performance']
        assert grade['components'] == expected['components']
        assert abs(grade['score']-expected['score']) < 1e-12
        save(target/'validated_grade.json', grade)
        checks.append(dict(id=case, status='PASS', score=grade['score'],
                           official_score=grade['official_score'],
                           scope='Full hidden evaluator with matching calibration; identical measured evidence reused'))
    save(ROOT/'calibrated_replay.json', dict(status='PASS', cases=checks,
                                          seconds=time.monotonic()-started))
    print(json.dumps(checks, indent=2), flush=True)


if __name__ == '__main__':
    main()
