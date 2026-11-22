# Architecture Guide: FFT64 Design Space

This is **background and design guidance**, not a prescribed solution. The agent remains responsible for the architecture, arithmetic, RTL, and precision choices.

## Arithmetic organization

A 64-point FFT can be decomposed into six radix-2 stages, each with 32 two-input butterflies. Different hardware architectures implement the *same dependencies* using different degrees of parallelism and storage. The natural-order output requirement includes any necessary data reordering.

| Option | Main organization | Typical opportunity | Typical cost or risk |
|---|---|---|---|
| R2SDF | Single streaming path with feedback delays | Regular processing; stage-wise data handling | Feedback buffers, butterflies and stage control |
| R2²SDF | Paired radix-2 stages with specialized twiddle handling | Reduce nontrivial rotations | Alignment and coefficient routing remain |
| R4MDC | Several parallel paths with commutators | Higher intrinsic throughput | More arithmetic, data routing, buffers, and serial I/O adaptation |
| Folded radix-2 | Reuse one or a few butterfly units | Reduce arithmetic duplication | Scheduling, memory port/bank conflicts, longer latency |
| Fully parallel | Many concurrent butterflies | Low transform latency at sufficient I/O width | Significant complete-design area |

For radix-2, the six-stage computation comprises 192 butterfly *operations*, not necessarily 192 physical butterfly units. An architecture that reduces core arithmetic may still require substantial standard-cell storage, output permutation and multiplexing.

## Precision/quantization choices

- Different data widths at selected stage boundaries;
- Twiddle coefficient precision, trivial rotations (e.g. ±1, ±j), and constant multiplication specialization;
- Explicit truncation versus round-to-nearest-even, including sign/tie behavior;
- Guard bits, intermediate scaling and overflow handling;
- Coupled real/imaginary error and near-minimum-RMS input behavior.

Keep **exact transformations** and **intentional numerical approximation** conceptually separate. All candidates must be evaluated on the *complete* FFT output against the same quantized-input float64 reference. Local butterfly error is not the whole-design SQNR.

## Questions worth testing

- Does a more parallel pipeline improve the scored throughput after accounting for the one-sample-per-cycle interface?
- Does the proposed memory organization really support every required simultaneous read and write?
- Are reordering and twiddle storage counted in area?
- Can lower twiddle precision harm low-energy complex inputs despite good average SQNR?
- Is an apparently faster circuit actually able to accept 1,024 consecutive frames at the claimed II?

Prefer a short series of measured hypotheses to an unvalidated list of architecture names. This document contains no optimized RTL or winning precision schedule.

## EDA optimization choices

The default synthesis recipe is a starting point. Test Boolean rewriting, resource sharing, compile effort, hierarchy and mapping choices through the editable [optimization templates](../OPTIMIZATION.md). A change in logic count is a hypothesis; its benefit is established by complete mapped area, fixed-constraint STA and mapped-to-RTL checks. Record both the RTL and the recipe for each candidate. Placement/routing recipes require a matched physical kit and do not determine the current pre-layout score.
