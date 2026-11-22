"""Resume-safe, three-worker review queue using a frozen valid calibration."""
from pathlib import Path
import csv
import fcntl
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value, indent=2)+'\n')
    temp.replace(path)


def main():
    guard = (ROOT/'driver.lock').open('a')
    fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
    campaign = json.loads((ROOT/'campaign.json').read_text())
    queue = list(campaign['cases'])
    running = {}
    finished = []
    started = time.monotonic()
    (ROOT/'logs').mkdir(exist_ok=True)
    while queue or running:
        while queue and len(running) < campaign['max_workers']:
            case = queue.pop(0)
            log = (ROOT/'logs'/(case['id']+'.log')).open('a')
            process = subprocess.Popen([sys.executable, ROOT/'worker.py', case['id']], stdout=log, stderr=subprocess.STDOUT)
            running[case['id']] = dict(process=process, log=log, started=time.monotonic())
        for name, state in list(running.items()):
            code = state['process'].poll()
            if code is not None:
                state['log'].close()
                finished.append(dict(id=name, returncode=code, wall_seconds=time.monotonic()-state['started']))
                del running[name]
                print('WORKER_DONE', name, code, flush=True)
        save(ROOT/'status.json', dict(status='RUNNING', driver_pid=os.getpid(),
             elapsed_seconds=time.monotonic()-started, finished=finished,
             pending=[c['id'] for c in queue],
             running={k:dict(pid=v['process'].pid,elapsed_seconds=time.monotonic()-v['started']) for k,v in running.items()}))
        if running:
            time.sleep(5)
    rows = []
    for case in campaign['cases']:
        directory = ROOT/'measurements'/case['id']
        path = directory/'result.json'
        if not path.exists():
            rows.append(dict(id=case['id'], status='UNSCORED_INFRASTRUCTURE', score_valid=False))
            continue
        result = json.loads(path.read_text())
        grade = result['grade']
        p = grade.get('performance', {})
        rows.append(dict(id=case['id'], status=result['status'], resolved=grade['resolved'],
             score_valid=grade['score_valid'], score=grade['score'], area_um2=result.get('ppa',{}).get('area_um2'),
             minimum_sqnr_db=result.get('quality',{}).get('minimum_frame_sqnr_db'),
             period_ns=p.get('certified_period_ns'), frame_ii=p.get('verified_frame_II_cycles'),
             throughput_ffts_s=p.get('effective_throughput_ffts_per_second'),
             first_output_cycles=p.get('first_output_cycles'),
             completion_cycles=max(result.get('latency',{}).get('frame_completion_cycles',[]), default=None),
             area_component=grade.get('components',{}).get('area'),
             throughput_component=grade.get('components',{}).get('throughput'),
             latency_component=grade.get('components',{}).get('latency'), reason=grade['reason']))
    state = 'COMPLETE' if all(r['score_valid'] for r in rows) else 'PARTIAL_INFRASTRUCTURE'
    save(ROOT/'summary.json', dict(status=state, cases=rows, elapsed_seconds=time.monotonic()-started))
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with (ROOT/'scores.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        writer.writerows(rows)
    save(ROOT/'status.json', dict(status=state, elapsed_seconds=time.monotonic()-started, finished=finished))
    print(json.dumps(rows, indent=2), flush=True)


if __name__ == '__main__':
    main()
