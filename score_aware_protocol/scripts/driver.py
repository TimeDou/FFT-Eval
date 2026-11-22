"""Real public-feedback and private-platform-validation executions."""
from pathlib import Path
import fcntl
import json
import os
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
os.environ.update(FFT_TECH_DIR='/mnt/mydata/.fft64/tech/99619e6e51b75f151556',
                  FFT_TOOLS_PREFIX='/mnt/mydata/.fft64/runtime',
                  FFT_PHYSICAL_CACHE_DIR=str(ROOT/'physical_cache'))
sys.path.insert(0,str(ROOT/'engine_private/fft64_benchmark/tools'))
from common import read,save,sha
from toolchain import prepare
from scoring import make_calibration,score_result,hardware_feasible,POLICY_SHA256


def main():
    guard=(ROOT/'driver.lock').open('a');fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
    config=read(ROOT/'config.json');started=time.monotonic()
    environment=prepare('commercial',allow_build=False);save(ROOT/'environment.json',environment)
    assert environment['ready']
    tasks=[dict(id='sdf_hidden',engine='engine_private',submission=ROOT/'engine_private/operator/baselines/sdf',audience='hidden',seed=config['hidden_seed']),
           dict(id='folded_hidden',engine='engine_private',submission=ROOT/'engine_private/operator/baselines/iterative',audience='hidden',seed=config['hidden_seed']),
           dict(id='public_preview',engine='engine_public',submission=ROOT/'public_submission',audience='public',seed=config['public_seed'])]
    running={};finished=[];streams=[]
    for task in tasks:
        out=ROOT/'measurements'/task['id'];prior=out/'result.json'
        if prior.exists()and hardware_feasible(read(prior)):
            finished.append(dict(id=task['id'],returncode=0,reused=True));continue
        (ROOT/'logs').mkdir(exist_ok=True)
        stream=(ROOT/'logs'/(task['id']+'.log')).open('a');streams.append(stream)
        argv=[sys.executable,ROOT/task['engine']/'fft64_benchmark/tools/evaluate.py',
              '--submission',task['submission'],'--out',out,'--backend','commercial','--profile','architecture',
              '--audience',task['audience'],'--seed',str(task['seed']),'--auto-ii']
        process=subprocess.Popen(list(map(str,argv)),stdout=stream,stderr=subprocess.STDOUT)
        running[task['id']]=dict(process=process,started=time.monotonic())
    while running:
        for name,state in list(running.items()):
            code=state['process'].poll()
            if code is not None:
                finished.append(dict(id=name,returncode=code,seconds=time.monotonic()-state['started']))
                del running[name];print('FINISHED',name,code,flush=True)
        save(ROOT/'status.json',dict(status='RUNNING',elapsed_seconds=time.monotonic()-started,finished=finished,
             running={n:dict(pid=s['process'].pid,seconds=time.monotonic()-s['started'])for n,s in running.items()}))
        if running:time.sleep(5)
    for stream in streams:stream.close()
    results={t['id']:read(ROOT/'measurements'/t['id']/'result.json')for t in tasks}
    if not all(hardware_feasible(r)for r in results.values()):
        save(ROOT/'status.json',dict(status='INCOMPLETE',finished=finished));raise RuntimeError('Inspect actual failed validation')
    public=results['public_preview']
    assert public['grade']['score_valid'] and not public['grade']['official_score']
    assert public['grade']['scoring_scope']=='public_preview'
    controls={name:results[key]for name,key in [('sdf','sdf_hidden'),('iterative','folded_hidden')]}
    sys.path.insert(0,str(ROOT/'engine_private/operator'))
    import evaluate_synopsys as runner
    settings=dict(benchmark_id=read(ROOT/'engine_private/fft64_benchmark/SPEC.json')['benchmark_id'],
         specification_sha256=sha(ROOT/'engine_private/fft64_benchmark/SPEC.json'),
         data_generator_sha256=sha(ROOT/'engine_private/fft64_benchmark/tools/model.py'),
         seed=config['hidden_seed'],scale=1,measurement_backend='commercial')
    identity=runner.platform_identity(environment);save(ROOT/'platform_identity.json',identity)
    save(ROOT/'evaluation_protocol.json',{k:v for k,v in settings.items()if k!='measurement_backend'})
    calibration=make_calibration(controls,'architecture',platform_fingerprint=runner.digest(identity),
         protocol_fingerprint=runner.digest(settings),baseline_results=controls,
         evaluation_protocol=dict(seed=config['hidden_seed'],scale=1))
    save(ROOT/'calibration.json',calibration)
    summary=[]
    for name,r in results.items():
        grade=score_result(r,calibration)if name!='public_preview'else r['grade']
        assert grade['score_valid'] and grade['resolved']
        save(ROOT/'measurements'/name/'validated_grade.json',grade)
        summary.append(dict(id=name,grade=grade,area_um2=r['ppa']['area_um2'],minimum_sqnr_db=r['quality']['minimum_frame_sqnr_db']))
    save(ROOT/'summary.json',dict(status='COMPLETE',policy_sha256=POLICY_SHA256,cases=summary))
    save(ROOT/'status.json',dict(status='COMPLETE',elapsed_seconds=time.monotonic()-started,finished=finished))
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
