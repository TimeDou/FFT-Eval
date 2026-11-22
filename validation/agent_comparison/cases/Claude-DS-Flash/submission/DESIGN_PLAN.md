# DESIGN_PLAN.md — 64-point fixed-point complex FFT (FFT64-Quant)

All numbers below are **measured** with the public `run_synopsys_debug.sh` flow
(commercial backend: VCS + Design Compiler + PrimeTime, ASAP7 RVT/TT, 10 ns
target clock). Nothing here is a claimed official score; the public preview
cannot produce a calibrated score.

## 1. Contract summary used for design decisions

| Item | Value |
|---|---|
| Transform | forward, unscaled, natural input, natural frequency output |
| Data | in 16-bit Q15, out 24-bit Q15, both components |
| Per-frame SQNR | >= 50 dB vs float64 FFT of the *same quantised* input |
| Service | 64 consecutive inputs; frame starts >= 384 cycles apart |
| Deadlines | first output in [63, 300], last output <= 364 cycles |
| Timing | 10 ns setup/hold after mapping; complete mapped cell area is scored |
| Score (architecture) | 0.60 area + 0.30 effective throughput + 0.10 first-output latency |

## 2. Architecture hypotheses and their expected trade-offs

| # | Hypothesis | Expected area | Expected II | Expected latency | Verdict |
|---|---|---|---|---|---|
| H1 | Streaming R2SDF (6 butterflies, 6 complex multipliers, 57-word shift-register delays), II = 64, needs a 64-word bit-reversal output buffer | high (6 multipliers + reorder buffer) | 64 | 64 | **rejected by analysis** |
| H2 | R2^2SDF (3 multipliers, 6 butterflies) + bit-reversal buffer | medium-high | 64 | 64 | rejected by analysis |
| H3 | Folded memory-based in-place radix-4 DIT, 1 radix-4 butterfly engine, k time-shared complex multipliers, 64-word 2R2W register file | low | 150–320 | 150–320 | **selected** |
| H4 | Same as H3 but radix-8 (2 stages x 8 butterflies) | medium (large 8-point DFT network, 8-word in-flight banks) | ~90 | ~90 | rejected: smaller II gain than area cost |

Key measured facts that drove the choice (ASAP7, DC `compile_ultra`):

* 64 x 44-bit 2R2W register file = **1606 um2**; the shift-register delay lines of
  an R2SDF (57 words) = 954 um2, i.e. the memory cost is comparable, so the
  decisive term is the multiplier count.
* One 3-multiplier Karatsuba complex multiplier (`cmul3`) = **252 um2**;
  a naive 4-multiplier complex multiplier = **456 um2**.
* An R2SDF/R2^2SDF additionally needs a 64-word bit-reversal output buffer
  (1254 um2) because an SDF emits bit-reversed order, while an **in-place
  memory array absorbs the bit reversal for free in the input write address**
  (base-4 digit reversal). That tips the choice to H3.

Selection: H3 with radix-4 (3 stages x 16 butterflies = 48 butterflies,
3 twiddle multiplications each). Stage 0 has only trivial twiddles (W4), so the
multiplier load is 81 complex products per frame.

## 3. Current candidate

* **Algorithm**: in-place radix-4 DIT, 3 stages. Input written at base-4
  digit-reversed addresses, output read sequentially -> natural order at both
  ends with zero extra storage.
* **Memory**: 64 entries x 2 x 22 bit, 2 read + 2 write ports (a register file;
  all storage is counted, no SRAM).
* **Datapath**: 22-bit signed Q15. `|x[n]| <= 0.5` and `|X[k]| <= 32`, so six
  growth bits plus sign fit in 22 bits -> **all butterfly additions are exact**
  and only the twiddle products are rounded (round-half-up by TWF bits).
* **Twiddle**: 14-bit/12-bit signed Q10 table with 1/8-wave symmetry (9 stored
  complex entries + swap/negate), precomputed one butterfly ahead into
  registers. W = 1 is exact, so stage 0 needs no multiplication at all.
* **Complex multiplier**: 3-multiplier Karatsuba form
  `t1=(ar+ai)wr, t2=ar(wi-wr), t3=ai(wr+wi), pr=t1-t3, pi=t1+t2`.
  The three operand pre-sums are held in registers so only the array
  multiplier and one rounding adder remain on the critical path.
* **Schedule**: 64 load cycles + 49 x 4 compute slots + 64 output cycles =
  324 cycles per frame. Slot 0/1 read the butterfly operands, slot 2 runs the
  three complex multipliers, slot 3 evaluates the radix-4 DFT. Each result word
  is written back on one of the four slots of the *following* butterfly, which
  lets a single write port serve the whole transform.
* **Throughput**: three complex multipliers in parallel (one per twiddle bank)
  -> one multiply slot per butterfly, so II is set by the memory slots and not
  by the arithmetic.

### Measured bottleneck

Two paths are nearly balanced at the 10 ns constraint (2.37 ns critical,
7.53 ns slack): (a) `state -> read-address mux -> 64:1 memory read mux ->
sum-precompute adder -> register`, and (b) `twiddle register -> array
multiplier -> rounding adder -> register`. Both are inherent to a folded
design that performs one complex multiply per read cycle; shortening one just
moves the critical path to the other (measured: removing the pre-sum adder
made the multiplier path the limiter at ~2.5 ns).

## 4. Measured decisions (see measurements.csv for the full table)

