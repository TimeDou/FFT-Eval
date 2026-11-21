"""Continuous-frame verification and empirical minimum-II qualification."""
from pathlib import Path
import csv
import numpy as np
from common import save,read,sha
from model import quality
from simulate import simulate,decode
from scoring import profile_policy


def validate_interval(interval):
    settings=profile_policy('architecture')['claimed_ii']
    if(type(interval)is not int or not settings['minimum']<=interval<=settings['maximum']):
        raise ValueError('frame_ii_cycles must be an integer from 64 through 384')
    return interval


def stream_schedule(frames,interval,seed=11,tail=True,reset_probes=True):
    validate_interval(interval)
    frames=np.asarray(frames,dtype=np.int64);rng=np.random.default_rng(seed)
    ev=[[1,0,0,0,0]]*3+[[0,0,0,0,0]]*2;probes=[]
    if reset_probes:
        for count,partial in [(8,False),(4,True)]:
            begin=len(ev)
            for j in range(count):
                x=frames[j%len(frames)]
                ev.extend([0,1,int(k==0),int(z[0]),int(z[1])]for k,z in enumerate(x))
                ev.extend([[0,0,0,0,0]]*(interval-64))
            if partial:
                ev.extend([0,1,int(k==0),int(z[0]),int(z[1])]for k,z in enumerate(frames[0][:20]))
            else:ev.extend([[0,0,0,0,0]]*17)
            probes.append(dict(epoch_start=begin,full_frames_offered=count,partial_frame=partial,reset_cycle=len(ev)))
            ev.extend([[1,0,0,0,0]]*3+[[0,0,0,0,0]]*3)
    ignore=len(ev);starts=[]
    extra_indices=rng.integers(0,len(frames),size=16)if tail else[]
    allframes=np.concatenate([frames,frames[extra_indices]],axis=0)if tail else frames
    for j,x in enumerate(allframes):
        starts.append(len(ev))
        ev.extend([0,1,int(k==0),int(z[0]),int(z[1])]for k,z in enumerate(x))
        if j<len(frames)-1:gap=interval-64
        elif j==len(frames)-1 and tail:gap=65568+384
        elif tail:gap=[interval,interval+1,interval+7,384][(j-len(frames))%4]-64
        else:gap=0
        ev.extend([[0,0,0,0,0]]*gap)
    ev.extend([[0,0,0,0,0]]*400)
    metadata=dict(frame_starts=starts,offered_min_frame_II=interval,clock_period_ns=10,
                  ignore_before_cycle=ignore,cancelled_partial_start=probes[-1]['epoch_start']if probes else None,
                  reset_probes=probes,continuous_frames=len(frames),mixed_gap_tail_frames=len(extra_indices),
                  offered_frame_intervals=sorted(set(np.diff(starts).tolist())))
    return np.asarray(ev,dtype=np.int64),metadata,allframes


def probe_intervals(source,frames,outdir,backend='vcs',seed=11):
    """Batch all integer intervals in ONE simulation, resetting each epoch.

    Probe capture records X sentinels. Every epoch is decoded and retained as a
    pass/fail observation; only a subsequent strict full-data gate test qualifies
    an interval for scoring.
    """
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    checkpoint=out/'probe_results.json'
    if checkpoint.exists():return read(checkpoint)
    settings=profile_policy('architecture')
    count=min(settings['ii_calibration']['pilot_frames_per_interval'],len(frames))
    rng=np.random.default_rng(seed);indices=rng.choice(len(frames),size=count,replace=False)
    selected=frames[indices];events=[];epochs=[];offset=0
    lo,hi=settings['ii_calibration']['pilot_all_integer_intervals']
    for interval in range(lo,hi+1):
        e,m,_=stream_schedule(selected,interval,seed,tail=False,reset_probes=False)
        events.append(e);epochs.append((interval,offset,len(e),m));offset+=len(e)
    batch=np.concatenate(events,axis=0)
    save(out/'probe_protocol.json',dict(intervals=[lo,hi],frame_indices=indices.tolist(),frames_per_interval=count,
                                       total_cycles=len(batch),scoring_use='qualification only; strict full test still required'))
    raw=simulate(source,batch,out/'simulation',backend,probe=True)
    results=[]
    for interval,start,length,metadata in epochs:
        item=dict(frame_ii_cycles=interval,pass_rtl=False)
        e=batch[start:start+length];r=raw[start:start+length].copy();r[:,0]-=start
        try:
            outputs,_=decode(r,e,metadata);q=quality(selected,outputs)
            item.update(pass_rtl=bool(q['feasible']),minimum_sqnr_db=q['minimum_frame_sqnr_db'])
            if not q['feasible']:item['reason']='SQNR/zero-frame failure'
        except (AssertionError,ValueError)as exc:item['reason']=str(exc)[:400]
        results.append(item)
    save(checkpoint,results)
    with(out/'intervals.csv').open('w',newline='')as stream:
        writer=csv.DictWriter(stream,['frame_ii_cycles','pass_rtl','minimum_sqnr_db','reason']);writer.writeheader();writer.writerows(results)
    return results


