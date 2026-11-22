"""Frozen independent area and architecture/throughput scoring profiles."""
from pathlib import Path
import hashlib
import json
import math

POLICY_PATH=Path(__file__).resolve().parents[1]/'profiles/policy.json'
POLICY=json.loads(POLICY_PATH.read_text())
POLICY_SHA256=hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest()
SCORING_ID='fft64_quant'


def measurement_context(result):
    """Comparable protocol and runtime identities, excluding the candidate RTL."""
    from cache import digest,runtime_identity
    from common import ROOT,sha
    runtime=runtime_identity(result['backend'])
    platform={k:runtime[k]for k in ['tools','libraries','drivers','flow_scripts','python_version','python_sha256','numpy_version']}
    protocol=dict(specification_sha256=sha(ROOT/'SPEC.json'),generator_sha256=sha(ROOT/'tools/model.py'),
                  seed=result['seed'],scale=result['scale'],audience=result['audience'])
    return dict(protocol_fingerprint=digest(protocol),measurement_platform_fingerprint=digest(platform))


def evaluation_outcome(result):
    status=result.get('status')
    if status in {'UNSCORED_INFRASTRUCTURE','ENVIRONMENT_ERROR','FAILED'}:
        return 'UNSCORED_INFRASTRUCTURE'
    if status in {'DESIGN_INVALID','QUALITY_FAILED','THROUGHPUT_FAILED'}:
        return 'DESIGN_INVALID'
    if status=='COMPLETE':
        if hardware_feasible(result):return 'FEASIBLE'
        # Missing evidence is not a demonstrated design violation.
        flags=[result.get('quality',{}).get('feasible'),result.get('protocol_pass'),
               result.get('mapped_simulation_pass'),result.get('ppa',{}).get('timing_pass')]
        if False in flags or result.get('ppa',{}).get('formal_status')=='FAILED':return 'DESIGN_INVALID'
        return 'INCOMPLETE'
    return 'INCOMPLETE'


def profile_policy(profile):
    if profile not in POLICY['profiles']:raise ValueError('Unknown scoring profile: '+str(profile))
    return POLICY['profiles'][profile]


def public_parameters():
    """All arithmetic score parameters are public and independent of inputs."""
    values=dict(POLICY['public_normalization'])
    for name,value in values.items():positive(value,name)
    if not values['area_half_credit_um2']>values['area_ideal_um2']:
        raise ValueError('Area half-credit anchor must exceed the ideal area')
    if not values['throughput_ideal_ffts_per_second']>values['throughput_min_ffts_per_second']:
        raise ValueError('Ideal throughput must exceed mandatory throughput')
    if not values['first_output_max_cycles']>values['first_output_ideal_cycles']:
        raise ValueError('Latency ceiling must exceed ideal latency')
    return values


def component_scores(measured,profile):
    """Smooth area feedback and logarithmic throughput over the measured range."""
    p=public_parameters();area=positive(measured['area_um2'],'area')
    ideal=p['area_ideal_um2'];half=p['area_half_credit_um2']
    area_score=1.0 if area<=ideal else (half-ideal)/(area+half-2*ideal)
    values=dict(area=area_score,throughput=0.0,latency=0.0)
    if profile=='architecture':
        t=positive(measured['effective_throughput_ffts_per_second'],'effective throughput')
        values['throughput']=normalized(math.log(t),math.log(p['throughput_min_ffts_per_second']),
                                       math.log(p['throughput_ideal_ffts_per_second']),False)
        values['latency']=normalized(measured['first_output_cycles'],p['first_output_max_cycles'],
                                     p['first_output_ideal_cycles'],True)
    return values


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
    contexts=[r.get('measurement_context')for r in results.values()]
    if any(context!=contexts[0]for context in contexts):
        raise ValueError('Accurate baselines must share the measured protocol and runtime')
    if contexts[0] is not None:metadata['measurement_context']=contexts[0]
    measured={name:performance(r,profile)for name,r in results.items()}
    best_area=min(measured,key=lambda n:measured[n]['area_um2'])
    area_best=measured[best_area]['area_um2'];p=public_parameters()
    first_result=next(iter(results.values()))
    references=dict(area_um2=p['area_half_credit_um2']);targets=dict(area_um2=p['area_ideal_um2'])
    sources=dict(area_reference='public_half_credit_anchor',area_target='public_ideal_anchor')
    if profile=='architecture':
        clock=POLICY['shared_spec']['clock_period_ns']
        references.update(throughput_ffts_per_second=p['throughput_min_ffts_per_second'],
                          first_output_latency_ns=p['first_output_max_cycles']*clock)
        targets.update(throughput_ffts_per_second=p['throughput_ideal_ffts_per_second'],
                       first_output_latency_ns=p['first_output_ideal_cycles']*clock)
        sources.update(throughput_reference='public_mandatory_service',throughput_target='public_scan_ceiling',
                       latency_reference='public_mandatory_deadline',latency_target='public_serial_input_bound')
    return dict(metadata,backend=first_result['backend'],flow_id=first_result['flow_id'],profile=profile,
                scoring_policy_id=SCORING_ID,policy_sha256=POLICY_SHA256,weights=policy['weights'],
                references=references,targets=targets,anchor_sources=sources,baseline_performance=measured,
                reference_area_um2=references['area_um2'],reference_design='public_physical_anchors',
                accurate_reference_area_um2=area_best,normalization_parameters=p,
                normalization='public fixed rational-area, logarithmic-throughput and linear-latency functions; accurate measurements validate the platform')


