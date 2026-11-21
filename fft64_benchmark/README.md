# FFT64-Quant: Public Task Package

**Purpose.** Design and improve a complete, synthesizable 64-point fixed-point complex FFT. This is an **open-design** task: the package provides a contract, interface declaration, architecture guidance, and test tools, but **no working FFT RTL**.

## Documents

- [TASK_EN.md](TASK_EN.md) / [TASK_ZH.md](TASK_ZH.md): the agent-facing task in English / Chinese
- [SPEC.json](SPEC.json): machine-readable functional and measurement contract
- [INTERFACE.md](INTERFACE.md): cycle-accurate RTL interface and reset semantics
- [ARCHITECTURE_GUIDE.md](ARCHITECTURE_GUIDE.md): design alternatives, not a solution
- [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md) / [DESIGN_PLAN_TEMPLATE.md](DESIGN_PLAN_TEMPLATE.md): evidence-based design loop
- [SCORING.md](SCORING.md) / [EVALUATION.md](EVALUATION.md): feasibility, score, and verification stages

## SSH container deployment

With sibling `Synopsys/` and `port.txt`, run `bash check_env.sh` from the repository root. Use `bash run_synopsys_debug.sh submission --quick --out runs/quick` for public debugging in the container, or `bash synopsys.sh exec -- <command>` to call its tools directly. The host needs only Python and SSH. See [REMOTE_SYNOPSYS.md](../REMOTE_SYNOPSYS.md).

## Tools installed in the current environment

```bash
bash fft64_benchmark/setup.sh --check-only
bash fft64_benchmark/run_preview.sh submission runs/quick --quick --no-build
bash fft64_benchmark/run_preview.sh submission runs/full --no-build
```

The `--quick` mode performs public numerical and mandatory sustained-protocol checks; the full mode additionally performs mapping, STA, mapped simulation, and the architecture-profile II/frequency measurements. **Quick PASS is not full hardware feasibility.** The full architecture search may be costly: it tests every integer frame interval from 64 to 384 using 1,024 consecutive frames per interval before representative mapped confirmation.

The evaluation selects available commercial tools first (VCS/DC/PrimeTime). Otherwise it uses installed open-source tools (Icarus/Verilator, Yosys/ABC, OpenSTA). The latter is a **pre-layout mapping and STA fallback**, not a post-route OpenROAD result. Do not compare raw results or calibrated scores across backend identities.

## Passing, scoring, and submission

Feasibility requires valid FFT behavior, per-frame SQNR ≥ 50 dB, protocol and reset correctness, 10 ns timing, and mapped-netlist consistency. The default `architecture` score combines area (60%), verified throughput (30%), and worst first-output latency (10%). A feasible design can receive zero score. Hidden calibration and input seeds are not part of this repository.

Submit `rtl/`, `DESIGN_PLAN.md`, and `measurements.csv`; `design_config.json` is optional. Its `frame_ii_cycles` is a scheduling hint only, not the official throughput measurement.

## NumPy and EDA dependencies

The default runtime reuses the selected Python interpreter's NumPy. If absent, setup installs the binary-only pinned version from the configured pip source or external offline wheel cache. `--no-build` prevents building missing EDA tools; it does not guarantee that a missing NumPy wheel can be installed offline. Verify the environment before the timed agent run. Use [requirements.txt](requirements.txt) for the pinned NumPy version.
