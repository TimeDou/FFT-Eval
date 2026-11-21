# EDA Agent Challenge: Design an Area- and Performance-Efficient, Quantized 64-Point FFT

## Background

A fast Fourier transform (FFT) computes the frequency-domain representation of complex-valued input samples. A hardware FFT must balance arithmetic units, data storage, data reordering, throughput, latency, and numerical accuracy. Different hardware organizations (such as single-path delay feedback, multi-path delay commutator, or iterative/folded FFT) make different area/performance trade-offs. Precision reduction at selected computation stages or twiddle factors can save hardware, but errors accumulate at the final outputs.

**Your task is to design and optimize a complete working FFT operator, not merely a butterfly or arithmetic submodule.** You may compare architectures, select an implementation, and adjust its quantization policy. You are not required to prove that your result is globally optimal.

## Functional requirement

- Compute a **forward, unscaled, complex 64-point FFT**:
  `X[k] = sum_{n=0}^{63} x[n] exp(-j*2*pi*n*k/64)` for `k=0..63`.
- Accept 64 inputs per frame in natural order and produce 64 outputs in **natural frequency order**, including any required reordering hardware.
- Input format: two signed 16-bit integers per complex sample, representing `real_int/2^15` and `imag_int/2^15`.
- Each input real/imag component lies in `[-0.5, 0.5]` (inclusive). Every nonzero evaluated frame has complex RMS at least `1/32`.
- Output format: two signed 24-bit integers per complex sample, representing `real_int/2^15` and `imag_int/2^15`. Output gain, phase, and frequency order must not be fitted to improve a score.

## Numerical quality

The reference FFT is evaluated in float64 using the **same already-quantized input samples**. For each evaluated nonzero frame, calculate

`SQNR(dB) = 10*log10( sum_k |X_ref[k]|^2 / sum_k |X_hw[k]-X_ref[k]|^2 )`.

Every nonzero test frame must achieve **SQNR >= 50 dB** (equivalently frame NMSE <= 1e-5). An all-zero input frame must produce exactly zero outputs. This metric measures **implementation-induced error**, not the earlier input ADC quantization error. Finite development and hidden test sets do not constitute a formal guarantee for all possible inputs.

## Hardware service contract — common workload

- Single synchronous clock, period **10 ns**.
- One complex input on each of 64 consecutive valid cycles per frame; a `frame_start` pulse marks its first sample.
- The testbench may start consecutive frames as often as **every 384 cycles**. Larger idle gaps are also legal.
- Emit 64 **consecutive** valid complex outputs, with one `out_start` pulse, in natural order.
- Relative to the first input edge: first valid output **no later than cycle 300**; final valid output **no later than cycle 364**. The first output must follow the last input required for that FFT.
- Synchronous reset may occur between or during frames. Any unfinished pre-reset frame is discarded; later valid frames must compute correctly.
- The complete design must meet the 10 ns timing constraint using the operator's fixed synthesis/STA setup.

**Important:** the 384-cycle input service period is a workload requirement, **not a claim that a pipeline SDF design cannot run faster**. All architectures are compared under this same interface and workload.

## Objective and allowable design methods

**Primary objective:** improve the throughput per mapped standard-cell area of the **complete FFT top module**, including combinational logic, pipeline/register state, twiddle storage, control, multiplexing, output reorder, and memories implemented in standard cells. There is no free SRAM or uncounted data path.

You may use:
- R2SDF, R2^2SDF, R4SDF, R2MDC, R4MDC, folded/iterative radix-2/radix-4, or another valid FFT architecture.
- Stage-dependent bit widths, truncation, round-to-nearest-even, coefficient precision, fixed-point scaling/guard bits and quantization-boundary placement.
- Exact arithmetic and architectural optimizations, such as constant-twiddle specialization, memory banking, resource sharing, legal retiming and pipeline organization.

You may **not** use gate-level approximate logic synthesis (ALS), approximate gate replacement/pruning, approximate compressor logic, or deliberate Boolean functional corruption unrelated to an explicit precision/quantization operation. Do not change the mathematical FFT gain, output order, clock, input range or SQNR threshold. Any algorithmic/resource optimization that preserves the declared fixed-point arithmetic is allowed.

## Recommended workflow

Use the installed platform environment first: run `bash setup.sh --check-only`. The default evaluator loads the EDA profile, prefers existing VCS/DC/PrimeTime, then reuses installed open-source tools, and only finally attempts builds of missing components. Do not begin by reinstalling Yosys or Icarus. Use `--no-build` to disable automatic tool compilation.

1. Read `SPEC.json`, `ARCHITECTURE_GUIDE.md`, and `INTERFACE.md`.
2. Create your own `DESIGN_PLAN.md` using `DESIGN_PLAN_TEMPLATE.md`, including at least two plausible architecture candidates and the first measurements you intend to make.
3. Implement or modify RTL. Establish one accurate (high-precision) baseline before aggressive quantization.
4. Compare architectures under the *same* full-top PPA, numeric and protocol flow. Then explore stage-wise precision/rounding choices.
5. After each material candidate experiment, revise `DESIGN_PLAN.md` with the measurement, decision, and next hypothesis. Keep a compact `measurements.csv`.
6. Submit the fully validated RTL with the best continuous PPA score, its configuration and the updated plan. The evaluator, not your report, measures actual quality, timing and mapped area.

## Success and ranking

- A candidate is **feasible** only if numeric quality, output order, reset/protocol, service rate, latency and timing all pass.
- Every feasible design receives `resolved=true`; there is no minimum score or area-saving threshold.
- Let `A` be complete mapped area, `II` the verified input frame interval, and `T` the STA limiting period. A single accurate reference design supplies `A_ref, II_ref, T_ref`. Define `E=(A_ref/A)*(II_ref/II)*(T_ref/T)` and `score=E/(1+E)`. The reference scores 0.5; higher throughput/area efficiency scores higher.
- Frequency enters once through `throughput=64/(II*T)`. The common verified workload currently uses II=384; no faster untested intrinsic II is assumed. See `SCORING.md` for definitions and examples.
- Your source design and all required data must be self-contained and synthesizable. The operator supplies trusted scripts and technology data.
- A failed design earns no hardware-quality ranking; verbose verification reports do not earn additional area credit.

**Hand in:** `rtl/` + top module `fft64_top`, `DESIGN_PLAN.md`, `measurements.csv` and optionally `design_config.json`. Detailed log files are not required in the narrative.
