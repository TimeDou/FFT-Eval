# FFT64-Quant: EDA Agent Design Task

## Objective

Develop a complete, synthesizable **64-point fixed-point complex FFT processor** from the public specification. The task is open-design: no working FFT RTL is supplied. Your objective is to satisfy every mandatory specification and improve the measured hardware quality through architecture selection, precision allocation, RTL optimization and, optionally, synthesis-flow exploration. The evaluated circuit includes its storage, control, data reordering and input/output logic—not only butterfly arithmetic.

## Mandatory contract

- **Transform:** forward, unscaled, 64-point complex FFT; natural-order input and natural-frequency-order output.
- **Data:** 16-bit signed input components and 24-bit signed output components, each with 15 fractional bits. Tested input components lie in [-0.5, 0.5]; nonzero frames have complex RMS ≥1/32.
- **Input service:** one valid complex sample per cycle for 64 consecutive cycles. Frames starting at least 384 cycles apart must be accepted without backpressure.
- **Output:** 64 consecutive valid samples in natural frequency order; `out_start` marks the first output. The first output cannot precede the final required input and must occur by cycle 300, and the last by cycle 364, relative to the first input edge (cycle 0).
- **Reset and clock:** synchronous, active-high reset aborts incomplete work. Only the specified rising-edge clock is allowed; mapped timing must pass the 10 ns requirement.
- **Numerical quality:** every evaluated nonzero frame must achieve SQNR ≥50 dB against the float64 FFT of the **same already-quantized input**. A zero input must produce exactly zero output. No fitted gain, phase, scaling or frequency permutation is permitted.

Here X is the same-input float64 reference and X-hat is the hardware output. SQNR is computed per complete complex frame:
\[
\mathrm{SQNR}_f=10\log_{10}\frac{\sum_{k=0}^{63}|X_f[k]|^2}{\sum_{k=0}^{63}|\hat X_f[k]-X_f[k]|^2}.
\]

The 384-cycle frame interval is the **mandatory minimum service capability**, not a limit on the throughput an architecture may achieve. Faster frame intervals are optional and contribute to the architecture score only when the evaluator verifies them. See [SPEC.json](SPEC.json) and [INTERFACE.md](INTERFACE.md) for the authoritative contract.

## Design freedom and restrictions

Choose a valid FFT architecture, including R2SDF, R2²SDF, R4MDC, folded/iterative designs or other implementations. You may change internal data/twiddle widths, rounding and truncation rules, guard bits, memory organization, pipeline scheduling, exact twiddle specialization and resource sharing. You may also explore synthesis effort, Boolean rewriting, optimization pass ordering and technology mapping.

To use a custom synthesis recipe, initialize `submission/flow/` with `bash build_implementation.sh submission --init-flow`, edit the provided DC or Yosys/ABC templates, and export `submission/implementation/mapped.v` together with `manifest.json`. The evaluator then **imports and measures the mapped standard-cell netlist**, checks it against the submitted RTL and enforces its own technology library, STA and numerical requirements. **Private scoring never executes submitted optimization scripts** or trusts self-reported PPA. For commands and build requirements, read [OPTIMIZATION.md](../OPTIMIZATION.md).

Approximate gate pruning, arbitrary approximate Boolean transformations, unrelated approximate compressors, simulation-only lookup implementations and modifications to the external FFT/streaming contract are forbidden. Explicit fixed-point quantization is permitted, but SQNR must remain feasible. Uncounted external SRAM or logic is not allowed. Optional P&R recipes are for development and do not affect the current pre-layout score.

## Recommended execution

1. Read [SPEC.json](SPEC.json), [INTERFACE.md](INTERFACE.md), [ARCHITECTURE_GUIDE.md](ARCHITECTURE_GUIDE.md), [SCORING.md](SCORING.md) and [EVALUATION.md](EVALUATION.md).
2. Create `submission/DESIGN_PLAN.md` with at least two architecture hypotheses and measurable expected trade-offs.
3. Implement a correct baseline in `submission/rtl/` and run public numerical/protocol checks.
4. Explore promising RTL, quantization and synthesis-recipe changes; measure complete mapped area and timing on the same backend.
5. Use long multi-frame capacity tests for promising candidates. Record measured results, failures and revised design decisions in `measurements.csv`.
6. Submit the best **verified** implementation, including a rebuilt mapped export if custom synthesis was used.

With a sibling `Synopsys/` mount and `port.txt`, run from the **FFT-Bench repository root**:

```bash
bash check_env.sh
bash run_synopsys_debug.sh submission --quick --out runs/quick
bash run_synopsys_debug.sh submission --profile area --out runs/area
bash run_synopsys_debug.sh submission --profile architecture --out runs/full
```

You may invoke the container's tools directly using `bash synopsys.sh exec -- <command>`. See [REMOTE_SYNOPSYS.md](../REMOTE_SYNOPSYS.md). If tools are installed locally, use `fft64_benchmark/run_preview.sh`. Use separate run directories for different RTL or recipes; a quick PASS is not full ASIC feasibility.

## Evaluation and deliverables

`resolved=true` requires numerical correctness, streaming/reset behavior, mandatory II=384 service, first/completion latency, mapped-netlist checks and 10 ns setup/hold timing. There is **no minimum area-reduction threshold**. The default `architecture` score combines complete mapped area (60%), verified sustainable throughput (30%) and maximum observed first-output latency (10%). SQNR above 50 dB does not earn a bonus. Numerical feasibility uses the minimum frame-level SQNR, latency uses the maximum observed per-frame value, and throughput uses the smallest **tested and verified** integer II in 64–384—not a value declared by the Agent.

The public evaluation uses at least 1,024 random nonzero frames; private hidden evaluation uses at least 8,192, both supplemented by directed inputs. Each candidate II is tested with at least 1,024 consecutive RTL frames, followed by representative mapped confirmation at the selected shortest passing II. These are empirical checks, not formal guarantees. Scores require a matching frozen calibration and cannot be compared across backends or scoring profiles.

Submit:

- `submission/rtl/`: self-contained synthesizable RTL with top module `fft64_top`;
- `submission/DESIGN_PLAN.md`: short hypothesis/experiment/decision record;
- `submission/measurements.csv`: actual measurements of significant candidates;
- `submission/design_config.json` (optional): RTL source list and non-authoritative II hint;
- `submission/flow/` and `submission/implementation/` when using custom synthesis: optimization recipe, complete mapped netlist and manifest.

The grader determines results independently. Do not alter the specification, scoring scripts, hidden data or calibration; do not fabricate measurements or change the submission after private feedback.
