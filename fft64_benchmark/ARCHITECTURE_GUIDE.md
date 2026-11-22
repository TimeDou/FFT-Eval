# FFT64 Architecture and Precision Design Guide

This guide identifies possible design directions; it is **not an implementation recipe or optimized solution**. All architectures must compute the same forward, unscaled, natural-order 64-point complex FFT under the specified external protocol.

## FFT computation versus hardware organization

A pure radix-2 decomposition contains six stages of 32 butterfly operations, or 192 butterfly **operations** per transform. The physical implementation need not contain 192 butterfly units: reuse, pipelining and parallelism determine how the computation is mapped to hardware.

| Architecture | Main organization | Potential benefit | Main implementation cost |
|---|---|---|---|
| R2SDF | One streaming path with feedback delays | Regular pipeline | Stage butterflies, storage and control |
| R2²SDF | Paired radix-2 stages with simplified rotations | Fewer nontrivial twiddle rotations | Feedback alignment and coefficient handling |
| R4MDC | Multiple parallel paths and commutators | Higher intrinsic parallel throughput | Arithmetic duplication, data movement and serial interface adaptation |
| Folded/iterative | Shared butterfly units with scheduled storage accesses | Reduced arithmetic duplication | Memory banking/ports, scheduling and latency |
| Fully parallel | Many simultaneous operations | Short computation latency with sufficient interface bandwidth | High complete-design area and routing overhead |

The 384-cycle minimum service requirement and one-complex-sample-per-cycle interface apply to **every** candidate. A design with more internal parallelism may or may not achieve a better verified throughput after accounting for input/output adaptation.

## Numerical precision choices

Candidate variables include intermediate data widths, guard bits, twiddle-factor widths, truncation or round-to-nearest-even, fixed-point scaling and quantization locations. Trivial rotations (such as multiplication by ±1 or ±j) can be specialized exactly. Any precision reduction must be evaluated on the **complete 64-point output**, using the float64 FFT of the same already-quantized input. Minimum per-frame SQNR—not local butterfly error or average SQNR—determines numerical feasibility.

Keep intentional **fixed-point quantization** distinct from **exact RTL or Boolean optimizations**. Approximate gate pruning, approximate compressors and arbitrary Boolean-function changes are outside the task.

## EDA optimization choices

The default DC or Yosys/ABC mapping is one possible strategy. Agent-controlled recipes can modify synthesis effort, hierarchy, resource sharing, Boolean rewriting and technology mapping. Use the public [optimization interface](../OPTIMIZATION.md) to export a structural netlist; private evaluation independently imports and measures it. A smaller logic count in an intermediate representation does not necessarily imply a smaller or faster complete mapped FFT.

## Useful experimental questions

- Does the memory organization support simultaneous accesses without conflicts?
- Is the natural-order output permutation fully implemented and counted?
- Does a shorter internal processing schedule pass long continuous-frame tests?
- Does lower precision remain feasible for low-energy and sign-sensitive inputs?
- Does a synthesis recipe improve final cell area or certified period after independent STA?
- Is a result specific to one backend or stable across repeated runs of the same frozen flow?

Prefer a few well-measured hypotheses to unsupported claims about an architecture's superiority. Physical placement/routing is optional and does not determine the present pre-layout score.
