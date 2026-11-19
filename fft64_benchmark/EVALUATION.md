# Evaluation

## What is measured?

`run_preview.sh` performs four steps on the submitted circuit:

1. Simulate legal input packets, natural-order output, reset recovery and idle intervals.
2. Compare each complete output frame with a float64 FFT of the same quantized input; measure SQNR and actual cycle latency.
3. Map the entire circuit into the supplied ASAP7 cells and check the fixed 10 ns timing target.
4. Simulate that mapped netlist on the same transactions and compare its output values and control cycles with its RTL.

The quick mode stops after steps 1–2. It is useful for debugging, but does not establish a final hardware result.

The official backend uses VCS, Design Compiler and PrimeTime. A local Yosys/ABC/OpenSTA backend supports development when commercial tools are unavailable. Its full-data gate simulation uses Verilator, with an additional Icarus four-state reset/corner subset; the commercial backend uses VCS four-state simulation throughout. These flows have separate area references.

## Public feedback

| Field | Meaning |
|---|---|
| `functional_pass` | Framing, reset, order and numerical checks passed |
| `worst_frame_sqnr_db` | Minimum over nonzero tested frames |
| `first_output_cycles`, `completion_cycles` | Observed frame latencies |
| `timing_pass`, `worst_slack_ns` | Fixed 10 ns constraints |
| `full_mapped_area_um2` | Entire mapped design, including storage |
| `mapped_simulation_pass` | Same-candidate RTL/netlist transaction comparison |
| `area_ratio` | Area relative to a calibrated accurate reference, when available |

Raw results and debugging logs remain in the requested output directory. Missing measurements are left unmeasured rather than reported as zero.

## Quality and ranking

Every nonzero tested frame needs SQNR ≥50 dB; zero input needs exact zero output. All offered frames must be returned within the stated deadlines. Larger gaps and resets are part of the protocol tests. Random seeds differ between public development and final evaluation; directed test families are shared and include low-RMS complex sign patterns.

For a fully feasible candidate, let `R=A/A_ref`. The proposed passing target is `R≤0.80`; the continuous score is `clip(1-R,0,1)`, the fractional area saving. No additional points are assigned for documentation length or the number of attempted designs.

Precision reduction is an available optimization, not a required operation. An exact architectural optimization that meets the same area and service target is also a valid solution.

`A_ref` is the smaller area of the operator's accurate implementations, measured with the same library, backend and constraints. It is separate from the float64 numerical oracle. The commercial area reference and proposed pass target must be calibrated and published before official agent trials. They remain pending in this package.

## Scope

This is the serial, area-oriented profile: 64 input cycles per frame with a 384-cycle service interval. It tests architecture selection under that load; it does not claim to test maximum-throughput MDC performance. A future 64-cycle or parallel-input profile would need separate calibration and ranking.

The current PPA objective is **pre-layout mapped area and ideal-interconnect STA**. No post-route or power result is implied. Finite numerical tests and mapped simulation are empirical checks; optional RTL-to-netlist formal checking is a separate verification step.
