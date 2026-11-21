"""Measure a complete FFT64 submission with one numerical/protocol/PPA flow."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import sys
import time
import traceback
import numpy as np

from common import ROOT, TECH, COMB, SEQ, flow_identity, read, save, sha
from model import make_frames, quality, reference as fft_reference
from simulate import schedule, simulate, decode
from toolchain import activate, probe, select_backend
from scoring import score_result, profile_policy


def assemble(submission):
    directory = Path(submission).resolve()
    config = read(directory/'design_config.json') if (directory/'design_config.json').exists() else {}
    sources = config.get('rtl')
    if sources is None:
        sources = sorted(str(p.relative_to(directory)) for p in (directory/'rtl').rglob('*')
                         if p.suffix in {'.sv', '.v'})
    if not sources:
        raise ValueError('Place synthesizable sources under rtl/ or list them in design_config.json:rtl')
    files = {}

    def expand(path, stack=()):
        path = path.resolve()
        if not path.is_relative_to(directory) or not path.is_file():
            raise ValueError('Source file is missing from the submission: '+str(path))
        if path in stack:
            raise ValueError('Recursive RTL include: '+str(path))
        text = path.read_text()
        files[str(path.relative_to(directory))] = sha(path)
        return re.sub(r'(?m)^\s*`include\s+"([^"]+)"[^\n]*',
                      lambda m: expand(path.parent/m[1], stack+(path,)), text)

    text = '\n'.join(expand(directory/rel) for rel in sources)
    code = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    for pattern in [r'\$(?:fopen|fread|fscanf|readmemh|readmemb|system|cos|sin|exp|sqrt|pow)\b',
                    r'\b(?:real|shortreal|DPI|force|release)\b',
                    r'`(?:ifn?def|elsif)\s+(?:SYNTHESIS|VERILATOR|VCS)', r'translate_off']:
        if re.search(pattern, code):
            raise ValueError('Use a synthesizable, self-contained hardware implementation: '+pattern)
    if re.search(r'\bnegedge\b', code) or any(
            name != 'clk' for name in re.findall(r'\bposedge\s+(\w+)', code)):
        raise ValueError('Use only the specified positive-edge clk')
    # The declaration is only a scheduling hint; capacity is measured.
    hint=config.get('frame_ii_cycles',384)
    if type(hint)is not int or not 64<=hint<=384:hint=384
    return text, dict(top='fft64_top', files=files, frame_ii_cycles=hint,
                      source_sha256=hashlib.sha256(text.encode()).hexdigest())


def used_cell_models(mapped):
    models = []
    for match in re.finditer(r'\bmodule\s+(\w+)\b.*?\bendmodule', (TECH/'cells_sim.v').read_text(), re.S):
        if re.search(r'\b'+re.escape(match[1])+r'\s+\S+\s*\(', mapped):
            models.append(match[0])
    if not models:
        raise ValueError('No mapped standard-cell models found')
    return '\n'.join(models)


def compact(result):
    quality_result = result.get('quality', {})
    latency = result.get('latency', {})
    ppa = result.get('ppa', {})
    return dict(status=result['status'], backend=result.get('backend'), profile=result.get('profile','area'),
                functional_pass=bool(result.get('protocol_pass') and quality_result.get('feasible')),
                worst_frame_sqnr_db=quality_result.get('minimum_frame_sqnr_db'),
                first_output_cycles=latency.get('first_output_latency_cycles'),
                completion_cycles=latency.get('frame_completion_cycles'),
                timing_pass=ppa.get('timing_pass'), worst_slack_ns=ppa.get('worst_setup_slack_ns'),
                full_mapped_area_um2=ppa.get('area_um2'),
                mapped_simulation_pass=result.get('mapped_simulation_pass'),
                area_ratio=result.get('grade', {}).get('area_ratio'),
                grade=result.get('grade'), failure=result.get('failure'))


def evaluate(submission, outdir, backend='auto', seed=20261118, scale=1,
             calibration=None, quick=False, formal=False, profile='architecture', auto_ii=True,
             audience='public'):
    from model import evaluation_frames,quality_union
    from throughput import stream_schedule,verify
    from scoring import POLICY
    profile_policy(profile)
    if audience!='public':raise ValueError('This checkout provides public evaluation only')
    if type(scale)is not int or scale<1:raise ValueError('scale must be a positive frame multiplier')
    directory=Path(outdir).resolve();directory.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();result=dict(status='RUNNING',backend=backend,seed=seed,scale=scale,profile=profile,audience=audience)
    def checkpoint(stage):
        save(directory/'checkpoint.json',dict(stage=stage,profile=profile,seconds=time.monotonic()-started))
        save(directory/'result.json',result)
    def merge_latency(*items):
        merged=dict(items[0])
        for key in ['first_output_latency_cycles','frame_completion_cycles','computational_tail_cycles']:
            merged[key]=sorted(set(v for item in items for v in item.get(key,[])))
        merged['maximum_first_output_latency_cycles']=max(merged['first_output_latency_cycles'])
        merged['maximum_frame_completion_cycles']=max(merged['frame_completion_cycles'])
        return merged
    try:
        activate();backend,why=select_backend(probe(quick),backend,calibration)
        result.update(backend=backend,selection_reason=why)
        if backend=='commercial'and not quick:
            from commercial import preflight
            environment=preflight();save(directory/'environment.json',environment)
            if not environment['ready']:raise EnvironmentError('VCS/DC/PrimeTime or matching libraries unavailable')
        source,info=assemble(submission);result['source']=info;save(directory/'source.json',info)
        count=POLICY['evaluation'][audience+'_random_nonzero_frames']*scale
        frames,labels=evaluation_frames(seed,count)
        result.update(dataset_frames=len(frames),independent_random_nonzero_frames=count,fft_length=64)
        save(directory/'dataset.json',dict(seed=seed,scale=scale,audience=audience,random_nonzero_frames=count,
             directed_frames=len(frames)-count,frames=len(frames),fft_length=64,complex_input_samples=len(frames)*64,labels=labels))
        simulator='iverilog'if backend=='local'else'vcs'
        checkpoint('NUMERICAL_'+audience.upper())
        events,meta=schedule(frames,seed+17)
        raw=simulate(source,events,directory/'rtl_sim',simulator)
        outputs,lat=decode(raw,events,meta);numerical=quality(frames,outputs)
        result.update(protocol_pass=True,quality=numerical,latency=lat)
        ref=fft_reference(frames);pred=(outputs[...,0]+1j*outputs[...,1])/32768
        error=np.sum(abs(pred-ref)**2,1);energy=np.sum(abs(ref)**2,1)
        save(directory/'per_frame_quality.json',[dict(id=i,family=labels[i],nmse=float(e/s)if s else None,
             sqnr_db=float(-10*np.log10(e/s))if s and e else None,exact=bool(e==0))for i,(e,s)in enumerate(zip(error,energy))])
        del events,raw,outputs,ref,pred
        if not numerical['feasible']:
            result['status']='QUALITY_FAILED'
        else:
            # The mandatory service is ALWAYS a long consecutive stream.
            checkpoint('MANDATORY_1024_FRAME_SERVICE')
            protocol_frames=frames[:POLICY['evaluation']['sustained_consecutive_frames']]
            events,meta,inputs=stream_schedule(protocol_frames,384,seed+29)
            raw=simulate(source,events,directory/'mandatory_service',simulator,reuse_compiled_from=directory/'rtl_sim')
            output,service_lat=decode(raw,events,meta);service_q=quality(inputs,output)
            result['mandatory_service']=dict(status='PASS'if service_q['feasible']else'FAIL',continuous_frames=len(protocol_frames),
                  quality=service_q,latency=service_lat,frame_ii_cycles=384)
            save(directory/'mandatory_service/protocol.json',meta)
            result['quality']=quality_union(numerical,service_q);result['latency']=merge_latency(lat,service_lat)
            del events,raw,output
            if not service_q['feasible']:result['status']='QUALITY_FAILED'
            elif quick:result['status']='QUICK_CHECK_PASSED'
            else:
                checkpoint('ASIC_MAPPING')
                if backend=='commercial':
                    from commercial import measure
                    ppa=measure(source,directory/'asic',formal)
                else:
                    from local_asic import measure,try_equivalence
                    ppa=measure(source,directory/'asic')
                    if formal:result['formal']=try_equivalence(source,directory/'asic')
                result.update(ppa=ppa,flow_id=flow_identity(backend))
                mapped=(directory/'asic/mapped.v').read_text();mapped_source=used_cell_models(mapped)+'\n'+mapped
                # Representative numeric, reset and continuous-protocol subset.
                mapped_frames=np.concatenate([frames[:POLICY['evaluation']['mapped_random_frames']],frames[count:]],axis=0)
                events,meta,inputs=stream_schedule(mapped_frames,384,seed+37)
                checkpoint('REPRESENTATIVE_MAPPED_SIMULATION')
                rr=simulate(source,events,directory/'mapped_reference_rtl',simulator,reuse_compiled_from=directory/'rtl_sim')
                ro,mapped_lat=decode(rr,events,meta)
                mapped_q=quality(inputs,ro)
                result['quality']=quality_union(result['quality'],mapped_q)
                result['latency']=merge_latency(result['latency'],mapped_lat)
                if not mapped_q['feasible']:raise ValueError('Mapped representative subset violates SQNR')
                modes=[0,1,20261121]if backend=='commercial'else[None]
                for mode in modes:
                    opts=dict(initialization=mode)if mode is not None else{}
                    gr=simulate(mapped_source,events,directory/'mapped_sim','vcs'if backend=='commercial'else'verilator',**opts)
                    go,_=decode(gr,events,meta)
                    assert np.array_equal(rr[:,1:3],gr[:,1:3]),'Mapped subset control/cycle mismatch'
                    assert np.array_equal(ro,go),'Mapped subset payload mismatch'
                result.update(mapped_simulation_pass=True,mapped_initial_state_modes=modes,
                              mapped_subset=dict(frames=len(inputs),random_frames=64,all_directed=True,protocol=True))
                del events,rr,ro,gr,go
                if profile=='architecture':
                    checkpoint('LONG_II_CAPACITY_SEARCH')
                    result['throughput_check']=verify(source,mapped_source,frames[:1024],directory/'throughput',
                        claimed_interval=info['frame_ii_cycles'],auto=True,backend=simulator,seed=seed+31,
                        rtl_compiled=directory/'rtl_sim',gate_compiled=directory/'mapped_sim'if backend=='commercial'else None)
                    capacity=result['throughput_check']
                    if capacity['status']!='PASS':result.update(status='THROUGHPUT_FAILED',failure=capacity.get('reason'))
                    else:
                        result['quality']=quality_union(result['quality'],capacity['quality'])
                        dense=dict(first_output_latency_cycles=capacity['first_output_latency_cycles'],
                                   frame_completion_cycles=[capacity['maximum_frame_completion_cycles']])
                        result['latency']=merge_latency(result['latency'],dense)
                        if ppa['timing_pass']:
                            checkpoint('FREQUENCY_SCAN')
                            from frequency import certify
                            ppa['fmax_certificate']=certify(directory/'asic',backend=backend)[0]
                if result['status']=='RUNNING':result['status']='COMPLETE'
                checkpoint('MEASUREMENTS_FINISHED')
    except Exception as exc:
        result.update(status='ENVIRONMENT_ERROR'if isinstance(exc,(EnvironmentError,FileNotFoundError))else'FAILED',
                      failure=str(exc),traceback=traceback.format_exc())
    result['seconds']=time.monotonic()-started;result['grade']=score_result(result,calibration)
    save(directory/'result.json',result);save(directory/'summary.json',compact(result));return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--submission', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--backend', choices=['auto', 'local', 'commercial'], default=os.environ.get('FFT_BACKEND','auto'))
    parser.add_argument('--seed', type=int, default=20261118)
    parser.add_argument('--scale', type=int, default=1)
    parser.add_argument('--calibration')
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--formal', action='store_true')
    parser.add_argument('--profile', choices=['area','architecture'], default='architecture')
    parser.add_argument('--auto-ii', action='store_true', help='Preview/calibration: qualify the smallest pilot-supported interval instead of a declared interval')
    parser.add_argument('--audience',choices=['public'],default='public')
    args = parser.parse_args()
    calibration = read(args.calibration) if args.calibration else None
    result = evaluate(args.submission, args.out, args.backend, args.seed, args.scale,
                      calibration, args.quick, args.formal, args.profile, args.auto_ii, args.audience)
    print(json.dumps(compact(result), indent=2))
    return 0 if result['status'] in {'COMPLETE', 'QUICK_CHECK_PASSED'} and result.get('ppa', {}).get('timing_pass', True) else 2


if __name__ == '__main__':
    sys.exit(main())
