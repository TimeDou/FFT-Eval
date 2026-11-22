# Evidence-Driven FFT Design Workflow

The benchmark evaluates a **working circuit and its measured hardware quality**, not the length of the design diary. Use the supplied tools and record the decisions that materially changed the design.

With sibling `Synopsys/` and `port.txt`, start with `bash check_env.sh`. Use the remote public preview and `synopsys.sh exec` for container debugging; do not construct another host EDA toolchain. Read the repository's `REMOTE_SYNOPSYS.md` for commands and log locations.

1. **Understand the contract.** Read `TASK_EN.md` or `TASK_ZH.md`, `SPEC.json`, and `INTERFACE.md`. Distinguish mandatory II=384 from optional faster service.
2. **Compare candidate architectures.** Read `ARCHITECTURE_GUIDE.md`; propose at least two different organizations and explain the expected area/throughput/latency trade-off.
3. **Establish a correct baseline.** Implement synthesizable RTL, pass the public numerical/protocol checks, then obtain mapped area and timing in one fixed backend.
4. **Make one measurable change.** Adjust a structure, explicit quantization choice or [optimization recipe](../OPTIMIZATION.md); predict the expected effect on area, SQNR, II, or latency.
5. **Evaluate and decide.** Run quick tests first, then hardware/throughput checks when worthwhile. Record a rejected result as well as an accepted one; never label a model estimate as a measured PPA result.
6. **Revise the plan.** Update `DESIGN_PLAN.md` only when an experiment changes a decision. Record the actual candidate data in `measurements.csv`.
7. **Freeze the final candidate.** Submit the self-contained RTL, any custom recipe and exported implementation, and a concise trace. Rebuild the implementation after changing RTL or recipes. Do not change the candidate after private evaluation feedback.

## Recommended measurement columns

`id,architecture,precision_policy,source_hash,recipe_hash,mapped_hash,backend,library_id,area_um2,worst_sqnr_db,verified_ii_cycles,certified_period_ns,maximum_first_cycles,maximum_completion_cycles,timing_pass,protocol_pass,status,notes`

Use empty fields for unavailable results, not `0`. A locally mapped area cannot be combined with a commercial reference area; official scores require a matching backend and frozen calibration. `frame_ii_cycles` in an optional config is a hint only; the evaluator measures capacity independently.
