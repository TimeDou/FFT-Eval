"""Separate hardware feasibility from continuous, calibrated PPA ranking."""
import math

SCORING_VERSION = 'verified_workload_throughput_per_area_v1'


def hardware_feasible(result):
    return bool(result.get('status') == 'COMPLETE'
                and result.get('quality', {}).get('feasible', False)
                and result.get('protocol_pass', False)
                and result.get('mapped_simulation_pass', False)
                and result.get('ppa', {}).get('timing_pass', False)
                and result.get('ppa', {}).get('formal_status') != 'FAILED')


def positive(value, name):
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError('Missing or invalid measured '+name)
    return value


def performance(result):
    """Use the serviced workload II, never assume a faster intrinsic frame II.

    The capacity at that II uses the pre-layout STA limiting period, including
    the fixed setup uncertainty. It is an estimate, not post-route Fmax or a
    measured physical-device rate. Target-clock service is reported separately.
    """
    ppa = result.get('ppa', {})
    latency = result.get('latency', {})
    area = positive(ppa.get('area_um2'), 'area')
    period = positive(ppa.get('effective_required_period_ns'), 'STA period')
    interval = positive(latency.get('offered_frame_II'), 'verified workload frame II')
    clock = positive(ppa.get('clock_period_ns', latency.get('clock_period_ns')), 'target clock period')
    rate = 64e9/(interval*period)
    return dict(area_um2=area, limiting_period_ns=period,
                prelayout_fmax_estimate_MHz=1000/period,
                verified_workload_frame_II_cycles=interval,
                target_clock_samples_per_second=64e9/(interval*clock),
                sta_throughput_samples_per_second=rate,
                sta_throughput_per_area=rate/area)


def make_calibration(results, **metadata):
    """Select one real exact design with the best throughput/area as anchor.

    Area, period and II always come from that same implementation; independent
    best-area and best-frequency numbers are not combined into a fictitious RTL.
    """
    if not results or not all(hardware_feasible(r) for r in results.values()):
        raise ValueError('Every accurate calibration design must pass all hardware checks')
    if len({(r.get('backend'), r.get('flow_id')) for r in results.values()}) != 1:
        raise ValueError('Calibration designs must share the same backend and flow')
    measured = {name: performance(result) for name, result in results.items()}
    selected = max(measured, key=lambda name: measured[name]['sta_throughput_per_area'])
    anchor = measured[selected]
    result = results[selected]
    return dict(metadata, backend=result['backend'], flow_id=result['flow_id'],
                scoring_version=SCORING_VERSION, reference_design=selected,
                reference_area_um2=anchor['area_um2'],
                reference_period_ns=anchor['limiting_period_ns'],
                reference_frame_II_cycles=anchor['verified_workload_frame_II_cycles'],
                reference_performance=anchor, baseline_performance=measured,
                score='E/(1+E), E=(A_ref/A)*(II_ref/II)*(T_ref/T)')


def score_result(result, calibration=None):
    feasible = hardware_feasible(result)
    grade = dict(resolved=feasible, feasible=feasible, score=0.0,
                 score_valid=not feasible and result.get('status') in {'COMPLETE','QUALITY_FAILED','FAILED'},
                 scoring_version=SCORING_VERSION, area_ratio=None)
    if not feasible:
        return dict(grade, reason='A required functional, quality, protocol, timing or mapped-netlist check did not pass.')
    try:
        measured = performance(result)
    except ValueError as exc:
        return dict(grade, resolved=False, feasible=False, reason=str(exc))
    if not calibration:
        return dict(grade, performance=measured,
                    reason='Required hardware checks passed; a matching PPA calibration is needed for a valid score.')
    if (calibration.get('backend') != result.get('backend')
            or calibration.get('flow_id') != result.get('flow_id')):
        return dict(grade, reason='Required hardware checks passed; PPA reference uses another backend or flow.')
    if calibration.get('scoring_version') != SCORING_VERSION:
        return dict(grade, reason='Required hardware checks passed; recalibrate for the current continuous PPA scoring policy.')
    try:
        area_ref = positive(calibration.get('reference_area_um2'), 'reference area')
        period_ref = positive(calibration.get('reference_period_ns'), 'reference period')
        interval_ref = positive(calibration.get('reference_frame_II_cycles'), 'reference workload II')
    except ValueError as exc:
        return dict(grade, reason=str(exc))
    area_ratio = measured['area_um2']/area_ref
    efficiency = ((area_ref/measured['area_um2'])*
                  (interval_ref/measured['verified_workload_frame_II_cycles'])*
                  (period_ref/measured['limiting_period_ns']))
    score = 1.0/(1.0+1.0/efficiency)
    return dict(grade, score=float(score), score_valid=True, area_ratio=area_ratio,
                relative_throughput_per_area=efficiency, performance=measured,
                reason='All required hardware specifications passed; score ranks throughput per area at the verified workload II (reference=0.5).')
