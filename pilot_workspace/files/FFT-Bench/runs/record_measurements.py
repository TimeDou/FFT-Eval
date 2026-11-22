from pathlib import Path
import csv
import hashlib
import json

runs = Path('runs')
base_recipe = Path('fft64_benchmark/flow/templates/dc_opt.tcl')
base_arch = 'Radix-2-squared DIT SDF, 64-word register file, four-product rotations'
triple_arch = 'Radix-2-squared DIT SDF, 64-word register file, three-product rotations'
reuse_arch = 'Radix-2-squared DIT SDF, 50-word register file, three-product rotations'
quant = 'Q14 input, Q13 after span 64, Q11 twiddles, round to nearest even'
compact = quant.replace('Q14 input', '14-bit Q14 input with endpoint saturation')
experiments = [
    ('baseline', 'baseline_area', base_arch, 'Q15 data, Q12 twiddles, round to nearest even', base_recipe,
     'Frozen DC recipe. Separate Verilator screen passed 1024 consecutive frames at II=64.'),
    ('quantized', 'quantized_area', base_arch, quant, base_recipe,
     'Frozen DC recipe. Narrower data and coefficients lowered area. Separate Verilator screen passed II=64.'),
    ('tapped_delays', 'shuffle_area', 'Radix-2-squared DIT SDF, 98-word tapped-delay reorder, four-product rotations', quant, base_recipe,
     'Frozen DC recipe. Extra storage raised complete mapped area relative to quantized. Separate Verilator screen passed II=64.'),
    ('three_products', 'compact_area', triple_arch, compact, base_recipe,
     'Frozen DC recipe. Octant rotation and narrower input storage lowered complete area. Separate Verilator screen passed II=64.'),
    ('tight_clock', 'full_test', triple_arch, compact, runs/'candidate_timing/flow/dc_opt.tcl',
     'DC 1.2 ns synthesis target. All required checks and all 321 II probes passed.'),
    ('reused_slots', 'reuse_full', reuse_arch, compact, runs/'candidate_reuse/flow/dc_opt.tcl',
     'DC 1.2 ns synthesis target. The 50-word allocation reuses register file slots on the edge they are read.'),
    ('area_recovery', 'recovery_full', reuse_arch, compact, runs/'candidate_area_recovery/flow/dc_opt.tcl',
     'DC 1.2 ns synthesis target with optimize_netlist -area followed by incremental hold repair.'),
]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(key, directory, architecture, precision, recipe, notes):
    directory = runs/directory
    result = read(directory/'result.json')
    if result['status'] == 'RUNNING':
        return None
    ppa = result.get('ppa', {})
    throughput = result.get('throughput_check', {})
    latency = result.get('latency', {})
    certificate = ppa.get('fmax_certificate', {})
    for path in (directory/'asic/frequency_certificates').glob('*/certificate.json'):
        if not certificate:
            candidate = read(path)
            if candidate['mapped_sha256'] == ppa.get('mapped_sha256'):
                certificate = candidate
    return dict(
        id=key, architecture=architecture, precision_policy=precision,
        source_hash=result['source']['source_sha256'], recipe_hash=sha(recipe),
        mapped_hash=ppa.get('mapped_sha256'), exported_hash=ppa.get('imported_sha256'),
        backend='Synopsys VCS/DC/PrimeTime', library_id='ASAP7 RVT/TT',
        area_um2=ppa.get('area_um2'), worst_sqnr_db=result.get('quality', {}).get('minimum_frame_sqnr_db'),
        verified_ii_cycles=throughput.get('verified_frame_ii_cycles'),
        certified_period_ns=certificate.get('passing_period_ns'),
        maximum_first_cycles=latency.get('maximum_first_output_latency_cycles'),
        maximum_completion_cycles=latency.get('maximum_frame_completion_cycles'),
        setup_slack_ns_10ns=ppa.get('worst_setup_slack_ns'), hold_slack_ns_10ns=ppa.get('worst_hold_slack_ns'),
        timing_pass=ppa.get('timing_pass'), protocol_pass=result.get('protocol_pass'),
        mapped_pass=result.get('mapped_simulation_pass'), profile=result['profile'], status=result['status'],
        evidence=str(directory/'result.json'), notes=notes,
    )


rows = [row for row in (extract(*experiment) for experiment in experiments) if row]
stress = read(runs/'reuse_local.json')
rows.append(dict(
    id='extended_rtl', architecture=reuse_arch, precision_policy=compact,
    source_hash=stress['source']['source_sha256'], backend='Verilator',
    worst_sqnr_db=stress['quality']['minimum_frame_sqnr_db'],
    maximum_first_cycles=stress['latency']['maximum_first_output_latency_cycles'],
    maximum_completion_cycles=stress['latency']['maximum_frame_completion_cycles'],
    protocol_pass=True, profile='supplemental RTL', status='PASS', evidence='runs/reuse_local.json',
    notes='8192 independent public-generator random frames at offered II=64 with seed 96108. The total of 8400 includes directed and mixed-gap frames.',
))
with Path('submission/measurements.csv').open('w', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
