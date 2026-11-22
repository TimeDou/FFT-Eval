"""Independent clock certification while full continuous-frame scans execute."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import time
import driver
from common import read,save
from frequency import certify
from toolchain import activate
ROOT=Path(__file__).resolve().parent


def run(name):
    activate();asic=ROOT/'measurements'/name/'asic';deadline=time.monotonic()+1200
    while not(asic/'metrics.json').exists():
        if time.monotonic()>deadline:return dict(id=name,status='WAIT_ENDED_MAIN_STILL_CERTIFIES')
        time.sleep(5)
    if not read(asic/'metrics.json').get('timing_pass'):return dict(id=name,status='SKIPPED_TIMING_FAIL')
    cert,_=certify(asic,'commercial')
    return dict(id=name,status=cert['status'],passing_period_ns=cert['passing_period_ns'])


if __name__=='__main__':
    rows=[]
    with ProcessPoolExecutor(max_workers=2)as pool:
        for future in as_completed([pool.submit(run,n)for n in ['sdf_hidden','folded_hidden','public_preview']]):
            row=future.result();rows.append(row);save(ROOT/'frequency_prefetch.json',rows);print(row,flush=True)
