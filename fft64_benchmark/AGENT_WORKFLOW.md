# Evidence-Driven Design Workflow

The evaluation rewards the final verified FFT implementation, not the length of a design journal. Maintain a short decision record so that architecture, precision and tool-flow choices can be explained by **actual measurements**.

## Recommended process

1. **Read the contract.** Inspect `TASK_EN.md` or `TASK_ZH.md`, `SPEC.json` and `INTERFACE.md`. Read SCORING.md and every numeric target in profiles/policy.json before choosing an architecture. Optimize 0.60 S_A + 0.30 S_T + 0.10 S_L; separate mandatory II=384 service from optional higher throughput.
2. **Form competing hypotheses.** Consider at least two FFT architectures with different area, storage, scheduling and throughput characteristics. The [architecture guide](ARCHITECTURE_GUIDE.md) provides options without prescribing a solution.
3. **Create a working baseline.** Implement synthesizable RTL and pass public functional, protocol and SQNR tests before optimizing area or II.
4. **Change one meaningful design choice.** Explore a hardware structure, explicit fixed-point quantization rule, or [EDA synthesis recipe](../OPTIMIZATION.md). State the expected effect and the measurement that could disprove it.
5. **Measure and compare.** Start with quick checks; synthesize and evaluate promising candidates with the same backend and reference policy. Use grade.components, grade.weighted_components and grade.score from complete architecture previews to compare trade-offs. Preserve negative experiments when they inform a decision.
6. **Revise the plan.** Update `DESIGN_PLAN.md` after material changes and append measured configurations to `measurements.csv`. Distinguish estimates from EDA measurements and partial tests from full scores.
7. **Freeze the best verified candidate.** Keep RTL, source and recipe hashes, and—when using custom synthesis—the exported structural netlist and manifest. Rebuild after changing RTL or recipe. Do not use private feedback to revise a submitted candidate.

With sibling `Synopsys/` and `port.txt`, use `check_env.sh`, `run_synopsys_debug.sh` and `synopsys.sh exec` for publicly authorized container debugging. Work in a separate output directory for each design candidate. See [REMOTE_SYNOPSYS.md](../REMOTE_SYNOPSYS.md).

## Suggested measurement schema

```text
id,architecture,precision_policy,source_hash,recipe_hash,mapped_hash,backend,library_id,area_um2,worst_sqnr_db,verified_ii_cycles,certified_period_ns,maximum_first_cycles,maximum_completion_cycles,area_score,throughput_score,latency_score,total_score,score_valid,scoring_scope,timing_pass,protocol_pass,status,notes
```

Leave unavailable values blank rather than using zero. Record component scores and total score only when the selected profile's complete evaluation returns valid feedback. Compare 0.60 ΔS_A, 0.30 ΔS_T and 0.10 ΔS_L when selecting the final design; a saturated component earns no further credit, and an area-only score cannot substitute for the combined objective. The `frame_ii_cycles` configuration field is a hint; official throughput is independently measured. A custom implementation's area and timing must be evaluated using the same frozen library and constraints as competing designs. The design plan and experiment log support qualitative analysis but do **not** directly change the numerical score.
