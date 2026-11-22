"""Continuous-frame verification and empirical minimum-II qualification."""
from pathlib import Path
import csv
import numpy as np
from common import save,read,sha,lock,DesignInvalidError
from cache import array_identity,runtime_identity,bind_directory,load_cached,save_cached
import hashlib
import time
import resource
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
    if not tail and not reset_probes and len(frames):
        # The exhaustive scan needs a regular stream. Allocate it directly:
        # avoid a large temporary Python list of per-cycle rows.
        starts=5+np.arange(len(frames),dtype=np.int64)*interval
        events=np.zeros((int(starts[-1])+64+400,5),dtype=np.int64)
        events[:3,0]=1
        for start,frame in zip(starts,frames):
            events[start:start+64,1]=1;events[start,2]=1
            events[start:start+64,3:5]=frame
        metadata=dict(frame_starts=starts.tolist(),offered_min_frame_II=interval,clock_period_ns=10,
            ignore_before_cycle=5,cancelled_partial_start=None,reset_probes=[],
            continuous_frames=len(frames),mixed_gap_tail_frames=0,
            offered_frame_intervals=[interval]if len(frames)>1 else[])
        return events,metadata,frames
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
    """Every tested II receives >=1024 consecutive frames; no short pilot."""
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    settings=profile_policy('architecture')['ii_calibration']
    identity=dict(backend=backend,source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                  frames=array_identity(frames),seed=seed,runtime=runtime_identity(backend),settings=settings)
    with lock(out/'lock'):
        bind_directory(out,identity)
        return _probe_intervals(source,frames,out,backend,seed,identity)


