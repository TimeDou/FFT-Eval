"""Independently certify completed mapped netlists during long RTL tests."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import worker
from common import read, save
from toolchain import activate
from frequency import certify

ROOT = Path(__file__).resolve().parent


def run(name):
    activate()
    asic = ROOT/'measurements'/name/'asic'
    deadline = time.monotonic()+1200
    while not (asic/'metrics.json').exists():
        result = ROOT/'measurements'/name/'result.json'
        if result.exists() and read(result).get('status') not in {'RUNNING', 'COMPLETE'}:
            return dict(id=name, status='SKIPPED_DESIGN_OR_TOOL_FAILURE')
        if time.monotonic() > deadline:
            return dict(id=name, status='PENDING_ASIC', reason='Prefetch wait ended; main evaluator still performs certification')
        time.sleep(5)
    if not read(asic/'metrics.json').get('timing_pass'):
        return dict(id=name, status='SKIPPED_TIMING_FAILURE')
    certificate, directory = certify(asic, 'commercial')
    return dict(id=name, status=certificate['status'], passing_period_ns=certificate['passing_period_ns'], directory=str(directory))


if __name__ == '__main__':
    cases = read(ROOT/'campaign.json')['cases']
    rows = []
    with ProcessPoolExecutor(max_workers=2) as pool:
        tasks = [pool.submit(run, c['id']) for c in cases]
        for future in as_completed(tasks):
            row = future.result()
            rows.append(row)
            save(ROOT/'frequency_prefetch.json', rows)
            print(row, flush=True)
