# Architecture Scoring Profile — Task Addendum

The **default** FFT64-Quant task in [TASK_EN.md](TASK_EN.md) uses the `architecture` profile. This file is only a short entrypoint, not a separate benchmark with different specifications.

Feasibility requires SQNR ≥ 50 dB per tested nonzero frame, correct FFT/protocol/reset behavior, mandatory II=384 service, 10 ns timing, and mapped consistency. A feasible design can score 0.

The continuous score weights **complete mapped area 60%**, **verified effective throughput 30%**, and **maximum observed first-output latency 10%**. Each integer II 64–384 is measured with ≥1,024 consecutive RTL frames; the shortest passing interval is confirmed on a mapped representative subset. An II declared in `design_config.json` is only a hint, not a scoring authority.

See [SCORING.md](SCORING.md) for the published nonlinear functions and fixed numerical anchors, and [EVALUATION.md](EVALUATION.md) for the public and hidden test stages. Accurate reference circuits validate the private platform/protocol; they do not set normalization scales. Complete public previews return valid component and combined scores without private calibration.
