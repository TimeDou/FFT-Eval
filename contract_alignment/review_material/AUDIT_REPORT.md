# FFT64-Quant public benchmark re-audit — 22 Nov 2026

## Scope and evidence level

**Source inspected:** `FFT-Bench_review_20261122_11757ac.zip` (one public `FFT-Bench/` repository). This upload does **not** include a revised FFT-Eval/private Code Grade package, private calibration data, a real Agent submission, or Synopsys tool logs. Those aspects cannot be certified from this upload.

I inspected the actual `SCORING.md`, `profiles/policy.json`, `tools/scoring.py`, `tools/evaluate.py`, `tools/throughput.py`, mapped-import and EDA backend code, public task docs, and report source. `python -m compileall` passed for included Python scripts. I ran direct numerical checks of `component_scores` and **three synthesized-data scoring-path tests** (public valid score without calibration; hidden unscored without matching validation; design-invalid valid zero), and checked `PRE_REGISTERED.json` hashes against the shipped PDF, Markdown report, builder, and policy; those four hashes match. **The archive contains no test suite**: previous claims about 128 regression tests cannot be repeated for this exact package. No actual DC/VCS/PT, Yosys, OpenSTA, SSH, full-II, or hidden evaluation was executed in this audit.

## Executive assessment

**Conditional GO for pilot Agent runs; NOT a fully verified official hidden-evaluation release.** The main public scoring and custom-synthesis flow are coherent: mandatory feasibility is distinct from score; area is rationally normalized, throughput logarithmically normalized, latency linearly normalized; complete public previews disclose score components without private calibration; custom mapped netlists are imported and independently measured. The new ideal score is aspirational rather than a claim about a physically achieved FFT. Several fixes and a real end-to-end smoke run should precede official ranking.

## High priority — documentation/code contract drift

**H1. `fft64_benchmark/SPEC.json` still declares the old area formula.** Its `scoring.area` text is `clip((A_ref-A)/(A_ref-0.5*A_ref),0,1)` and refers to an accurate baseline area. The actual `tools/scoring.py` uses `clip(3500/(A+3000),0,1)` with public 500/4000 µm² anchors. The JSON field is misleading and contradicts the scoring policy. **Fix the JSON before Agent launch**, not just the Markdown. See `SPEC_JSON_CHANGE_REQUEST.md` for exact replacements.

**H2. `SPEC.json` still says missing calibration implies `score_valid=false`.** That is no longer true for a complete public preview. `score_result` explicitly computes public score components without calibration; official hidden evaluation still requires matching calibration. Fix the field description.

**H3. `REMOTE_SYNOPSYS.md` suggests public runs cannot get a valid score without calibration.** This contradicts the revised public grading behavior and can misdirect Agents. A replacement file is included. Ensure `README.md` and the initial prompt explicitly state that public, complete `architecture` previews yield score components and total score.

**H4. The new *private* Code Grade was not supplied.** There is no way to confirm that its policy SHA-256 is `62311a56189365e4c4202522e2b74558dbc75c87259432c568a63bbcddd424aa`, that it imports the mapped netlist rather than running Agent recipes, or that it preserves infrastructure failures. Validate the private package and run a matched end-to-end smoke before claiming official readiness.

## Engineering issues to verify

**E1. Long throughput sweep still needs real resource tests.** The current `tools/throughput.py` batches **eight** consecutive IIs at a time, down from 64 in an earlier version, records Python-process peak RSS, and probes 64–384 inclusive at 1,024 frames/II. This reduces the memory spike without reducing test coverage. The main regular streams still cover roughly **74 million simulated clock events** before extra tests; instrument actual simulator/container RSS, disk I/O and elapsed time. Python RSS excludes EDA subprocesses.

**E2. The ideal scales must be checked against an actual candidate distribution.** Mathematical checks show the new area term remains positive for all finite positive areas and gives half credit at 4,000 µm². This does **not** prove practical separation across submitted designs. Before starting official Agent comparisons, use independent pilot candidates to inspect the distribution of `score`, `components`, and the fraction at `0` or `1`. Avoid tuning anchors after official outcomes are known; any adjustment requires a new public/frozen benchmark revision.

**E3. Imported-netlist provenance is weaker than independent hardware verification.** The submitted manifest checks source/netlist/recipe/library content consistency; because the manifest originates from the Agent, it is **not** cryptographic proof that a stated DC/Yosys recipe was actually executed. The evaluator's structural checks, STA, and RTL/netlist comparisons are the actual safeguards. If the paper makes tool-recipe-provenance claims, require operator-trusted build receipts.

