# EDA Agent Task: FFT64 Architecture and Precision Co-Design

## 1. Goal

Design a **complete synthesizable 64-point complex FFT processor** that satisfies the functional and hardware contract and improves area, sustained throughput, and first-output latency. The task is open-design: no completed FFT RTL is provided. The evaluation rewards measured circuit quality, not the number of candidate designs or the length of a design report.

An FFT circuit includes more than butterfly arithmetic: all buffers, register state, routing, control, twiddle-factor storage, and output reordering are part of the hardware cost. You may compare architectures and change the design strategy as measurements become available; no globally optimal solution is required.

## 2. Mandatory functional contract

- **Transform:** 64-point, forward, unscaled complex FFT, natural-order input and natural-frequency-order output.
- **Input:** one complex sample per valid clock edge for 64 consecutive edges; each real/imaginary component is signed 16-bit with 15 fractional bits, within [-0.5, 0.5]. Tested nonzero frames have complex RMS ≥ 1/32.
- **Output:** 64 consecutive valid frequency bins; each component is signed 24-bit with 15 fractional bits. The first output has `out_start=1`.
- **Clock:** one synchronous rising-edge `clk`; mandatory 10 ns timing constraint, no extra clock.
- **Service rate:** accept frames starting every 384 clock cycles, and legal larger gaps, without backpressure.
- **Latency:** first valid output no later than cycle 300 and last valid output no later than cycle 364, measured from the first input edge (cycle 0). The first output cannot precede the last required input.
- **Reset:** synchronous active-high reset aborts incomplete frames. Later frames must be processed correctly.

The 384-cycle interval is the **mandatory workload**, not a limit on the maximum capability of SDF/MDC architectures. A design may earn higher throughput credit by successfully handling shorter frame intervals.

## 3. Numerical accuracy

The numerical reference is a float64 FFT of the **same quantized input**, not the signal before input quantization. For each nonzero 64-point frame:

\[
\mathrm{SQNR}_f = 10\log_{10}\frac{\sum_{k=0}^{63}|X_f[k]|^2}{\sum_{k=0}^{63}|\hat{X}_f[k]-X_f[k]|^2}.
\]

**Every nonzero test frame must achieve SQNR ≥ 50 dB.** A zero input frame must yield exactly zero output. Gain, phase, frequency permutation, and output scaling cannot be fitted after simulation to improve the score. Public and hidden finite-sample tests are not a formal guarantee over the entire input domain.

## 4. Allowed design decisions

**Allowed:** R2SDF, R2²SDF, R4MDC, folded/iterative FFT, and other valid architectures; stage-dependent data/twiddle precision; explicit truncation or rounding (including round-to-nearest-even); guard bits and quantization boundaries; exact resource sharing, twiddle specialization, memory banking, and legal retiming/pipelining.

**Not allowed:** approximate logic synthesis (ALS), arbitrary approximate gate pruning/replacement, approximate compressors unrelated to explicit quantization, simulation-only/lookup implementations, or modifications to the external FFT function, I/O ordering, numerical domain, or service contract.

All area calculations include the **complete top-level mapped implementation**, including standard-cell memories, controls, registers, multiplexers, and output reordering. There is no free SRAM.

## 5. Recommended workflow

When sibling `Synopsys/` and `port.txt` are present, use the provided SSH transport instead of installing EDA tools on the host. From the repository root, run `bash check_env.sh`, then `bash run_synopsys_debug.sh submission --quick --out runs/quick`. Use `--profile area` for mapping/STA feedback and `--profile architecture` for the full throughput/frequency profile. `bash synopsys.sh exec -- <command>` calls tools directly in the container. See the repository's `REMOTE_SYNOPSYS.md`.

For tools installed directly in the current environment, run from the **repository root**:

```bash
bash fft64_benchmark/setup.sh --check-only
bash fft64_benchmark/run_preview.sh submission runs/quick --quick --no-build
bash fft64_benchmark/run_preview.sh submission runs/full --no-build
```

1. Read `fft64_benchmark/SPEC.json`, `fft64_benchmark/INTERFACE.md`, and `fft64_benchmark/ARCHITECTURE_GUIDE.md`.
2. Create `submission/DESIGN_PLAN.md`: compare at least two architecture ideas and state measurable hypotheses.
3. Build an initially correct, sufficiently precise design before changing numerical precision.
4. Measure complete-design numerical quality and ASIC results; compare alternatives using the same backend.
5. After each meaningful experiment, update the plan with the measured outcome, decision, and next test; record data in `measurements.csv`.
6. Submit your best feasible RTL and its concise design record.

The evaluator may use installed Synopsys tools, otherwise installed open-source simulation/mapping/STA tools. A preview run without matching frozen calibration can report useful measurements but **not an official score**. Do not rebuild the EDA toolchain unless necessary and permitted.

## 6. Evaluation and score

**Feasibility (`resolved`) is separate from optimization quality (`score`).** There is no minimum area reduction or minimum score to pass. Mandatory numerical, protocol, reset, timing, and mapped-netlist checks must all succeed.

The default `architecture` score combines mapped area **60%**, measured sustainable throughput **30%**, and maximum observed first-output latency **10%**. SQNR is a hard constraint; higher SQNR is not rewarded. Official throughput is based on the **smallest verified integer frame interval** in 64–384, not a claim in `design_config.json`. Each interval is exercised by at least 1,024 consecutive frames; the winning interval receives additional mapped-netlist confirmation. Optional faster intervals may fail without invalidating the mandatory 384-cycle service.

Numerical test sizes: ≥1,024 public nonzero random frames and ≥8,192 hidden nonzero random frames, each supplemented by directed cases. Worst-frame SQNR and worst observed per-frame latency determine feasibility. See [SCORING.md](SCORING.md) and [EVALUATION.md](EVALUATION.md).

## 7. Deliverables

- `submission/rtl/`: self-contained synthesizable modules, top `fft64_top`
- `submission/DESIGN_PLAN.md`: updated hypotheses and design choices
- `submission/measurements.csv`: reproducible candidate measurements
- `submission/design_config.json` (optional): source files and scheduling hint

The evaluator remeasures circuit quality; self-reported numbers do not determine the grade. No hidden feedback is provided for changing the final submission.
