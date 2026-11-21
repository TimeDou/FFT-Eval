# Operator Validation

Run the regression suite from the repository root:

```bash
python3 -m unittest discover -s operator/tests -q
```

Check the intended backend before an evaluation:

```bash
bash run_evaluation.sh --check-only
```

Regression fixtures validate workflow behavior and scoring formulas. A licensed hardware evaluation additionally requires RTL simulation, complete mapping, setup/hold STA, representative mapped comparison, long continuous-frame measurements and frequency certification. Keep the raw reports with source, input, tool, library and policy hashes. Measurement evidence is described in [VALIDATION.md](../VALIDATION.md).

Throughput caches authenticate the RTL, input frames, seed, backend, tool binaries, evaluator scripts and policy. Mapped qualification also authenticates the mapped netlist and initial-state modes. Corrupt or incomplete records are not accepted as completed measurements. A conflicting output-directory identity requires a separate directory and preserves the existing results.

Tool failures and missing measurements are unscored. Explicit design violations remain valid zero-score observations. Submission-document completeness is reported separately and does not alter the hardware score.
