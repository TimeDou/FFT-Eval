# Manual JSON correction required before official Agent launch

The new scoring formulas are implemented in `fft64_benchmark/tools/scoring.py` and published in `SCORING.md`, but `fft64_benchmark/SPEC.json` retains two older explanatory strings. **No executable scoring change is proposed.** Edit only the stale strings to avoid misleading Agents.

### Path `scoring.area`

**Old:**

```json
"area": "clip((A_ref-A)/(A_ref-0.5*A_ref),0,1); A_ref is smallest validated accurate mapped area"
```

**New:**

```json
"area": "clip((A_half-A_ideal)/(A+A_half-2*A_ideal),0,1); public A_ideal=500 um2 and A_half=4000 um2; accurate baseline area does not set the score scale"
```

### Path `scoring.missing_calibration`

**Old:**

```json
"missing_calibration": "score_valid=false; hardware feasibility remains separately available"
```

**New:**

```json
"missing_calibration": "complete public previews compute component and combined scores from fixed public anchors without private calibration; official hidden grading requires matching platform/protocol validation; otherwise the hidden score is invalid"
```

### Additional consistency suggestion

Update `scoring.architecture` from generic 'normalized terms and calibration' to 'published rational-area, logarithmic-throughput and linear-latency functions in profiles/policy.json'. It is not mathematically incorrect today, but the word 'calibration' could imply that reference circuits modify the normalization anchors.

Do not edit the scores stored in `profiles/policy.json` merely to repair these descriptions. A modified `SPEC.json` changes the specification hash in measurement cache identities and should be deployed with a new clearly identified benchmark revision. Verify any private operator's cached identities and calibration before official runs.
