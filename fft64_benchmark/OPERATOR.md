# FFT64-Quant: Private Operator Protocol

This document applies to **FFT-Eval operators only**. Keep accurate baseline RTL, private input seeds, private platform/protocol calibration and all grading results inaccessible to Agents. Score formulas and numeric anchors are public. The separate FFT-Bench repository is the only public task source.

## Freeze before scoring

Select the backend, standard-cell libraries, trusted STA constraints, numerical protocol, scoring profile and calibration before starting a ranked campaign. The default `architecture` profile uses area, verified throughput and maximum first-output latency; the `area` profile is a separate diagnostic. Different backends must receive independent calibration and rankings.

Calibrate the two accurate reference circuits using the default mapping recipe and identical trusted measurement settings. Candidate recipes may differ, but the **independent measurement** and normalization anchors must remain fixed. Do not retune targets using evaluated Agent results.

## Agent-generated mapped implementations

Public development may execute arbitrary Agent-provided DC/Yosys/ABC optimization scripts. Private grading must **never execute those scripts**. If the Agent supplies `implementation/mapped.v`, validate its structural form and manifest consistency; import it into the trusted mapping/STA environment without running new optimization or accepting self-reported metrics. Verify legal cells, complete area, setup/hold, numerical behavior, reset and representative RTL/mapped consistency. A manifest is not proof of a genuine EDA execution history.

If no exported implementation and no custom recipe is submitted, apply the trusted default mapping. A custom recipe without the corresponding export is not a complete candidate for full scoring.

## Required evidence and outcomes

The score must rely on minimum tested per-frame SQNR, maximum observed first/completion delays, continuous II measurements and certified timing of the same mapped netlist. Preserve source hashes, tool identities, calibration fingerprints, per-frame data, mapped checks and raw reports.

Only `score_valid=true` results may be ranked. `DESIGN_INVALID` is a measured hardware failure with a valid zero score. Tool and license faults, timeouts, malformed outputs or missing calibration are `UNSCORED_INFRASTRUCTURE`; the platform's three-field result should be excluded from ranking when its `reason` begins with this prefix. Quick or unfinished runs are incomplete, not final scores.

The platform `grading/test_by_code.py` currently requires a **commercial** calibration, although the broader operator scripts can run an independently calibrated open-source backend. Verify an actual end-to-end commercial execution before official scoring. See [operator/SCORING_PROFILES.md](../operator/SCORING_PROFILES.md) and [EVALUATION.md](EVALUATION.md).
