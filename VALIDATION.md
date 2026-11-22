# Validation and Measurement Evidence

## Regression coverage

From the repository root, run:

```bash
python3 -m unittest discover -s operator/tests -q
```

The suite covers scoring, input-domain and protocol checks, cache identity and partial checkpoints, simulator drivers, tool entrypoints, and infrastructure outcomes. It also checks custom implementation manifests, independent import without running candidate recipes, source/netlist-specific caches, private source snapshots, and scalar STA alias compatibility. Tests use clearly identified synthetic traces or tool fixtures where licensed hardware measurement is unnecessary. They do not establish ASIC performance.

## Hardware evidence

The private `Codex-GPT-6.1-Sol-Max` branch contains `submission/` and `evaluation/`. Its evaluation records include the executed source snapshot, per-frame quality and latency, interval sweeps, calibration, mapped results and setup/hold reports. The measurement source and policy hashes identify the executed implementation. A source-only export of `main` does not include these separate result files.

The measurement dataset uses 8,192 random nonzero frames plus 192 directed frames per design. The capacity sweep contains 321 integer intervals from 64 through 384, with 1,024 continuous RTL frames at every interval. Mapped checks cover representative numerical/protocol subsets and three binary initial-state modes. These are finite-sample measurements and pre-layout synthesis / ideal-interconnect STA.

## Interpreting outcomes

- `FEASIBLE`: all selected-profile hardware requirements pass. A score of zero is allowed.
- `DESIGN_INVALID`: an observed numerical, protocol, RTL or timing violation; a valid zero-score result.
- `UNSCORED_INFRASTRUCTURE`: unavailable or failed tools, timeout, malformed measurement, or mismatched calibration; exclude from ranking and retry after diagnosis.
- `INCOMPLETE`: quick checks or unfinished measurement; no final score.

`score_valid` determines whether a numeric score may enter ranking. Commercial and open-source backends require separate matching calibrations. All ASIC timing and area are pre-layout; no P&R, power, silicon-frequency or formal worst-case numerical claim is made.
