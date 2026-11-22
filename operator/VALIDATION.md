# Operator Validation Checklist

From the private repository root, run:

```bash
python3 -m unittest discover -s operator/tests -q
bash run_evaluation.sh --check-only
```

The first command executes **source-level regression fixtures**; the second checks the available evaluation environment. Neither alone proves complete commercial ASIC behavior. Before a ranked campaign, perform at least one full end-to-end evaluation with real tools, the selected backend, the calibrated reference and a known-correct FFT submission. Preserve complete raw logs and confirm that mapped verification, 321 II observations and frequency certification actually finish.

Verify the following independently:

1. Fixed task specification, hidden seed/protocol and scoring policy match the calibration.
2. RTL, mapped netlist and any implementation manifest have matching content identities.
3. Imported mapped netlist uses only approved cells and the trusted library/SDC; submitted recipes are **not** executed privately.
4. Numerical feasibility uses the minimum SQNR over nonzero frames and exact-zero checking; mandatory protocol and latency use long multi-frame streams.
5. Throughput is derived from the smallest passing tested II and selected mapped confirmation; frequency uses a setup/hold-passing period on that same netlist.
6. Design violations (`DESIGN_INVALID`) are distinguished from tool/license/timeouts (`UNSCORED_INFRASTRUCTURE`), and the latter are excluded from ranking.
7. Peak memory, disk usage and runtime for the complete 321-interval capacity test are acceptable in the actual container.

Result directories use source/tool/library/seed/policy identities; changed inputs require new directories and corrupt caches cannot count as valid measurements. Source-only archives and regression fixtures do not replace original PPA reports. See [VALIDATION.md](../VALIDATION.md).
