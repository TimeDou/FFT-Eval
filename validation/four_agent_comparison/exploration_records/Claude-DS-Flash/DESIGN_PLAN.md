# 作者原始探索记录（文字与表格）

以下为作者保存的 DESIGN_PLAN.md，保留其假设、过程和自测叙述。历史相对路径指向原始私有分支；包内只附 measurements.csv。其中未经独立证明的解释和理论断言，请结合 STRATEGY_COMPARISON.md 与 DOCUMENT_NOTES.md 阅读。

---

# DESIGN_PLAN.md — FFT64 streaming R2SDF design record

## Goal and constraints
- Task/profile: FFT64-Quant, `architecture` profile: S = 0.60·S_A + 0.30·S_T + 0.10·S_L.
- 64-pt forward unscaled complex FFT, 16-bit signed in / 24-bit signed out, 15 fractional bits,
  natural in/out order, per-frame SQNR ≥ 50 dB, exact zero on zero input, synchronous reset,
  384-cycle mandatory service, first output ≤ 300 cycles, last ≤ 364, 10 ns STA.
- Public anchors: A_ideal 500 um², A_half 4000 um²; T_min = 1e9/(384·10) = 260416.67 FFT/s;
  T_ideal = 62.5e6 FFT/s; L_ideal 63, L_max 300 cycles.

## Candidate architectures
- **H1 (selected) R2SDF** — single-path delay feedback, DIF: six butterflies, 63 complex-word delay
  storage, 1 sample/cycle streaming. Lowest area that still streams at the full input rate; the 30 %
  throughput and 10 % latency terms outweigh the cost of a bit-reversal output buffer.
- **H2 memory-based iterative FFT** — one 64-word frame memory, one butterfly, in-place, natural
  order for free. Storage is minimal but ~192 butterfly cycles/frame force II ≥ 224–384 and a first
  output near the 300-cycle deadline; paper estimate (area ≈ 2.3–2.5 kum², S_T ≈ 0.15, S_L ≈ 0.03)
  gives ≈ 0.55–0.56, below H1. Rejected without building.
- **H3 multi-port memory / 2–4 parallel butterfly folded designs** — a 64-way read mux per bit per
  port makes multi-ported register memories larger than the SDF at equal II. Rejected on reasoning.
- **H4 R2²SDF** — two instead of three nontrivial complex multipliers, ≈ 0.35 kum² saving (≈ +0.02
  score), needs a different memory layout. Left as future work (not measured).

## Final candidate (C2)
- Architecture: 6-stage radix-2 SDF (DIF), delay lines 32/16/8/4/2/1 complex words, one output
  pipeline register per stage, per-stage widths 16→22 bits (15 fractional bits throughout).
- Twiddles: Q2.10 constants (12-bit, Q2.10) selected by a balanced 2:1 mux tree; the coefficient
  registers of stages 1–3 are loaded one cycle ahead so no mux delay sits in the multiply path.
  Complex multiply with round-half-up (add 2^9 before the 10-bit arithmetic shift). Stages 4–6 have
  trivial/single-constant twiddles and are folded by the synthesiser.
- Output: 64-word frame buffer written at bit-reversal addresses, read sequentially; the emit is
  armed by a 134-bit shift register (frame start → +134 cycles). Measured first output 134 cycles and
  completion 197 cycles on every frame (constant latency).
- Control: 8-bit position counter `sc` (0..132), free-running datapath. A frame may start at any
  cycle provided frames are ≥ 129 cycles apart, so the pipeline (Σ(M+1) = 69 positions) is zeroed by
  the idle input; the SDF state therefore always represents the real sample history. Frames offered
  closer than that are dropped and recorded as failing optional intervals (65 of them, 64..128).
- Reset: synchronous; frame counter, arm shift register and emit state cleared, delay lines and
  output registers cleared through a per-bit AND mask (cheaper than a reset mux).
- Synthesis recipe `flow/dc_opt.tcl`: re-target the clock to 700 ps, `compile_ultra
  -timing_high_effort_script` + `compile -incremental_mapping -only_hold_time`. The grading flow
  re-constrains this fixed netlist with the benchmark SDC; the recipe only steers optimisation.

## Measured decisions
| ID | Hypothesis / change | Observation (measured) | Accept/reject |
|---|---|---|---|
| E001 | 6-stage R2SDF, width growth, 12-bit twiddles | 69.0 dB min SQNR (official quick, 2256 frames) | accept |
| E002 | shift-register delay depth M+1, tap M | delay becomes M+1 → FFT wrong | reject (depth M, tap M-1) |
| E003 | frame counter loaded with 0 at the frame start | one-cycle offset between sample and phase | reject (load 1) |
| E004 | stall the datapath between frames | SDF state must match the real sample history | reject (free-running shift) |
| E005 | unregistered 32-way coefficient case mux | 4.42 ns critical path (mux + multiply + rounding) | reject |
| E006 | balanced mux tree + registered coefficients + Q2.10 | 2.55 ns path, 3270.7 um² | accept |
| E007 | DC synthesis target 2000 / 1200 / 700 / 550 ps | paths 2.00 / 1.09 / 0.65 / 0.64 ns, areas 3276 / 3259 / 3696 / 3781 um² | accept 700 ps (best score) |
| E008 | 20-bit output buffer (13 fractional bits) | |X| = 32 frames wrap; min SQNR −3 dB | reject (22 bits) |
| E009 | AND-mask reset instead of reset mux | same speed, slightly smaller | accept |
| E010 | hand-specialised stages 4–6 (no multipliers) | 3254.8 um² at the same path as 3267 um²; DC folds the constants better | reject |
| E011 | reorder buffer for II = 64 (2 banks) | +64 complex words ≈ +1.2 kum² for ΔS_T ≈ +0.038 | reject (net negative) |
| E012 | synthesis target 550 ps | path only 0.639 ns (vs 0.647) but area 3781 um² → score 0.582 < 0.584 | reject |

## Best measured design (submitted)
- RTL `submission/rtl/fft64_top.sv` (sha256 3d830328…), recipe `submission/flow/dc_opt.tcl`
  (sha256 a8d1d6aa…), exported netlist `submission/implementation/mapped.v` (manifest-bound).
- Public architecture preview (complete evaluation, `runs/arch_c2`):
  - resolved = true, feasible = true, score = **0.5841**
  - worst-frame SQNR 66.70 dB over 264816 frames, zero input exact
  - verified II = 129 (1024 continuous frames), first output 134 cycles, completion 197 cycles
  - mapped area 3695.72 um², certified period 0.7642 ns (831→1308 MHz scan), hold slack +0.021 ns
  - components S_A 0.5227, S_T 0.6682, S_L 0.7004 (weighted 0.3136 / 0.2005 / 0.0700)
- Alternatives measured and compared in `measurements.csv`: 1.20 ns synthesis target (score 0.5808,
  area 3267 um²), 550 ps target (0.582 predicted, area 3781 um²).

## Next action / stopping criterion
- Further gains require either an R2²SDF rewrite (one fewer complex multiplier) or pipelining inside
  the multipliers to break the ~0.64 ns multiply path (predicted ≈ +0.01–0.02 but needs a new
  delay-line alignment), or a 2-bank output buffer to reach II = 64 (net negative on score).
  All remaining ideas were quantified as smaller than 0.02 score, so the search stops here.
