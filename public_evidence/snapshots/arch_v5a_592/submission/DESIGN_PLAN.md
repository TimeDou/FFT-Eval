# FFT64-Quant design record

## Goal and constraints

- Default `architecture` profile: S = 0.60·S_A + 0.30·S_T + 0.10·S_L, with
  S_A = 3500/(A+3000), S_T = ln(T/T_min)/ln 240 (T = 1e9/(II·P)), S_L = (300−L)/237.
- Hard constraints: 64-pt forward unscaled FFT, natural I/O order, 16-bit in / 24-bit out (Q15),
  per-frame SQNR ≥ 50 dB, exact zero for zero input, II=384 service, first output ≤ 300,
  last ≤ 364, 10 ns setup/hold, one posedge clock, synchronous reset.
- Marginal values near the current design (A≈2000 µm², P≈0.6 ns, L≈123):
  100 µm² ≈ 0.0084, 0.1 ns ≈ 0.009, 10 latency cycles ≈ 0.0042, halving II ≈ 0.038.

## Architecture hypotheses (before implementation)

| Hypothesis | Expected effect |
|---|---|
| H1 Streaming R2³SDF (DIF) + serial bit-reversal (II=64) | 63-word feedback memory + 49-word reorder, 1 general rotator + 2 W8 rotators. Best throughput (II=64) with the minimum memory of pipelined radix-2 FFTs. |
| H2 Memory-based / folded radix-2 (one butterfly, II≥192) | Less arithmetic, but needs ≥64 words + read multiplexers, II≥192–384 and latency ≥250: S_T drop (≈0.1–0.3) cannot be repaid by area (would need A < ~700 µm²). Rejected analytically. |
| H3 R2²SDF (two general rotators) | Compared to H1: W64+W16 rotators instead of W64+2×W8; similar arithmetic, same memory. Kept as fallback. |
| H4 Bit-reversed input (DIT-like SDF, natural output) | Reorder at the narrower input (15 b) but delays grow with width: model count 3748 vs 3666 storage bits for H1. Rejected. |

Storage dominates (≈63 % of area is flip-flops), so data widths and register count drive area;
II=64 is free in the SDF structure, so the throughput lever is the certified clock period.

## Current candidate (E008, v2c)

- R2³SDF DIF, six SDF butterfly stages (delays 32…1), −j folded into the butterfly
  (negation of the imaginary path merged into the add/sub selection), W8 constant rotators
  (K=181/256, rounded), one W64 rotator (10-bit coefficients, rounded), Garrido optimum
  bit-reversal (bit exchanges 3↔2, 4↔1, 5↔0; 4+14+31 words).
- Fixed point: LSB exponents m=[0,1,1,2,2,2,5] (input, after each stage), rotator outputs
  mA=1, mB=2, mC=3; truncation in butterflies 1–5, rounding at stage 6 and in rotators;
  input clamp +16384→+16383 so the input is 15 bits; every width computed from exact
  interval analysis of the quantized linear map (no overflow possible for legal inputs).
- Area tricks: alternating-polarity shift registers (DFFHQN has inverted output), no output
  register on stage 6, per-segment frame-synchronized counters (gap-tolerant).
- Synthesis: compile_ultra timing-driven at an internal 0.60 ns clock, register retiming only
  inside the rotators, hold fixing; evaluator re-measures the flattened netlist.

## Measured decisions

| ID | Hypothesis / change | Observation (measured) | Decision |
|---|---|---|---|
| E001 | H1 baseline RTL | quick PASS: SQNR 55.08 dB, L=120 | keep architecture |
| E003 | alternating-polarity delay lines | dev synth 2038→1885 µm² at 10 ns | accept |
| E004/5 | tighter clock targets, rotator pipelining + retiming | 0.8 ns: +150 µm² without retiming, +3 with; 0.5 ns costs +340 | accept retiming, target ~0.6 ns |
| E006/7 | exact widths, clamp, negation merge, precision search | −106 µm² at equal timing; storage 3974 bits | accept |
| E008 | tb=9 twiddles | full preview **0.7470** (A 1994.3, P 0.6023, II 64, L 123, SQNR 53.29) | current best |
| E009 | 3-mult (Gauss) W64 | +19 µm² | reject |
| E010 | tb=8 | −3 µm², margin 1.7 dB | reject (risk) |

## Next actions

1. Cheaper W64 rotator (octant folding → unsigned 9-entry coefficients).
2. Explore clock targets 0.5–0.55 ns with better-placed pipeline registers.
3. Precision re-search with rounding carried in butterfly adders.
