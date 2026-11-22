from pathlib import Path
import hashlib,json,os,sys,time,traceback,resource,shutil

ROOT=Path(__file__).resolve().parent
os.environ.update(FFT_TECH_DIR='/mnt/mydata/.fft64/tech/99619e6e51b75f151556',
    FFT_TOOLS_PREFIX='/mnt/mydata/.fft64/runtime',
    FFT_PHYSICAL_CACHE_DIR='/mnt/mydata/.fft64/physical_cache')
sys.path.insert(0,str(ROOT/'engine/fft64_benchmark/tools'))
from common import save,read,sha,lock
from evaluate import evaluate
from scoring import hardware_feasible,profile_policy
from cache import digest,array_identity,runtime_identity
import throughput


def capacity_cache(source,frames,outdir,backend='vcs',seed=11):
    """Share only identical, authenticated RTL-capacity measurements.

    Mapped qualification remains private to each implementation. No identity
    or measurement payload is relabelled to enable reuse.
    """
    identity=dict(backend=backend,source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        frames=array_identity(frames),seed=seed,runtime=runtime_identity(backend),
        settings=profile_policy('architecture')['ii_calibration'])
    destination=ROOT/'rtl_capacity_cache'/digest(identity)
    destination.mkdir(parents=True,exist_ok=True)
    requested=Path(outdir);requested.parent.mkdir(parents=True,exist_ok=True)
    if not requested.exists():requested.symlink_to(destination,target_is_directory=True)
    if requested.resolve()!=destination.resolve():raise RuntimeError('Capacity cache target mismatch')
    save(requested.parent/'capacity_cache_provenance.json',dict(directory=str(destination),identity=identity,
         scope='Same RTL, frames, seed, tools, evaluator and policy; mapped netlists are checked separately'))
    return original_probe(source,frames,requested,backend,seed)


original_probe=throughput.probe_intervals
throughput.probe_intervals=capacity_cache


def main():
    case_id=sys.argv[1];campaign=read(ROOT/'campaign.json')
    case=next(c for c in campaign['cases']if c['id']==case_id)
    submission=ROOT/'submissions'/case_id;out=ROOT/'measurements'/case_id
    if sha(submission/'rtl/fft64_top.sv')!=case['rtl_sha256']:raise RuntimeError('Frozen RTL changed')
    started=time.monotonic()
    with lock(ROOT/'locks'/(case_id+'.lock')):
        prior=out/'result.json'
        if prior.exists():
            value=read(prior)
            if hardware_feasible(value)or value.get('status')in ['DESIGN_INVALID','QUALITY_FAILED']:
                print('REUSED',case_id,value['status'],flush=True);return
            save(ROOT/'attempts'/case_id/(str(time.time_ns())+'.json'),value)
        try:
            if case.get('custom_build'):
                from build_implementation import build
                from implementation import export_artifacts
                result=build(submission,ROOT/'builds'/case_id,'commercial',10000,1800)
                if not(submission/'implementation').exists():
                    export_artifacts(result['implementation'],submission,ROOT/'builds'/case_id/'export_backup')
            result=evaluate(submission,out,'commercial',seed=campaign['seed'],scale=1,
                profile='architecture',audience='hidden',quick=case.get('quick',False))
            print('DONE',case_id,result.get('status'),flush=True)
        except Exception as exc:
            save(out/'worker_failure.json',dict(status='UNSCORED_INFRASTRUCTURE',failure=str(exc),traceback=traceback.format_exc()))
            print('WORKER_ERROR',case_id,str(exc),flush=True)
        finally:
            own=resource.getrusage(resource.RUSAGE_SELF);children=resource.getrusage(resource.RUSAGE_CHILDREN)
            save(out/'worker_resources.json',dict(wall_seconds=time.monotonic()-started,
                python_peak_rss_kib=own.ru_maxrss,largest_child_peak_rss_kib=children.ru_maxrss,
                user_cpu_seconds=own.ru_utime+children.ru_utime,system_cpu_seconds=own.ru_stime+children.ru_stime,
                scope='Separate Python peak and maximum child peak, not aggregate concurrent RSS'))


if __name__=='__main__':main()