def normalized(value,reference,target,lower_is_better):
    span=(reference-target)if lower_is_better else(target-reference)
    if span<0:raise ValueError('Normalization target is in the wrong direction')
    if span==0:return float(value<=target)if lower_is_better else float(value>=target)
    gain=(reference-value)if lower_is_better else(value-reference)
    return float(min(1,max(0,gain/span)))


def score_result(result,calibration=None):
    profile=result.get('profile','area');profile_policy(profile)
    feasible=hardware_feasible(result)
    outcome=evaluation_outcome(result)
    grade=dict(resolved=feasible,feasible=feasible,score=0.0,
               score_valid=outcome=='DESIGN_INVALID',evaluation_outcome=outcome,
               scoring_policy_id=SCORING_ID,profile=profile,policy_sha256=POLICY_SHA256,area_ratio=None,
               scoring_scope='public_preview'if result.get('audience')=='public'else'hidden_evaluation',
               official_score=bool(outcome=='DESIGN_INVALID'and result.get('audience')=='hidden'))
    if outcome=='UNSCORED_INFRASTRUCTURE':return dict(grade,reason='UNSCORED_INFRASTRUCTURE: '+result.get('failure','Measurement could not be completed.'))
    if result.get('status')=='QUICK_CHECK_PASSED':return dict(grade,reason='INCOMPLETE: Public numerical and sustained protocol checks passed; ASIC/capacity scoring was not requested.')
    if outcome=='INCOMPLETE':return dict(grade,reason='INCOMPLETE: Evaluation evidence is not complete; no final score.')
    if not feasible:return dict(grade,reason='DESIGN_INVALID: A required numerical, protocol, timing or RTL/mapped check failed.')
    try:measured=performance(result,profile)
    except ValueError as exc:return dict(grade,reason=str(exc))
    policy=profile_policy(profile)
    preview=result.get('audience')=='public'
    if not calibration and not preview:
        return dict(grade,performance=measured,reason='UNSCORED_INFRASTRUCTURE: Hidden grading requires matching platform/protocol validation calibration; public previews use the published score parameters directly.')
    if calibration:
        expected=dict(backend=result.get('backend'),flow_id=result.get('flow_id'),profile=profile,
                      scoring_policy_id=SCORING_ID,policy_sha256=POLICY_SHA256)
        if any(calibration.get(k)!=v for k,v in expected.items()):
            return dict(grade,reason='UNSCORED_INFRASTRUCTURE: Calibration belongs to another profile, policy, backend or flow; recalibrate.')
        if calibration.get('measurement_context')!=result.get('measurement_context'):
            return dict(grade,reason='UNSCORED_INFRASTRUCTURE: Calibration protocol, numerical runtime or tool identity does not match.')
        if calibration.get('weights')!=policy['weights'] or calibration.get('normalization_parameters')!=public_parameters():
            return dict(grade,reason='UNSCORED_INFRASTRUCTURE: Calibration does not match the published weights and numeric normalization.')
    components=component_scores(measured,profile)
    score=sum(policy['weights'][k]*v for k,v in components.items())
    return dict(grade,score=float(score),score_valid=True,area_ratio=measured['area_um2']/public_parameters()['area_half_credit_um2'],
                components=components,weighted_components={k:policy['weights'][k]*v for k,v in components.items()},
                weights=policy['weights'],performance=measured,normalization_parameters=public_parameters(),
                scoring_scope='public_preview'if preview else'hidden_evaluation',official_score=not preview,
                reason=('PUBLIC_PREVIEW: All public hardware checks passed; component scores use the published fixed numeric targets. Final acceptance requires independent hidden evaluation.'if preview else
                        'All required profile specifications passed; continuous hardware score has no pass threshold.'))
