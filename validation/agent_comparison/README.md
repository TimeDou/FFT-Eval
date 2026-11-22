# Independent review of three completed FFT64 Agent runs

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
