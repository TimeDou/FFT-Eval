# FFT64 Operator Reference and Evaluation Tools

This directory is private. It contains **two accurate fixed-point FFT baseline implementations**, calibration utilities, and regression tests. These are for reference calibration only; **neither baseline nor the operator's prior optimized designs should be included in the agent's initial workspace**.

## Execution

From the private repository root:

```bash
# Unit/control regressions (synthetic fixtures, not actual commercial PPA)
python3 -m unittest discover -s operator/tests -v

# Full evaluation using a selected backend
bash run_evaluation.sh /absolute/path/to/submission \
  --backend auto --profile architecture --out /absolute/path/to/evaluation

# Force commercial Synopsys where available
bash run_synopsys.sh /absolute/path/to/submission \
  --backend commercial --profile architecture --out /absolute/path/to/evaluation
```

The `architecture` profile is the **default**. The optional `area` profile is an independent diagnostic; its numeric score and calibration must not be mixed with architecture results. See [SCORING_PROFILES.md](SCORING_PROFILES.md) and [../fft64_benchmark/SCORING.md](../fft64_benchmark/SCORING.md).

Calibration measures accurate SDF and folded radix-2 designs using the same standard-cell library, protocol, timing constraints, tools, and profile as candidate designs. Separate backends require separate normalization anchors. The float64 FFT of the **same quantized input** is the numerical oracle; an accurate fixed-point baseline is not numerically exact relative to float64.

## Evidence and limits

Regression tests exercise scoring, cache/protocol logic, simulation drivers, and operator entrypoints using clearly identified fixtures. Real hardware evidence and its scope are described in [VALIDATION.md](../VALIDATION.md). A source-only main export and an agent's measurement bundle are separate review inputs.
