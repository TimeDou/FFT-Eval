# Native FFT64 v0.4: architecture profile

N=64, P_in=P_out=1, ASAP7 RVT/TT, 10ns common target, complete RTL and mapped VCS tests; pre-layout synthesis / ideal-interconnect STA.

| Design | Area µm² | Certified period ns | Verified II | FFT/s | First-output ns @10ns | Min SQNR dB | Score | Specs |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Accurate frame-isolated R2SDF | 3644.52 | 4.363281 | 197 | 1163377.2 | 1330 | 70.58 | 0.134211 | PASS |
| Accurate folded radix-2 | 2437.28 | 3.839600 | 320 | 813886.9 | 2560 | 70.58 | 0.298590 | PASS |
| Quantized banked radix-2 reference | 1614.78 | 3.820557 | 320 | 817943.6 | 2560 | 55.30 | 0.502826 | PASS |

Weights, target ratios, and scan settings were frozen before these measurements; policy SHA-256: `78639b42bf9bb24595d4a23c3f199d26774c0d32c5968397c8a427f1c9f2efb4`. Calibration uses accurate baselines only. `resolved` is independent of score. SQNR is a hard constraint, with no precision bonus.

Area and architecture have separate normalization vectors. Blank frequency/II fields in the area profile mean those quantities were not needed for scoring. Architecture frequency comes from the passing endpoint of a measured setup/hold clock scan; throughput is certified frequency divided by the verified declared frame interval. First-output scoring uses the common 10ns clock, so frequency is not rewarded again through latency.

The baseline called R2SDF is the provided frame-isolated implementation. Its measured service capacity must not be confused with the best possible fully-streaming R2SDF. Verified II is empirical under the saved workload, not a formal all-input minimum.

All successful and failed II pilots, strict mapped checks, clock-scan endpoints and hashes are retained. Three mapped runs use time-zero all-zero, all-one and seeded binary register starts, followed by ordinary reset operation. No runtime signal repair occurs. Full raw logs/netlists remain in the original evaluation directory. No P&R, power or silicon Fmax was measured. See SCORING.md for normalization equations and pre-registration.