def _probe_intervals(source,frames,out,backend,seed,identity):
    started=time.monotonic()
    checkpoint=out/'probe_results.json'
    settings=profile_policy('architecture')['ii_calibration'];count=settings['pilot_frames_per_interval']
    if len(frames)<count:raise ValueError('Throughput trial needs at least 1024 frames')
    lo,hi=settings['pilot_all_integer_intervals']
    def valid(rows,begin,end):
        return (isinstance(rows,list) and len(rows)==end-begin and
            all(isinstance(row,dict) and row.get('frame_ii_cycles')==interval and
                row.get('tested_frames')==count and type(row.get('pass_rtl'))is bool and
                (not row['pass_rtl'] or isinstance(row.get('quality'),dict))
                for interval,row in zip(range(begin,end),rows)))
    cached=load_cached(checkpoint,identity)
    if valid(cached,lo,hi+1):return cached
    rng=np.random.default_rng(seed);indices=rng.choice(len(frames),size=count,replace=False)
    selected=np.asarray(frames)[indices];results=[];compiled=None;maximum_batch_input_bytes=0
    chunk_size=settings['chunk_intervals'];(out/'latencies').mkdir(exist_ok=True)
    save(out/'probe_protocol.json',dict(intervals=[lo,hi],frame_indices=indices.tolist(),frames_per_interval=count,
        fft_length=64,method='exhaustive integer-II long RTL measurements; no claimed-II score'))
    for begin in range(lo,hi+1,chunk_size):
        chunk_started=time.monotonic()
        end=min(hi+1,begin+chunk_size);chunk=out/('intervals_'+str(begin)+'_'+str(end-1));chunk.mkdir(exist_ok=True)
        saved=chunk/'results.json'
        chunk_identity=dict(identity,intervals=[begin,end-1])
        cached=load_cached(saved,chunk_identity)
        if valid(cached,begin,end):
            results.extend(cached)
            if compiled is None and(chunk/'simulation/simv').exists():compiled=chunk/'simulation'
            continue
        events=[];epochs=[];offset=0
        for interval in range(begin,end):
            e,m,_=stream_schedule(selected,interval,seed,tail=False,reset_probes=False)
            events.append(e);epochs.append((interval,offset,len(e),m));offset+=len(e)
        batch=np.concatenate(events,axis=0);del events
        maximum_batch_input_bytes=max(maximum_batch_input_bytes,batch.nbytes)
        raw=simulate(source,batch,chunk/'simulation',backend,probe=True,reuse_compiled_from=compiled)
        if compiled is None:compiled=chunk/'simulation'
        measured=[]
        for interval,start,length,metadata in epochs:
            item=dict(frame_ii_cycles=interval,tested_frames=count,pass_rtl=False)
            e=batch[start:start+length];r=raw[start:start+length].copy();r[:,0]-=start
            try:
                outputs,lat=decode(r,e,metadata);q=quality(selected,outputs)
                item.update(pass_rtl=bool(q['feasible']),minimum_sqnr_db=q['minimum_frame_sqnr_db'],quality=q,
                            maximum_first_output_cycles=lat['maximum_first_output_latency_cycles'],
                            maximum_completion_cycles=lat['maximum_frame_completion_cycles'])
                np.savez_compressed(out/'latencies'/('ii_'+str(interval)+'.npz'),
                    first=lat['per_frame_first_output_latency_cycles'],completion=lat['per_frame_completion_cycles'])
                if not q['feasible']:item['reason']='SQNR or exact-zero failure'
            except (AssertionError,ValueError)as exc:item['reason']=str(exc)[:400]
            measured.append(item)
        save_cached(saved,measured,chunk_identity);results.extend(measured)
        save(chunk/'resources.json',dict(intervals=[begin,end-1],cycles=len(batch),
            input_array_bytes=batch.nbytes,output_array_bytes=raw.nbytes,
            wall_seconds=time.monotonic()-chunk_started,
            python_process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            scope='Python process lifetime peak; excludes EDA subprocess memory'))
        save(out/'progress.json',dict(status='RUNNING',completed_intervals=len(results),total_intervals=hi-lo+1,
            frames_per_interval=count,last_interval=end-1,chunk_intervals=chunk_size,
            maximum_batch_input_bytes=maximum_batch_input_bytes,
            process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        del raw,batch
    with(out/'intervals.csv').open('w',newline='')as stream:
        writer=csv.DictWriter(stream,['frame_ii_cycles','tested_frames','pass_rtl','minimum_sqnr_db','maximum_first_output_cycles','maximum_completion_cycles','reason'],extrasaction='ignore')
        writer.writeheader();writer.writerows(results)
    save(out/'progress.json',dict(status='COMPLETE',completed_intervals=len(results),frames_per_interval=count,
        wall_seconds=time.monotonic()-started,process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        chunk_intervals=chunk_size,maximum_batch_input_bytes=maximum_batch_input_bytes,
        resource_scope='current Python process; tool subprocess resources are recorded separately'))
    save_cached(checkpoint,results,identity)
    return results


def qualify(source,mapped_source,frames,outdir,interval,backend='vcs',seed=11,
            rtl_compiled=None,gate_compiled=None):
    interval=validate_interval(interval);out=Path(outdir)/('ii_'+str(interval));out.mkdir(parents=True,exist_ok=True)
    identity=dict(backend=backend,source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                  mapped_source_sha256=hashlib.sha256(mapped_source.encode()).hexdigest(),
                  frames=array_identity(frames),interval=interval,seed=seed,runtime=runtime_identity(backend),
                  mapped_runtime=runtime_identity('verilator'if backend=='iverilog'else backend),
                  gate_initial_state_modes=[0,1,20261121]if backend=='vcs'else[None])
    with lock(out/'lock'):
        bind_directory(out,identity)
        return _qualify(source,mapped_source,frames,out,interval,backend,seed,rtl_compiled,gate_compiled,identity)


def _qualify(source,mapped_source,frames,out,interval,backend,seed,rtl_compiled,gate_compiled,identity):
    path=out/'qualification.json'
    cached=load_cached(path,identity)
    if isinstance(cached,dict) and cached.get('status')in{'PASS','FAIL'}:return cached
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
            mapped_backend='verilator'if backend=='iverilog'else backend
            gate=simulate(mapped_source,events,out/'mapped',mapped_backend,reuse_compiled_from=gate_compiled if backend=='vcs'else None,**options)
            gout,_=decode(gate,events,metadata)
            assert np.array_equal(gate[:,1:3],raw[:,1:3]),'Stream mapped/RTL control-cycle mismatch'
            assert np.array_equal(gout,outputs),'Stream mapped/RTL payload mismatch'
        result.update(status='PASS',mapped_pass=True,verified_frame_ii_cycles=interval,
                      gate_initial_state_modes=modes,continuous_frames_verified=len(frames),
                      mixed_gap_and_dense_reset_verified=True)
    except (AssertionError,DesignInvalidError)as exc:
        result.update(status='FAIL',reason=str(exc)[:1800])
    save_cached(path,result,identity);return result


def verify(source,mapped_source,frames,outdir,claimed_interval=384,auto=False,backend='vcs',seed=11,
           rtl_compiled=None,gate_compiled=None):
    """Measured capacity, independent of an agent's declared/theoretical II."""
    from model import quality_union
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    observations=probe_intervals(source,frames,out/'long_intervals',backend,seed)
    mandatory=next(x for x in observations if x['frame_ii_cycles']==384)
    if not mandatory['pass_rtl']:
        result=dict(status='FAIL',mapped_pass=False,reason='Mandatory 384-cycle long service failed',mandatory=mandatory)
        save(out/'result.json',result);return result
    passed=[x for x in observations if x['pass_rtl']];attempts=[]
    for selected in passed:
        interval=selected['frame_ii_cycles']
        # Mapping equivalence is a representative subset, separate from the
        # 1024-frame-per-II RTL capacity measurement.
        subset=frames[:128]
        result=qualify(source,mapped_source,subset,out/'mapped_subset',interval,backend,seed,
                       rtl_compiled=rtl_compiled,gate_compiled=gate_compiled)
        attempts.append(dict(interval=interval,status=result['status']))
        save(out/'attempts.json',attempts)
        if result['status']=='PASS':
            result=dict(result,quality=quality_union(*(x['quality']for x in passed),result['quality']),
                qualification_method='exhaustive long RTL service measurement + representative RTL/mapped subset',
                verified_frame_ii_cycles=interval,continuous_frames_verified=selected['tested_frames'],
                mapped_subset_frames=len(subset),ignored_agent_claim=claimed_interval,
                first_output_latency_cycles=[max(x['maximum_first_output_cycles']for x in passed)],
                maximum_frame_completion_cycles=max(x['maximum_completion_cycles']for x in passed),
                optional_shorter_failures=sum(not x['pass_rtl']for x in observations),
                minimum_claim='smallest passing tested integer II; finite-frame evidence, not a formal worst-case guarantee',
                directory=str((out/'mapped_subset'/('ii_'+str(interval))).resolve()))
            save(out/'result.json',result);return result
    result=dict(status='FAIL',mapped_pass=False,reason='No long-tested interval passed mapped subset',attempts=attempts)
    save(out/'result.json',result);return result
