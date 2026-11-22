# Public score-aware protocol and restart decision

The prior Agent results remain pilot experiments under their original policy. Their immutable submitted circuits, measured scores, complete verification and analysis are retained on the individual result branches and in validation/agent_comparison. The additional pilot_workspace records on each branch preserve development sources, logs, measurements and explicit exclusions for reconstructible generated artifacts before the local workspaces are cleared.

The restarted task publishes all numerical scales and returns complete public component/combined scoring feedback. The architecture weights remain 0.60 / 0.30 / 0.10.

- Area credit is 3500/(A+3000), capped at one: ideal area 500 um2, half-credit area 4000 um2. This broad scale covers ordinary accurate implementations without making all larger designs indistinguishable at zero.
- Throughput credit is log(T/T_min)/log(240), clamped to [0,1]. T_min=1e9/(384*10) FFT/s and T_ideal=62500000 FFT/s. The ideal is the maximum observable under the declared 0.25 ns clock-scan floor and II=64 lower bound, rather than a target selected to favor one Agent.
- Latency credit is (300-L)/237, clamped to [0,1], with a 63-cycle serial-input ideal.

The simultaneous 500 um2 / 62.5 M FFT/s / 63-cycle point is intentionally demanding and is not claimed to be a realizable circuit. Public half-credit/ideal scales are objective parameters, not hidden-input statistics or an accurate reference netlist. Ordinary designs should occupy an informative middle range. The old hardware below is used to inspect the transfer functions and sensitivity only; these numbers do not replace any historical official score or establish a new Agent ranking.

| Design | Frozen pilot score | New-objective diagnostic |
|---|---:|---:|
| exact_folded | 0.099199 | 0.467164 |
| exact_sdf | 0.202616 | 0.468446 |
| twiddle9_folded | 0.189292 | 0.482170 |
| quantized_banked | 0.504748 | 0.536274 |
| pipelined_folded | 0.111626 | 0.457873 |
| timing2ns_folded | 0.207665 | 0.491487 |
| abc_default | 0.158005 | 0.424576 |
| abc_resyn2 | 0.150455 | 0.413663 |
| Claude-DS-Flash | 0.161277 | 0.474054 |
| Codex-GPT-6.1-Sol-Max | 0.917386 | 0.661257 |
| Codex-GPT-6.2-Sol-Max | 0.384592 | 0.674778 |

The 11 feasible hardware samples span 0.4137–0.6748, with 11 distinct values at six decimal places. They are not concentrated at zero and none reaches the ideal point. Both high-throughput Agent samples retain different throughput components, unlike the pilot's saturation. These finite samples do not establish universal score discrimination.

Public feedback and hidden acceptance are separate. A complete public preview has score_valid=true, scoring_scope=public_preview and official_score=false. Hidden grading uses the identical arithmetic scales and still requires private platform/protocol validation. Quick/incomplete or tool-failed runs remain unscored; a measured mandatory-spec violation is a valid zero score.

Each restarted Agent must receive the same public task, numerical anchors, initial prompt and execution budget. Workspaces and their containers are reset after archival; retained dependencies contain no candidate circuit or private scoring data. Start a fresh Agent conversation as well: clearing files does not clear an already-running conversation's model context. This is a new controlled run, not continuation using privileged pilot feedback.

## Source and retained evidence

The published public task is commit `11757acc369f00cbbdaedb4fd022b0bc99f98c7b` on FFT-Bench/main; the matching private evaluator is commit `1dc9097456092bfa00d2ee6b7875aeefc1882ff2` on FFT-Eval/main. [The common startup prompt](https://github.com/TimeDou/FFT-Bench/blob/11757acc369f00cbbdaedb4fd022b0bc99f98c7b/START_PROMPT.md) explicitly states the combined objective and directs the Agent to public numerical anchors and measured component feedback. Numerical FFT constraints and the 321-point II coverage remain fixed.

The [historical comparison and analysis](../validation/agent_comparison/RESULTS.md) retains the original pilot grades. Development sources, logs, measurements and documented generated-artifact exclusions were appended to the following private result branches before any local removal:

| Pilot branch | Preservation commit | Fresh SSH port |
|---|---|---:|
| agents/Claude-DS-Flash | 3a954aeef12ba970d7255b8b6e7dca768a08c432 | 2201 |
| agents/Codex-GPT-6.1-Sol-Max | 6c7abf049e827a8f67feb285a39e33d1d0b544dd | 2204 |
| agents/Codex-GPT-6.2-Sol-Max | 3e5a16d8a3ba310ffffba68a1bc91ac07ea31326 | 2205 |

[Reset and real environment-check receipts](reset_receipts/verification.json) distinguish the three recreated workspaces from the unused Fable workspace synchronized at port2206. Each new clone is clean and contains no old candidate. The original image and tool/library bytes are retained; old shared experiment directories and per-container working state were removed for the three completed pilots.

[Native validation evidence](validation/README.md) covers actual public preview scoring, independent hidden accurate controls, matching hidden-calibration replay, a commercial grader attachment and the complete regression log. [Diagnostic source summaries](diagnostic_sources/index.json) and [diagnostic arithmetic checks](diagnostic_verification.json) make the finite-sample normalization assessment independently inspectable. [PDF](normalization.pdf) and [PNG](normalization.png) curves are reproducible with scripts/plot_normalization.py using the public policy alone.
