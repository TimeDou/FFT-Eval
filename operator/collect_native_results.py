"""Collect completed native results without changing any recorded experiment."""
from pathlib import Path
import argparse
import csv
import json
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'fft64_benchmark/tools'))
from scoring import score_result


def read(path):return json.loads(Path(path).read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evaluation_directory')
    parser.add_argument('--shared-dir',default='/home/sj/ALS/DP2.0/DSBench/Synopsys')
    parser.add_argument('--container-share',default='/mnt/mydata')
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    evaluation=Path(args.evaluation_directory).resolve();shared=Path(args.shared_dir).resolve()
    out=Path(args.out).resolve()
    summary=read(evaluation/'summary.json')
    if summary['status']!='COMPLETE':raise ValueError('Evaluation is not complete: '+summary['status'])
    calibration=read(evaluation/'calibration.json')
    def host(path):
        p=Path(path)
        if p.is_relative_to(args.container_share):return shared/p.relative_to(args.container_share)
        return p
    out.mkdir(parents=True,exist_ok=True)
    for name in ['environment.json','platform_identity.json','protocol.json','calibration.json','summary.json','code_result.json','scores.csv']:
        if(evaluation/name).exists():shutil.copy2(evaluation/name,out/name)
    location=host(read(evaluation/'calibration_location.json')['directory'])
    entries=[(name,'accurate baseline',result,location/name)
             for name,result in calibration['baseline_results'].items()]
    for row in summary['submissions']:
        directory=host(row['result_directory'])
        entries.append((row['id'],'candidate',read(directory/'result.json'),directory))
    rows=[]
    for name,kind,result,directory in entries:
        grade=score_result(result,calibration);performance=grade.get('performance',{})
        ppa=result.get('ppa',{});lat=result.get('latency',{})
        first=max(lat.get('first_output_latency_cycles',[]),default=None)
        completion=max(lat.get('frame_completion_cycles',[]),default=None)
        rows.append(dict(design=name,kind=kind,status=result['status'],resolved=grade['resolved'],score=grade['score'],
                         score_valid=grade['score_valid'],area_um2=ppa.get('area_um2'),register_area_um2=ppa.get('register_area_um2'),
                         limiting_period_ns=performance.get('limiting_period_ns'),
                         prelayout_fmax_estimate_MHz=performance.get('prelayout_fmax_estimate_MHz'),
                         verified_workload_frame_II_cycles=performance.get('verified_workload_frame_II_cycles'),
                         target_clock_samples_per_second=performance.get('target_clock_samples_per_second'),
                         sta_throughput_samples_per_second=performance.get('sta_throughput_samples_per_second'),
                         first_output_cycles=first,frame_completion_cycles=completion,
                         first_output_ns=first*10 if first is not None else None,
                         frame_completion_ns=completion*10 if completion is not None else None,
                         minimum_sqnr_db=result.get('quality',{}).get('minimum_frame_sqnr_db'),
                         frames=result.get('dataset_frames'),mapped_pass=result.get('mapped_simulation_pass'),
                         mapped_initial_state_modes=json.dumps(result.get('mapped_initial_state_modes')),
                         worst_slack_ns=ppa.get('worst_setup_slack_ns'),
                         source_sha256=result.get('source',{}).get('source_sha256'),
                         mapped_sha256=ppa.get('mapped_sha256'),raw_directory=str(directory)))
        target=out/'designs'/name;target.mkdir(parents=True,exist_ok=True)
        for file in ['result.json','per_frame_quality.json','dataset.json','source.json','mapping_schedule.json']:
            if(directory/file).exists():shutil.copy2(directory/file,target/file)
        for file in ['dc_metrics.json','dc_area.rpt','dc_timing.rpt','dc_units.rpt','pt_metrics.json','pt_timing.rpt','pt_units.rpt','pt_check.rpt','signature.json']:
            if(directory/'asic'/file).exists():shutil.copy2(directory/'asic'/file,target/file)
        (target/'scored_with_complete_calibration.json').write_text(json.dumps(grade,indent=2)+'\n')
    with(out/'measurements.csv').open('w',newline='')as stream:
        writer=csv.DictWriter(stream,list(rows[0]));writer.writeheader();writer.writerows(rows)
    report=dict(status='COMPLETE',backend='commercial',scoring_version=calibration['scoring_version'],
                reference_design=calibration['reference_design'],measurements=rows,
                measurement_scope='Native VCS/DC/PrimeTime; pre-layout area and ideal-interconnect STA; no post-route/power claim',
                raw_evaluation_directory=str(evaluation))
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    table=['| Design | Area µm² | STA limit ns | Fmax estimate MHz | Minimum SQNR dB | First/completion cycles | Score | Specs |',
           '|---|---:|---:|---:|---:|---:|---:|---|']
    labels={'sdf':'Accurate R2SDF','iterative':'Accurate folded radix-2',
            'fft64_solution':'Quantized banked radix-2 reference'}
    for row in rows:
        table.append(f"| {labels.get(row['design'],row['design'])} | {row['area_um2']:.2f} | {row['limiting_period_ns']:.4f} | {row['prelayout_fmax_estimate_MHz']:.2f} | {row['minimum_sqnr_db']:.2f} | {row['first_output_cycles']}/{row['frame_completion_cycles']} | {row['score']:.6f} | {'PASS'if row['resolved']else'FAIL'} |")
    text='''# Local Synopsys validation

The complete benchmark ran in the SSH-accessible Synopsys container, including both accurate calibration architectures and the candidate RTL. No open-source PPA replaced native commercial measurements.

'''+ '\n'.join(table)+f'''

All rows use N=64, one complex input/output per valid cycle, the same ASAP7 RVT/TT libraries, 10 ns target clock, verified frame II=384, and the same protocol and input seed. Target-clock service is 16.6667 M complex samples/s. The Fmax and throughput used for ranking are estimates from pre-layout STA, not physical-device or post-route measurements.

The reference anchor is `{calibration['reference_design']}`. Every design satisfying the required specifications has `resolved=true`; score has no pass threshold. `score=E/(1+E)` ranks normalized throughput/area efficiency, with the anchor at 0.5.

Mapped VCS verification runs the complete dataset from all-zero, all-one, and seed-20261121 time-zero register states. It compares control cycles and all valid payload samples to ordinary four-state RTL simulation, including resets during processing and long idle periods. No signal is repaired after time zero. This covers the observed reset X-pessimism artifact without masking it by testing only all-zero initialization.

Machine-readable data, per-frame quality, mapping/STA reports and source/library/tool identities are saved beside this report. Full compile/runtime logs and netlists remain in the original evaluation directory and its feedback archive. Power and P&R were not measured.
'''
    (out/'RESULTS.md').write_text(text)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
