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

Measured numerical screens (commercial VCS): F001 fails at 48.3534 dB;
F002 rounded Q13 passes at 50.6203 dB, first/last 256/319.
F003 uses two butterflies, four parity banks, Q14 data and Q11 twiddles:
56.3619 dB, first/last 160/223. F004 uses an exact three-real-product
complex multiply and gives the same quick SQNR and latency. Quick checks
include 1,024 consecutive mandatory-service frames but do not certify hardware.
F002 mapped diagnostic currently reports 1767.56256 um2 and passing 10 ns
setup/hold; representative gate simulation is still pending. F003 full
architecture preview and F004 mapped diagnostic are running.

## Decisions after measured architecture/precision changes

The complete F003 architecture run passed every public check, all integer IIs
64..384 were tested with 1,024 frames each, and II=224 was verified. Area
2213.14194 um2, certified period 3.687255859375 ns, worst SQNR 56.3619 dB,
first/last 160/223, public combined preview 0.5460158728.

S001 demonstrates that streaming can offset its area penalty: area3125.50002,
II64, certified period2.93505859375 ns, first/last139/202 and public preview
0.5759404055. Weighted change from F003: area -0.05999893, throughput +0.08106271,
latency +0.00886076, total +0.02992453. Both results use the same commercial
backend, libraries and policy.

S002 starts the natural-order burst 14 cycles earlier using
max(bit_reverse(k)-k)=49 and a safe first memory read 50 cycles after the first
reorder write. Alternating write orientation permits a single64-word memory
for II64, because the following frame overwrites the preceding read order.
S003 reduces twiddle precision from11 to9 fractional bits: quick minimum
55.7582dB. R001 pairs radix2 stages into radix2-squared and removes two
nontrivial rotations: quick55.9494dB, first/last121/184, mapped2738.82384um2.

R002 reduces fractional precision after each of the first two radix4 groups
(Q14 ->Q13 ->Q12). Biased half-up stage rounding gives minimum51.3049dB.
R003 uses round-to-nearest-even at input and these two stage boundaries,
raising quick minimum to53.2548dB. It preserves all FFT gain in the external
Q15 reconstruction. R004 registers decoded coefficients and three exact real
products for each remaining complex multiplication; same numerical result,
first/last123/186. The added two cycles will be accepted only if weighted
area/throughput gains exceed the0.00084388 latency-score cost.

Custom flow experiments C001/C002/C003/C004 use1ns/0.7ns/0.5ns/0.5ns synthesis
targets respectively, with compile_ultra and explicit incremental hold repair.
Final measurement always independently imports the export under the fixed
benchmark constraints; producer timing is not frequency certification.
The installed DC reports that its timing_high_effort_script flag is ignored;
clock-target steering still demonstrably changes mapping and timing.
Full frequency scans, gate comparisons and II searches remain pending for
candidates not yet marked COMPLETE in measurements.csv.

Current fully verified best (will be replaced only by a higher complete score):
C001, public architecture preview0.6350273249, II64, period1.002197265625ns,
area3227.92452um2, worstSQNR55.7582dB, first/last125/188. Export and recipes
copied into submission. Relative to default S003, weighted area contribution
-0.00879223 and throughput +0.05360537, latency unchanged, total+0.04481314.
This is evidence that synthesis clock steering justifies its area cost.

## Data-path organization

Each paired DIF group forms a=x0+x2, b=x1+x3, c=x0-x2, d=x1-x3.
The first SDF stage applies only the exact -j rotation to d. The second
forms (a+b), (a-b), (c-j*d), (c+j*d) in four successive quarters, then
applies twiddle powers0,2*j,j,3*j respectively. The next pair uses the same
identity on16-point groups; the final4-point groups require no nontrivial
coefficient. This implements the full forward FFT without frame scaling.

Pipeline data memories need no reset. A reset clears all valid/start delay
chains, frame counters and reorder controls. Every selected valid datum has
been overwritten by the new complete frame before use. Reset aborts an
inflight output prefix by dropping valid. All registers use the given
positive-edge clock; the synthesized flop arrays and all muxes are counted.

The staged-precision candidates accept Q15 external input, use RNE when
converting to Q14, and maintain one guard bit per butterfly. After paired
stages2 and4, RNE reduces Q14->Q13 and Q13->Q12. Final19-bit Q12 samples are
sign-extended and shifted left3 into the external24-bit Q15 fields; this
restores the fixed-point representation, without changing FFT gain. Both
remaining complex rotations use signed Q9 coefficients and one rounding
boundary after exact products/sums. C004 adds registers before and after
three-real-product arithmetic and predecodes coefficients before their
registers. C005 tests a shared one-hot decoder/OR reduction for the64-word
output memory read. These last candidates retain the same quick numerical
result,53.2547708dB, and first/last123/186 cycles.
