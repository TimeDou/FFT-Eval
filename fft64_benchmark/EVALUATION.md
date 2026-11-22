# FFT64-Quant: Verification and Measurement Protocol

The benchmark evaluates a **complete 64-point FFT**, not an isolated butterfly. Functional feasibility and hardware quality are measured separately. Public evaluations support iterative design; final hidden evaluation uses independent data and frozen operator settings.

## 1. Validation stages

| Stage | Test scope | Decision or measurement |
|---|---|---|
| Numerical RTL | 1,024 public or 8,192 hidden random nonzero frames, plus directed inputs | Minimum per-frame SQNR ≥50 dB; zero input produces exact zero |
| Mandatory service | At least 1,024 consecutive frames at II=384; reset and variable-gap cases | No lost/extra frames; per-frame first output ≤300 and last output ≤364 cycles |
| Hardware implementation | Default synthesis or imported structural ASAP7 netlist | Complete mapped area; setup/hold at 10 ns |
| RTL/mapped comparison | Representative numerical, protocol and reset cases | Same output data, valid/start signals and clock cycles |
| Throughput search | All 321 integer intervals, II=64–384; at least 1,024 RTL frames each | Shortest passing II, followed by a mapped confirmation subset of 128 frames plus gap/reset probes |
| STA period certification | Reconstraint of one fixed mapped netlist | Setup/hold-passing endpoint with ≤0.01 ns bracket, unless the configured scan floor is reached |

For numerical feasibility, use the **minimum SQNR over nonzero tested frames**, not the average. For latency, use the **maximum observed first-output and completion delays across frames**, not the first transaction. The throughput metric uses the smallest empirically verified II, not an Agent-declared value. Failure at an optional shorter II does not invalidate mandatory 384-cycle operation.

## 2. Public evaluation

From the repository root:

```bash
bash fft64_benchmark/setup.sh --check-only
bash fft64_benchmark/run_preview.sh submission runs/quick --quick --no-build
bash fft64_benchmark/run_preview.sh submission runs/full --no-build
```

Use `--backend commercial` or `--backend local` to select explicitly. Automatic preparation prefers available commercial tools; otherwise the open-source fallback uses Icarus/Verilator, Yosys/ABC, and OpenSTA. This is **pre-layout** mapping and timing, not complete OpenROAD place-and-route. The selected backend is fixed during a run; tool or license failures do not trigger an undocumented switch. Complete public evaluations return valid component and combined preview scores using the published numeric scales, without private calibration. Final hidden grading also requires matching private platform/protocol validation.

The full architecture profile performs a long-stream test at every integer II. It batches at most eight intervals at a time and preallocates regular input schedules; all 321 intervals and 1,024 frames per interval are retained. Each completed chunk records array sizes, runtime and Python-process peak RSS; EDA subprocess memory requires separate measurement. Use quick numerical/protocol tests to reject unsuitable candidates before running ASIC and capacity evaluation. A quick PASS is **not** full hardware feasibility.

## 3. Agent-controlled synthesis

To create editable optimization scripts:

```bash
bash build_implementation.sh submission --init-flow
```

After editing `submission/flow/`, build and export `submission/implementation/mapped.v` and its manifest using [OPTIMIZATION.md](../OPTIMIZATION.md). An exported mapped netlist is imported for independent measurement. The evaluator does not run submitted Tcl, Yosys or ABC scripts in private scoring; it checks mapped-cell legality, source/manifest consistency, timing, and representative RTL/netlist behavior. With no custom export, the frozen default mapping is used. If custom recipes exist without a complete export, full evaluation requires the Agent to build first; quick checks remain RTL-only.

## 4. What the evidence supports

Long-stream capacity is a measured result over **finite frames and the tested II range**; it is not proof of a globally minimal II. Large RTL datasets and smaller mapped-netlist subsets establish different coverage. The tool flow gives **pre-layout**, ideal-interconnect standard-cell area and STA estimates, not post-route frequency, power or silicon performance. Optional formal equivalence is reported separately.

Record the backend, tool and library identities, submitted RTL, imported netlist hash when present, selected profile, reference calibration, worst SQNR, maximum per-frame latency, verified II and certified period. Do not compare raw results or scores from different backends or profiles.

## 5. Caches and evaluation outcomes

Completed caches are tied to RTL, imported implementation, recipe manifest, input frames and seeds, simulator/tool versions, technology libraries, evaluation scripts and scoring policy. Changed inputs require a new output directory; corrupt or incomplete records must not become PASS results.

A proven hardware violation is `DESIGN_INVALID` and receives a valid zero score. License errors, tool failures, timeouts and missing or inconsistent measurements are `UNSCORED_INFRASTRUCTURE` (`score_valid=false`) and must be excluded from ranking. Partial/quick checks are `INCOMPLETE`. Submission-document completeness is recorded separately from hardware score.
