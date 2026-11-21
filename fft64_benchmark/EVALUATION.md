# Evaluation

## What is measured?

`run_preview.sh` performs four steps on the submitted circuit:

1. Simulate legal input packets, natural-order output, reset recovery and idle intervals.
2. Compare each complete output frame with a float64 FFT of the same quantized input; measure SQNR and actual cycle latency.
3. Map the entire circuit into the supplied ASAP7 cells and check the fixed 10 ns timing target.
4. Simulate that mapped netlist on the same transactions and compare its output values and control cycles with its RTL.

The quick mode stops after steps 1–2. It is useful for debugging, but does not establish a final hardware result.

The official backend uses VCS, Design Compiler and PrimeTime. A local Yosys/ABC/OpenSTA backend supports development when commercial tools are unavailable. Its full-data gate simulation uses Verilator, with an additional Icarus four-state reset/corner subset; the commercial backend uses VCS four-state simulation throughout. These flows have separate area references. Commercial gate simulation checks three time-zero register starts (all zero, all one, and seed 20261121) to avoid reconvergent-reset X-pessimism. Each complete transaction trace must match ordinary four-state RTL; no signals are forced or repaired during reset or execution. Runtime Fatal messages are checked even when an old simulator returns exit code zero.

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

Every design that passes the selected profile's hardware requirements has `resolved=true`, including feasible zero-score designs. Default `area` scoring normalizes mapped area between the smallest validated accurate baseline and 50% of that area. Optional `architecture` scoring uses 60% area, 30% certified sustained throughput and 10% first-output latency. It adds declared-II continuous RTL/mapped qualification and a fixed-netlist PrimeTime clock scan; fixed-clock slack is never substituted for Fmax. The profiles have independent frozen targets and calibrations. SQNR is a hard constraint, without an extra precision reward. See `SCORING.md` and `profiles/policy.json`. Documentation length and the number of attempts do not earn points.

Precision reduction is an available optimization, not a required operation. An exact architectural optimization that meets the same area and service target is also a valid solution.

The anchor is the operator's accurate implementation with the best measured throughput/area, using the same library, backend and constraints. It is separate from the float64 numerical oracle. The commercial anchor must be calibrated on the target platform before official agent trials; the runner does this automatically.

## Scope

This is the serial-interface profile: 64 input cycles per frame with a 384-cycle service interval. It tests architecture selection and STA-supported throughput/area under that verified II; it does not claim to test the intrinsic maximum-throughput MDC capacity. A future 64-cycle or parallel-input workload would need separate calibration and ranking.

The current PPA objective is **pre-layout mapped area and ideal-interconnect STA**. No post-route or power result is implied. Finite numerical tests and mapped simulation are empirical checks; optional RTL-to-netlist formal checking is a separate verification step.
