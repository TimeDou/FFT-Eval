# Local Synopsys validation

The complete benchmark ran in the SSH-accessible Synopsys container, including both accurate calibration architectures and the candidate RTL. No open-source PPA replaced native commercial measurements.

| Design | Area µm² | STA limit ns | Fmax estimate MHz | Minimum SQNR dB | First/completion cycles | Score | Specs |
|---|---:|---:|---:|---:|---:|---:|---|
| Accurate R2SDF | 3644.52 | 4.3625 | 229.23 | 70.58 | 133/196 | 0.369820 | PASS |
| Accurate folded radix-2 | 2436.06 | 3.8301 | 261.09 | 70.58 | 256/319 | 0.500000 | PASS |
| Quantized banked radix-2 reference | 1614.78 | 3.8150 | 262.12 | 55.30 | 256/319 | 0.602319 | PASS |

All rows use N=64, one complex input/output per valid cycle, the same ASAP7 RVT/TT libraries, 10 ns target clock, verified frame II=384, and the same protocol and input seed. Target-clock service is 16.6667 M complex samples/s. The Fmax and throughput used for ranking are estimates from pre-layout STA, not physical-device or post-route measurements.

The reference anchor is `iterative`. Every design satisfying the required specifications has `resolved=true`; score has no pass threshold. `score=E/(1+E)` ranks normalized throughput/area efficiency, with the anchor at 0.5.

Mapped VCS verification runs the complete dataset from all-zero, all-one, and seed-20261121 time-zero register states. It compares control cycles and all valid payload samples to ordinary four-state RTL simulation, including resets during processing and long idle periods. No signal is repaired after time zero. This covers the observed reset X-pessimism artifact without masking it by testing only all-zero initialization.

Machine-readable data, per-frame quality, mapping/STA reports and source/library/tool identities are saved beside this report. Full compile/runtime logs and netlists remain in the original evaluation directory and its feedback archive. Power and P&R were not measured.
