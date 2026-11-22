# FFT64-Quant: Feasibility and Hardware-Quality Scoring

The default `architecture` profile measures complete-circuit area, verified throughput, and first-output latency. The optional `area` profile is a separate diagnostic; **scores from different profiles or EDA backends are not comparable**. The numerical and I/O requirements are specified in [SPEC.json](SPEC.json).

## 1. Feasibility

A design is feasible (`resolved=true`) only when it passes every mandatory test: FFT function and output ordering, per-frame SQNR of at least 50 dB for each evaluated nonzero frame, exact zero output for zero input, streaming protocol and reset behavior, sustained service at II=384, first-output/completion deadlines, 10 ns setup/hold timing, and representative RTL-to-mapped verification. **There is no minimum area saving or score required to pass.** A feasible design may have a score of zero.

Infrastructure failures are different from design violations. The evaluator preserves `score_valid` internally: `DESIGN_INVALID` is a demonstrated violation and a valid zero-score result, whereas `UNSCORED_INFRASTRUCTURE` and `INCOMPLETE` are not ranked. The platform's three-field result includes the corresponding prefix in `reason` because it has no separate `score_valid` field.

## 2. Measured quantities

| Metric | Definition | Evaluation rule |
|---|---|---|
| Mapped area, \(A\) | Sum of the areas of all mapped top-level standard-cell instances | Includes registers, memory implemented in cells, reordering, routing logic, arithmetic and control |
| Verified frame interval, \(II_{\rm ver}\) | Smallest tested integer interval in 64–384 cycles/frame that passes long-stream RTL verification and representative mapped confirmation | Each integer II is tested with at least 1,024 consecutive RTL frames; `frame_ii_cycles` in `design_config.json` is a hint only |
| Certified period, \(P_{\rm STA}\) | Passing setup/hold period on the **fixed mapped netlist** | PrimeTime or OpenSTA scan; passing/failing bracket ≤ 0.01 ns unless the scan floor is reached |
| Effective throughput, \(T\) | \(10^9/(II_{\rm ver}P_{\rm STA})\) FFTs/s, for period in ns | Uses verified II and STA-estimated frequency; not measured silicon frequency |
| First-output latency, \(L\) | Maximum observed per-frame delay from first input to first valid output, in cycles | Measured across scored transactions at the common 10 ns target clock |

The maximum observed frame-completion latency is also a mandatory feasibility check. The latency component uses the common target clock rather than the certified minimum period, so frequency is rewarded only through throughput.

## 3. Continuous score

Let \([x]_0^1=\min(1,\max(0,x))\). For feasible designs, the default policy defines

\[
S_A=\left[\frac{A_{\rm ref}-A}{A_{\rm ref}-A_{\rm goal}}\right]_0^1,
\qquad A_{\rm goal}=0.5A_{\rm ref},
\]
\[
S_T=\left[\frac{T-T_{\rm req}}{T_{\rm goal}-T_{\rm req}}\right]_0^1,
\qquad T_{\rm req}=\frac{10^9}{384\cdot10}\ \mathrm{FFTs/s},
\]
\[
S_L=\left[\frac{300-L}{300-L_{\rm goal}}\right]_0^1,
\]
\[
S=0.60S_A+0.30S_T+0.10S_L.
\]

The accurate-reference set comprises two separately validated designs. \(A_{\rm ref}\) is their smaller mapped area; \(T_{\rm goal}\) is twice their higher verified effective throughput; and \(L_{\rm goal}\) is the greater of half their shorter first-output latency and 63 cycles. These reference values form a **component-wise envelope**, not necessarily one physical circuit. Higher SQNR earns no additional credit after the 50 dB requirement is met.

The independent `area` profile uses \(S=S_A\). All weights, goal ratios, backend calibration and measurement conditions are fixed before evaluated Agent runs; the final values live in [profiles/policy.json](profiles/policy.json).

## 4. Verification workload and flow choices

The public numerical test contains 1,024 random nonzero frames plus directed cases; hidden evaluation uses 8,192 independently generated random nonzero frames plus directed cases. Feasibility uses the **minimum** SQNR across tested nonzero frames. At least 1,024 consecutive frames verify the mandatory 384-cycle service. The architecture profile probes every integer II from 64 through 384 with at least 1,024 RTL frames and checks the selected best passing interval again using a 128-frame representative RTL/mapped subset. These finite samples do not establish formal worst-case equivalence or optimal II.

Agents may tune RTL and synthesis recipes. The public builder exports a flattened ASAP7 standard-cell netlist and manifest; the evaluator **imports that netlist without executing submitted recipes or resynthesizing it**. It independently counts cells, performs fixed-constraint STA, and compares mapped behavior with RTL. Without a custom export, the trusted default mapping applies. Accurate reference implementations use the frozen default mapping recipe, while submitted candidates may use other recipes. Commercial and open-source evaluation backends require separate calibration; all current QoR values are **pre-layout** estimates.

## 5. Official result

The platform writes `/eval/code_result.json` with exactly `resolved`, `score`, and `reason`. For example:

```json
{"resolved": true, "score": 0.0, "reason": "All mandatory checks passed."}
```

This is an illustrative format, not a measured design result. A tool/license/calibration failure must instead be marked `UNSCORED_INFRASTRUCTURE` and excluded from ranking. Source hashes, tool identities, timing certificates, area reports and component scores are retained in private measurement records.

`submission_completeness.json` separately reports missing documentation or measurement tables. Their absence does not change electrical feasibility or hardware-quality scoring.
