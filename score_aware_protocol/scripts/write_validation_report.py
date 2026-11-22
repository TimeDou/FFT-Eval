"""Describe actual score-feedback validation without relabeling pilot grades."""
from pathlib import Path
import argparse
import json


def read(path):
    return json.loads(Path(path).read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    root, target = args.run, args.out
    summary = read(root/'summary.json')
    assert summary['status'] == 'COMPLETE'
    rows = []
    resources = []
    names = dict(sdf_hidden='Accurate 64-point streaming reference',
                 folded_hidden='Accurate 64-point folded reference',
                 public_preview='Archived 64-point streaming candidate (validation fixture)')
    for case in summary['cases']:
        ident = case['id']
        result = read(root/'measurements'/ident/'result.json')
        grade = read(root/'measurements'/ident/'validated_grade.json')
        perf = grade['performance']
        assert grade['score_valid'] and grade['resolved']
        rows.append(f"| {names[ident]} | {result['audience']} | {perf['area_um2']:.5f} | "
                    f"{perf['certified_period_ns']:.9f} | {perf['verified_frame_II_cycles']} | "
                    f"{perf['first_output_cycles']} | {case['minimum_sqnr_db']:.4f} | {grade['score']:.9f} |")
        progress = read(root/'measurements'/ident/'throughput/long_intervals/progress.json')
        assert progress['status'] == 'COMPLETE' and progress['completed_intervals'] == 321
        resources.append(f"| {names[ident]} | {progress['wall_seconds']:.1f} | "
                         f"{progress['process_peak_rss_kib']/1024:.1f} | {progress['maximum_batch_input_bytes']/1024**2:.1f} |")
    target.mkdir(parents=True, exist_ok=True)
    commits = read(root/'published_source_commits.json')
    text = '''# Native scoring-feedback and environment validation

The new public numerical scales and actionable preview feedback were tested with real VCS, Design Compiler and PrimeTime. These are evaluator validation fixtures, not new Agent submissions or a new ranking. Historical Agent grades and their original policies remain unchanged on the pilot branches.

Both accurate controls use a fresh private hidden protocol (8192 independent random nonzero frames plus 192 directed frames). The archived candidate uses the actual public evaluator (1024 random nonzero frames plus 192 directed frames), with no private calibration supplied. All three complete the full 321-point II scan, 1024 consecutive frames per interval, representative mapped-netlist checks under three initial-state modes, mandatory service/reset/deadline checks and fixed-netlist STA clock certification. Optional short-II failures are retained. The public candidate receives quantitative components and total score with scoring_scope=public_preview and official_score=false.

The two accurate controls then establish matching private platform/protocol validation. Their measurements do not set any scoring denominator or numeric target. The actual hidden evaluate() path was replayed with this calibration and matching cached physical evidence; both returned valid official hidden scores identical to direct scoring of the same measurements. The replay does not count as a second independent dataset or a new hardware search.

| Hardware fixture | Audience | Area (um2) | Passing period (ns) | Verified frame II | Worst first output (cycles) | Minimum SQNR (dB) | Score |
|---|---|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(rows) + '''

All PPA is pre-layout mapped-cell area and ideal-interconnect STA. SQNR is an empirical result on the declared finite data, not a formal numerical guarantee. The complete raw result, component scores, policy binding, mapped netlists, tool logs, STA certificates, interval summaries and input-generator configuration are retained alongside this report. Large per-cycle text and reconstructible simulator builds remain at the private original run directory recorded in FILE_MANIFEST.json.

## Measured scan resources

Every integer interval 64–384 was tested; no coverage was reduced for this check. Batches hold at most eight II workloads concurrently in one Python process. These figures describe the scanner's Python process and largest single input array, not total machine/container peak memory. Native tool subprocess resources are recorded separately in the logs.

| Hardware fixture | Long-II scan wall seconds | Python peak RSS (MiB) | Largest single input array (MiB) |
|---|---:|---:|---:|
''' + '\n'.join(resources) + '''

## Restart and regression evidence

The complete 135-test regression suite passes. Public scoring/normalization source, tests, documentation and the rebuilt report were committed and pushed before the restarted workspaces were created. The three completed Agent workspaces and their containers were cleared only after their pilot development records and final verified results were pushed to private result branches. Each restarted clone contains one public commit, is clean, and contains no old candidate or experiment. Existing public dependencies were reinstalled from verified sources. Each workspace passed a real environment check including RTL simulation, mapped simulation, DC and PrimeTime. The unused Fable workspace was synchronized and independently passed the same check. These small smoke circuits are environment checks, not FFT results.

The simultaneous ideal objective (500 um2, 62.5 million FFT/s, 63-cycle first output) remains deliberately demanding. The 11 preexisting feasible circuits span 0.4137–0.6748 under an explicitly labelled diagnostic transfer-function replay, with 11 distinct scores at six decimals. This demonstrates useful differentiation on these finite samples, not a universal guarantee or a retrospective official reranking. A fresh common prompt and execution budget are required for the next Agent comparison. Filesystem/container reset does not erase an existing Agent conversation's context.

## Frozen source identity

'''
    text += '```json\n' + json.dumps(commits, indent=2) + '\n```\n'
    (target/'README.md').write_text(text)
    print(target/'README.md')


if __name__ == '__main__':
    main()
