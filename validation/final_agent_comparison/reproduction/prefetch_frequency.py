"""Certify completed candidate mappings while independent II scans execute."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import time
import launcher
from common import read,save
from frequency import certify
from toolchain import activate

ROOT=Path(__file__).resolve().parent


def run(name):
    activate()
    deadline=time.monotonic()+1500
    while True:
        choices=list((ROOT/'evaluation/candidates'/name/'runs').glob('*/asic/metrics.json'))
        if len(choices)==1:
            asic=choices[0].parent
            if not read(asic/'metrics.json').get('timing_pass'):
                return dict(id=name,status='SKIPPED_TIMING_FAIL')
            result,_=certify(asic,'commercial')
            return dict(id=name,status=result['status'],passing_period_ns=result['passing_period_ns'])
        if len(choices)>1:
            raise RuntimeError('Multiple candidate identities; inspect rather than choose silently')
        if time.monotonic()>deadline:
            return dict(id=name,status='WAIT_ENDED_MAIN_STILL_CERTIFIES')
        time.sleep(5)


if __name__=='__main__':
    names=[case['id']for case in read(ROOT/'campaign.json')['cases']]
    rows=[]
    with ProcessPoolExecutor(max_workers=2)as pool:
        for task in as_completed([pool.submit(run,name)for name in names]):
            row=task.result();rows.append(row)
            save(ROOT/'frequency_prefetch.json',rows)
            print(row,flush=True)
