# FFT64-Quant design and experiment record

## Contract and scope

64-point forward unscaled complex FFT, natural input/output, Q15 external
components, synchronous reset, no secondary clock. Feasibility requires every
nonzero frame SQNR >=50 dB, exact zero, II=384 service, first output <=300,
completion <=364, 10 ns setup/hold, and mapped/RTL cycle and data agreement.
Only public benchmark tools and datasets are used. All measurements are
pre-layout ASAP7 RVT/TT; public previews are not hidden scores.

## Initial architecture hypotheses

1. **Folded in-place radix-2 DIT.** One butterfly, two parity banks of 32
   complex words. Bit-reverse input addresses and read natural output addresses.
   Any FFT butterfly flips one address bit, hence always crosses banks. This
   limits physical arithmetic and avoids a separate reorder buffer. Hypothesis:
   lower mapped area than a streaming pipeline; read muxes, write enables and
   variable twiddle products may dominate. Initial schedule: load64 + compute192
   + output64; predicted first/completion 256/319, not yet measurements.
2. **Streaming radix-2 / radix-2-squared SDF.** Six delay stages and output
   reorder storage, optional simplified quarter-turns and constant rotations.
   Hypothesis: much smaller II but more butterflies and storage; worth revisiting
   if folded arithmetic/memory costs or measured throughput are poor. No claim
   that either architecture is optimal before synthesis.

## Precision hypotheses

Start with signed 22-bit Q15 storage and Q14 twiddles, exact unity/quarter-turn
rotations, rounded nontrivial rotations. Then measure narrower Q14/Q13 storage
and coefficients. Rounding must preserve exact zero. SQNR above 50 dB has no
scoring bonus, but a measured margin is desirable for independent frames.

## Planned measurable revisions

After a correct baseline: reduce coefficient/data width; compare four-real-
product versus three-real-product complex rotation; fuse the first stage into
input capture and last stage into natural output to remove compute cycles.
Measure area, timing, latency and SQNR for candidates with the same backend.
Use the complete architecture evaluator on the retained candidate. Default
synthesis first; custom recipes only if supported by measurable benefit.

## Environment

Initial check found VCS/DC/PT executables but no suitable container Python.
The documented `check_env.sh --prepare-python` installs an isolated runtime;
no global EDA configuration is modified. Detailed environment logs are in
`runs/environment`.
