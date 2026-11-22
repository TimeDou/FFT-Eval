# Operator Scoring Profiles and Reproducible Evaluation

## 1. Current profile

**FFT64-Quant defaults to `architecture`.** It uses hard functional/quality requirements and a continuous hardware score with **60% mapped area, 30% verified throughput, 10% worst first-output latency**. `area` remains an independent **diagnostic** profile, not the default and not comparable to architecture-profile scores.

Use one frozen profile, protocol, backend and toolchain for an evaluation campaign. Do not replace a failed candidate's performance with a previous PASS or a result from another physical flow.

## 2. Commands

From the private evaluator root:

```bash
bash run_evaluation.sh /absolute/path/to/submission \
  --backend auto --profile architecture --out /absolute/path/to/eval_run

bash run_synopsys.sh /absolute/path/to/submission \
  --backend commercial --profile architecture --out /absolute/path/to/eval_synopsys

# Optional area-only diagnostic, in a SEPARATE output directory
bash run_synopsys.sh /absolute/path/to/submission \
  --backend commercial --profile area --out /absolute/path/to/eval_area
```

The private Docker wrapper is `run_synopsys_docker.sh`; see the operator environment configuration for its SSH/shared-mount requirements. Keep private credentials, accurate baselines, calibration, hidden inputs and results outside the agent checkout.

## 3. Calibration and scoring

Calibrate the accurate R2SDF and folded radix-2 baselines **before candidate scoring** with the chosen EDA measurement backend and provided default mapping recipe. Candidate synthesis recipes may differ; the independent measurement, library and constraints remain common. For `architecture`, the area reference is the smaller validated baseline area; the throughput reference is the mandatory II=384 service at 10 ns, while its goal is twice the highest *measured accurate-baseline* throughput; the latency reference is the 300-cycle deadline, with a goal tied to the fastest accurate baseline and a 63-cycle physical floor. These anchors are not necessarily obtained from one physical baseline circuit.

A candidate's reported throughput is

\[
T_{\mathrm{eff}}=10^9/(II_{\mathrm{ver}}P_{\mathrm{STA}})\quad\text{FFTs/s}
\]

with \(II_{\mathrm{ver}}\) the empirically shortest passing integer II from 64–384, and \(P_{\mathrm{STA}}\) a setup/hold-passing certified period on the **fixed mapped netlist**. Each integer II is exercised with ≥1,024 consecutive RTL frames; the selected minimum is independently checked using a representative mapped subset (128 frames, plus the specified gap/reset behavior). The `frame_ii_cycles` value in `design_config.json` is a **hint**, not an independently scoring declared minimum. Clock certification brackets a passing/failing clock within 0.01 ns unless the configured scan floor is reached.

The first-output latency score uses the maximum observed per-frame latency at the **common 10 ns clock**, avoiding a second frequency reward. Numerical quality is a hard SQNR ≥50 dB constraint with no precision bonus. Complete definitions are in [SCORING.md](../fft64_benchmark/SCORING.md).

Default DC mapping performs area optimization followed by incremental hold repair. A custom implementation is instead imported without optimization or hold repair, so its actual cells are measured. Both paths use independent cell-area counting and the same ideal-interconnect setup/hold STA. All candidates must pass those final checks. Never source submitted recipes in the private evaluator. See [OPTIMIZATION.md](../OPTIMIZATION.md).

## 4. Caches, grading, and result evidence

Candidate runs are keyed by RTL source, any exported mapped netlist and recipe manifest, evaluation protocol/seed, backend/platform identity, profile and scoring policy. Mapping caches can be shared across profiles only when the input implementation and measurement flow are identical; **normalization and completed score caches cannot**. Store hashes and the raw measurement directory along with every result.

The private DSBench attachment uses the filename `area_reference.json` for the calibrated profile. It is a **profile-specific calibration object**, not simply a scalar area denominator. Create it only after verifying a commercial baseline calibration:

```bash
python3 fft64_benchmark/grading/make_grader.py \
  --profile architecture \
  --calibration /private/calibration.json \
  --out /private/grader_attachment
```

The official three-field result is `resolved`, `score`, and `reason`; internal reports must additionally preserve `score_valid`/infrastructure status, component scores, measured II, certified period, first/completion latencies, mapped area, worst-frame SQNR and reference hashes.

Unit tests, nominal numerical simulation, a representative gate subset, full mapped long-stream tests, and full hidden numerical evaluation are **different evidence levels**. All hardware data are pre-layout synthesis and ideal-interconnect STA; no post-route, power, or silicon Fmax claim is supported.

## Measurement outcomes and resume

`score_valid=true` is required for ranking. A demonstrated design violation has outcome `DESIGN_INVALID` and a valid zero score. Tool crashes, license faults, timeouts, incomplete outputs and calibration mismatches have no valid score; their three-field `reason` starts with `UNSCORED_INFRASTRUCTURE:`. Quick or unfinished evaluations use `INCOMPLETE:`. The three-field format itself remains `resolved`, `score`, `reason`.

All result directories bind their content identity before using checkpoints. Keep a separate directory when changing RTL, frames, seed, tools, libraries, policy, profile or mapping. A corrupt aggregate can be reconstructed from authenticated completed chunks. Incomplete tool attempts are retried, rather than cached as design failures. `long_intervals/progress.json` records elapsed time and Python-process peak RSS; tool execution receipts record command runtimes.

`DESIGN_PLAN.md` and `measurements.csv` are checked separately in `submission_completeness.json`. Their absence is reported without changing electrical feasibility or hardware quality.
