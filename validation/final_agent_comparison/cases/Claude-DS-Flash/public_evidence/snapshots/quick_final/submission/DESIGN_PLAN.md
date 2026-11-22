# DESIGN_PLAN.md — FFT64 streaming R2SDF design record

## Goal and constraints
- Task/profile: FFT64-Quant, `architecture` profile: S = 0.60·S_A + 0.30·S_T + 0.10·S_L.
- 64-pt forward unscaled complex FFT, 16-bit signed in / 24-bit signed out, 15 fractional bits,
  natural in/out order, per-frame SQNR ≥ 50 dB, exact zero on zero input, synchronous reset,
  384-cycle mandatory service, first output ≤ 300 cycles, last ≤ 364, 10 ns STA.
- Public anchors: A_ideal 500 um², A_half 4000 um²; T_min = 1e9/(384·10) = 260416.67 FFT/s;
  T_ideal = 62.5e6 FFT/s; L_ideal 63, L_max 300 cycles.

## Candidate architectures
- **H1 (selected) R2SDF**, single-path delay feedback, DIF: six butterflies, 63 complex-word delay
  storage, 1 sample/cycle streaming. Hypothesis: lowest area that still permits a high frame rate;
  the 30 % throughput and 10 % latency terms outweigh the cost of a bit-reversal output buffer.
- **H2 memory-based iterative FFT** (one 64-word frame memory, 1 butterfly): smallest storage but
  ~192 butterfly cycles/frame ⇒ II ≥ 320–384, S_T ≈ 0, first output close to the 300-cycle limit.
  Rejected: predicted combined score ≈ 0.46 vs ≈ 0.55 for H1 (measured H1 area/latency confirm).
- **H3 multi-port memory / 2–4 parallel butterfly folded designs**: multi-ported register memory is
  larger than the SDF at equal II (a 64-way read mux costs ~1 mux per bit per port).

## Current candidate (final)
- Architecture: 6-stage radix-2 SDF (DIF), delay lines 32/16/8/4/2/1 complex words, one output
  pipeline register per stage, data widths 16→22 bits (15 fractional bits throughout).
- Twiddles: Q2.10 constants (12-bit) selected by a balanced 2:1 mux tree; coefficients for stages
  1–3 are registered one cycle ahead so the multiplier never sees the mux delay. Complex multiply
  with round-half-up (add 2^9 before the 10-bit arithmetic shift).
- Output: 64-word frame buffer written at bit-reversal addresses, read sequentially; the emit is
  armed by a 134-bit shift register (frame start → +134). Measured first output = 134 cycles,
  completion = 197 cycles, on every tested frame (constant latency).
- Control: 8-bit position counter `sc` (0..132), free-running datapath; frames may start at any
  cycle when ≥ 129 cycles apart, so the pipeline (Σ(M+1) = 69 positions) is flushed with zeros in
  the gap. Frames offered closer than that are dropped (recorded as failing optional intervals).
- Reset: synchronous; frame counter/arm/emit state cleared, delay lines and output registers cleared
  through a per-bit AND mask (cheaper than a reset mux).

## Measured decisions
| ID | Hypothesis / change | Observation (measured) | Accept/reject |
|---|---|---|---|
| E001 | 6-stage R2SDF, per-stage width growth, 12-bit twiddles | 69.0 dB min SQNR (official quick, 2256 frames) | accept |
| E002 | shift-register delay depth M+1 with tap M | delay becomes M+1, FFT wrong | reject (depth M, tap M-1) |
| E003 | frame counter loaded with 0 at frame start | one-cycle offset between sample and phase | reject (load 1) |
| E004 | stall the datapath between frames | SDF state must represent the real sample history | reject (free-running shift) |
| E005 | unregistered 32-way coefficient case mux | 4.42 ns critical path (coef mux + multiply) | reject |
| E006 | balanced mux tree + registered coefficients + 10-bit twiddles | 2.55 ns path, area 3271 um² | accept |
| E007 | DC synthesis target 2000 ps / 1200 ps | path 2.00 / 1.09 ns at nearly equal area | accept (recipe target) |
| E008 | output buffer 20 bits (13 fractional) | large-magnitude frames (|X| = 32) wrap; SQNR −3 dB | reject (keep 22 bits) |
| E009 | AND-mask reset instead of reset mux | area 3271 → 3135 um² at equal speed | accept |

## Best measured design
- RTL: `submission/rtl/fft64_top.sv`; recipe: `submission/flow/dc_opt.tcl`;
  exported netlist: `submission/implementation/mapped.v`.
- Worst-frame SQNR 66.7 dB (2256-frame public set; 66.6 dB over 3×2240 additional random frames),
  zero input exact, verified II = 129, first output 134 cycles, completion 197 cycles.
- Mapped area and certified period: see `measurements.csv` (public preview numbers).

## Next action
- Compare DC synthesis targets 1200 ps / 700 ps at equal RTL and select the higher combined score.
