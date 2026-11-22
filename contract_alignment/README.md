# Task-contract and startup-document alignment

The stale specification and SSH descriptions are corrected in both repositories. The public policy, normalization anchors, weights, numerical requirements and runtime scorer are unchanged. The expanded bilingual startup prompt explains nonlinear normalization, component saturation, weighted trade-offs and custom mapped-netlist delivery. Real Synopsys verification and source-level checks are complete; these are evaluator fixtures, not new Agent ranking results.

## Applied review material

At synchronization time DSBench/chat-new-markdown contained four files: AUDIT_REPORT.md, SPEC_JSON_CHANGE_REQUEST.md, START_CN.md and SYNC_MAP.md. The supplied Chinese startup prose is retained in START_PROMPT.md, with heading normalization and one sentence supplying the existing input range/RMS/reference from SPEC. An equivalent full English prompt is included. The specification, SSH guide, optimization guide, task text and score-driven workflow were aligned with this material.

SYNC_MAP refers to fourteen complete files under revised/FFT-Bench, but that directory and those replacement bodies were not supplied. They have not been represented as verbatim replacements. The available originals and their hashes are retained under review_material/ and in source_alignment.json. The audit report itself is archival review evidence, not Agent task instructions.

## Corrected contract

SPEC.scoring.area now describes the public rational-area function and 500/4000 um2 anchors. SPEC.scoring.architecture names the rational-area, logarithmic-throughput and linear-latency functions. SPEC.scoring.latency_score spells out the 63-to-300-cycle scale. SPEC.scoring.missing_calibration and the SSH/root/optimization guides distinguish a valid public preview from calibrated official hidden grading. Every non-scoring section of SPEC is unchanged.

The registration record also binds the current SPEC hash. The existing policy, report source, rendered PDF and report-builder hashes are unchanged. Even descriptive changes alter the protocol identity, so previous calibration is rejected rather than relabeled or edited. Fresh accurate references establish matching native calibration. The actual private operator cached_evaluate path applies that calibration to its matching native results; reuse is recorded and is not a second independent experiment.

## Actual native validation

Both accurate references were evaluated on 8192 independent hidden random nonzero frames plus 192 directed frames. The custom fixture was freshly synthesized and exported using DC, then independently imported by the public evaluator on 1024 random nonzero frames plus 192 directed frames, without private calibration. Every case completes all 321 integer IIs with 1024 consecutive RTL frames per interval, representative RTL/mapped comparisons from three initial states, reset/deadline checks and fixed-netlist setup/hold STA certification. Shorter unsupported intervals are retained as optional failures.

| Fixture | Score scope | Area (um2) | Certified period (ns) | Verified II | Worst first output (cycles) | Minimum SQNR (dB) | Score |
|---|---|---:|---:|---:|---:|---:|---:|
| Accurate streaming FFT64 reference | hidden_evaluation | 3644.51886 | 4.363281250 | 197 | 133 | 70.6974 | 0.468446136 |
| Accurate folded FFT64 reference | hidden_evaluation | 2437.28028 | 3.839599609 | 320 | 256 | 70.6974 | 0.467164129 |
| Streaming FFT64 fixture, freshly built/exported with custom DC recipe | public_preview | 2415.94974 | 1.202148438 | 64 | 127 | 56.2840 | 0.674778371 |

The new private Code Grade attachment contains exactly the same policy, scoring source and SPEC as the public source snapshot. Its matching private calibration is included separately. Public preview returns score_valid=true, scoring_scope=public_preview and official_score=false; calibrated hidden results return valid official scores. The native rejection record confirms that the previous calibration cannot score this protocol even though normalization policy is unchanged.

These are pre-layout mapped-cell and ideal-interconnect STA measurements. SQNR is empirical on the declared finite inputs. Full RTL long-stream coverage and representative mapped coverage have different scopes. The source regression suite contains 136 passing tests, including registration/specification binding and stale-calibration rejection; it supplements the real measurements.

## Resources and retained records

Native probe progress files retain Python-process peak RSS and scan wall time. process_resources.json separately samples measurement/prefetch process trees including EDA subprocesses; its summed RSS may double-count shared pages and may miss peaks between samples or before sampling began. It is not an exact cgroup/container peak. Disk usage is recorded for this run only. No claim about post-route PPA, silicon frequency or a new Agent ranking is made.

The archive retains raw JSON/CSV metrics, native tool logs/reports, actual mapped netlists, custom build/export evidence, source hashes, regression logs and grading artifacts. Reconstructible simulator objects and large per-cycle text remain at original_run_directory in FILE_MANIFEST.json. Previous pilot histories, grades and experiment directories are preserved.

## Frozen source and scoring identity

```json
{
  "source_commits": {
    "FFT-Bench": "4a31a2a5fd4edefeae70d35a91b5b914c50e029d",
    "FFT-Eval": "5d54b562c59f45aef0bfacf2fe2a140a6ad21040"
  },
  "policy_sha256": "62311a56189365e4c4202522e2b74558dbc75c87259432c568a63bbcddd424aa",
  "specification_sha256": "ddb6077e204fde38ea6bb22cd5a3279abe6939124c443f8253e16f3ecb62f011",
  "scoring_source_sha256": "b2a887f48174335c987255d28c6ea2cafd5f78f406b0163cacd35816732c39b7"
}
```
