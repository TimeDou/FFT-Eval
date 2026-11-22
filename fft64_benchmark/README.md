# FFT64-Quant: Public Benchmark Package

This package defines an **open-design** EDA Agent task: design and optimize a complete, synthesizable 64-point fixed-point complex FFT. It provides specifications, RTL ports, testing infrastructure and design guidance, but **no completed FFT implementation**.

## Read first

| Document | Purpose |
|---|---|
| [TASK_EN.md](TASK_EN.md) / [TASK_ZH.md](TASK_ZH.md) | Agent-facing task in English / Chinese |
| [SPEC.json](SPEC.json) | Machine-readable FFT, numerical and I/O contract |
| [INTERFACE.md](INTERFACE.md) | Cycle-accurate streaming and reset requirements |
| [ARCHITECTURE_GUIDE.md](ARCHITECTURE_GUIDE.md) | FFT architecture and precision options |
| [SCORING.md](SCORING.md) / [EVALUATION.md](EVALUATION.md) | Feasibility, quality scores and verification workload |
| [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md) / [DESIGN_PLAN_TEMPLATE.md](DESIGN_PLAN_TEMPLATE.md) | Evidence-driven iterative design record |
| [OPTIMIZATION.md](../OPTIMIZATION.md) | Editable DC/Yosys/ABC flow and netlist export |
| [Technical report](../docs/FFT64-Quant.pdf) / [report source](../docs/FFT64-Quant.md) | Architecture, precision, synthesis-flow and measurement methodology |

## Development entrypoints

From the **FFT-Bench repository root**, with locally installed tools:

```bash
bash fft64_benchmark/setup.sh --check-only
bash fft64_benchmark/run_preview.sh submission runs/quick --quick --no-build
bash fft64_benchmark/run_preview.sh submission runs/full --no-build
```

With sibling `Synopsys/` and `port.txt`, commercial tools can instead be called in the running SSH container:

```bash
bash check_env.sh
bash run_synopsys_debug.sh submission --quick --out runs/quick
bash run_synopsys_debug.sh submission --profile architecture --out runs/full
```

Details appear in [REMOTE_SYNOPSYS.md](../REMOTE_SYNOPSYS.md). The full architecture evaluation probes all integer frame intervals from 64 to 384 and may be resource-intensive. A quick PASS checks public numerical/protocol behavior, **not** full ASIC feasibility.

## Custom synthesis

Initialize editable templates with:

```bash
bash build_implementation.sh submission --init-flow
```

Agents can explore synthesis recipes and export a flattened ASAP7 netlist as `submission/implementation/mapped.v` with a matching manifest. The evaluator imports and independently measures this circuit under fixed library, timing and verification requirements; it does **not** execute submitted Tcl/Yosys/ABC scripts in hidden grading. Without a complete custom export, the default mapping applies only when no custom recipe is submitted. Current scores are based on **pre-layout** standard-cell area and ideal-interconnect STA, not complete P&R.

## Feasibility and scoring

`resolved=true` means that every mandatory FFT, SQNR, reset, protocol, 384-cycle service, timing and representative RTL/mapped check passes. The default `architecture` score combines complete area (60%), measured sustainable throughput (30%) and maximum observed first-output latency (10%). Feasibility has no minimum score threshold; SQNR above 50 dB gives no extra reward. All functions and numerical scales are public in SCORING.md and profiles/policy.json. Complete public evaluation returns component and combined preview scores directly. The area profile is a separate diagnostic.

Submit `rtl/`, `DESIGN_PLAN.md` and `measurements.csv`, with an optional `design_config.json`. If using custom synthesis, also keep `flow/` and `implementation/`. The public repository contains neither hidden data nor private calibration. Backend identity, tool/library version and scoring profile must be frozen for comparable measurements.
