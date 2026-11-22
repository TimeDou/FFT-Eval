# FFT64-Quant: design and measured selection

## Objective and constraints

Architecture profile: S=0.60*S_A+0.30*S_T+0.10*S_L, with S_A=clip(3500/(A+3000)), S_T=clip(ln(T/260416.66666666666)/ln(240)), S_L=clip((300-L)/237). All values below are commercial public previews using the fixed ASAP7 RVT/TT libraries; none is an official hidden grade. SQNR above 50 dB has no score bonus. The 500 um2, 62.5 M FFT/s and 63-cycle scales are aspirational anchors.

Mandatory contract: complete 64-point forward unscaled FFT, natural input/output, signed 16-bit input and 24-bit output with 15 fractional bits; each tested nonzero frame >=50 dB, exact zero frame; synchronous high reset aborts inflight work; 64 consecutive outputs, 384-cycle service, first output<=300 and last<=364, setup and hold at 10 ns.

## Initial competing hypotheses and numerical screens

- Folded radix2 with one shared butterfly minimizes arithmetic, but bank muxes and 192 compute cycles can lose throughput and latency credit.
- Two shared butterflies with four parity banks trade duplicated arithmetic for 96 compute cycles and shorter bank muxes.
- Streaming SDF can earn enough II/frequency credit to justify more storage and arithmetic; radix2-squared pairing and a single alternating reorder buffer may limit its area cost.

F001 used 20-bit Q13 storage and Q13 twiddles with truncation; numerical screen failed at 48.353385 dB. F002 rounded inputs/products and passed at 50.620292 dB, first/last 256/319. Its complete area diagnostic passed mapped checks at 1767.56256 um2; no combined architecture score is claimed. F003 used two butterflies, four parity banks, Q14 data and Q11 twiddles. F004 replaced four real products by three exact products; area fell from 2213.14194 to 2108.98242 um2 but fixed-clock STA path estimate worsened from 3.6779 to 4.3187 ns. The diagnostic alone did not justify selecting F004; it has no full combined score.

S002 began natural-order reads 14 cycles sooner than S001. S003 reduced coefficient precision to 9 fractional bits. R001 paired radix2 stages into radix2-squared, removing two nontrivial complex multipliers. R002 tried half-up stage rounding at Q14->Q13->Q12 and passed at 51.304864 dB; R003 changed input and stage boundaries to nearest-even and passed at 53.254771 dB. R004 predecoded coefficients and registered three exact real products; numerical output stayed the same, with two added cycles. R005/C005 tested one-hot output memory reads. R006/C006 and R007/C007 quantized only final reorder storage to Q10 and Q11 respectively. The Q10 screen passed at 50.220814 dB; independent public-seed 8192-frame screens gave 50.284084 dB (Q10) and 51.954103 dB (Q11). These are public development inputs, not hidden evaluation data.

## Complete architecture measurements

| Candidate | Area um2 | Worst SQNR dB | Verified II | Certified ns | First / last cycles | Public score |
|---|---:|---:|---:|---:|---:|---:|
| F003 | 2213.14194 | 56.361896 | 224 | 3.687255859 | 160 / 223 | 0.546015873 |
| S001 | 3125.50002 | 56.361896 | 64 | 2.935058594 | 139 / 202 | 0.575940406 |
| S003 | 3069.65862 | 55.758176 | 64 | 2.668457031 | 125 / 188 | 0.590214187 |
| R001 | 2738.82384 | 55.949368 | 64 | 2.697021484 | 121 / 184 | 0.611264546 |
| C001 | 3227.92452 | 55.758176 | 64 | 1.002197266 | 125 / 188 | 0.635027325 |
| C002 | 3073.79934 | 55.949368 | 64 | 0.811767578 | 121 / 184 | 0.656806751 |
| C003 | 2954.30166 | 53.254771 | 64 | 0.811767578 | 121 / 184 | 0.663745601 |
| C004 | 3014.19630 | 53.254771 | 64 | 0.640380859 | 123 / 186 | 0.672370565 |
| C005 (selected) | 3023.22132 | 53.254771 | 64 | 0.630859375 | 123 / 186 | 0.672667356 |
| C006 | 3101.16600 | 50.220814 | 64 | 0.640380859 | 123 / 186 | 0.667393230 |
| C007 | 3170.07108 | 52.557272 | 64 | 0.640380859 | 123 / 186 | 0.663549371 |

All full runs use 1024 independent random frames plus 192 directed frames, 1024-frame continuous mandatory service, all 321 integer IIs 64..384 with 1024 consecutive RTL frames each, representative mapped comparisons from initial modes 0, 1, 20261121, and fixed-netlist PrimeTime clock scans. The smallest passing II is independently measured. Failed optional intervals are not mandatory violations. Quick screens and area diagnostics are separate rows in measurements.csv and have no combined score.

## Weighted decisions

| Comparison | 0.60 delta area | 0.30 delta throughput | 0.10 delta latency | Delta total |
|---|---:|---:|---:|---:|
| F003 -> S001 | -0.059998932 | +0.081062706 | +0.008860759 | +0.029924533 |
| S001 -> S003 | +0.003154059 | +0.005212549 | +0.005907173 | +0.014273781 |
| S003 -> R001 | +0.019945425 | -0.000582830 | +0.001687764 | +0.021050359 |
| S003 -> C001 | -0.008792230 | +0.053605368 | +0.000000000 | +0.044813138 |
| R001 -> C002 | -0.020181294 | +0.065723499 | +0.000000000 | +0.045542205 |
| C002 -> C003 | +0.006938850 | +0.000000000 | +0.000000000 | +0.006938850 |
| C003 -> C004 | -0.003512358 | +0.012981204 | -0.000843882 | +0.008624964 |
| C004 -> C005 | -0.000523192 | +0.000819984 | +0.000000000 | +0.000296792 |
| C005 -> C006 | -0.004454143 | -0.000819984 | +0.000000000 | -0.005274126 |
| C005 -> C007 | -0.008298002 | -0.000819984 | +0.000000000 | -0.009117986 |

