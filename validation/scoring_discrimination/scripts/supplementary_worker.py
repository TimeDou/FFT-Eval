from pathlib import Path
import json,sys,time,resource,traceback
import worker
from common import read,save,sha,lock
from scoring import hardware_feasible

ROOT=Path(__file__).resolve().parent


def main():
    name=sys.argv[1];data=read(ROOT/'supplementary_cases.json')
    case=next(c for c in data['cases']if c['id']==name)
    folder=ROOT/'supplementary'/name;submission=folder/'submission';out=folder/'measurement'
    if sha(submission/'rtl/fft64_top.sv')!=case['source_sha256']:raise RuntimeError('Supplementary RTL changed')
    started=time.monotonic()
    with lock(folder/'execution.lock'):
        if(out/'result.json').exists()and hardware_feasible(read(out/'result.json')):
            print('REUSED',name);return
        protocol=read(ROOT/'campaign.json')
        result=worker.evaluate(submission,out,'commercial',seed=protocol['seed'],scale=1,
            profile='architecture',audience='hidden')
        own=resource.getrusage(resource.RUSAGE_SELF);children=resource.getrusage(resource.RUSAGE_CHILDREN)
        save(folder/'worker_resources.json',dict(wall_seconds=time.monotonic()-started,
            python_peak_rss_kib=own.ru_maxrss,largest_child_peak_rss_kib=children.ru_maxrss,
            user_cpu_seconds=own.ru_utime+children.ru_utime,system_cpu_seconds=own.ru_stime+children.ru_stime))
        print(name,result.get('status'),flush=True)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        save(ROOT/'supplementary'/sys.argv[1]/'worker_failure.json',dict(status='UNSCORED_INFRASTRUCTURE',reason=str(exc),traceback=traceback.format_exc()))
        raise
