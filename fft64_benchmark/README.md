# FFT64-Quant public benchmark

Implement a 64-point fixed-point complex FFT and optimize architecture, precision, quantization, constant arithmetic, buffering and pipelining. Read TASK_ZH.md or TASK_EN.md, SPEC.json, INTERFACE.md and ARCHITECTURE_GUIDE.md. No finished RTL is supplied.

```bash
bash setup.sh --check-only
bash run_preview.sh /workspace/submission /workspace/runs/numerical --quick --no-build
bash run_preview.sh /workspace/submission /workspace/runs/ppa --no-build
```

Use installed Synopsys tools first; otherwise use installed open-source tools. Setup builds missing open-source dependencies only when allowed; --no-build disables this. Override tool paths with FFT_VCS, FFT_DC, FFT_PT, FFT_STA, FFT_ABC and FFT_PYTHON as needed.

Public numerical testing has >=1,024 independent nonzero frames plus directed cases. FFT length remains 64. The quick command also checks >=1,024 consecutive mandatory-service frames; it skips ASIC measurement. Complete evaluation measures area, clock-scan timing and long-frame service. The official combined objective is 60/30/10 area/throughput/latency. A public run without the operator's matching calibration provides hardware feedback with score_valid=false. Hidden inputs and official scoring are evaluated separately. See SCORING.md.

Submit rtl/, design_config.json, DESIGN_PLAN.md and measurements.csv. The small public_data examples are interface examples, not the full numerical evaluation workload.
