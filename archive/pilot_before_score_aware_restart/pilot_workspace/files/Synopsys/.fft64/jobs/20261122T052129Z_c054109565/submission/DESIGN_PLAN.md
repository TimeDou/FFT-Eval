# FFT64 design plan

The core accepts uninterrupted 64-sample frames and produces natural-order, unscaled complex FFTs. Each comparison uses complete standard-cell area and the benchmark's fixed PrimeTime constraints. Candidate precision must pass the per-frame SQNR threshold, including near-minimum-RMS and zero-input cases.

## Initial hypotheses

- **Streaming radix-2-squared DIT.** Bit-reverse the narrow input into a single 64-word register file, then process it at one sample per cycle with six delay-feedback butterflies. Alternate the register file's address orientation between frames so a new frame can reuse slots as the previous frame is read. The pairwise FFT factorization should require only two general rotators. Measure minimum sustained II, first-output latency, and the area of twiddles and storage.
- **Streaming DIF.** Put the long butterfly delays first and move bit reversal to the output. The later delay lines would be shorter and wider, which could reduce their total bit count. The reordered samples would be wider and the arithmetic schedule would change. Compare the storage implications against DIT when deciding whether to map this option.
- **Folded butterflies.** A scheduled shared butterfly could reduce arithmetic area. A one-butterfly radix-2 schedule takes at least 192 butterfly cycles, before input, output and pipeline overhead. Two memory ports and frame overlap would affect the complete area and the attainable II. Revisit folding if the streaming candidate shows that arithmetic dominates its mapped area.

## Baseline and experiments

Start with conservative per-stage growth, 12 fractional twiddle bits, and direct four-product complex multiplication. Once the floating-point reference and protocol checks pass, measure the baseline with the public ASIC flow. Use the timing and area reports to select experiments in twiddle precision and multiplier structure, storage organization, or tighter synthesis targets. A quicker RTL or area-only run screens candidates before the full architecture profile.
