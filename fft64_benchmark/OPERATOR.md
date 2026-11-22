# FFT64-Quant: Private Operator Instructions

**This file belongs in FFT-Eval, not the public FFT-Bench checkout.** Keep accurate baseline RTL, scoring calibration, hidden seeds, private grader and agent results inaccessible to the evaluated agent.

## Freeze before scoring

1. Choose the **default `architecture` profile** (or deliberately run a separate `area` diagnostic).
2. Select one backend (`commercial` when its tools and licenses are usable, otherwise `local`) and freeze its tool executables, cell library, constraints and score policy.
3. Freeze the input protocol/seed and generated frame family. Public numerical ≥1,024 nonzero random frames; hidden ≥8,192, both with directed cases. The mandatory 384-cycle service and each tested integer II use ≥1,024 consecutive frames.
4. Calibrate the accurate SDF and folded radix-2 baselines with **the same measurement backend and provided default mapping recipe**. Store exact source/library/tool hashes and raw results. Candidate recipes may differ; direct artifact import retains their optimization while final measurement remains common.
5. Only after successful calibration, evaluate agent submissions and publish scores.

## Evaluator use

From the private repository root:

```bash
bash run_evaluation.sh /absolute/path/to/submission \
  --backend auto --profile architecture --out /absolute/path/to/evaluation
```

A complete `architecture` run tests all integer IIs 64–384 with long RTL streams and validates the selected minimum on a representative mapped subset. Verified II is **measured**, not taken from the agent's `frame_ii_cycles` hint. Highest-frequency credit comes from a passing setup/hold STA clock-scan endpoint; first-output latency uses the worst observed value at the common 10 ns clock. SQNR feasibility uses the **minimum** across applicable nonzero input frames. Optional faster-II failures do not negate the mandatory service contract.

Custom synthesis scripts run only in the public development environment. The private evaluator accepts a source/library-bound structural implementation and independently counts cells, runs STA and validates mapped behavior. Do not execute submitted scripts or use their reports as measurement data. [OPTIMIZATION.md](../OPTIMIZATION.md) describes the interface. Freeze the evaluator and reference anchors before a ranked campaign; caches and calibrations must match their recorded source identities.

## DSBench attachment

Generate a commercial-only private attachment with a calibration that matches the chosen profile and input protocol:

```bash
python3 fft64_benchmark/grading/make_grader.py \
  --profile architecture --calibration /private/calibration.json \
  --out /private/grading_files
```

Deliver the grader and calibrated reference **only to the grading environment**. The file named `area_reference.json` may contain architecture-profile anchors; inspect its embedded `profile` and policy hash. The interface exports exactly `resolved`, `score`, `reason`; retain additional private logs that distinguish invalid designs from infrastructure failures.

Measurements establish finite-sample functional and numerical behavior, pre-layout mapped area and ideal-interconnect timing. Report only the evidence produced by the selected flow.
