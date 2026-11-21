"""Collect completed native profile results; preserve source experiments."""
from pathlib import Path
import argparse
import csv
import json
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'fft64_benchmark/tools'))
from scoring import score_result,POLICY_SHA256


def read(path):return json.loads(Path(path).read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('evaluation_directory')
    p.add_argument('--shared-dir',default='/home/sj/ALS/DP2.0/DSBench/Synopsys')
    p.add_argument('--container-share',default='/mnt/mydata');p.add_argument('--out',required=True)
    args=p.parse_args();evaluation=Path(args.evaluation_directory).resolve();shared=Path(args.shared_dir).resolve()
    out=Path(args.out).resolve();summary=read(evaluation/'summary.json')
    if summary['status']!='COMPLETE':raise ValueError('Evaluation not complete: '+summary['status'])
    cal=read(evaluation/'calibration.json');profile=cal['profile']
    if cal.get('policy_sha256')!=POLICY_SHA256:raise ValueError('Use the collector from the matching frozen scoring policy')
    def host(path):
        path=Path(path)
        return shared/path.relative_to(args.container_share)if path.is_relative_to(args.container_share)else path
    out.mkdir(parents=True,exist_ok=True)
    for name in ['environment.json','platform_identity.json','protocol.json','calibration.json','summary.json','code_result.json','scores.csv']:
        if(evaluation/name).exists():shutil.copy2(evaluation/name,out/name)
    location=host(read(evaluation/'calibration_location.json')['directory'])
    entries=[(name,'accurate baseline',r,location/name)for name,r in cal['baseline_results'].items()]
    entries += [(r['id'],'candidate',read(host(r['result_directory'])/'result.json'),host(r['result_directory']))for r in summary['submissions']]
    rows=[]
    for name,kind,r,d in entries:
        g=score_result(r,cal);perf=g.get('performance',{});ppa=r.get('ppa',{});lat=r.get('latency',{})
        rows.append(dict(design=name,kind=kind,profile=profile,status=r['status'],resolved=g['resolved'],score=g['score'],score_valid=g['score_valid'],
            area_um2=ppa.get('area_um2'),register_area_um2=ppa.get('register_area_um2'),
            area_component=g.get('components',{}).get('area'),throughput_component=g.get('components',{}).get('throughput'),latency_component=g.get('components',{}).get('latency'),
            certified_period_ns=perf.get('certified_period_ns'),certified_setup_fmax_MHz=perf.get('certified_setup_fmax_MHz'),verified_frame_II_cycles=perf.get('verified_frame_II_cycles'),
            effective_throughput_ffts_per_second=perf.get('effective_throughput_ffts_per_second'),effective_throughput_samples_per_second=perf.get('effective_throughput_samples_per_second'),
            first_output_cycles=perf.get('first_output_cycles'),first_output_ns=perf.get('first_output_latency_ns'),first_output_at_certified_clock_ns=perf.get('first_output_latency_at_certified_clock_ns'),
            frame_completion_cycles=max(lat.get('frame_completion_cycles',[])+r.get('throughput_check',{}).get('latency',{}).get('frame_completion_cycles',[]),default=None),minimum_sqnr_db=min(x for x in [r.get('quality',{}).get('minimum_frame_sqnr_db'),r.get('throughput_check',{}).get('quality',{}).get('minimum_frame_sqnr_db')]if x is not None),frames=r.get('dataset_frames'),
            mapped_pass=r.get('mapped_simulation_pass'),worst_setup_slack_ns=ppa.get('worst_setup_slack_ns'),worst_hold_slack_ns=ppa.get('worst_hold_slack_ns'),
            source_sha256=r.get('source',{}).get('source_sha256'),mapped_sha256=ppa.get('mapped_sha256'),raw_directory=str(d)))
        target=out/'designs'/name;target.mkdir(parents=True,exist_ok=True)
        for file in ['result.json','per_frame_quality.json','dataset.json','source.json','checkpoint.json']:
            if(d/file).exists():shutil.copy2(d/file,target/file)
        for file in ['dc_metrics.json','dc_area.rpt','dc_timing.rpt','dc_units.rpt','pt_metrics.json','pt_timing.rpt','pt_hold.rpt','pt_units.rpt','pt_check.rpt','signature.json','physical_cache.json']:
            if(d/'asic'/file).exists():shutil.copy2(d/'asic'/file,target/file)
        t=r.get('throughput_check',{}).get('directory')
        if t:
            src=host(t)
            for file in ['qualification.json','protocol.json']:
                if(src/file).exists():
                    (target/'throughput').mkdir(exist_ok=True);shutil.copy2(src/file,target/'throughput'/file)
            for file in ['attempts.json','long_intervals/intervals.csv','long_intervals/probe_protocol.json','long_intervals/probe_results.json','long_intervals/progress.json']:
                src=d/'throughput'/file
                if src.exists():
                    dst=target/'throughput'/file;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        certificate=ppa.get('fmax_certificate',{})
        if certificate:
            src=host(certificate['certificate_directory'])
            for file in ['certificate.json','identity.json','trials.csv','setup_at_passing.rpt','hold_at_passing.rpt','fmax_scan/trials.csv','fmax_scan/setup_at_passing.rpt','fmax_scan/hold_at_passing.rpt','fmax_scan/check_at_passing.rpt']:
                dst=target/'frequency'/file;dst.parent.mkdir(parents=True,exist_ok=True)
                if(src/file).exists():shutil.copy2(src/file,dst)
        (target/'scored_with_complete_calibration.json').write_text(json.dumps(g,indent=2)+'\n')
    with(out/'measurements.csv').open('w',newline='')as f:
        w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
    report=dict(status='COMPLETE',profile=profile,scoring_version=cal['scoring_version'],policy_sha256=POLICY_SHA256,
        measurements=rows,measurement_scope='Native VCS/DC/PrimeTime; synthesis cell area and ideal-interconnect STA; no post-route or power claim',raw_evaluation_directory=str(evaluation))
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    labels={'sdf':'Accurate frame-isolated R2SDF','iterative':'Accurate folded radix-2','fft64_solution':'Quantized banked radix-2 reference'}
    def fmt(v,d=3):return '—'if v is None else f'{v:.{d}f}'
    table=['| Design | Area µm² | Certified period ns | Verified II | FFT/s | First-output ns @10ns | Min SQNR dB | Score | Specs |','|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in rows:
        table.append(f"| {labels.get(r['design'],r['design'])} | {fmt(r['area_um2'],2)} | {fmt(r['certified_period_ns'],6)} | {fmt(r['verified_frame_II_cycles'],0)} | {fmt(r['effective_throughput_ffts_per_second'],1)} | {fmt(r['first_output_ns'],0)} | {fmt(r['minimum_sqnr_db'],2)} | {r['score']:.6f} | {'PASS'if r['resolved']else'FAIL'} |")
    text=f'''# Native FFT64 v0.4: {profile} profile

N=64, P_in=P_out=1, ASAP7 RVT/TT, 10ns common target, complete RTL and mapped VCS tests; pre-layout synthesis / ideal-interconnect STA.

'''+ '\n'.join(table)+f'''

Weights, target ratios, and scan settings were frozen before these measurements; policy SHA-256: `{POLICY_SHA256}`. Calibration uses accurate baselines only. `resolved` is independent of score. SQNR is a hard constraint, with no precision bonus.

Area and architecture have separate normalization vectors. Blank frequency/II fields in the area profile mean those quantities were not needed for scoring. Architecture frequency comes from the passing endpoint of a measured setup/hold clock scan; throughput is certified frequency divided by the verified declared frame interval. First-output scoring uses the common 10ns clock, so frequency is not rewarded again through latency.

The baseline called R2SDF is the provided frame-isolated implementation. Its measured service capacity must not be confused with the best possible fully-streaming R2SDF. Verified II is empirical under the saved workload, not a formal all-input minimum.

All successful and failed II pilots, strict mapped checks, clock-scan endpoints and hashes are retained. Three mapped runs use time-zero all-zero, all-one and seeded binary register starts, followed by ordinary reset operation. No runtime signal repair occurs. Full raw logs/netlists remain in the original evaluation directory. No P&R, power or silicon Fmax was measured. See SCORING.md for normalization equations and pre-registration.
'''
    (out/'RESULTS.md').write_text(text)
    print(json.dumps(dict(status='COMPLETE',profile=profile,designs=len(rows),output=str(out)),indent=2))

if __name__=='__main__':main()
