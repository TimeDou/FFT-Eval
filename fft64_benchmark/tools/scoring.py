"""Frozen independent area and architecture/throughput scoring profiles."""
from pathlib import Path
import hashlib
import json
import math

POLICY_PATH=Path(__file__).resolve().parents[1]/'profiles/policy.json'
POLICY=json.loads(POLICY_PATH.read_text())
POLICY_SHA256=hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest()
SCORING_VERSION='fft64_quant_pdf_long_frames_v1'


def profile_policy(profile):
    if profile not in POLICY['profiles']:raise ValueError('Unknown scoring profile: '+str(profile))
    return POLICY['profiles'][profile]


def hardware_feasible(result):
    passed=bool(result.get('status')=='COMPLETE'
                and result.get('quality',{}).get('feasible',False)
                and result.get('protocol_pass',False)
                and result.get('mapped_simulation_pass',False)
                and result.get('ppa',{}).get('timing_pass',False)
                and result.get('ppa',{}).get('formal_status')!='FAILED')
    if result.get('profile','area')=='architecture':
        passed=passed and result.get('throughput_check',{}).get('status')=='PASS'
    if passed:
        try:performance(result)
        except (ValueError,TypeError,KeyError):passed=False
    return bool(passed)


def positive(value,name):
    if type(value)not in(int,float)or not math.isfinite(value)or value<=0:
        raise ValueError('Missing or invalid measured '+name)
    return value


def performance(result,profile=None):
    profile=profile or result.get('profile','area');profile_policy(profile)
    ppa=result.get('ppa',{});lat=result.get('latency',{})
    area=positive(ppa.get('area_um2'),'area')
    clock=positive(ppa.get('clock_period_ns',lat.get('clock_period_ns')),'common clock period')
    first=lat.get('first_output_latency_cycles',[])
    first_cycles=positive(max(first)if first else None,'first-output cycles')
    out=dict(area_um2=area,first_output_cycles=first_cycles,first_output_latency_ns=first_cycles*clock,
             target_clock_period_ns=clock,base_frame_II_cycles=lat.get('offered_frame_II'),
             measured_frequency_in_score=False)
    if profile=='area':return out
    stream=result.get('throughput_check',{})
    if stream.get('status')!='PASS' or not stream.get('mapped_pass'):
        raise ValueError('Continuous-frame RTL and mapped verification is required')
    interval=positive(stream.get('verified_frame_ii_cycles'),'verified stream frame II')
    certificate=ppa.get('fmax_certificate',{})
    if(certificate.get('status')!='CERTIFIED' or not certificate.get('hold_pass')
       or certificate.get('mapped_sha256')!=ppa.get('mapped_sha256')):
        raise ValueError('A matching passing clock-scan certificate is required; fixed-clock slack is insufficient')
    period=positive(certificate.get('passing_period_ns'),'certified passing clock period')
    resolution=profile_policy('architecture')['fmax_scan']['resolution_ns']
    if certificate.get('capped_at_minimum_period'):
        if abs(period-profile_policy('architecture')['fmax_scan']['minimum_period_ns'])>1e-8:
            raise ValueError('Invalid frequency scan cap')
    else:
        failing=positive(certificate.get('failing_period_ns'),'certified failing clock period')
        if failing>=period:raise ValueError('Invalid frequency scan bracket')
        if period-failing>resolution+1e-9:raise ValueError('Frequency scan bracket is wider than the frozen resolution')
    dense_first=stream.get('first_output_latency_cycles',[])
    if dense_first:first_cycles=max(first_cycles,max(dense_first))
    return dict(out,first_output_cycles=first_cycles,first_output_latency_ns=first_cycles*clock,
                certified_period_ns=period,certified_setup_fmax_MHz=1000/period,
                verified_frame_II_cycles=interval,effective_throughput_ffts_per_second=1e9/(interval*period),
                effective_throughput_samples_per_second=64e9/(interval*period),
                first_output_latency_at_certified_clock_ns=first_cycles*period)


