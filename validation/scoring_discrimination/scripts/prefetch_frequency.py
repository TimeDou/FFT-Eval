"""Run independent fixed-netlist STA scans while long RTL capacity tests run."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import json,sys,time
import worker
from common import read,save
from frequency import certify

ROOT=Path(__file__).resolve().parent


def measure(item):
    name,directory=item
    started=time.monotonic()
    try:
        metrics=read(Path(directory)/'metrics.json')
        if not metrics.get('timing_pass'):return dict(id=name,status='SKIPPED_TIMING_FAILURE')
        certificate,path=certify(directory,'commercial')
        return dict(id=name,status='CERTIFIED',seconds=time.monotonic()-started,
                    passing_period_ns=certificate['passing_period_ns'],directory=str(path))
    except Exception as exc:return dict(id=name,status='UNSCORED_INFRASTRUCTURE',reason=str(exc))


if __name__=='__main__':
    campaign=read(ROOT/'campaign.json')
    items=[(c['id'],str(ROOT/'measurements'/c['id']/'asic'))for c in campaign['cases']if not c.get('quick')]
    items.extend((c['id'],str(ROOT/'supplementary'/c['id']/'measurement/asic'))for c in read(ROOT/'supplementary_cases.json')['cases'])
    for name,path in items:
        if not(Path(path)/'metrics.json').exists():raise RuntimeError('Wait for complete physical metrics: '+name)
    rows=[]
    with ProcessPoolExecutor(max_workers=2)as pool:
        for future in as_completed([pool.submit(measure,item)for item in items]):
            row=future.result();rows.append(row);save(ROOT/'frequency_prefetch.json',rows);print(row,flush=True)
