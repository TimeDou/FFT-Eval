# FFT64 scoring-discrimination evidence

Read [RESULTS.md](RESULTS.md) for the measured comparison and the area-normalization limitation. This directory belongs in the private evaluator repository because it contains hidden inputs, calibration references and complete candidate designs.

The benchmark implementation and scoring policy are unchanged. The evaluator source is Git commit `38a69c08b520eed4b724866f53e2e50a3965cf15`; `campaign.json` records the policy hash, seed, cases and execution settings. `calibration.json` uses only the two accurate references. It is valid for its recorded protocol/tool context; another environment must generate its own matching calibration.

## Contents

| Path | Contents |
|---|---|
| `analysis/measured_scores.csv` | Final comparable hardware measurements and calibrated scores, all nine cases |
| `analysis/*_grade.json` | Final complete grade for each case |
| `analysis/scorer_controls.csv` | Eleven explicitly labelled scorer-only replay checks |
| `analysis/clock_grid_sensitivity.csv` | Scan-resolution bounds, not alternate valid scores |
| `analysis/profile_comparison.csv` | Separate area-profile diagnostic from the measured hardware |
| `analysis/*.pdf`, `analysis/*.png` | Score decomposition, hardware scatter plots and analytical transfer functions |
| `cases/*/submission/` | Actual submitted RTL, configuration and exported custom netlist/recipes where applicable |
| `cases/*/measurement/` | Original measurements, per-frame quality, mapping/STA reports and gate-simulation receipts |
| `capacity/` | Five identity-bound RTL scans, each 321 IIs × 1,024 frames, including failed intervals |
| `numeric_evidence/` | Actual quantized inputs, observed outputs and per-frame latencies in compressed NumPy archives |
| `construction/` | DC/ABC build recipes, identities and reports |
| `cleanup/` | Cleanup plan/receipts in gzip format and preservation checks |
| `FILE_MANIFEST.json` | SHA-256 and byte length of archived evidence |

`measurement/result.json` is preserved verbatim and may contain a provisional, uncalibrated grade. Use `analysis/*_grade.json` and `analysis/measured_scores.csv` for final scoring. The failed quantization case intentionally has no ASIC result.

The original campaign is retained at:

```text
/mnt/DATA1/sj/ALS/DP2.0/DSBench/Synopsys/scoring_checks/scoring_20261122_115331
```

Inside the original SSH container the same directory is `/mnt/mydata/scoring_checks/scoring_20261122_115331`. Large per-cycle text, simulator builds and the frozen source tar remain there. This evidence directory preserves actual observations and reports without duplicating those large intermediates. File hashes establish content consistency, not a cryptographically trusted execution attestation.

## Verify the archive without commercial EDA

From the FFT-Eval repository root, using Python with NumPy:

```bash
python3 validation/scoring_discrimination/scripts/verify_evidence.py
```

This verifies archived hashes, recomputes grades from the unchanged scoring implementation, recomputes numerical quality from actual observed FFT outputs, checks sampled exact-family equality, validates mapped-netlist hash binding, and checks all 321 intervals in each of the five capacity scans. It does not rerun VCS/DC/PrimeTime and cannot replace those original executions. Its saved result is [verification.json](verification.json).

## Rerun an individual hardware comparison

Use the private evaluator in an environment with the supplied ASAP7 libraries and VCS/DC/PrimeTime. The following is the native-container form; invoke it through the repository's SSH bridge when running from the host. Set the library/tool prefix as described in the repository deployment instructions.

```bash
python3 fft64_benchmark/tools/evaluate.py \
  --submission validation/scoring_discrimination/cases/twiddle9_folded/submission \
  --backend commercial --profile architecture --audience hidden --auto-ii \
  --seed 30896565 --out /mnt/mydata/rechecks/twiddle9
```

Use a fresh output path for a changed measurement identity. A standalone rerun without matching calibration produces hardware feedback and an unscored grade. To obtain a final score on another environment, run the two accurate baselines there, generate matching calibration using `tools/scoring.py:make_calibration`, then apply `score_result` to all candidates under that same protocol and tool context. Do not relabel another environment's calibration hashes.

The archived helper scripts besides `verify_evidence.py` are the exact experiment scripts used with the original campaign layout: they expect `campaign.json`, `engine/`, `measurements/` and other working directories next to the scripts. They are retained for inspection and resuming the original layout, rather than advertised as standalone entry points inside this compact evidence directory. The public build/export workflow and the independent evaluator remain the supported route for new experiments.

## Restore archived historical JSON

Only rebuildable old simulator products were deleted. Large Yosys JSON were archived losslessly and can be restored beside their compressed copy:

```bash
gzip -dk /absolute/path/to/mapped.json.gz
```

See `cleanup/receipts.jsonl.gz` for original hashes and paths. Current experiments, handwritten RTL, final mapped Verilog and numerical datasets were retained.
