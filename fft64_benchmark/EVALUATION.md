# Evaluation Protocol: FFT64-Quant

The benchmark distinguishes **functional feasibility** from **hardware quality**. The public pipeline supports iterative design; hidden evaluation uses independent inputs and an operator-frozen configuration. The numerical metric is evaluated on the **complete 64-point frame**, not individual butterflies.

## Validation stages

| Stage | Inputs | What it establishes |
|---|---|---|
| Public numerical | ≥1,024 random nonzero frames plus directed cases | Minimum per-frame SQNR ≥50 dB; zero input gives zero output |
| Mandatory service | ≥1,024 consecutive frames, II=384, plus reset and gap cases | No lost/extra frames; max first-output ≤300 and completion ≤364 cycles |
| Hardware mapping/STA | Complete top RTL | Full standard-cell area; 10 ns setup/hold requirements |
| Mapped comparison | Representative numeric and protocol subset | Same output/control cycles and values as candidate RTL |
| II capacity | All integer intervals 64–384, ≥1,024 RTL frames each | Smallest observed passing II; selected II receives 128-frame mapped confirmation |
| Frequency certification | Reconstraint on a fixed mapped netlist | Setup/hold-passing period certificate, ≤0.01 ns bracket |
| Hidden numerical | ≥8,192 independently generated nonzero frames plus directed cases | Final SQNR feasibility on independent data |

The **minimum SQNR** over scored nonzero frames determines numerical feasibility; the **maximum observed per-frame first-output and completion delays** determine latency feasibility. Optional II intervals may fail without invalidating mandatory 384-cycle operation. The first-output latency score uses a common 10 ns clock; effective throughput uses the certified clock period.

## Running the public evaluator

From the repository root:

```bash
bash fft64_benchmark/setup.sh --check-only
bash fft64_benchmark/run_preview.sh submission runs/quick --quick --no-build
bash fft64_benchmark/run_preview.sh submission runs/full --no-build
```

Use `--backend commercial` or `--backend local` to select a backend explicitly. Automatic preparation prefers installed Synopsys tools with ready libraries, and otherwise selects installed open-source tools. A subsequent license or tool failure is unscored; it does not switch the backend during a run. Open-source fallback is **Yosys/ABC mapping plus OpenSTA timing and open-source simulation**; it is not a complete place-and-route OpenROAD implementation. Missing licenses, tools, or calibration make a run unscored; consult the run's `status` and `reason`.

The complete architecture-profile II sweep is expensive; a quick PASS should not be described as a full PPA PASS. Reusing previous results is valid only when the RTL source, inputs, random seeds, backend/tool versions, libraries, and flow settings match. Hidden data and the private calibration must remain outside the agent workspace.

## Interpretation

Measurements are **finite-sample** and ASIC QoR is **pre-layout**. The tests are not a formal worst-case error proof, formal sequential equivalence proof, post-route frequency measurement, or power measurement. Different backends require independently frozen accurate baseline references; do not mix their raw QoR or scores.

## Checkpoints and outcomes

Caches bind the submitted RTL, exact input frames, seed, simulator/tool binaries, libraries, evaluator and flow scripts, and policy. Mapped qualification additionally binds its mapped source and initialization settings. Identity conflicts preserve the existing measurement and require a new output directory; incomplete or corrupt records cannot produce PASS.

A demonstrated design failure is `DESIGN_INVALID`. Failed tools, timeouts or missing/malformed measurement data are `UNSCORED_INFRASTRUCTURE` and have `score_valid=false`. Quick and unfinished runs are `INCOMPLETE`. Check submission-document completeness separately from the hardware score.
