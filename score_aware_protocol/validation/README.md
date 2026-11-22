# Native scoring-feedback and environment validation

The new public numerical scales and actionable preview feedback were tested with real VCS, Design Compiler and PrimeTime. These are evaluator validation fixtures, not new Agent submissions or a new ranking. Historical Agent grades and their original policies remain unchanged on the pilot branches.

Both accurate controls use a fresh private hidden protocol (8192 independent random nonzero frames plus 192 directed frames). The archived candidate uses the actual public evaluator (1024 random nonzero frames plus 192 directed frames), with no private calibration supplied. All three complete the full 321-point II scan, 1024 consecutive frames per interval, representative mapped-netlist checks under three initial-state modes, mandatory service/reset/deadline checks and fixed-netlist STA clock certification. Optional short-II failures are retained. The public candidate receives quantitative components and total score with scoring_scope=public_preview and official_score=false.

The two accurate controls then establish matching private platform/protocol validation. Their measurements do not set any scoring denominator or numeric target. The actual hidden evaluate() path was replayed with this calibration and matching cached physical evidence; both returned valid official hidden scores identical to direct scoring of the same measurements. The replay does not count as a second independent dataset or a new hardware search.

| Hardware fixture | Audience | Area (um2) | Passing period (ns) | Verified frame II | Worst first output (cycles) | Minimum SQNR (dB) | Score |
|---|---|---:|---:|---:|---:|---:|---:|
| Accurate 64-point streaming reference | hidden | 3644.51886 | 4.363281250 | 197 | 133 | 70.7216 | 0.468446136 |
| Accurate 64-point folded reference | hidden | 2437.28028 | 3.839599609 | 320 | 256 | 70.7216 | 0.467164129 |
| Archived 64-point streaming candidate (validation fixture) | public | 2415.94974 | 1.202148438 | 64 | 127 | 56.2840 | 0.674778371 |

All PPA is pre-layout mapped-cell area and ideal-interconnect STA. SQNR is an empirical result on the declared finite data, not a formal numerical guarantee. The complete raw result, component scores, policy binding, mapped netlists, tool logs, STA certificates, interval summaries and input-generator configuration are retained alongside this report. Large per-cycle text and reconstructible simulator builds remain at the private original run directory recorded in FILE_MANIFEST.json.

## Measured scan resources

Every integer interval 64–384 was tested; no coverage was reduced for this check. Batches hold at most eight II workloads concurrently in one Python process. These figures describe the scanner's Python process and largest single input array, not total machine/container peak memory. Native tool subprocess resources are recorded separately in the logs.

| Hardware fixture | Long-II scan wall seconds | Python peak RSS (MiB) | Largest single input array (MiB) |
|---|---:|---:|---:|
| Accurate 64-point streaming reference | 1249.8 | 591.4 | 118.6 |
| Accurate 64-point folded reference | 1115.4 | 590.7 | 118.6 |
| Archived 64-point streaming candidate (validation fixture) | 1126.8 | 419.6 | 118.6 |

## Restart and regression evidence

The complete 135-test regression suite passes. Public scoring/normalization source, tests, documentation and the rebuilt report were committed and pushed before the restarted workspaces were created. The three completed Agent workspaces and their containers were cleared only after their pilot development records and final verified results were pushed to private result branches. Each restarted clone contains one public commit, is clean, and contains no old candidate or experiment. Existing public dependencies were reinstalled from verified sources. Each workspace passed a real environment check including RTL simulation, mapped simulation, DC and PrimeTime. The unused Fable workspace was synchronized and independently passed the same check. These small smoke circuits are environment checks, not FFT results.

The simultaneous ideal objective (500 um2, 62.5 million FFT/s, 63-cycle first output) remains deliberately demanding. The 11 preexisting feasible circuits span 0.4137–0.6748 under an explicitly labelled diagnostic transfer-function replay, with 11 distinct scores at six decimals. This demonstrates useful differentiation on these finite samples, not a universal guarantee or a retrospective official reranking. A fresh common prompt and execution budget are required for the next Agent comparison. Filesystem/container reset does not erase an existing Agent conversation's context.

## Frozen source identity

```json
{
  "FFT-Bench": "11757acc369f00cbbdaedb4fd022b0bc99f98c7b",
  "FFT-Eval": "1dc9097456092bfa00d2ee6b7875aeefc1882ff2"
}
```
