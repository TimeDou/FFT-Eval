from pathlib import Path
import csv,fcntl,hashlib,json,os,subprocess,sys,time,traceback

ROOT=Path(__file__).resolve().parent
os.environ.update(FFT_TECH_DIR='/mnt/mydata/.fft64/tech/99619e6e51b75f151556',
    FFT_TOOLS_PREFIX='/mnt/mydata/.fft64/runtime',
    FFT_PHYSICAL_CACHE_DIR='/mnt/mydata/.fft64/physical_cache')
sys.path.insert(0,str(ROOT/'engine/fft64_benchmark/tools'))
from common import save,read,sha
from toolchain import prepare
from scoring import make_calibration,score_result,performance


def main():
    guard=(ROOT/'driver.lock').open('a')
    try:fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise RuntimeError('This campaign already has a running driver')
    campaign=read(ROOT/'campaign.json')
    environment=prepare('commercial',allow_build=False)
    save(ROOT/'environment.json',environment)
    if not environment['ready']:raise RuntimeError('Commercial tools/libraries unavailable')
    queue=list(campaign['cases']);running={};finished=[];started=time.monotonic();streams=[]
    while queue or running:
        while queue and len(running)<campaign['max_workers']:
            case=queue.pop(0);directory=ROOT/'logs';directory.mkdir(exist_ok=True)
            log=(directory/(case['id']+'.log')).open('a');streams.append(log)
            process=subprocess.Popen([sys.executable,ROOT/'worker.py',case['id']],stdout=log,stderr=subprocess.STDOUT)
            running[case['id']]=dict(process=process,started=time.monotonic())
        for case_id,state in list(running.items()):
            code=state['process'].poll()
            if code is not None:
                finished.append(dict(id=case_id,returncode=code,wall_seconds=time.monotonic()-state['started']))
                print('FINISHED',case_id,code,flush=True);del running[case_id]
        save(ROOT/'status.json',dict(status='RUNNING',driver_pid=os.getpid(),elapsed_seconds=time.monotonic()-started,
            pending=[c['id']for c in queue],running={k:dict(pid=v['process'].pid,elapsed_seconds=time.monotonic()-v['started'])for k,v in running.items()},finished=finished))
        if running:time.sleep(5)
    for log in streams:log.close()
    results={}
    for case in campaign['cases']:
        path=ROOT/'measurements'/case['id']/'result.json'
        if path.exists():results[case['id']]=read(path)
    baselines={k:results[k]for k in campaign['calibration_designs']if k in results}
    calibration=make_calibration(baselines,'architecture',campaign_source_commit=campaign['source_commit'],
        campaign_manifest_sha256=sha(ROOT/'campaign.json'),audience='hidden',seed=campaign['seed'])
    save(ROOT/'calibration.json',calibration)
    rows=[]
    for case in campaign['cases']:
        result=results.get(case['id'])
        if result is None:
            rows.append(dict(id=case['id'],name=case['name'],status='UNSCORED_INFRASTRUCTURE',score_valid=False));continue
        grade=score_result(result,calibration)
        save(ROOT/'measurements'/case['id']/'scored_result.json',dict(result,grade=grade))
        measured=grade.get('performance',{});components=grade.get('components',{})
        rows.append(dict(id=case['id'],name=case['name'],role=case['role'],status=result['status'],resolved=grade['resolved'],
            score_valid=grade['score_valid'],score=grade['score'],area_um2=measured.get('area_um2'),
            certified_period_ns=measured.get('certified_period_ns'),frame_ii=measured.get('verified_frame_II_cycles'),
            throughput=measured.get('effective_throughput_ffts_per_second'),first_output_cycles=measured.get('first_output_cycles'),
            min_sqnr_db=result.get('quality',{}).get('minimum_frame_sqnr_db'),
            area_component=components.get('area'),throughput_component=components.get('throughput'),latency_component=components.get('latency'),
            reason=grade['reason']))
    save(ROOT/'summary.json',dict(status='COMPLETE',source_commit=campaign['source_commit'],cases=rows,
        runtime_seconds=time.monotonic()-started,calibration=calibration))
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with(ROOT/'scores.csv').open('w',newline='')as stream:
        writer=csv.DictWriter(stream,fields);writer.writeheader();writer.writerows(rows)
    save(ROOT/'status.json',dict(status='COMPLETE',elapsed_seconds=time.monotonic()-started,finished=finished,
                                summary=str(ROOT/'summary.json')))
    print(json.dumps(rows,indent=2),flush=True)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        save(ROOT/'driver_failure.json',dict(status='UNSCORED_INFRASTRUCTURE',failure=str(exc),traceback=traceback.format_exc()))
        raise