**E4. Incomplete/tool-failure results need external ranking safeguards.** Internal `score_valid` and `evaluation_outcome` distinguish `UNSCORED_INFRASTRUCTURE` and `INCOMPLETE` from `DESIGN_INVALID`. The external `resolved/score/reason` interface cannot carry an independent validity boolean. Ensure the ranking platform does not treat an infrastructure zero as the Agent's measured zero; log the detailed internal record and inspect `reason` semantics.

**E5. Backend fairness.** The current local path is Icarus/Verilator + Yosys/ABC + OpenSTA with **pre-layout** PPA, not full OpenROAD placement/routing. The commercial path uses VCS/DC/PT. Do not mix raw area/frequency or scores across backends in one official ranking. Official private grading is described as commercial; verify it in the private package.

## Verified scoring formula and sensitivity

The policy and implementation agree on:

- `area`: \(S_A=[3500/(A+3000)]_0^1\) for A in µm². It equals 1 at 500 µm² and 0.5 at 4,000 µm², remaining positive above both.
- `throughput`: \(S_T=[\ln(T/T_{\min})/\ln(240)]_0^1\), where \(T_{\min}=10^9/(384\cdot10)\) FFT/s and \(T_{\rm ideal}=62.5\times 10^6\) FFT/s.
- `latency`: \(S_L=[(300-L)/237]_0^1\), with \(L_{\rm ideal}=63\) cycles.
- `architecture`: \(S=0.60S_A+0.30S_T+0.10S_L\). `area` diagnostic uses area alone. Feasibility remains independent of score.

**Illustrative formula-only values (not synthesized FFTs):**

| Area (µm²) | Verified II | Certified period (ns) | Max first latency | S_A | S_T | S_L | S |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,000 | 64 | 3.00 | 130 | 0.700 | 0.547 | 0.717 | 0.656 |
| 4,000 | 384 | 10.00 | 300 | 0.500 | 0.000 | 0.000 | 0.300 |
| 6,000 | 256 | 4.00 | 200 | 0.389 | 0.241 | 0.422 | 0.348 |
| 9,000 | 384 | 10.00 | 300 | 0.292 | 0.000 | 0.000 | 0.175 |

The score remains sensitive to area above the half-credit anchor; nevertheless a single area weight of 0.6 means throughput improvements can still be outweighed by area regressions. Agents should evaluate **weighted component deltas**, not just raw PPA or percentages.

## Source behavior and testing detail

- `tools/scoring.py`: computes public score directly from `public_normalization` in `policy.json`; hides private-grade validity behind platform calibration; separate feasibility/quality status.
- `tools/throughput.py`: probes 321 integer II values, 1,024 frames each, with 8-II chunks and identity-bound caches. Selected II is confirmed on a representative 128-frame mapped subset with gap/reset probes; it is **the smallest passing tested II**, not a formal global minimum.
- `tools/implementation.py` and `tools/commercial.py`: custom synthesis exports and imports ASAP7 structural netlists, with trusted fixed constraints and independent checks. The hidden evaluator must still be checked separately.
- `profiles/PRE_REGISTERED.json`: its four recorded hashes match current supplied policy, report source, PDF, and builder. **Editing the public report or policy after this audit requires a new explicit freeze and corresponding hash updates before official runs**. Changes to SPEC also affect evaluation protocol cache identities.
- Python source compiled successfully; public-preview, hidden-missing-calibration and invalid-design scoring-path smoke tests passed using constructed measurement dictionaries; score function anchor/sanity checks passed. No shipped test suite or EDA executables were available for comprehensive runtime testing.

## Release checklist before starting official Agents

1. Fix outdated JSON scoring descriptions; propagate revised public Markdown and startup prompts uniformly.
2. Verify the *private FFT-Eval* policy, Code Grade status handling, and independent mapped-import behavior.
3. Run one known-valid RTL case and one custom-flow mapped export through real `check_env.sh`, public full evaluation and private smoke validation; separately test an invalid design and a forced license/tool failure.
4. Record full II sweep runtime, peak RSS including simulator subprocesses, disk usage, and an STA certificate on the actual Synopsys container.
5. Verify that agents receive identical public policy and equally scoped tool access, budgets, FFT-Bench revision, and independent workspace/mount.
6. If revising the frozen PDF/report/policy, publish a new revision with hashes before evaluated runs. Do **not** tune anchors after observing official Agent results.