def qualify(source,mapped_source,frames,outdir,interval,backend='vcs',seed=11,
            rtl_compiled=None,gate_compiled=None):
    interval=validate_interval(interval);out=Path(outdir)/('ii_'+str(interval));out.mkdir(parents=True,exist_ok=True)
    path=out/'qualification.json'
    if path.exists():return read(path)
    events,metadata,inputs=stream_schedule(frames,interval,seed)
    save(out/'protocol.json',metadata)
    result=dict(status='RUNNING',claimed_frame_ii_cycles=interval,full_dataset_frames=len(frames),
                additional_gap_frames=len(inputs)-len(frames),mapped_pass=False,verification='strict full-data RTL/gate')
    try:
        raw=simulate(source,events,out/'rtl',backend,reuse_compiled_from=rtl_compiled)
        outputs,latency=decode(raw,events,metadata);q=quality(inputs,outputs)
        result.update(quality=q,first_output_latency_cycles=latency['first_output_latency_cycles'],latency=latency)
        if not q['feasible']:raise AssertionError('SQNR/zero-frame failure at declared continuous frame interval')
        modes=[0,1,20261121]if backend=='vcs'else[None]
        for mode in modes:
            options=dict(initialization=mode)if mode is not None else{}
            gate=simulate(mapped_source,events,out/'mapped',backend,reuse_compiled_from=gate_compiled,**options)
            gout,_=decode(gate,events,metadata)
            assert np.array_equal(gate[:,1:3],raw[:,1:3]),'Stream mapped/RTL control-cycle mismatch'
            assert np.array_equal(gout,outputs),'Stream mapped/RTL payload mismatch'
        result.update(status='PASS',mapped_pass=True,verified_frame_ii_cycles=interval,
                      gate_initial_state_modes=modes,continuous_frames_verified=len(frames),
                      mixed_gap_and_dense_reset_verified=True)
    except (AssertionError,ValueError,RuntimeError)as exc:
        # Tool failures are re-raised; an incomplete infrastructure run must not
        # be cached as an expected design failure.
        if isinstance(exc,RuntimeError)and __import__('re').search(r'license|not found|Timeout',str(exc),__import__('re').I):raise
        result.update(status='FAIL',reason=str(exc)[:1800])
    save(path,result);return result


def verify(source,mapped_source,frames,outdir,claimed_interval=384,auto=False,backend='vcs',seed=11,
           rtl_compiled=None,gate_compiled=None):
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    if auto:
        observations=probe_intervals(source,frames,out/'pilot',backend,seed)
        intervals=[x['frame_ii_cycles']for x in observations if x['pass_rtl']]
    else:intervals=[validate_interval(claimed_interval)]
    attempts=[]
    for interval in intervals:
        result=qualify(source,mapped_source,frames,out/'full',interval,backend,seed,
                       rtl_compiled=rtl_compiled,gate_compiled=gate_compiled)
        attempts.append(dict(interval=interval,status=result['status']))
        save(out/'attempts.json',attempts)
        if result['status']=='PASS':
            result=dict(result,qualification_method='all-integer pilot plus full validation'if auto else'agent claim plus full validation',
                        minimum_claim='smallest successful full-tested interval in pilot-qualified set'if auto else'verified declared interval; not a formal global minimum',
                        directory=str((out/'full'/('ii_'+str(interval))).resolve()))
            save(out/'result.json',result);return result
    result=dict(status='FAIL',mapped_pass=False,reason='No requested interval passed strict full validation',attempts=attempts)
    save(out/'result.json',result);return result