Choose the highest completed feasible combined preview, even when another candidate has lower area, more SQNR or shorter latency. All selected score components are below saturation; II 64 is already the lower boundary of the tested serial-interface range.

The narrower final buffers were retained only as experiments: fewer storage bits do not imply smaller complete mapped area. Their rounding logic and resulting timing-driven mapping must be included. The selected design is chosen by the full combined score, with no SQNR bonus.

## Final implementation

Selected **C005**, score **0.672667356470**, resolved=true, score_valid=true, scoring_scope=public_preview, official_score=false. Mapped area 3023.221320002 um2; II 64; certified period 0.630859375000 ns; effective throughput 24767801.858 FFT/s; worst first/last 123/186 cycles. Minimum SQNR across all matching-source public runs is 53.254770813 dB. Zero-frame output is exact.

Final components: S_A=0.581084408832, S_T=0.831110556224, S_L=0.746835443038. Weighted contributions are 0.348650645299, 0.249333166867, 0.074683544304 respectively.

The final radix2-squared SDF pipeline has feedback depths 32, 16, 8, 4, 2, 1 complex samples. For each paired group a=x0+x2, b=x1+x3, c=x0-x2, d=x1-x3: the first stage applies only exact -j to d; the second forms a+b, a-b, c-j*d, c+j*d in four quarters, followed by twiddle exponents 0, 2*j, j, 3*j. There are two nontrivial complex rotations. Each uses three exact real products with no intermediate quantization, registered coefficients/products, and one post-product quantization boundary.

Nearest-even Q15->Q14 at input, Q14->Q13 after stage 2 and Q13->Q12 after stage 4; 19-bit Q12 final reorder storage; outputs shift left 3 into external Q15.
A guard bit is added at each butterfly. Twiddle factors have 9 fractional bits in signed 10-bit coefficients; unit and quarter rotations bypass multiplication exactly. Fixed-point representation shifts preserve external FFT gain. Products use half-up nearest rounding, while the explicitly named narrowing boundaries use nearest-even. No gate pruning or approximate arithmetic compressors are used.

Natural-order output uses one 64-word complex flop memory. Successive frames alternate sequential and bit-reversed write addresses; each following frame overwrites in the preceding read order, safely supporting II 64 without a second frame buffer. Since max(bit_reverse(k)-k)=49, the first read at offset 50 is safe and yields one 64-cycle output burst. All buffers, read/write muxes, coefficient logic and control are counted.

All state uses the specified positive-edge clock. Reset clears valid/start chains, counters and reorder state; data arrays need no reset because a fresh complete transaction overwrites each valid datum before use. Long idle gaps do not advance a free-running frame timer. All reset and gap tests passed.

## Synthesis and provenance

The custom DC recipe flattens hierarchy, sets a 0.5 ns synthesis target, fixes multiple-port nets, keeps the direct clock, runs compile_ultra with a timing request, then incremental hold repair. The installed DC reports its timing_high_effort_script flag as ignored; clock steering and legal mapping still produce the measured implementation. The 0.5 ns target is an optimization request, not a timing claim. Independent grading imports the structural netlist without recipe execution, applies the fixed 10 ns SDC and certifies the actual period above. Constraints, libraries, scorer and reference were never changed.

RTL source SHA256: `7d4a8287c6e9d7e2ad2b8a6318b47c290c7814ae81a4ff276cf2ef4cfd5e01d3`.
Submitted mapped SHA256: `877fb54295983dc817e2af185260df2d81a26cbb2094ab1758b55a3d9aa4a7af`.
flow/dc_opt.tcl SHA256: `73d061c4b926a593266e0de6016bf70ebdd124a6a1a516ad8d5a626276a245f4`.
implementation/manifest.json SHA256: `60459248f8290a33fc79259a641adcca97e80375cfeb6f778b3453bb6e8ccc61`.
Authoritative public report: `runs/arch_C005/result.json`, copied byte-for-byte to `submission/public_verification.json`. Selection/report hashes are in `frozen_selection.json`. All experiments and source snapshots remain under `experiments/`; full measurements and per-component scores are in `measurements.csv`.

Reproduce with `bash run_synopsys_debug.sh submission --profile architecture --out runs/reproduce_final` from FFT-Bench. To regenerate the export with the matching recipe use `bash synopsys.sh build submission --export --out runs/rebuild_final`, then independently evaluate in a fresh output directory.

The selected C005 build timing report identifies the stage3 pre-add/combined-product path as the remaining frequency bottleneck (bf_reg_re to prod_combined). The producer requested 0.5 ns and did not meet it; only the independently certified period above is used in the score. The exact three-product transformation was also checked offline against existing R003/R004 public simulation traces: all 77,824 scored complex outputs matched bit-for-bit across 1,216 frames after accounting for the two added latency cycles; see experiments/three_product_equivalence.json.

## Limits and stopping decision

Stopped after 11 completed architecture candidates plus numerical and area screens. The selected candidate has the highest complete feasible public score in this search. No global optimality or hidden-test acceptance is claimed. SQNR margin on the worst observed matching-source public frame is 3.254771 dB; this is finite empirical coverage. Timing/area are pre-layout ideal-interconnect measurements, not routed/silicon performance or power. Formal equivalence and P&R were not run; required multi-initial-state mapped simulation and STA passed. No private FFT-Eval resources, calibration or hidden inputs were accessed.
