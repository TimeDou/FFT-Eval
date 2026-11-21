# FFT64 architecture and throughput task

Read `TASK_EN.md` first. Keep its mathematical FFT, input range, 50dB SQNR, natural output order, top-level interface, reset, 10ns timing and output deadlines. This task explicitly selects the **v0.4 architecture profile**. ALS is unnecessary.

Choose an FFT architecture and optimize precision/quantization, constant specialization, memory/resource sharing and legal pipelining. Ranking uses 60% complete mapped area, 30% verified sustained throughput and 10% first-output latency. See `SCORING.md` and `profiles/policy.json` for the frozen equations and targets. Frequency enters only through throughput. SQNR earns no bonus beyond feasibility.

Declare integer `frame_ii_cycles` from 64 to 384 in `design_config.json` (default 384). Verification continuously sends many frames at that interval, then tests mixed gaps, long idle and reset. First-output latency or one successful transaction does not establish sustainable II. Each frame still provides 64 consecutive complex samples through the original interface.

```bash
bash run_preview.sh /workspace/submission /workspace/runs/architecture \
  --profile architecture --backend commercial
```

Development may add `--auto-ii` to find the smallest empirically qualified interval, then write the chosen declaration into the configuration. Official evaluation verifies the declaration. Frequency requires a PrimeTime setup/hold clock scan on the fixed mapped netlist. Open-source-only development can still use the default area preview; final architecture scoring is obtained through the common Synopsys evaluator, never by substituting fixed-clock slack or an untested II.

Submit RTL, configuration, design plan and concise measurements. The operator must choose the architecture profile, calibration and final protocol before starting agent evaluation, rather than switching profiles after observing agent results.
