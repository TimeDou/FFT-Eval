# FFT64-Quant: Operator Tools

The `operator/` directory is **private**. It includes two accurate fixed-point FFT baseline implementations (R2SDF and folded radix-2), calibration utilities and regression tests. Publish the numerical score scales and functions. Keep baseline RTL, hidden seeds, private validation calibration and other Agent results inaccessible to evaluated Agents.

## Main commands

```bash
# Synthetic regression tests
python3 -m unittest discover -s operator/tests -q

# Evaluate on the selected backend
bash run_evaluation.sh /absolute/path/to/submission \
  --backend auto --profile architecture --out /absolute/path/to/evaluation

# Force the commercial backend
bash run_synopsys.sh /absolute/path/to/submission \
  --backend commercial --profile architecture --out /absolute/path/to/evaluation_synopsys
```

The default `architecture` profile combines complete mapped area, verified throughput and maximum first-output latency. The optional `area` profile needs separate calibration and must not be mixed into architecture rankings. See [SCORING_PROFILES.md](SCORING_PROFILES.md).

## Independent verification and calibration

Calibrate both accurate baselines using the same backend, libraries, fixed timing constraints, measurement protocol and default synthesis recipe. Candidate implementations may be generated with their own publicly executed synthesis recipes; **private evaluation imports their mapped netlists, rather than running the recipes**. Each candidate must pass mapped-cell legality, fixed-constraint STA, and representative RTL/netlist comparison before hardware results are accepted.

An Agent-supplied manifest provides internal consistency checks but is not trusted evidence of an executed EDA recipe. If recipe-to-netlist provenance is an experimental requirement, capture independent build logs and source hashes in a controlled build environment. Numerical evaluation always uses the same-input float64 reference, not one of the fixed-point baseline outputs.

Use the [validation report](../VALIDATION.md) to distinguish code regression results from complete ASIC experiments. Tool failures and absent calibration are unscored and must be excluded from rankings.
