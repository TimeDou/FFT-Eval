# Codex-GPT-6.1-Sol-Max: verified FFT64 submission

The original final submission is in [submission/](submission/). Independent private evaluation passed numerical, protocol, mandatory continuous service, timing and representative RTL/mapped checks. This is a measured result of one Agent run, not a model-wide capability claim.

| Measurement | Result |
|---|---:|
| Resolved / score valid | true / true |
| Frozen architecture score | 0.917385665 |
| Complete mapped cell area | 1275.53130 μm² |
| Sequential cell area | 634.24458 μm² |
| Certified passing clock period | 1.506835937500 ns |
| Certified frequency | 663.642255 MHz |
| Minimum verified frame II | 258 cycles |
| Effective throughput at certified clock | 2572256.804 FFT/s |
| Maximum first-output / completion latency | 194 / 257 cycles |
| First-output latency at certified clock | 292.326172 ns |
| Minimum hidden per-frame SQNR | 54.809096 dB |

Technology: ASAP7 RVT/TT. Measurement: native VCS/DC/PrimeTime, pre-layout cell area and ideal-interconnect STA. All designs have 64 points and external input/output parallelism 1. The mandatory clock is 10 ns; scoring throughput uses an independent fixed-netlist clock scan. Latency scoring uses the common 10 ns clock, rather than rewarding frequency twice.

Private numerical coverage is 8,192 independent random nonzero frames plus 192 directed cases. Each of the 321 integer intervals 64–384 was exercised with 1,024 consecutive RTL frames. The selected interval passed a representative mapped subset with gap and reset probes from three gate initial states. These are finite observed checks, not a formal worst-case error or full sequential-equivalence guarantee.

The private evaluator imported any supplied mapped netlist and independently measured it. It did not execute Agent optimization scripts. The source, mapped artifact and manifest content are checked, without claiming cryptographically trusted build attestation.

- Final grade: [agent_evaluation/grade.json](agent_evaluation/grade.json).
- Original final measurement: [measurement/result.json](agent_evaluation/measurement/result.json).
- Original public evidence, kept separate: [public_evidence/](agent_evaluation/public_evidence/).
- Actual hidden numerical observations: [numeric_evidence/](agent_evaluation/numeric_evidence/).
- Full interval results: [probe_results.json](agent_evaluation/measurement/throughput/long_intervals/probe_results.json).
- Frozen calibration and provenance: [calibration.json](agent_evaluation/calibration.json), [provenance.json](agent_evaluation/provenance.json).

To verify the archive and replay its numerical outputs and score without EDA tools, run from the repository root with NumPy installed:

```bash
python3 agent_evaluation/verify_archive.py agent_evaluation
```

The verifier does not rerun VCS/DC/PrimeTime. Score replay permits an absolute 1e-14 tolerance for last-bit floating-point runtime differences; the original native score is authoritative. See the companion `validation/three-agent-comparison` branch for the comparison, normalization limitations and design-reasoning review. Other prior result branches are retained unchanged.
