# DESIGN_PLAN.md — FFT64 streaming R2SDF design record

## Goal and constraints
- Task/profile: FFT64-Quant, `architecture` profile. Score = 0.60·S_A + 0.30·S_T + 0.10·S_L.
- 64-pt forward unscaled complex FFT, 16-bit signed in / 24-bit signed out, 15 fractional bits,
  natural order in/out, per-frame SQNR ≥ 50 dB, exact zero on zero input, synchronous reset,
  384-cycle mandatory service, first output ≤ 300 cycles, last ≤ 364, 10 ns STA.
- Public anchors: A_ideal 500 um², A_half 4000 um²; T_min = 1e9/(384·10); T_ideal = 62.5e6 FFT/s;
  L_ideal 63, L_max 300 cycles.

## Candidate architectures and hypotheses
- H1 R2SDF (single-path delay feedback, DIF): 6 butterflies, 63 complex-word delay storage,
  II = 64 in principle (1 sample/cycle streaming), bit-reversed output needing a reorder buffer.
  Hypothesis: lowest area for full streaming throughput; throughput (30 %) plus latency (10 %)
  outweigh the store-and-reorder cost.
- H2 memory-based iterative radix-2/4 (single 64-word frame memory, 1 butterfly): smallest storage,
  but ~192+ butterfly cycles per frame ⇒ II ≥ 384 (S_T = 0) and first output near the 300-cycle limit.
  Hypothesis: better area score, much worse combined score.
- H3 folded/pipelined hybrids (2–4 parallel butterflies) rejected on paper: multi-ported memory makes
  them larger than the SDF at equal II.

## Current candidate (C1)
- Architecture: 6-stage radix-2 SDF (DIF), delays 32/16/8/4/2/1 complex words, one pipeline register
  per stage, per-stage width growth 16→22 bits (15 fractional bits throughout).
- Twiddles: Q2.12 constants selected by a per-stage case table; complex multiply with round-half-up
  (add 2^11 before the 12-bit arithmetic shift).
- Output: 64-word frame buffer written at bit-reversal addresses, read sequentially; frame emit
  armed by a 134-bit shift register (`start` → +134 cycles), so first output = cycle 134.
- Control: 8-bit frame counter `sc` (0..132), free-running datapath; frames may start at any cycle
  and must be ≥ 129 cycles apart so the pipeline (Σ(M+1) zeros) is flushed between frames.
- Reset: synchronous, clears the frame counter, arm shift register, emit state and all delay lines.

## Measured decisions
| ID | Hypothesis / change | Observation | Accept/reject |
|---|---|---|---|
| E001 | R2SDF datapath, circular-buffer model in Python, 12-bit twiddles | 69–76 dB min SQNR on official frame set | accept |
| E002 | shift-register delay depth M+1 | delay becomes M+1 ⇒ wrong FFT | reject (depth M, tap M-1) |
| E003 | frame counter starts at 1 on frame start | fixed off-by-one between input sample and phase | accept |
| E004 | stall pipeline between frames | SDF state must reflect real sample history; stalling keeps stale state | reject (free-running shift) |

## Next action
- Official quick + area runs; then tune precision/width and synthesis recipe.
