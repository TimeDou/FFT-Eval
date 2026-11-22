"""Retain source-contract review and compact real native validation evidence."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import shutil


def read(path):
    return json.loads(Path(path).read_text())


def copy(source, target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def compact(source, target):
    ignored = {'csrc','simv.daidir','dc_work','__pycache__','obj'}
    names = {'simv','vectors.txt','output.txt','source.sv','tb.sv','staged.sv','mapped.ddc','lock'}
    for path in sorted(source.rglob('*')):
        if not path.is_file() or any(part in ignored for part in path.parts) or path.name in names:
            continue
        if path.name == 'mapped.v' and 'frequency_certificates' in path.parts:
            continue
        if path.suffix in {'.json','.csv','.rpt','.log','.sdc','.tcl','.npz','.zip'} or path.name in {'mapped.v','input_mapped.v'}:
            copy(path, target/path.relative_to(source))


def write_report(root, target):
    check = read(root/'contract_check.json')
    results = read(root/'summary.json')['cases']
    names = dict(sdf_hidden='Accurate streaming FFT64 reference',
                 folded_hidden='Accurate folded FFT64 reference',
                 public_preview='Streaming FFT64 fixture, freshly built/exported with custom DC recipe')
    rows, summary = [], []
    for case in results:
        grade = case['grade']
        assert grade['resolved'] and grade['score_valid']
        perf = grade['performance']
        probe = read(root/'measurements'/case['id']/'throughput/long_intervals/progress.json')
        assert probe['status'] == 'COMPLETE' and probe['completed_intervals'] == 321
        rows.append(f"| {names[case['id']]} | {grade['scoring_scope']} | {perf['area_um2']:.5f} | "
                    f"{perf['certified_period_ns']:.9f} | {perf['verified_frame_II_cycles']} | "
                    f"{perf['first_output_cycles']} | {case['minimum_sqnr_db']:.4f} | {grade['score']:.9f} |")
        summary.append(dict(design=names[case['id']],scope=grade['scoring_scope'],
            area_um2=perf['area_um2'],period_ns=perf['certified_period_ns'],verified_ii=perf['verified_frame_II_cycles'],
            maximum_first_output_cycles=perf['first_output_cycles'],minimum_sqnr_db=case['minimum_sqnr_db'],
            area_component=grade['components']['area'],throughput_component=grade['components']['throughput'],
            latency_component=grade['components']['latency'],score=grade['score'],score_valid=True,
            official_score=grade['official_score'],long_ii_scan_seconds=probe['wall_seconds'],
            python_peak_rss_kib=probe['process_peak_rss_kib']))
    with (target/'native_summary.csv').open('w') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(summary[0]))
        writer.writeheader();writer.writerows(summary)
    commits = read(root/'published_source_commits.json')
    text = '''# Task-contract and startup-document alignment

The stale specification and SSH descriptions are corrected in both repositories. The public policy, normalization anchors, weights, numerical requirements and runtime scorer are unchanged. The expanded bilingual startup prompt explains nonlinear normalization, component saturation, weighted trade-offs and custom mapped-netlist delivery. Real Synopsys verification and source-level checks are complete; these are evaluator fixtures, not new Agent ranking results.

## Applied review material

At synchronization time DSBench/chat-new-markdown contained four files: AUDIT_REPORT.md, SPEC_JSON_CHANGE_REQUEST.md, START_CN.md and SYNC_MAP.md. The supplied Chinese startup prose is retained in START_PROMPT.md, with heading normalization and one sentence supplying the existing input range/RMS/reference from SPEC. An equivalent full English prompt is included. The specification, SSH guide, optimization guide, task text and score-driven workflow were aligned with this material.

SYNC_MAP refers to fourteen complete files under revised/FFT-Bench, but that directory and those replacement bodies were not supplied. They have not been represented as verbatim replacements. The available originals and their hashes are retained under review_material/ and in source_alignment.json. The audit report itself is archival review evidence, not Agent task instructions.

## Corrected contract

SPEC.scoring.area now describes the public rational-area function and 500/4000 um2 anchors. SPEC.scoring.architecture names the rational-area, logarithmic-throughput and linear-latency functions. SPEC.scoring.latency_score spells out the 63-to-300-cycle scale. SPEC.scoring.missing_calibration and the SSH/root/optimization guides distinguish a valid public preview from calibrated official hidden grading. Every non-scoring section of SPEC is unchanged.

The registration record also binds the current SPEC hash. The existing policy, report source, rendered PDF and report-builder hashes are unchanged. Even descriptive changes alter the protocol identity, so previous calibration is rejected rather than relabeled or edited. Fresh accurate references establish matching native calibration. The actual private operator cached_evaluate path applies that calibration to its matching native results; reuse is recorded and is not a second independent experiment.

## Actual native validation

Both accurate references were evaluated on 8192 independent hidden random nonzero frames plus 192 directed frames. The custom fixture was freshly synthesized and exported using DC, then independently imported by the public evaluator on 1024 random nonzero frames plus 192 directed frames, without private calibration. Every case completes all 321 integer IIs with 1024 consecutive RTL frames per interval, representative RTL/mapped comparisons from three initial states, reset/deadline checks and fixed-netlist setup/hold STA certification. Shorter unsupported intervals are retained as optional failures.

| Fixture | Score scope | Area (um2) | Certified period (ns) | Verified II | Worst first output (cycles) | Minimum SQNR (dB) | Score |
|---|---|---:|---:|---:|---:|---:|---:|
'''+'\n'.join(rows)+'''

The new private Code Grade attachment contains exactly the same policy, scoring source and SPEC as the public source snapshot. Its matching private calibration is included separately. Public preview returns score_valid=true, scoring_scope=public_preview and official_score=false; calibrated hidden results return valid official scores. The native rejection record confirms that the previous calibration cannot score this protocol even though normalization policy is unchanged.

These are pre-layout mapped-cell and ideal-interconnect STA measurements. SQNR is empirical on the declared finite inputs. Full RTL long-stream coverage and representative mapped coverage have different scopes. The source regression suite contains 136 passing tests, including registration/specification binding and stale-calibration rejection; it supplements the real measurements.

## Resources and retained records

Native probe progress files retain Python-process peak RSS and scan wall time. process_resources.json separately samples measurement/prefetch process trees including EDA subprocesses; its summed RSS may double-count shared pages and may miss peaks between samples or before sampling began. It is not an exact cgroup/container peak. Disk usage is recorded for this run only. No claim about post-route PPA, silicon frequency or a new Agent ranking is made.

The archive retains raw JSON/CSV metrics, native tool logs/reports, actual mapped netlists, custom build/export evidence, source hashes, regression logs and grading artifacts. Reconstructible simulator objects and large per-cycle text remain at original_run_directory in FILE_MANIFEST.json. Previous pilot histories, grades and experiment directories are preserved.

## Frozen source and scoring identity

'''
    text += '```json\n'+json.dumps(dict(source_commits=commits,policy_sha256=check['policy_sha256'],
        specification_sha256=check['specification_sha256'],scoring_source_sha256=check['scoring_source_sha256']),indent=2)+'\n```\n'
    (target/'README.md').write_text(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args = parser.parse_args()
    root,target = args.run.resolve(),args.out.resolve()
    assert read(root/'status.json')['status'] == 'COMPLETE'
    assert read(root/'contract_check.json')['status'] == 'PASS'
    target.mkdir(parents=True,exist_ok=True)
    for name in ['config.json','status.json','summary.json','contract_check.json',
                 'published_source_commits.json','source_alignment.json','calibration.json',
                 'calibrated_operator_check.json','prior_calibration_rejection.json','stale_grader_rejection.json',
                 'environment.json','platform_identity.json','frequency_prefetch.json',
                 'process_resources.json','preparation_notes.json','regression_136_tests.log',
                 'custom_build_receipt.json','disk_usage.json','stale_grader_rejection.log']:
        copy(root/name,target/'native'/name)
    for folder in ['measurements','custom_build','grader','logs']:
        compact(root/folder,target/'native'/folder)
    shutil.copytree(root/'public_submission',target/'native/public_submission',dirs_exist_ok=True)
    for name in ['sdf','iterative']:
        shutil.copytree(root/'engine_private/operator/baselines'/name,
                        target/'native/accurate_controls'/name,dirs_exist_ok=True)
    for name in ['driver.py','public_worker.py','prefetch_frequency.py','resource_sampler.py','driver.log','prefetch.log']:
        copy(root/name,target/'native/scripts'/name)
    source = Path(__file__).resolve().parent
    for path in source.iterdir():
        if path.is_file():
            copy(path,target/'scripts'/path.name)
    review = source.parents[1]/'DSBench/chat-new-markdown'
    for path in review.iterdir():
        if path.is_file():
            copy(path,target/'review_material'/path.name)
    write_report(root,target)
    files = {str(p.relative_to(target)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
             for p in sorted(target.rglob('*'))if p.is_file()and p.name!='FILE_MANIFEST.json'
             and '__pycache__'not in p.parts and p.suffix!='.pyc'}
    (target/'FILE_MANIFEST.json').write_text(json.dumps(dict(files=files,
        original_run_directory=str(root),excluded='Reconstructible EDA build objects and large per-cycle vectors/output text; retained privately at original run'),indent=2)+'\n')
    print(json.dumps(dict(files=len(files),bytes=sum(item['bytes']for item in files.values())),indent=2))


if __name__ == '__main__':
    main()
