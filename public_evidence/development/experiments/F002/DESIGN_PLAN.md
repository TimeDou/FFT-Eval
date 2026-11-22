# FFT64-Quant design record

Target: architecture profile, complete forward unscaled 64-point complex FFT,
natural I/O, signed Q15 external data, minimum frame SQNR 50 dB, synchronous
abort/reset, II <=384, first output <=300 and completion <=364, 10 ns timing.
Public score: 0.60*clip(3500/(area+3000)) + 0.30*clip(log(T/260416.6667)/log(240))
+ 0.10*clip((300-L)/237). Higher SQNR is only feasibility margin.

Competing hypotheses:
- Folded radix-2 with parity-banked register storage: one shared butterfly and
  complex multiplier may save sufficient area to offset modest throughput and latency.
- Streaming SDF (including radix-2-squared): higher throughput and lower latency,
  but stage arithmetic and natural-order output buffering may dominate area.
- Two shared butterflies and four banks: intermediate option to test if the
  latency and throughput gains justify duplicated arithmetic.

Initial candidate F001: folded DIF; 64 complex words, split by index parity,
20-bit components with 13 fractional bits; input discards two Q15 LSBs,
13-fraction-bit twiddles, arithmetic shifts at multiplier outputs. Six 32-cycle
passes; sequential load and natural-order read of bit-reversed storage.
All storage and muxing are included; data flops need no reset because a fresh
complete input overwrites them before any valid output. No measurement yet.

Plan: quick four-state numerical/protocol screen, commercial mapped area and
setup/hold plus netlist comparison, complete architecture capacity/frequency
certification. Preserve the best fully verified candidate. Subsequent precision,
banking and flow revisions require fresh run directories and matching exports.