| ID | Change | Measured observation | Decision |
|---|---|---|---|
| E001 | First working folded radix-4 RTL (3 multipliers, sequential output) | area 2882 um2, slack 5.76 ns, SQNR 71.66 dB, first output 259 | accept as baseline |
| E002 | Register the read addresses and twiddle values one butterfly ahead | slack 5.76 -> 6.40 ns, area 2882 (unchanged) | accept |
| E003 | Register the *twiddle values* (not just the index) | slack 6.40 -> 7.18 ns, area +110 um2 | accept: latency/throughput dominate the small area cost |
| E004 | Precompute the Karatsuba operand sums in registers (`arpai`, `wr+wi`, `wi-wr`) | slack 7.18 -> 7.47 ns | accept |
| E005 | Stream the natural-order output during the last radix-4 stage | **SQNR destroyed (0.9 dB)**: a radix-4 stage emits X[b], X[b+16], X[b+32], X[b+48] per butterfly, so contiguous output words are *not* available early | reject, reverted |
| E006 | Stage-0 fast path (3 slots instead of 4, multiplier bypassed) | first output 259 -> 243, completion 322 -> 306, SQNR unchanged | accept |
| E007 | Twiddle precision 12 -> 10 fractional bits (14 -> 12 bit Q10) | SQNR 71.66 -> 67.60 dB, area 3018.7 -> 2886.8 um2 | accept: still 17 dB margin |
| E008 | Single write port: one result word per butterfly slot instead of two (the E006 stage-0 3-slot fast path no longer fits, so it is dropped; the exactness-preserving twiddle bypass for stage 0 is kept) | area 2886.8 -> **2662.2 um2**, II 308 -> 324, latency 243 -> 259, slack 7.49 -> 7.53 ns | **accept**: -7.8 % area costs only 5 % throughput and 7 % latency; area carries 60 % of the weight |

### Rejected / analysed but not built

* **R2SDF / R2^2SDF**: the measured 1606 um2 register file vs 954 um2 of SDF
  delay lines does not repay 3-6 complex multipliers (252-756 um2 each pair)
  plus the mandatory 1254 um2 bit-reversal buffer.
* **Fully parallel (192 butterfly units)**: arithmetic area scales ~50x.
* **Output streaming**: measured to be structurally impossible (E005).
* **Banked memory to halve the read-mux cost**: proved impossible — a fixed
  bank function would have to be injective on the cosets of all three radix-4
  stages simultaneously, which no fixed 2-bit function is.

## 5. Best measured design

* RTL: `submission/rtl/{fft64_top,cmul3,twiddle_gen}.v`
* Measured (`runs/arch1`, E007 candidate, commercial backend, default mapping
  recipe): worst-frame SQNR **67.60 dB**, mapped area **2886.8 um2**,
  first output 243 / completion 306 cycles, worst setup slack 7.49 ns,
  smallest verified II **308** over 1024 continuous frames plus a mapped
  RTL/gate comparison, PrimeTime-certified period **2.5161 ns**
  (397.4 MHz), effective throughput **1.290e6 FFT/s**.
* **Submitted design (E008, single write port)** measured end-to-end in
  `runs/arch2` with the full `architecture` profile:
  * `resolved = true`, `feasible = true` (every mandatory check passed)
  * worst-frame SQNR **67.60 dB** (limit 50), zero frame exactly zero
  * full mapped area **2662.25 um2**
  * smallest verified II **324 cycles** (all 321 intervals 64..384 tested with
    1024 continuous frames each; 323 and below fail, 324 and above pass)
  * mapped RTL/gate comparison PASS at II = 324 (128 frames, 3 gate initial
    states, gap and dense-reset probes)
  * PrimeTime-certified period **2.4685 ns** (405.1 MHz), hold passes
  * effective throughput **1.2503e6 FFT/s** (4.8x the mandatory 384-cycle
    service rate)
  * first output **259** cycles, completion **322** cycles (limits 300 / 364)
* E008 was selected over the slightly faster E007 (2886.8 um2, II 308,
  2.5161 ns, 1.290e6 FFT/s) because area carries 60 % of the weight: at any
  reference area below ~5770 um2 E008 scores higher, and above it the loss is
  under 0.015.

## 6. Remaining limitations and next actions

* The frame interval is set by `load(64) + compute(196) + output(64) = 324`
  cycles. Overlapping the load with stage 0 would save ~15 cycles (stage-0
  entry i is fully loaded at cycle 48 + 4*(i&3) + (i>>2) with a reordered
  butterfly sequence), and starting the next load 46 cycles into the output
  phase (the largest safe offset `max(A - dr4(A)) = 45`) would save a further
  ~18 cycles. Both were left out because they only move the 30 %-weighted
  throughput term by a few percent while adding real scheduling risk.
* The memory subsystem (2816 flops + two 64:1 read muxes) is ~45 % of the
  area; the read-mux cost is irreducible for a 2-read-port random-access array
  (see the banking proof above).
* A custom synthesis recipe was not adopted: the frozen default recipe
  (`compile_ultra -area_high_effort_script` plus hold repair) is what the
  reference designs use, so the measurement stays comparable and no
  exported netlist can drift out of sync with the RTL.
* Further work would target a 2-cycle pipelined multiplier. Splitting the
  Karatsuba products from the rounding adder keeps II at 324 but lowers the
  certified period from ~2.5 ns to ~1.9 ns (measured estimate: +90 um2 of
  product registers), worth about +0.01 total score at the current balance,
  so it was not adopted.
* A custom DC recipe was evaluated analytically and rejected: the score
  derivative of area (60 % weight, ~289 um2 per 0.09 score) dominates the
  derivative of the certified period at the 10 ns mapping point, so the
  minimum-area default recipe is the right operating point.
