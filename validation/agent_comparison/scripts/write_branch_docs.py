"""Write readable branch entry points from completed independent measurements."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
WORKSPACE = Path('/mnt/DATA1/sj/ALS/DP2.0/DSBench')


if __name__ == '__main__':
    summary = json.loads((ROOT/'analysis/summary.json').read_text())
    assert summary['status'] == 'COMPLETE'
    comparison = WORKSPACE/'FFT-Eval-agent-comparison/validation/agent_comparison'
    for row in summary['cases']:
        name = row['agent']
        branch = WORKSPACE/('FFT-Eval-agent-'+name)
        text = f'''# {name}: verified FFT64 submission

The original final submission is in [submission/](submission/). Independent private evaluation passed numerical, protocol, mandatory continuous service, timing and representative RTL/mapped checks. This is a measured result of one Agent run, not a model-wide capability claim.

| Measurement | Result |
|---|---:|
| Resolved / score valid | true / true |
| Frozen architecture score | {row['score']:.9f} |
| Complete mapped cell area | {row['area_um2']:.5f} μm² |
| Sequential cell area | {row['sequential_area_um2']:.5f} μm² |
| Certified passing clock period | {row['period_ns']:.12f} ns |
| Certified frequency | {row['fmax_mhz']:.6f} MHz |
| Minimum verified frame II | {row['frame_ii']} cycles |
| Effective throughput at certified clock | {row['throughput_ffts_s']:.3f} FFT/s |
| Maximum first-output / completion latency | {row['first_output_cycles']} / {row['completion_cycles']} cycles |
| First-output latency at certified clock | {row['first_output_certified_clock_ns']:.6f} ns |
| Minimum hidden per-frame SQNR | {row['minimum_hidden_sqnr_db']:.6f} dB |

Technology: ASAP7 RVT/TT. Measurement: native VCS/DC/PrimeTime, pre-layout cell area and ideal-interconnect STA. All designs have 64 points and external input/output parallelism 1. The mandatory clock is 10 ns; scoring throughput uses an independent fixed-netlist clock scan. Latency scoring uses the common 10 ns clock, rather than rewarding frequency twice.

Private numerical coverage is 8,192 independent random nonzero frames plus 192 directed cases. Each of the 321 integer intervals 64–384 was exercised with 1,024 consecutive RTL frames. The selected interval passed a representative mapped subset with gap and reset probes from three gate initial states. These are finite observed checks, not a formal worst-case error or full sequential-equivalence guarantee.

The private evaluator imported any supplied mapped netlist and independently measured it. It did not execute Agent optimization scripts. The source, mapped artifact and manifest content are checked, without claiming cryptographically trusted build attestation.

- Final grade: [agent_evaluation/grade.json](agent_evaluation/grade.json).
- Original final measurement: [measurement/result.json](agent_evaluation/measurement/result.json).
- Original public evidence, kept separate: [public_evidence/](agent_evaluation/public_evidence/).
- Actual hidden numerical observations: [numeric_evidence/](agent_evaluation/numeric_evidence/).
- Full interval results: [probe_results.json](agent_evaluation/measurement/throughput/long_intervals/probe_results.json).
- Frozen calibration and provenance: [calibration.json](agent_evaluation/calibration.json), [provenance.json](agent_evaluation/provenance.json).

To verify the archive and replay its numerical outputs and score without EDA tools, run from the repository root with NumPy installed:

```bash
python3 agent_evaluation/verify_archive.py agent_evaluation
```

The verifier does not rerun VCS/DC/PrimeTime. Score replay permits an absolute 1e-14 tolerance for last-bit floating-point runtime differences; the original native score is authoritative. See the companion `validation/three-agent-comparison` branch for the comparison, normalization limitations and design-reasoning review. Other prior result branches are retained unchanged.
'''
        (branch/'AGENT_RESULT.md').write_text(text)
    (comparison/'README.md').write_text('''# Independent review of three completed FFT64 Agent runs

Read [RESULTS.md](RESULTS.md) for the conclusions and [analysis/comparison.csv](analysis/comparison.csv) for the final comparable measurements. The benchmark implementation, scoring policy and accurate-reference calibration were not changed for these candidates.

This private archive preserves all three final submissions, independently remeasured hidden results, calibration evidence, actual compact numerical observations, full II summaries, mapped netlists and tool reports. Large per-cycle text and simulator products remain at the recorded original campaign path. Public previews are archived separately and are not presented as calibrated hidden scores.

## Verify without EDA tools

From the FFT-Eval repository root, using Python with NumPy:

```bash
python3 validation/agent_comparison/scripts/verify_archive.py validation/agent_comparison
```

This checks file hashes, regenerates the exact private inputs, recomputes numerical quality from observed outputs, validates source/netlist identities, checks frequency traces and capacity summaries, reproduces calibration from the two accurate baseline measurements, and recalculates the three grades. Score replay permits an absolute 1e-14 tolerance for last-bit floating-point runtime differences; published scores remain the native recorded values. The saved result is [verification.json](verification.json). It is an archive verification, not another EDA execution.

## Layout

| Path | Contents |
|---|---|
| `cases/<Agent>/submission/` | Untouched final submission, including any exported implementation and recipe |
| `cases/<Agent>/agent_evaluation/measurement/` | Independent private measurement and reports |
| `cases/<Agent>/agent_evaluation/public_evidence/` | Previous public preview, distinct from private scoring |
| `calibration_baselines/` | Accurate folded and block-scheduled R2SDF source and actual complete results |
| `calibration.json` | Matching frozen architecture calibration |
| `numeric_evidence/` | Actual shared hidden input and per-design observed numerical outputs |
| `analysis/` | Comparison CSVs, quality families and PDF/PNG figures |
| `architecture_claim_check.json` | Exhaustive radix-4 bank-allocation counterexample; no new hardware PPA claim |
| `new_agent_environment.json` | Public-only Claude-Fable-5.2 environment readiness receipt |
| `scripts/` | Exact experiment orchestration, analysis and verification scripts |
| `FILE_MANIFEST.json` | Content hashes, excluding the manifest and regenerable verification receipt |

Individual private branches are `agents/Claude-DS-Flash`, `agents/Codex-GPT-6.1-Sol-Max` and `agents/Codex-GPT-6.2-Sol-Max`. Each has its own `AGENT_RESULT.md`, submission and raw evidence. The older branch named `Codex-GPT-6.1-Sol-Max` is preserved and should not be confused with the new `agents/` branch.

To run a fresh hidden EDA evaluation, use the private repository's standard evaluator with `--submission`, `--audience hidden`, `--profile architecture`, a fresh `--out`, and a calibration matching that runtime and protocol. The copied orchestration helpers expect the original campaign layout with `engine/`, `measurements/` and `submissions/` beside them; the compact archive is intended for review and verification. Do not expose its hidden inputs, baselines or calibration in the new Agent workspace.
''')
    print('Readable branch reports written.')
