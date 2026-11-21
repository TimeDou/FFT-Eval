# FFT architecture notes — starting ideas, not an answer

Read this document **before** writing `DESIGN_PLAN.md`. It deliberately presents choices rather than an optimized implementation.

## What is being optimized?

A 64-point complex FFT is six radix-2 stages (or an equivalent higher-radix decomposition). The FFT contains butterflies, coefficient rotations, buffering, scheduling and reordering. A design that minimizes only butterfly arithmetic is incomplete: memory/registers, control, multiplexers and natural-order outputs can dominate area and latency.

## Plausible architecture families

| Family | Candidate benefit | Possible cost/risk |
|---|---|---|
| Radix-2 SDF | Streaming regular pipeline, relatively small buffering | Stage hardware/control and pipeline state |
| Radix-2^2 SDF | Fewer nontrivial twiddle rotations in some stages | More elaborate stage timing and coefficient routing |
| Radix-4 MDC | Parallel data paths and high throughput potential | More buffers, commutators, multipliers and I/O adaptation |
| Folded/in-place radix-2 | Reuse one/few butterflies to reduce area | Longer frame latency, higher memory-port/mux cost, limited throughput |
| Fully parallel | Low algorithmic latency, high data rate | Large arithmetic and register area |

**Do not assume an architecture is universally superior.** A single-sample-per-cycle interface and a relaxed frame service period may favor folding; a higher-throughput contract may require pipeline/parallelism. Compare the actual complete implementation with the same timing and workload.

## Legal approximation knobs

1. Precision of data at individual stage boundaries.
2. Twiddle coefficient precision and placement of exact/trivial rotations.
3. Truncation versus round-to-nearest-even and the location of rounding boundaries.
4. Intermediate guard bits, fixed-point scale handling, and overflow/saturation behavior.
5. Signed real/imaginary pairing and their effect on final-frame SQNR.

Keep any exact architectural simplification (banking, arithmetic identity, resource sharing, pipeline organization) **separate** from numerical precision reductions when interpreting results. The hidden input set may expose correlated low-RMS I/Q and sign changes; a policy that performs well only on Gaussian data may fail.

## One possible exploration sequence (non-prescriptive)

- Establish two high-precision architecture candidates with complete protocol, synthesis and STA results.
- Compare total area, register/mux area, output latency, and frame service rate; select one to optimize further.
- Probe twiddle precision and stage precision independently; then combine changes and re-measure **whole-design** SQNR and mapped area.
- Record negative results. A pipeline cut that improves slack but adds area may not help when 10 ns is already met.

## Think before implementation

- Why might a smaller multiplier lead to larger total area once extra rounding and routing are included?
- Can the chosen storage/banking scheme sustain every required read/write at the same edge?
- Is the natural-order output permutation implemented and included in the area?
- Does a low-RMS complex frame reveal different behavior than a high-energy real-only tone?
- Which two candidate architectures are genuinely distinguishable under the **current** service-period constraint?

This document intentionally does **not** give a known winning precision schedule or an optimized RTL netlist.
