# FFT64 design plan

The core accepts uninterrupted 64-sample frames and produces natural-order, unscaled complex FFTs. Each comparison uses complete standard-cell area and the benchmark's fixed PrimeTime constraints. Candidate precision must pass the per-frame SQNR threshold, including near-minimum-RMS and zero-input cases.

## Initial hypotheses

- **Streaming radix-2-squared DIT.** Bit-reverse the narrow input into a single 64-word register file, then process it at one sample per cycle with six delay-feedback butterflies. Alternate the register file's address orientation between frames so a new frame can reuse slots as the previous frame is read. The pairwise FFT factorization should require only two general rotators. Measure minimum sustained II, first-output latency, and the area of twiddles and storage.
- **Radix-2 SDF.** A separate twiddle after each relevant butterfly would simplify the stage equations but add general rotations at the same serial I/O rate. The paired stages are the first choice for reducing arithmetic area.
- **Streaming DIF.** Put the long butterfly delays first and move bit reversal to the output. The later delay lines would be shorter and wider, which could reduce their total bit count. The reordered samples would be wider and the arithmetic schedule would change. Compare the storage implications against DIT when deciding whether to map this option.
- **Radix-4 MDC.** Parallel internal lanes could reduce compute latency. The serial interface still limits the frame interval to 64 cycles or more, and the parallel lanes require commutators and input and output serialization. Measure the single-path design first to establish whether spending area on lower latency is justified.
- **Folded butterflies.** A scheduled shared butterfly could reduce arithmetic area. A one-butterfly radix-2 schedule takes at least 192 butterfly cycles, before input, output and pipeline overhead. Two memory ports and frame overlap would affect the complete area and the attainable II. Revisit folding if the streaming candidate shows that arithmetic dominates its mapped area.

## Baseline and experiments

Start with conservative per-stage growth, 12 fractional twiddle bits, and direct four-product complex multiplication. Once the floating-point reference and protocol checks pass, measure the baseline with the public ASIC flow. Use the timing and area reports to select experiments in twiddle precision and multiplier structure, storage organization, or tighter synthesis targets. A quicker RTL or area-only run screens candidates before the full architecture profile.

### Fixed-point and rotator experiments

The Q15 baseline passed the public numerical and protocol checks at 71.66 dB minimum SQNR. Rounding the input to 14 fractional bits, using 11 fractional bits for twiddles and rounding to 13 fractional bits at the span-64 rotator lowered default mapped area by 7.7%. Minimum SQNR was 56.28 dB. Output wiring restores the two binary places required by the external Q15 interface.

The next version stored each input in 14 signed bits, saturating the positive endpoint to 8191 in Q14. Both widths before the span-16 rotation shrink by one bit. The rotation can increase component magnitude, so its output regains that bit. Swap and sign changes reduce both rotators to one octant. With integer coefficients `c` and `s`, the rotator computes `p = (re + im) * s`, `re' = re * (c - s) + p`, and `im' = im * (c + s) - p`. The products implement the same Q11 rotation as the four-product form before rounding. Restoring the signs and quadrant takes one additional cycle per rotator.

The input rounding error is bounded by 1 Q15 count per component, except for the +16384 endpoint. A frame that contains that endpoint has enough signal energy to keep its relative input error below the general 0.001382 bound. The largest complex coefficient errors at spans 16 and 64 are 0.000139 and 0.000281. Accounting for round-to-even at both boundaries and the norm growth of the FFT butterflies bounds relative output error by 0.002981 over the specified input domain, equivalent to 50.51 dB. This is an analytical bound. The CSV records measured minima.

### Reorder storage experiments

Three cascaded bit swaps can replace random access with always-shifting tapped delays. The 98 storage positions and associated registers outweighed the reduction in combinational logic. The default mapping was 2,916.25 µm² against 2,738.02 µm² for the same precision and four-product arithmetic with a 64-word register file.

The 50-word variant retains one register file. Bit-reversed reads begin 50 cycles after the first write, one cycle beyond the maximum displacement of 49. At II=64, every later write can reuse the slot read at that edge. The first 50 writes initialize the slots and the next 14 writes reuse the slots of the first 14 reads. The remaining 50 reads define a permutation of the slots for the following frame. Packing its cycles into aligned address groups makes each frame advance the low address bits modulo the group size. A longer input gap shifts later-frame writes away from earlier-frame reads, so the same address schedule applies. Only the control state needs reset. A reset suppresses reads until the new frame's inputs have populated the slots they access.

### Synthesis experiments

The default flow's critical paths were in the coefficient multipliers. A custom DC build used a 1.2 ns synthesis target with incremental hold repair. The installed DC version logged both legacy effort-script switches as ignored. The tight clock target changed the optimization, and a separate trial invokes `optimize_netlist -area` explicitly after mapping. The public evaluator imports each built netlist and applies the benchmark's fixed area and STA procedure.

## Selected implementation

The three-product design with 64 reorder words certified at 2.221 ns under the default flow and 1.202 ns with the tighter synthesis target. The 50-word reorder reduced area from 2,526.90 to 2,418.94 µm² at the faster period. Area recovery reduced it further to 2,415.95 µm² with the same certified period, sustained interval, and observed latency. That build is the submitted one. It reduces complete mapped area by 18.6% relative to the initial Q15 baseline.

The final architecture run passed all 321 integer IIs with 1,024 consecutive RTL frames per interval. At II=64 the evaluator confirmed the exact RTL output stream on the mapped netlist over the 128-frame subset and additional gap and reset cases, with each of the three initial states. Maximum first-output and completion latency were 127 and 190 cycles. Minimum public SQNR was 56.28 dB, and zero-input outputs were exact. An additional RTL run with 8,192 generated random frames at II=64 and a separate public-generator seed measured a 55.81 dB minimum.

The final public evaluation is in `runs/recovery_full/result.json`. It confirms hardware feasibility. The area and certified period describe the pre-layout netlist under ideal interconnect. An official score requires frozen reference calibration.

## Measurement environment

The Synopsys smoke check passed after the benchmark prepared its isolated Python runtime and compiled the supplied Liberty files. Commercial measurements use VCS L-2016.06, DC L-2016.03-SP1 and PrimeTime M-2016.12-SP1 with the supplied ASAP7 RVT/TT library. Verilator was used for additional RTL screening. The measurement CSV distinguishes the submitted netlist hash from the hash of the structural netlist after the evaluator imports it.

Reproduce the final build and public evaluation from the repository root with fresh run directories.

```bash
bash synopsys.sh build submission --export --out runs/rebuild
bash run_synopsys_debug.sh submission --profile architecture --out runs/recheck
```
