# FFT64 design record

## Architecture

The initial streaming radix-2² DIF implementation used two general rotators and one addressed 64-word output reorder buffer. Alternating read and write permutations let consecutive frames share the buffer. The baseline was intended to establish whether full-rate service could offset the mapped storage and read-mux area.

A folded FFT could share more arithmetic and lengthen the compute schedule. Its extra memory ports, longer initiation interval and later first output would need to buy enough area credit to recover those penalties. The DIF baseline and the DIT replacement both verified at II=64. The DIT delay-line cost made retaining continuous service the better experiment direction.

The DIT implementation applies the bit swaps (5,0), (4,1) and (3,2) at the input. These swaps use delays of 31, 14 and 4 complex words. For each pair of index bits, the later word bypasses the delay when it meets its earlier partner. The earlier word recirculates through the same delay once more. Equal-bit words pass through once. The three swaps and six SDF butterflies each advance their phase counter on local valid samples. Their output-valid delay preserves the 64-cycle burst across short, long and variable input gaps. Synchronous reset clears the valid pipelines and phase counters, so aborted payload cannot become valid.

The radix-2² DIT pairs use delays of 1/2, 4/8 and 16/32. The odd difference of the first butterfly in each pair absorbs a quarter-turn. The two general rotations precede the last two pairs. The DIT stages naturally emit bins in ascending frequency order, with a valid-sample counter marking the first bin. The feedback delays and all reordering storage map to standard-cell registers.

## Precision

The initial DIF and DIT designs used 15 fractional bits throughout and 12 fractional-bit twiddles. The three-product rotators in the first optimized DIT design used 12 fractional-bit twiddles and rounded Q15 to Q13 and then Q12.

The narrower design stores the input as a signed 15-bit Q15 word, saturating the +0.5 endpoint by one input LSB. Each butterfly adds one result bit. The W16 rotator uses Q9 coefficients and rounds to Q14, with a guard bit for component growth in the rotation. The W64 rotator uses Q10 coefficients and rounds to Q12. A three-real-product identity implements each complex product at the declared coefficient precision. The quarter-turns use signed swaps and negations. The final 19-bit result is sign extended and shifted by three to deliver the external 24-bit Q15 format and unscaled forward gain.

The absolute-residual variant factors the sign of the reduced angle into the input preadder and imaginary output accumulator. This puts the unity bit of cos(t)+sin(t) at a constant one and reduces the coefficient table to nonnegative residual angles. Both variants round by adding half of the output step before slicing. The split-product experiment keeps this quantization but registers low and high coefficient-chunk products before joining them.

An error budget uses the 1024-raw-unit minimum input RMS. With normalization for analysis, every radix-2² pair has unitary gain after division by two. The endpoint clamp contributes at most 1/16384 relative L2 error. The maximum complex coefficient errors are 0.000139 for W16 and 0.000567 for W64. Rounding at those boundaries contributes at most sqrt(2)/(2 × 1024) and 4 × sqrt(2)/(4 × 1024) when referred to the input. Carrying the coefficient gains through the previous error term gives a relative L2 bound of 0.002839, or 50.93 dB. The stage ranges include the worst-case complex component growth. The bound and the public per-frame measurements use the FFT of the actual quantized input.

## Synthesis and verification

The frozen DC baseline and the custom exports use the same ASAP7 RVT/TT libraries. Custom builds adjusted DC's optimization clock, used compile_ultra and then repaired minimum-delay paths with incremental hold mapping. The 640 ps area-recovery experiment added optimize_netlist -area. The independent import reapplied the public SDC and counted all mapped cells. PrimeTime separately bracketed each certified period on a fixed mapped netlist.

Architecture previews compared 1024 sustained frames at each of the 321 tested intervals. The minimum passing interval was checked again with 128 mapped frames, variable gaps and reset probes. VCS checked the RTL and mapped controls and payload from zero, one and seeded time-zero register initialization. The precision stress run used 8192 independent public random frames at seed 290113.

## Measurements

See [measurements.csv](measurements.csv) for source and mapping hashes, run paths, and weighted score differences. Quick checks and area diagnostics are identified by their profiles. Weighted deltas use the architecture comparison noted in each experiment. Only completed, resolved architecture previews determine which RTL and mapped implementation to submit.

### Completed architecture previews

| Candidate | Area (µm²) | II | Certified period (ns) | First / last cycles | Min SQNR (dB) | Public score |
|---|---:|---:|---:|---:|---:|---:|
| r22_baseline | 3061.23 | 64 | 2.59229 | 137 / 200 | 71.27 | 0.587217 |
| r22_dit | 2519.89 | 64 | 3.05884 | 124 / 187 | 71.66 | 0.617622 |
| r22_gauss_dc | 2398.82 | 64 | 0.90698 | 128 / 191 | 56.77 | 0.691009 |
| r22_narrow | 2319.77 | 64 | 0.75464 | 128 / 191 | 59.60 | 0.706855 |
| r22_split | 2513.08 | 64 | 0.62134 | 130 / 193 | 59.60 | 0.702808 |
| r22_tight | 2371.64 | 64 | 0.64038 | 128 / 191 | 59.60 | 0.712029 |
| r22_abs | 2353.01 | 64 | 0.64038 | 128 / 191 | 59.60 | 0.713390 |
| r22_abs_retime | 2447.12 | 64 | 0.58325 | 128 / 191 | 59.60 | 0.711727 |
| r22_abs_recover | 2344.67 | 64 | 0.64038 | 128 / 191 | 59.60 | 0.714002 |
| **r22_short_reorder** | 2327.20 | 64 | 0.64038 | 126 / 189 | 59.60 | 0.716134 |

The selected export is **r22_short_reorder**. It improves the baseline score by 0.128917. Its weighted area, throughput and latency contributions are 0.394203, 0.248513 and 0.073418. PrimeTime bracketed its period between 0.63086 ns and 0.64038 ns. [Selected public summary](../runs/arch_r22_short_reorder/summary.json)

The addressed DIF to streaming DIT change gained 0.03398 in weighted area and 0.00549 in weighted latency, with a 0.00906 reduction in throughput credit. The split-product pipeline gained 0.01064 in weighted throughput relative to the 750 ps unsplit build, with reductions of 0.01384 in area credit and 0.00084 in latency credit. Its combined score fell by 0.00405.

The Verilator mixed-gap check of the short-reorder RTL covered 2,049 frames including a zero frame, minimum-RMS impulses and a 66,001-cycle input gap. Its worst SQNR was 58.74 dB with exact zero output. This numerical check is separate from the commercial architecture previews.

The exported RTL, DC recipe, structural netlist and manifest match the selected public run. The area and timing measurements are pre-layout. Independent hidden acceptance and post-route performance remain outside these measurements.
