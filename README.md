# FFT64-Quant: Private Evaluation Repository

**Operator only.** This repository contains accurate reference RTL, calibration tools, hidden evaluation code and regression tests. Do not place any of these private resources in an Agent's development workspace. The separate FFT-Bench repository is the public task package.

## Evaluation contract

FFT64-Quant requires a correct, unscaled, natural-order 64-point fixed-point complex FFT. Mandatory checks cover per-frame SQNR ≥50 dB, input/output and reset behavior, sustained II=384 service, output latency, 10 ns setup/hold timing and representative RTL/mapped agreement. `resolved` indicates feasibility independently of hardware-quality score. The default `architecture` profile combines area (60%), verified effective throughput (30%) and worst observed first-output latency (10%). The optional `area` profile is a separate diagnostic.

Two accurate fixed-point implementations—R2SDF and folded radix-2—serve as **calibration anchors**, not agent-visible solutions. The float64 FFT of the same quantized input is the distinct numerical oracle. Candidate synthesis recipes may differ from the baseline default recipe, but final evaluation uses the same technology library, timing constraints and independent measurement procedure.

## Operator commands

From the private repository root:

```bash
# Environment inspection
bash run_evaluation.sh --check-only

# Development or private evaluation on the selected backend
bash run_evaluation.sh /absolute/path/to/submission \
  --backend auto --profile architecture --out /absolute/path/to/eval_run

# Explicit commercial evaluation
bash run_synopsys.sh /absolute/path/to/submission \
  --backend commercial --profile architecture --out /absolute/path/to/eval_synopsys

# Regression fixtures (not real ASIC runs)
python3 -m unittest discover -s operator/tests -q
```

The Docker/SSH operator path is provided by `run_synopsys_docker.sh`; the public Agent-facing path is documented in FFT-Bench's `REMOTE_SYNOPSYS.md`. Use an independent result directory for every changed candidate and freeze the backend for a scored campaign.

## Custom implementation evaluation

A candidate may submit a flattened ASAP7 netlist (`implementation/mapped.v`) with a matching manifest and optional development recipes. The private evaluator **does not execute those recipes**. It imports the structural netlist, checks mapped cells, independently measures complete area and setup/hold timing, and verifies representative mapped behavior against the submitted RTL. With no custom implementation, trusted default synthesis is used. The manifest checks submitted-content consistency; it is not a cryptographically trusted record of EDA tool execution. See [OPTIMIZATION.md](OPTIMIZATION.md).

## Test coverage and interpretation

Numerical tests use 1,024 public or 8,192 hidden random nonzero frames plus directed cases. Mandatory long-stream service runs at II=384. Architecture throughput probes 321 integer II values (64–384) with at least 1,024 RTL frames per interval and representative mapped confirmation at the selected shortest passing value. The minimum per-frame SQNR and maximum per-frame latencies govern feasibility. Area and frequency estimates are **pre-layout**; mapped comparisons are subsets, not full hidden-set sequential-equivalence proofs.

Only a matching calibrated backend/profile/toolchain can produce a valid score. `DESIGN_INVALID` indicates an observed hardware violation; `UNSCORED_INFRASTRUCTURE` indicates an unavailable or interrupted measurement and must not enter rankings. See [VALIDATION.md](VALIDATION.md) and [operator/SCORING_PROFILES.md](operator/SCORING_PROFILES.md).

## Private grading attachment

`fft64_benchmark/grading/make_grader.py` packages the official **commercial** DSBench evaluator against a frozen commercial calibration. The filename `area_reference.json` contains a full profile-specific calibration object, not merely one area number. The Code Grade result has exactly `resolved`, `score` and `reason`; internal records retain `score_valid`, component measurements and tool/experiment identities.

Keep real execution receipts, baseline calibration and source snapshots together. Source files alone do not establish measured hardware performance. Offline runtimes can use a supplied wheel cache; do not include hidden material in public archives or Agent-visible mounts.
