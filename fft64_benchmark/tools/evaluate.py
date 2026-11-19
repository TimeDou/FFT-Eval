"""Measure a complete FFT64 submission with one numerical/protocol/PPA flow."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import sys
import time
import traceback
import numpy as np

from common import ROOT, TECH, COMB, SEQ, flow_identity, read, save, sha
from model import make_frames, quality, reference as fft_reference
from simulate import schedule, simulate, decode


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
    return text, dict(top='fft64_top', files=files,
                      source_sha256=hashlib.sha256(text.encode()).hexdigest())


def used_cell_models(mapped):
    models = []
    for match in re.finditer(r'\bmodule\s+(\w+)\b.*?\bendmodule', (TECH/'cells_sim.v').read_text(), re.S):
        if re.search(r'\b'+re.escape(match[1])+r'\s+\S+\s*\(', mapped):
            models.append(match[0])
    if not models:
        raise ValueError('No mapped standard-cell models found')
    return '\n'.join(models)


def score_result(result, calibration=None):
    passed = (result.get('status') == 'COMPLETE'
              and result.get('quality', {}).get('feasible', False)
              and result.get('protocol_pass', False)
              and result.get('mapped_simulation_pass', False)
              and result.get('ppa', {}).get('timing_pass', False)
              and result.get('ppa', {}).get('formal_status') != 'FAILED')
    if not calibration:
        return dict(resolved=False, score=0.0, area_ratio=None,
                    reason='Measured without an area calibration; functional/PPA feedback is available.')
    if calibration.get('backend') != result.get('backend') or calibration.get('flow_id') != result.get('flow_id'):
        return dict(resolved=False, score=0.0, area_ratio=None,
                    reason='Area reference uses a different backend or measurement setup.')
    base = calibration['reference_area_um2']
    area = result.get('ppa', {}).get('area_um2')
    if not math.isfinite(base) or base <= 0:
        raise ValueError('Invalid reference area')
    if area is None or not math.isfinite(area) or area <= 0 or not passed:
        return dict(resolved=False, score=0.0, area_ratio=None,
                    reason='A functional, quality, timing or mapped-simulation check did not pass.')
    ratio = area/base
    return dict(resolved=ratio <= calibration.get('pass_area_ratio', .8),
                score=float(max(0.0, min(1.0, 1-ratio))), area_ratio=ratio,
                reason='All hardware checks passed; score is the fractional full-design area saving.')


def compact(result):
    quality_result = result.get('quality', {})
    latency = result.get('latency', {})
    ppa = result.get('ppa', {})
    return dict(status=result['status'],
                functional_pass=bool(result.get('protocol_pass') and quality_result.get('feasible')),
                worst_frame_sqnr_db=quality_result.get('minimum_frame_sqnr_db'),
                first_output_cycles=latency.get('first_output_latency_cycles'),
                completion_cycles=latency.get('frame_completion_cycles'),
                timing_pass=ppa.get('timing_pass'), worst_slack_ns=ppa.get('worst_setup_slack_ns'),
                full_mapped_area_um2=ppa.get('area_um2'),
                mapped_simulation_pass=result.get('mapped_simulation_pass'),
                area_ratio=result.get('grade', {}).get('area_ratio'),
                grade=result.get('grade'), failure=result.get('failure'))


def evaluate(submission, outdir, backend='local', seed=20261118, scale=1,
             calibration=None, quick=False, formal=False):
    directory = Path(outdir).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    result = dict(status='RUNNING', backend=backend, seed=seed, scale=scale)
    try:
        spec = read(ROOT/'SPEC.json')
        assert spec['fft']['points'] == 64 and spec['numeric']['per_nonzero_frame_sqnr_min_db'] == 50
        assert spec['timing_protocol']['min_frame_start_interval_cycles'] == 384
        assert spec['timing_protocol']['clock_period_ns'] == 10
        if backend == 'commercial':
            from commercial import preflight
            environment = preflight()
            save(directory/'environment.json', environment)
            if not environment['ready']:
                raise EnvironmentError('VCS/DC/PrimeTime or matching compiled libraries are unavailable; see environment.json')
        source, information = assemble(submission)
        result['source'] = information
        save(directory/'source.json', information)
        if quick:
            frames = np.asarray([x['inputs_iq'] for x in read(ROOT/'public_data/dev_inputs.json')['frames']], dtype=np.int64)
            labels = [x['id'] for x in read(ROOT/'public_data/dev_inputs.json')['frames']]
        else:
            frames, labels = make_frames(seed, scale)
        events, metadata = schedule(frames, seed+17)
        save(directory/'dataset.json', dict(seed=seed, scale=scale, labels=labels,
                                           frames=len(frames), frame_starts=metadata['frame_starts']))
        result['dataset_frames'] = len(frames)
        raw = simulate(source, events, directory/'rtl_sim', 'iverilog' if backend == 'local' else 'vcs')
        outputs, latency = decode(raw, events, metadata)
        quality_result = quality(frames, outputs)
        result.update(protocol_pass=True, quality=quality_result, latency=latency)
        reference = fft_reference(frames)
        predicted = (outputs[..., 0]+1j*outputs[..., 1])/(1 << 15)
        errors = np.sum(abs(predicted-reference)**2, 1)
        energies = np.sum(abs(reference)**2, 1)
        save(directory/'per_frame_quality.json', [
            dict(id=i, family=labels[i], nmse=float(e/s) if s else None,
                 sqnr_db=float(-10*np.log10(e/s)) if s and e else None,
                 exact=bool(e == 0)) for i, (e, s) in enumerate(zip(errors, energies))])
        if not quality_result['feasible']:
            result['status'] = 'QUALITY_FAILED'
        elif quick:
            result['status'] = 'QUICK_CHECK_PASSED'
        else:
            if backend == 'local':
                from local_asic import measure, try_equivalence
                ppa = measure(source, directory/'asic')
                if formal:
                    result['formal'] = try_equivalence(source, directory/'asic')
            else:
                from commercial import measure
                ppa = measure(source, directory/'asic', formal)
            result.update(ppa=ppa, flow_id=flow_identity(backend))
            mapped_source = used_cell_models((directory/'asic/mapped.v').read_text())+'\n'+(directory/'asic/mapped.v').read_text()
            gate_raw = simulate(mapped_source, events, directory/'mapped_sim',
                                'verilator' if backend == 'local' else 'vcs')
            gate_outputs, _ = decode(gate_raw, events, metadata)
            assert np.array_equal(gate_raw[:, 1:3], raw[:, 1:3]), 'Mapped control/cycle mismatch'
            assert np.array_equal(gate_outputs, outputs), 'Mapped payload differs from the RTL'
            if backend == 'local':
                tiny = np.vstack([frames[:2], frames[-3:]])
                tiny_events, tiny_metadata = schedule(tiny, 17)
                four_raw = simulate(mapped_source, tiny_events, directory/'mapped_fourstate', 'iverilog')
                four_outputs, _ = decode(four_raw, tiny_events, tiny_metadata)
                rtl_four = simulate(source, tiny_events, directory/'rtl_fourstate', 'iverilog')
                rtl_outputs, _ = decode(rtl_four, tiny_events, tiny_metadata)
                assert np.array_equal(four_raw[:, 1:3], rtl_four[:, 1:3]) and np.array_equal(four_outputs, rtl_outputs)
            result.update(status='COMPLETE', mapped_simulation_pass=True,
                          mapped_full_four_state=backend == 'commercial')
    except Exception as exc:
        result.update(status='ENVIRONMENT_ERROR' if isinstance(exc, (EnvironmentError, FileNotFoundError)) else 'FAILED',
                      failure=str(exc), traceback=traceback.format_exc())
    result['seconds'] = time.monotonic()-started
    result['grade'] = score_result(result, calibration)
    save(directory/'result.json', result)
    save(directory/'summary.json', compact(result))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--submission', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--backend', choices=['local', 'commercial'], default='commercial')
    parser.add_argument('--seed', type=int, default=20261118)
    parser.add_argument('--scale', type=int, default=1)
    parser.add_argument('--calibration')
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--formal', action='store_true')
    args = parser.parse_args()
    calibration = read(args.calibration) if args.calibration else None
    result = evaluate(args.submission, args.out, args.backend, args.seed, args.scale,
                      calibration, args.quick, args.formal)
    print(json.dumps(compact(result), indent=2))
    return 0 if result['status'] in {'COMPLETE', 'QUICK_CHECK_PASSED'} and result.get('ppa', {}).get('timing_pass', True) else 2


if __name__ == '__main__':
    sys.exit(main())
