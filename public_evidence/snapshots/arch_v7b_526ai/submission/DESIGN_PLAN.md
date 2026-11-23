# FFT64-Quant design record

## Goal and constraints

- Default `architecture` profile: S = 0.60·S_A + 0.30·S_T + 0.10·S_L with
  S_A = 3500/(A+3000), S_T = ln(T/T_min)/ln 240 (T = 1e9/(II·P)), S_L = (300−L)/237.
- Hard constraints: 64-point forward unscaled FFT, natural I/O order, 16-bit in / 24-bit out (Q15),
  per-frame SQNR ≥ 50 dB, exact zero for zero input, II=384 service, first output ≤ 300,
  last ≤ 364, 10 ns setup/hold, single posedge clock, synchronous reset.
- Marginal values at the final operating point (A≈1970 µm², P≈0.536 ns, L=122):
  10 µm² ≈ 0.00085, 10 ps ≈ 0.0010, 1 latency cycle ≈ 0.00042, halving II ≈ 0.038.
  So 1 cycle of latency ≈ 5 µm² ≈ 4 ps; throughput doubling would be worth ≈ 450 µm².

## Architecture hypotheses (made before implementation)

| Hypothesis | Expected effect | Outcome |
|---|---|---|
| H1 streaming R2³SDF (DIF) + serial bit reversal | II=64 for free (one sample/cycle), 63-word feedback + 49-word reorder (the minimum of 112 words for SDF + elementary bit exchanges, confirmed by a shortest-path search over schedules), 1 general rotator + 2 W8 rotators | **selected** |
| H2 memory-based / folded radix-2 | fewer butterflies but ≥64 random-access words with multi-port muxes, II ≥ 160–384, L ≥ 250; needs A < ~1500 µm² just to break even on S_T | rejected analytically |
| H3 R2²SDF | W64 + W16 rotator (W16 ≈ 3 constant multipliers) instead of W64 + 2×W8 | rejected (more arithmetic) |
| H4 bit-reversed input (DIT-like) or partial input-side bit exchanges | same 112 words, but long delays move to the wide end of the pipeline | rejected: +49 bits/component (full), 0/−4 bits for partial swaps |
| H5 lifting-form W64 rotator (3 shears) | 15 instead of 20 Booth rows, fewer flops, but 3 serial multiply-adds each ~410 ps of a 435 ps budget | estimated break-even, not built |

Storage dominates: 4242 flip-flops ≈ 1237 µm² (63 %) of the final 1971 µm².

## Final candidate (E030, "v7b" RTL + auto-ungroup/iterated recipe)

- **Architecture:** R2³SDF DIF; six SDF butterflies (delays 32,16,8,4,2,1); −j rotations after stages
  1 and 4 folded into the following butterfly (re/im swap + exchange of the imaginary sum/difference);
  W8 rotators after stages 2 and 5, hand-pipelined over 2 cycles (cycle 1: pre-add (a+b, b−a) with the
  re/im swap folded into one 4:1 select; cycle 2: ×181/256 with rounding); one general W64 rotator after
  stage 3 (64-entry ROM, 10-bit signed coefficients, 4 Booth multipliers, rounding, 3 register stages
  placed by DC retiming); Garrido bit-reversal (bit exchanges 3↔2, 4↔1, 5↔0: 4+14+31 words).
- **Fixed point:** input clamp +16384→+16383 (15 bits); LSB exponents (×2⁻¹⁵) after input/stages 1–6:
  m=[0,1,1,2,2,3,5], W8a/W64/W8b outputs at LSB 1/2/3. Butterflies 1–5 truncate (each drops ≤ 1 bit,
  where floor and rounding have the same MSE); stage 6 and all rotators round. W8 constant 181/256
  (|error| 1.1e-4), W64 coefficients rounded to 2⁻⁹. Every width comes from an exact interval
  analysis of the quantized linear map, so no legal input can overflow (checked bit-exactly with
  ±16384 corner stress frames).
- **Noise budget** (analytic, min-RMS frame): output rounding 56 %, three 1-bit truncations 28 %,
  twiddle quantization 9 %, rotator rounding 7 % → 52.9 dB expected, measured worst 52.5–53.1 dB.
  This allocation is balanced: every 1-bit narrowing tried costs more SQNR per µm² than it saves.
- **Area tricks:** alternating-polarity shift registers (DFFHQN only has QN) −153 µm²; no output
  register on stages 1 and 6; negation merged into butterflies; registered-position segment
  controllers with early-start flags; 3-bit counters for segments 5/6.
