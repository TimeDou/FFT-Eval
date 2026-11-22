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

## First measured revisions

- The 22-bit baseline passed 1,216 public numerical RTL frames (Icarus), worst
  SQNR 74.9669 dB, first/completion 256/319. This is simulation evidence,
  not mapped hardware feasibility.
- Fused stage 0 into the last 32 input clocks and stage 5 into the first 32
  output clocks. Parity banking is unchanged. Measured first/completion became
  192/255; 1,024 continuous frames plus 16 mixed-gap frames passed at II=256.
- An 18-bit fixed scaling schedule divides by two after stages 2,3,4,5 and
  restores the accumulated factor 16 at the output. Rounding stage divisions
  to nearest even gives 55.0687 dB minimum on public RTL simulation with Q9
  coefficients. The model rejected 17-bit storage with the corresponding
  fixed schedule (49.7 dB); initial Q12 input truncation also failed.
- Three real products compute the exact same complex rotation before the
  declared rounding. Compact signed Q9 coefficients exclude +1 from the ROM
  because unity bypasses the multiplier. Public RTL results match the
  four-product design exactly; synthesis decides whether this saves area.
- Revised hypothesis: fixed late-stage shifts waste precision in low-energy
  frames. A shared adaptive block exponent can retain the input's precision
  longer and reduce register width. Two accumulated leading-magnitude flags
  choose 0/1/2-bit shifts only at stage boundaries, conservatively bounding
  each next butterfly by 3*M (stage 1 uses the tighter 2*M trivial-rotation
  bound). Rotated operands and pre-shift sums are widened to prevent overflow.
  Output left shift restores the FFT gain. Measured public RTL worst SQNR:
  16-bit 60.6597 dB; 15-bit 55.0001 dB. Both retain first/completion 192/255.
  Area/timing measurements will decide whether flag and shift overhead pays.

The first adaptive candidate exposed a compiler-portability issue: Icarus
accepted a register reference before its declaration, while VCS rejected it.
Declarations were moved before use, then the corrected candidate passed VCS
quick and full mapped checks. The initial failed log is retained in
`runs/quick_block15`; arithmetic behavior did not change.

## Mapped comparison and revised strategy

All of the following area-profile runs passed public numerical/protocol,
mandatory service, mapped comparison from three initial states, and 10 ns
setup/hold on the same commercial ASAP7 backend:

| Candidate | Area (um2) | First / completion (cycles) | Worst public SQNR (dB) |
|---|---:|---:|---:|
| 22-bit baseline | 1768.33530 | 256 / 319 | 74.9669 |
| Fused fixed 18-bit, 3 products | 1347.32322 | 192 / 255 | 55.0687 |
| Fused fixed 18-bit, 4 products | 1368.52254 | 192 / 255 | 55.0687 |
| Adaptive 15-bit | 1215.65124 | 192 / 255 | 55.0001 |
| Adaptive 15-bit, one pipeline register stage | 1238.54184 | 193 / 256 | 55.0001 |
| Adaptive 15-bit, two pipeline register stages | 1271.55096 | 194 / 257 | 55.0001 |
| Adaptive 15-bit, DC 2 ns target | 1318.39650 | 192 / 255 | 55.0001 |

Measured three-product rotation saves only 21.20 um2 versus four products in
the fixed-width candidate, while its 10 ns slack is worse. Thus fewer
multipliers alone did not predict the better timing result.

The adaptive 15-bit design also passed 8,592 additional self-generated public
frames at seed 761239, including maximum-bin growth and magnitude-boundary
patterns: worst 54.8681 dB. This is additional public robustness evidence,
not a hidden-evaluation result.

Pipeline stages carry addresses, stage identity and valid bits. Writes from
one stage overlap reads from the next; the address ordering avoids read-after-
write hazards at these two pipeline depths. The block exponent changes after
the final writeback of a stage, before the next stage's quantization. Measured
public 1,024-frame service plus mixed gaps passed at II=257 and 258 respectively.

Independent PrimeTime scans certified 3.687255859 ns for adaptive 15-bit,
2.906494141 ns for one pipeline stage, and 2.373291016 ns for two pipeline
stages, all with setup and hold passing and <0.01 ns passing/failing brackets.
These are pre-layout certificates, not silicon or post-route frequencies.

The 2 ns unpipelined custom mapping meets its target but costs 102.75 um2 over
its relaxed mapping. A final 1.5 ns mapping experiment on the two-stage
pipeline tests whether timing can improve with a smaller area penalty.

## Final selected hardware

The retained implementation is the 15-bit adaptive-block-exponent folded FFT
with two butterfly pipeline register stages and a custom DC mapping target of
1.5 ns. Independent import measured **1275.53130 um2**, 9749 standard cells,
and **634.24458 um2** of sequential area. At the mandatory 10 ns clock, setup
slack is **8.500350586 ns** and hold slack **0.012975995 ns**. The full
architecture-capacity and frequency checks are recorded below after completion.