def make_calibration(results,profile='area',**metadata):
    policy=profile_policy(profile)
    if not results or not all(hardware_feasible(r)for r in results.values()):
        raise ValueError('All accurate baselines must pass the selected profile')
    if len({(r.get('backend'),r.get('flow_id'))for r in results.values()})!=1:
        raise ValueError('Accurate baselines must share backend and measurement flow')
    measured={name:performance(r,profile)for name,r in results.items()}
    best_area=min(measured,key=lambda n:measured[n]['area_um2'])
    area_best=measured[best_area]['area_um2']
    first_result=next(iter(results.values()))
    references=dict(area_um2=area_best);targets=dict(area_um2=area_best*policy['targets']['area_ratio_to_best_accurate'])
    sources=dict(area_reference=best_area,area_target=best_area)
    if profile=='architecture':
        worst_area=max(measured,key=lambda n:measured[n]['area_um2'])
        slowest=min(measured,key=lambda n:measured[n]['effective_throughput_ffts_per_second'])
        fastest=max(measured,key=lambda n:measured[n]['effective_throughput_ffts_per_second'])
        longest=max(measured,key=lambda n:measured[n]['first_output_latency_ns'])
        shortest=min(measured,key=lambda n:measured[n]['first_output_latency_ns'])
        references=dict(area_um2=area_best,
                        throughput_ffts_per_second=1e9/(384*POLICY['shared_spec']['clock_period_ns']),
                        first_output_latency_ns=300*POLICY['shared_spec']['clock_period_ns'])
        targets.update(throughput_ffts_per_second=measured[fastest]['effective_throughput_ffts_per_second']*policy['targets']['throughput_ratio_to_best_accurate'],
                       first_output_latency_ns=max(measured[shortest]['first_output_latency_ns']*policy['targets']['latency_ratio_to_best_accurate'],
                           policy['targets']['latency_physical_floor_cycles']*POLICY['shared_spec']['clock_period_ns']))
        sources.update(area_reference=best_area,throughput_reference='mandatory_384_cycle_service',throughput_target=fastest,
                       latency_reference='mandatory_300_cycle_deadline',latency_target=shortest)
    return dict(metadata,backend=first_result['backend'],flow_id=first_result['flow_id'],profile=profile,
                scoring_version=SCORING_VERSION,policy_sha256=POLICY_SHA256,weights=policy['weights'],
                references=references,targets=targets,anchor_sources=sources,baseline_performance=measured,
                reference_area_um2=references['area_um2'],reference_design=best_area if profile=='area'else'paper_contract_and_accurate_calibration',
                normalization='frozen targets relative to accurate baselines only; no candidate adaptation')


def normalized(value,reference,target,lower_is_better):
    span=(reference-target)if lower_is_better else(target-reference)
    if span<0:raise ValueError('Normalization target is in the wrong direction')
    if span==0:return float(value<=target)if lower_is_better else float(value>=target)
    gain=(reference-value)if lower_is_better else(value-reference)
    return float(min(1,max(0,gain/span)))


def score_result(result,calibration=None):
    profile=result.get('profile','area');profile_policy(profile)
    feasible=hardware_feasible(result)
    grade=dict(resolved=feasible,feasible=feasible,score=0.0,
               score_valid=not feasible and result.get('status')in{'COMPLETE','QUALITY_FAILED','FAILED','THROUGHPUT_FAILED'},
               scoring_version=SCORING_VERSION,profile=profile,policy_sha256=POLICY_SHA256,area_ratio=None)
    if not feasible:return dict(grade,reason='A required numerical, protocol, timing, RTL/mapped or declared-throughput check failed.')
    try:measured=performance(result,profile)
    except ValueError as exc:return dict(grade,reason=str(exc))
    if not calibration:return dict(grade,performance=measured,reason='Hardware checks passed; matching frozen profile calibration is required.')
    expected=dict(backend=result.get('backend'),flow_id=result.get('flow_id'),profile=profile,
                  scoring_version=SCORING_VERSION,policy_sha256=POLICY_SHA256)
    if any(calibration.get(k)!=v for k,v in expected.items()):
        return dict(grade,reason='Calibration belongs to another profile, policy, backend or flow; recalibrate.')
    policy=profile_policy(profile)
    if calibration.get('weights')!=policy['weights']:
        return dict(grade,reason='Calibration weights do not match the frozen policy.')
    refs=calibration['references'];targets=calibration['targets']
    components=dict(area=normalized(measured['area_um2'],refs['area_um2'],targets['area_um2'],True),throughput=0.,latency=0.)
    if profile=='architecture':
        components.update(throughput=normalized(measured['effective_throughput_ffts_per_second'],refs['throughput_ffts_per_second'],targets['throughput_ffts_per_second'],False),
                          latency=normalized(measured['first_output_latency_ns'],refs['first_output_latency_ns'],targets['first_output_latency_ns'],True))
    score=sum(policy['weights'][k]*v for k,v in components.items())
    return dict(grade,score=float(score),score_valid=True,area_ratio=measured['area_um2']/refs['area_um2'],
                components=components,weights=policy['weights'],performance=measured,
                reason='All required profile specifications passed; continuous hardware score has no pass threshold.')
