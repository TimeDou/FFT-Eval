# FFT64-Quant: Operator Scoring and Calibration

## Evaluation profiles

The default `architecture` profile uses mapped area (60%), verified effective throughput (30%) and maximum observed first-output latency (10%), subject to mandatory FFT, SQNR, reset, protocol, II=384, mapped-equivalence and timing checks. The `area` profile is an independent diagnostic and **must not** be combined numerically with architecture scores. The definitive configuration is `fft64_benchmark/profiles/policy.json`.

## Calibration

Before evaluating Agents, measure accurate R2SDF and folded radix-2 baselines using the same backend, default mapping recipe, library, constraints, protocol and policy. These measurements validate the platform and protocol; they do not change the public score scales. Area uses 500 um2 ideal and 4000 um2 half-credit anchors; throughput uses 260416.66666666666 to 62500000 FFT/s on a logarithmic scale; latency uses the 300-to-63-cycle interval. The componentwise ideal combination is demanding and need not represent one realizable circuit. Public previews use these exact scales without private calibration; official hidden grading binds the same scales to private validation metadata.

For each candidate,

\[
T_{\mathrm{eff}}=\frac{10^9}{II_{\mathrm{ver}}P_{\mathrm{STA}}}\quad\mathrm{FFTs/s},
\]

where \(II_{\mathrm{ver}}\) is the smallest passing integer interval in 64–384, established by at least 1,024 consecutive RTL frames per interval and a 128-frame representative mapped check at the selected interval. \(P_{\mathrm{STA}}\) is a setup/hold-passing period measured by a clock scan of the **same fixed mapped netlist**. The scan bracket is ≤0.01 ns unless the predefined lower scan bound is reached. The latency component uses the common **10 ns** clock, avoiding a second frequency reward. SQNR ≥50 dB is a hard constraint and receives no bonus.

## Candidate-controlled synthesis

Accurate reference designs use the frozen **default mapping recipe**. Agent candidates may optimize their own DC or Yosys/ABC recipe during public development and submit the resulting flattened ASAP7 mapped netlist. Private grading **never sources submitted Tcl/Yosys/ABC files**, trusts Agent PPA reports or resynthesizes that imported netlist. Instead, independently check legal standard-cell instances, aggregate cell area, 10 ns setup/hold timing, timing-frequency certification and mapped-to-RTL behavior. Candidate area gains due to a different legal synthesis strategy are intentionally counted.

A manifest containing source, netlist, recipe and library hashes supports *content consistency*, not independent proof of the build command that produced the netlist. Retain independently captured tool logs if recipe provenance must be demonstrated. Optional P&R exploration is outside the current scored pre-layout flow.

## Run commands

```bash
bash run_evaluation.sh /absolute/path/to/submission \
  --backend auto --profile architecture --out /absolute/path/to/eval_run

bash run_synopsys.sh /absolute/path/to/submission \
  --backend commercial --profile architecture --out /absolute/path/to/eval_commercial

python3 fft64_benchmark/grading/make_grader.py \
  --profile architecture --calibration /private/calibration.json \
  --out /private/grader_attachment
```

The DSBench Code Grade attachment currently requires **commercial calibration**, even though the broader operator runner offers an open-source fallback. In the attachment, `area_reference.json` is a profile-specific calibration object. The three-field public result cannot encode `score_valid`; platform ranking logic must inspect `reason` and exclude any `UNSCORED_INFRASTRUCTURE` or incomplete output.

## Caches and reporting

Store RTL and mapped source hashes, manifest, profile, backend, tool/library identities, random seeds, validation results and raw timing/area reports. Reusing an output directory is safe only when its full input identity matches. A design violating a mandatory specification is `DESIGN_INVALID` with a valid zero score; tool/measurement failures are `UNSCORED_INFRASTRUCTURE` and must not be ranked. Document completeness is reported separately.

These are synthesis-stage, ideal-interconnect measurements: do not report post-route timing, power or silicon Fmax. Complete long RTL tests and representative mapped tests have different coverage and should be reported distinctly.
