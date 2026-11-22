# FFT64-Quant: Feasibility and Hardware-Quality Scoring

Optimize the combined normalized hardware score, rather than a single PPA metric. The default `architecture` profile uses complete mapped area (60%), verified effective throughput (30%) and worst first-output latency (10%). Every numeric parameter is public in [profiles/policy.json](profiles/policy.json), and a complete public evaluation returns component scores and the combined preview score without private calibration.

## Feasibility and measured quantities

`resolved=true` requires FFT behavior, natural output order, per-frame SQNR >=50 dB, exact zero output for zero input, reset and protocol behavior, sustained II=384 service, first/completion deadlines, 10 ns setup/hold timing and representative RTL/mapped agreement. There is no score threshold or minimum area saving required to pass. Higher SQNR earns no bonus after the constraint is met.

Area A is the complete mapped cell area in um2, including all storage, arithmetic, control and reordering. The measured minimum frame II comes from all integer intervals 64–384, each with at least 1024 continuous RTL frames and representative mapped confirmation at the selected interval. A fixed-netlist STA clock scan supplies passing period P in ns; a claimed II, estimated slack or producer-reported area cannot substitute for these measurements.

\[
T=\frac{10^9}{II_{ver}P}\quad\mathrm{FFTs/s}.
\]

Latency L is the largest first-input to first-output delay over scored frames, in cycles at the common 10 ns clock. Frequency contributes through T only. Completion latency is also a mandatory check.

## Public numerical parameters

| Quantity | Frozen value | Meaning |
|---|---:|---|
| Ideal area A_ideal | 500 um2 | Area component reaches one |
| Half-credit area A_half | 4000 um2 | Area component equals 0.5 |
| Mandatory throughput T_min | 260416.66666666666 FFT/s | 384 cycles at 10 ns |
| Ideal throughput T_ideal | 62500000 FFT/s | II=64 at the 0.25 ns STA scan floor |
| Ideal first-output latency L_ideal | 63 cycles | Last required input arrives at cycle 63 |
| Maximum first-output latency L_max | 300 cycles | Mandatory first-output deadline |
| Architecture weights | 0.60 / 0.30 / 0.10 | Area / throughput / latency |

These are public objective scales, not measurements of one ideal FFT. Achieving score one requires all three ideal values simultaneously. This combination is intentionally demanding; the benchmark does not claim that it is physically achievable. The 4000 um2 area scale provides useful feedback over a broad range of implementations without making a design above an accurate reference area receive zero area credit.

## Continuous score

Let clip(x,0,1) clamp a value to [0,1].

\[
S_A=\operatorname{clip}\left(\frac{A_{half}-A_{ideal}}{A+A_{half}-2A_{ideal}},0,1\right)
=\operatorname{clip}\left(\frac{3500}{A+3000},0,1\right).
\]

Area credit decreases continuously for every A>500, remains positive for finite measured area, and equals 0.5 at 4000 um2. There is no zero-credit interval above a reference circuit's area.

\[
S_T=\operatorname{clip}\left(\frac{\ln(T/T_{min})}{\ln(T_{ideal}/T_{min})},0,1\right)
=\operatorname{clip}\left(\frac{\ln(T/T_{min})}{\ln(240)},0,1\right).
\]

Each doubling of throughput below the ideal adds the same component gain, ln(2)/ln(240), approximately 0.12647. Throughput remains discriminative up to the maximum supported by the declared II and clock-scan bounds.

\[
S_L=\operatorname{clip}\left(\frac{300-L}{300-63},0,1\right),
\qquad S=0.60S_A+0.30S_T+0.10S_L.
\]

The optional `area` profile uses S=S_A and is a separate diagnostic. Use the full `architecture` profile to select the submitted design. Neither recipe names nor a larger number of experiments earns credit.

## Public feedback and final hidden grading

A complete public run returns `grade.components`, `grade.weighted_components`, `grade.score`, the measured PPA and public normalization parameters. It sets `score_valid=true`, `scoring_scope=public_preview` and `official_score=false`. This is valid optimization feedback on public data; final acceptance still depends on independent hidden evaluation. Quick checks and unfinished measurements have no complete hardware score.

Final hidden grading uses the identical public formula and numeric scales, with private input data and matching platform/protocol validation calibration. Accurate fixed-point references validate the environment; they do not secretly choose or alter the score denominator. The private seed, reference RTL and execution records remain private. The score alone never establishes that a hidden test was passed.

Commercial and open-source previews report their backend and are not mixed in one ranking. Official DSBench grading uses the declared commercial environment. A tool failure, timeout or missing official validation is unscored infrastructure, while an observed design-specification violation is a valid zero score. Full internal records preserve that distinction.

## Development commands

From the repository root:

```bash
bash check_env.sh
bash run_synopsys_debug.sh submission --quick --out runs/quick
bash run_synopsys_debug.sh submission --profile architecture --out runs/full
```

Use measured component gains to choose between candidates. Keep the input format, SQNR requirement and timing/protocol rules fixed. All current area and timing results are pre-layout estimates. See [EVALUATION.md](EVALUATION.md) for coverage and [OPTIMIZATION.md](../OPTIMIZATION.md) for custom recipe export and independent netlist measurement.
