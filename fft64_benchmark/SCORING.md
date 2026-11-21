# FFT64-Quant: Feasibility and Scoring

This document describes the **default `architecture` profile**. `--profile area` is a separate diagnostic profile and its scores must not be mixed with architecture-profile scores. The numerical contract is defined in [SPEC.json](SPEC.json); the equations below agree with the report in [FFT64-Quant.pdf](../docs/FFT64-Quant.pdf).

## 1. Feasibility is independent of optimization quality

`resolved=true` means that all mandatory checks pass: FFT function and natural-order outputs; minimum nonzero-frame SQNR ≥ 50 dB and exact zero for zero frames; reset and input/output protocol; service at II=384; first-output and completion deadlines; 10 ns setup/hold timing; and representative RTL-to-mapped-netlist consistency. No minimum area reduction or score is required. A feasible design may receive `score=0`.

An infrastructure failure or missing valid calibration is **not** a hardware design failure; no official score is assigned. Internal results set `score_valid=false`. The three-field platform result uses the prefix `UNSCORED_INFRASTRUCTURE:` in `reason`; such results must be excluded from rankings even if its required numeric `score` field is zero.

## 2. Measured hardware quantities

- **Area,** \(A\): complete pre-layout mapped top-module standard-cell area, including sequential cells, control, reordering, and all standard-cell storage.
- **Verified frame interval,** \(II_{\mathrm{ver}}\): the smallest passing integer II in **64–384 cycles/frame**, found from at least **1,024 consecutive RTL frames at every interval**, with a representative mapped-netlist check at the selected interval. Optional faster-II failures do not invalidate II=384 feasibility. The user-provided `frame_ii_cycles` is only a hint.
- **Certified clock period,** \(P_{\mathrm{STA}}\): a setup/hold-passing PrimeTime or OpenSTA clock-scan endpoint on the same fixed mapped netlist, with a passing/failing bracket ≤ 0.01 ns unless the configured scan floor is reached. This is pre-layout estimated timing, **not silicon Fmax**.
- **Throughput,** \(T_{\mathrm{eff}}=10^9/(II_{\mathrm{ver}}P_{\mathrm{STA}})\) FFTs/s, with the period in ns. Frequency contributes through this term once; no separate frequency bonus is added.
- **Latency,** \(L\): the **maximum observed first-output latency** across scored completed frames, in cycles. The latency score uses the **common 10 ns target clock**, so frequency is not rewarded twice. Frame-completion latency is also checked per frame, but not scored separately.

## 3. Continuous score

For every feasible candidate, normalize the three components to [0,1]:

\[
S_A=\operatorname{clip}\left(\frac{A_{\mathrm{ref}}-A}{A_{\mathrm{ref}}-A_{\mathrm{goal}}},0,1\right),\qquad A_{\mathrm{goal}}=0.5A_{\mathrm{ref}},
\]
\[
S_T=\operatorname{clip}\left(\frac{T_{\mathrm{eff}}-T_{\mathrm{req}}}{T_{\mathrm{goal}}-T_{\mathrm{req}}},0,1\right),
\]
\[
S_L=\operatorname{clip}\left(\frac{300-L}{300-L_{\mathrm{goal}}},0,1\right).
\]

Here \(T_{\mathrm{req}}=10^9/(384\cdot10)\) FFTs/s; \(T_{\mathrm{goal}}\) is twice the fastest measured throughput among the validated accurate calibration designs; and \(L_{\mathrm{goal}}\) is the larger of half the shortest accurate first-output latency and the physical lower bound of 63 cycles. All references and targets are **profile- and backend-specific**. The default combined score is

\[
\boxed{S=0.60S_A+0.30S_T+0.10S_L.}
\]

A demonstrated violation of a mandatory hardware condition is `DESIGN_INVALID` and receives a valid score of zero. An interrupted or failed measurement is unscored. These normalization targets and weights come from `profiles/policy.json` and are frozen before scored agent runs; they are **not** re-tuned using the results of evaluated agents. Higher SQNR does not earn extra credit once the 50 dB threshold is passed.

## 4. Validation workload and comparability

- Numerical: at least **1,024 public** / **8,192 hidden** independently generated nonzero 64-point frames, plus directed cases. Feasibility uses the **minimum** nonzero-frame SQNR; it is not based on the average.
- Mandatory service: at least **1,024 consecutive frames** at II=384, with variable gaps, reset probes, and worst per-frame first/completion latency measured.
- Architecture capacity: each integer II from 64 through 384 receives at least **1,024 consecutive RTL frames**; the selected shortest passing II is checked again against a representative **128-frame RTL/mapped subset**, including mixed gaps and reset cases. This is empirical capacity, not a proof that no shorter interval could work.
- Mapped numerical/protocol comparison uses **representative subsets** and cannot be reported as 8,192 fully mapped frames.
- Each backend is calibrated on two accurate FFT baselines using the **same flow** as the candidate. Commercial VCS/DC/PrimeTime and open-source Icarus/Verilator/Yosys/ABC/OpenSTA metrics are reported separately. All reported ASIC area/timing values are pre-layout/ideal-interconnect unless explicitly stated otherwise.

## 5. Grader output

The platform writes `/eval/code_result.json` with exactly:

```json
{"resolved": true, "score": 0.0, "reason": "Mandatory specifications passed."}
```

The example illustrates that **a zero score can still be feasible**, not an actual candidate result. Detailed measurements, backend identity, calibration fingerprint, per-frame errors, timing certificates, and cache identities are stored in the private evaluation output. Absence of calibrated tools or an interrupted run must be treated as **unscored infrastructure**, not a valid zero-performance design.

Submission completeness is reported separately in `submission_completeness.json`. Missing design notes or a measurement table does not alter measured hardware feasibility or the hardware score. A warning records an invalid optional II hint; throughput remains measured.