- **Synthesis recipe (`flow/dc_opt.tcl`):** internal clock 535 ps, which is a grid point of the
  evaluator's bisection scan (250 + 9750·j/1024 ps), so the certified period equals the target;
  `compile_ultra` (auto-ungroup allowed), retiming only inside the W64 rotator, Booth encoding,
  `optimize_netlist -area`, one `compile_ultra -incremental` + second `optimize_netlist -area`,
  incremental hold repair (needed: input-port paths violate hold by 1.4 ps without it).
  The exported flat netlist is re-measured by the evaluator; no Yosys/ABC flow is used.

## Measured decisions

| ID | Change | Measured observation | Decision |
|---|---|---|---|
| E001 | H1 baseline | quick PASS, SQNR 55.08 dB, L=120 | keep architecture |
| E003 | alternating-polarity delay lines | 2038 → 1885 µm² (10 ns) | accept |
| E004/5 | faster targets; rotator pipelining + retiming | retiming makes 0.6–0.8 ns nearly free | accept |
| E006/7 | exact widths, clamp, negation merge, precision search | −106 µm² at equal timing | accept |
| E008 | full evaluation (0.60 ns) | **0.7470** (1994.3 µm², 0.6023 ns, L=123) | baseline |
| E009/10 | Gauss 3-mult W64; tb=8 | +19 µm²; −3 µm² with only 1.7 dB margin | reject |
| E011/12 | rotator pipeline depth sweep; stage-6 register | (2,3,3) best; stage-6 register costs +42 | (2,3,x), no reg |
| E013/14 | XOR negation; 3-bit counters | +52 µm² / −3.8 µm² | reject / accept |
| E015 | m5=3 + recipe sweep | −25 µm²; recipes within ±2 µm², butterfly retiming +17 | accept m5=3 |
| E016 | registered controllers | **0.7496** (1969.0 µm², 0.5928 ns, L=124) | accept |
| E017 | DC options sweep | optimize_netlist −6.5; Booth on −1; Booth off +86; two-pass +42 | accept first two |
| E019–21 | hand-pipelined W8, register removal, R4 | −21 µm²; only stage 1/4 registers removable; R4=2 +121, R4=4 +18..31 | accept W8, R4=3 |
| E022/23 | swap folded into W8 select; target sweep 592→535 ps | faster clock now pays; projected S flat 0.7548–0.7559 | v7b |
| E024 | full evaluations v7b @554 / @535 ps | **0.75569** / **0.75585** | submit @535 |
| E025 | 526 / 516 ps | 1983.3 / 2034.6 µm² → projected 0.7558 / 0.7525 | 535 is optimal |
| E026/27 | radix-8 Booth; iterated recovery; stage-3 register removal | +60; −1.7; misses timing | reject; see below |
| E029 | recipe variants on the same RTL (no hold fix, iterated ×2, auto-ungroup, auto-ungroup+iterated) | hold −1.36 ps without repair; 1968.9 / 1969.0 / **1967.0 µm²** | auto-ungroup+iterated |
| E030 | full evaluation of E029 best | **0.75618** (1967.0 µm², 0.53564 ns, L=122) | **submitted** |
| E018/28 | 8192-frame robustness (3 seeds) | min SQNR 52.64–52.70 dB, service PASS | margin ≈ 2.6 dB |

## Best measured design

- Candidate E030; RTL sha256 `10d5092a3a200fcf…`, netlist sha256 `b136f7e2776adcb1…` (full hashes in
  measurements.csv); backend commercial (VCS/DC/PT, ASAP7 RVT TT); agent-mapped netlist + manifest.
- Public architecture preview (runs/arch_v7b_535ai): area 1967.017 µm², certified period 0.53564 ns
  (failing 0.52612 ns), verified II 64, worst first output 122 cycles (completion 185),
  minimum frame SQNR 53.08 dB; components S_A 0.7046, S_T 0.8610, S_L 0.7511
  → **S = 0.75618 (public_preview, not an official hidden score)**.
- Considered against v7b@535 old recipe (0.75585), v7b@554 (0.75569), v5a (0.7496), v2c (0.7470):
  highest verified preview.

## Remaining limitations

- Latency floor for SDF + bit reversal is ≈112 cycles (63 + 49); L=122 includes 10 pipeline registers
  that each cost more area/period than the 0.00042 a cycle is worth.
- SQNR feasibility is empirical (≥ 52.5 dB over ~48k public/synthetic frames incl. min-RMS stress),
  not a formal worst-case bound; the hidden data set is independent.
- Area/timing are pre-layout (ideal interconnect).
