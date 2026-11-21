# Lightweight design loop for the agent

The purpose is to test engineering judgment and iterative hardware optimization, **not documentation volume**.

Use the supplied environment first. Run `bash setup.sh --check-only`; `setup.sh` and `run_preview.sh` load DSBench's EDA profile and prefer installed VCS/DC/PrimeTime. Installed open-source tools are the next choice; source builds are only a last fallback for missing components. Do not start by rebuilding Yosys or Icarus. `--no-build` restricts preview to existing EDA tools.

1. **Read:** `TASK_EN.md` or `TASK_ZH.md`, `SPEC.json`, `ARCHITECTURE_GUIDE.md`, `INTERFACE.md`.
2. **Plan:** create `DESIGN_PLAN.md` yourself; identify at least two plausible architecture families and measurable hypotheses. Treat the guide as background, not as a required prescribed design.
3. **Build a correct baseline:** run functional, protocol, synthesis and STA checks in the supplied EDA environment. Establish a measured area reference for your own comparison.
4. **Choose one experiment:** make a structural or precision change. Run quick public numeric tests first, then the full preview evaluator for promising candidates.
5. **Update the plan:** record one row with the actual results and why you accepted or rejected the change; adjust the *next* hypothesis. `measurements.csv` may be the source of detailed numbers; the plan should contain decisions only.
6. **Freeze final candidate:** no switching after official hidden feedback. Submit synthesizable RTL and enough configuration data to repeat it.

Prefer a short, evidence-driven design plan over large integrity reports. A failed experiment that motivates a useful revision demonstrates good design reasoning. Documentation is only a supporting trace; the actual RTL and measured QoR determine success.

## Suggested `measurements.csv` columns

`id,architecture,precision_policy,rtl_commit,area_um2,area_ratio,worst_frame_sqnr_db,first_cycle,last_cycle,timing_pass,protocol_pass,status,notes`

Use blank/unmeasured rather than fabricated zeros. Only values from the frozen official mapped flow count as final score.