This mapping costs only 3.98034 um2 over the relaxed two-stage mapping while
substantially improving timing. It has lower measured area and greater 10 ns setup slack than the unpipelined
2 ns mapping. The minimum-area alternative remains archived in
`experiments/block15`; a matching frozen scoring calibration is unavailable,
so the exact combined-score ranking of Pareto alternatives cannot be proved.
The final choice favors the large measured timing improvement at modest area
cost, with all candidate raw measurements preserved.

Precision and implementation details:

- External components remain signed Q15: 16-bit input, 24-bit output.
- Input is rounded once to Q14 (ties toward positive infinity). Two parity
  banks each contain 32 complex 15-bit words, implemented entirely in counted
  standard-cell registers. Input bit reversal and natural output addressing
  provide the complete reorder function without an external memory.
- The first butterfly stage divides by two. Subsequent stages use a shared
  0/1/2-bit shift selected from the preceding stage's accumulated magnitude
  flags; all such divisions round to nearest even. A four-bit exponent tracks
  every division, including input quantization. A signed output shift restores
  the unscaled external FFT gain.
- Signed Q9 twiddles use 10 bits. Unity and -j rotations are exact bypasses;
  nontrivial rotations use three full integer products and then declared
  nearest rounding (ties toward positive infinity). No approximate Boolean
  transformations or approximate compressors are used.
- Two pipeline register stages separate memory reads, complex products, and
  butterfly writeback. Metadata tracks bank addresses, stage boundaries,
  validity and the first output. Reset clears control/valid state and aborts
  pending work; storage is overwritten by a new complete frame.
- Only the input `clk` rising edge is used. ROM, register banks, muxes,
  exponent control, pipeline state, rounding and output adaptation are all
  part of the mapped top. No SRAM macros, generated clocks or external logic.

The custom recipe uses `compile_ultra -area_high_effort_script` followed by
incremental hold repair. Its 1500 ps synthesis target steers mapping only;
independent evaluation retains the benchmark's 10 ns SDC and fixed libraries.
`implementation/manifest.json` binds the exact RTL, mapped artifact, recipe
and library hashes. Exported recipe copies accompany the netlist. No scripts,
thresholds, policies or specifications in the benchmark were changed.

## Completed full architecture verification

`runs/final_architecture` completed successfully with public hardware feasibility
`resolved=true`. The matching frozen calibration is unavailable (`score_valid=false`);
no hidden or official score is claimed.

- Complete mapped area: 1275.53130 um2, **27.87% smaller** than our
  initial 22-bit baseline on the same backend.
- Minimum public evaluated SQNR: 55.000071 dB; exact zero passed.
  An additional 8,592 self-generated public RTL frames passed at
  54.868109 dB minimum.
- All **321 integer intervals 64..384** were exercised with **1,024 continuous
  RTL frames per interval**. Smallest passing II: **258 cycles**; 128 mapped
  confirmation frames plus 16 gap-tail frames passed, with dense reset probes.
- Maximum first output: **194 cycles**; maximum completion: **257 cycles**.
- Fixed-netlist PrimeTime certificate: passing **1.506835937500 ns**,
  failing **1.497314453125 ns**, setup and hold pass. Frequency
  **663.642255 MHz**, effective throughput
  **2572256.804 FFTs/s** under the benchmark definition.
- Full representative and best-II RTL/mapped comparisons pass from initial
  states 0, 1, and seed 20261121. Additional reset-abort testing at 31 offsets,
  including the active output interval and pipeline boundaries, passed from all
  three states; the next frame starts immediately after reset.

The retained design costs **4.93%** more area than the fully verified minimum-area
15-bit alternative, for **2.428x** its measured effective throughput and two extra
latency cycles. This is the selected architecture trade-off; without frozen
reference normalization it is not a claim of a globally optimal score.

Reports and hashes are in `verification/`, including the full public result,
321-interval CSV, frequency trials and setup/hold reports. `measurements.csv`
contains actual candidate results, with model-only screens labeled separately.
The exported structural netlist and recipe exactly match the final RTL hashes.
Benchmark tracked specifications, tools and policy files remain unchanged.

Reproduce independent evaluation from the repository root with:

```bash
bash run_synopsys_debug.sh submission --profile architecture --out runs/recheck_final
```

After any RTL or recipe change, rebuild/export first using a new output directory:

```bash
bash synopsys.sh build submission --export --out runs/rebuild_final
```

Remaining limits: the measurements are pre-layout and empirical over the tested
frames; formal equivalence, routed timing, power and global optimality are not
established. Input capture, compute and output phases largely share one storage
array; this implementation's verified II is 258, rather than a one-sample-per-
clock continuous streaming FFT. No hidden data or private calibration was used.
