# Manual synchronization plan

All replacements are complete Markdown files under `revised/FFT-Bench/`, mirroring the original directory layout. This package **does not change the uploaded repository**. `MARKDOWN_REWRITES.diff` shows line-by-line changes from the uploaded archive.

| Original path | Supplied replacement | Reason for revision |
|---|---|---|
| `README.md` | `revised/FFT-Bench/README.md` | Clear entrypoint, current scoring, public preview, custom flow |
| `START_PROMPT.md` | `revised/FFT-Bench/START_PROMPT.md` | Balanced bilingual startup; explicit nonlinear scoring and flow path |
| `OPTIMIZATION.md` | `revised/FFT-Bench/OPTIMIZATION.md` | Distinguish fixed public anchors from accurate reference calibration |
| `REMOTE_SYNOPSYS.md` | `revised/FFT-Bench/REMOTE_SYNOPSYS.md` | Fix obsolete claim that public score requires private calibration |
| `fft64_benchmark/TASK_EN.md` | `revised/FFT-Bench/fft64_benchmark/TASK_EN.md` | Explain aspirational ideal and smooth area feedback |
| `fft64_benchmark/TASK_ZH.md` | `revised/FFT-Bench/fft64_benchmark/TASK_ZH.md` | Same content in concise Chinese |
| `fft64_benchmark/SCORING.md` | `revised/FFT-Bench/fft64_benchmark/SCORING.md` | Explicit anchors, smooth-area/log-throughput formulas and weighted deltas |
| `fft64_benchmark/EVALUATION.md` | `revised/FFT-Bench/fft64_benchmark/EVALUATION.md` | Clarify frozen public policy hash vs private platform validation |
| `fft64_benchmark/AGENT_WORKFLOW.md` | `revised/FFT-Bench/fft64_benchmark/AGENT_WORKFLOW.md` | Score-aware design revisions and component saturation |
| `fft64_benchmark/DESIGN_PLAN_TEMPLATE.md` | `revised/FFT-Bench/fft64_benchmark/DESIGN_PLAN_TEMPLATE.md` | Track component scores and valid vs partial results |
| `fft64_benchmark/ARCHITECTURE_GUIDE.md` | `revised/FFT-Bench/fft64_benchmark/ARCHITECTURE_GUIDE.md` | Connect architecture trade-offs to actual combined score |
| `fft64_benchmark/README.md` | `revised/FFT-Bench/fft64_benchmark/README.md` | Emphasize public score anchors and exact documentation links |
| `fft64_benchmark/TASK_ARCHITECTURE_EN.md` | `revised/FFT-Bench/fft64_benchmark/TASK_ARCHITECTURE_EN.md` | Remove implication of hidden baseline-normalized score |
| `fft64_benchmark/TASK_ARCHITECTURE_ZH.md` | `revised/FFT-Bench/fft64_benchmark/TASK_ARCHITECTURE_ZH.md` | Same correction in Chinese |

The following needed correction is **JSON, not Markdown**: `fft64_benchmark/SPEC.json`; see `SPEC_JSON_CHANGE_REQUEST.md`.

The report `docs/FFT64-Quant.md` and its PDF are already internally aligned with the new scoring scales in the uploaded archive. They were **not** overwritten here to preserve the verified pre-registration hashes. If the revised paper `latex/background.tex` and `latex/methodology.tex` are incorporated into that report or if `docs/FFT64-Quant.md` is otherwise changed, regenerate the PDF and perform an explicit version re-freeze. Do not quietly change already published hashes mid-experiment.

For the academic manuscript, use `latex/background.tex`, `latex/methodology.tex`, and `latex/figs/benchmark_overview.tikz`; keep the image files from `latex/figs/`. `latex/experimental_setup_scoring.tex` is a **suggested** setup table populated with the *current public policy* values, to be frozen and checked against the actual run before reporting experiments. The `.diff` files in `latex/` show changes relative to the prior conversation's manuscript.

Full-equivalent Chinese and English prompts are in `prompts/START_CN.md` and `prompts/START_EN.md`. All Agents in the same comparison must receive the same public policy, available tools, workspace isolation, and budget; do not mix prompt versions in one official ranking.
