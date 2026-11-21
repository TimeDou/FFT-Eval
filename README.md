# FFT64-Quant Private Evaluator

**Private operator repository. Do not expose this repository, reference RTL, private calibration, seeds, or scoring results to evaluated agents.** The public agent package is maintained separately in FFT-Bench.

## Evaluation objective

Evaluate a complete 64-point fixed-point FFT. Feasibility requires correct numerical, reset, protocol, mandatory II=384 service, 10 ns timing, and mapped-netlist behavior. Feasible designs are scored continuously using complete mapped area (60%), verified effective throughput (30%), and maximum first-output latency (10%). A low or zero hardware score **does not** make a feasible design unresolved. Default profile: `architecture`; `area` is a separate diagnostic profile.

The implementation uses two isolated baselines (accurate R2SDF and accurate folded radix-2), **not an optimized reference solution**, to calibrate each EDA backend. The float64 FFT of the same already-quantized input remains the numerical reference.

## Operator commands

```bash
# Check environment, tools, and library availability
bash run_evaluation.sh --check-only

# Automatically select the available backend
bash run_evaluation.sh /absolute/path/to/submission \
  --profile architecture --backend auto --out /absolute/path/to/evaluation_run

# Explicit commercial run (requires calibrated tools/licenses)
bash run_synopsys.sh /absolute/path/to/submission \
  --profile architecture --backend commercial --out /absolute/path/to/evaluation_run

# Regression tests (Python fixtures; not a substitute for real EDA runs)
python3 -m unittest discover -s operator/tests -v
```

`run_synopsys_docker.sh` supports the operator-controlled SSH Docker environment; see [operator/SCORING_PROFILES.md](operator/SCORING_PROFILES.md). Use absolute paths and separate candidate evaluation directories. The public task entrypoint uses `fft64_benchmark/run_preview.sh`.

## Test scope and measurements

- Public numerical: ≥1,024 random nonzero frames + directed cases.
- Hidden numerical: ≥8,192 random nonzero frames + directed cases.
- Mandatory service: ≥1,024 consecutive frames at II=384, including resets and irregular gaps.
- Architecture throughput: 321 integer IIs (64–384), ≥1,024 RTL frames per interval; shortlisted best II receives representative 128-frame mapped confirmation.
- Mapped verification: representative numerical/transaction subset under the supported initialization modes, not the entire hidden numerical set.
- Clock and area: full synthesis plus setup/hold-constrained STA on a fixed mapped netlist. Physical data are **pre-layout**, with no post-route or power claims.

A candidate is compared only with a **matching calibrated reference** from the same backend, libraries, frozen protocol, and scoring profile. The selected backend must not change within an evaluated campaign. If the required tool/license/calibration is unavailable, mark the run **UNSCORED_INFRASTRUCTURE** rather than ranking it as a valid zero-score design.

## Measurement evidence

[VALIDATION.md](VALIDATION.md) explains the regression coverage and where to find measured RTL, mapped netlists, calibration, simulator logs and STA reports. Source-only exports contain evaluator code; the private agent-result branch contains the separate measurement evidence. Use the source snapshot recorded with each measurement to reproduce it.

## Packaging

`fft64_benchmark/grading/make_grader.py` prepares a small private DSBench attachment for a **commercial** frozen calibration. Verify its input protocol and environment fingerprint before release; its `area_reference.json` filename holds a profile-specific calibration, not merely an area number. The `code_result.json` interface contains exactly `resolved`, `score`, and `reason`, with detailed measurements kept separately.

## Python dependency

Setup reuses an installed NumPy. If it is absent, pip installs a compatible binary wheel from the configured package source. For offline Docker evaluation, provide an external wheel cache with `--wheelhouse /absolute/shared/path/to/wheels`; the cache is not part of the repository or source snapshot.
