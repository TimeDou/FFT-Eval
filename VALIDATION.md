# FFT64-Quant: Validation Evidence and Limits

## Source regression suite

From the private repository root:

```bash
python3 -m unittest discover -s operator/tests -q
```

Tests cover scoring, numerical/protocol fixtures, mapped implementation manifests, cache identity, grading entrypoints, SSH runner behavior, tool invocation and outcome classification. Synthetic stubs and tool mocks are used where commercial software is unavailable. **Passing these tests does not establish that a complete FFT has been synthesized and verified on the deployed EDA tools.** The exact count and outcome should be recorded from each environment's own run.

## Hardware measurement evidence

Actual hardware claims must be supported by the candidate RTL source snapshot, imported or generated mapped netlist, library/tool versions, calibration, input seeds, per-frame numerical results, sustained II observations, representative gate comparisons, setup/hold reports, frequency scan and raw tool logs. A source-only export does not include evidence stored in a separate experimental branch or result directory.

The private `Codex-GPT-6.1-Sol-Max` branch contains a submission and evaluation records. Main-branch source snapshots omit those result files. Use each measurement's recorded source, policy and tool identities when checking or reproducing it; do not treat it as validation of a different checkout.

## Scope of a completed measurement

The configured hidden numerical workload includes 8,192 random nonzero frames plus directed cases. Architecture evaluation probes every integer II in 64–384 with at least 1,024 continuous RTL frames per interval; the selected shortest passing II receives mapped confirmation on a representative subset. Complete mapped numerical verification is **not** performed over every hidden frame. Hardware QoR refers to pre-layout mapped area and ideal-interconnect STA, not post-route PPA or silicon frequency.

An official hidden outcome is rankable only when score_valid=true and matching private platform/protocol validation is available. A complete public preview has valid numeric feedback with scoring_scope=public_preview and official_score=false, using the same public normalization. Tool/license failure, timeout or missing measurement is `UNSCORED_INFRASTRUCTURE`, not design failure; quick or partial execution is `INCOMPLETE`. Document completeness is evaluated separately.
