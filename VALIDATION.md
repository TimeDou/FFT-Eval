# FFT64-Quant v0.5 implementation validation

- The public toolkit passed 1,024 independent nonzero frames plus 192 directed cases, and a separate 1,024-frame mandatory continuous service test. Each frame remains 64 points.
- The accurate calibration designs and migrated reference submission each completed 8,192 independent random frames plus 192 directed cases. All 321 integer IIs from 64 through 384 received 1,024 consecutive RTL frames per design. Failed optional intervals are retained rather than failing mandatory feasibility.
- Representative mapped subsets were compared against RTL from three VCS time-zero initialization modes. Clock certification uses setup/hold-passing reconstraints on fixed mapped netlists. Mapping caches were reused only for matching RTL, library and physical flow.
- The open-source public flow was actually checked using Yosys/ABC, Icarus/Verilator and OpenSTA, including a passing fixed-netlist clock scan. Its data is separate from the commercial score; a full hidden open-source calibration campaign was not run.
- 75 operator regressions passed on host and native container Python. They include synthetic fixtures and are separate from the above real EDA measurements.

Detailed submission records, raw CSV/JSON, per-frame latencies and the immutable campaign source are on branch `Codex-GPT-6.1-Sol-Max`, under `evaluation/` and `RESULTS.md`. This is a migrated author reference, not a fresh independent agent rollout. Main holds the evaluator.

The campaign's immutable snapshot predates later deployment, open-source fallback, hint-validation and reporting refinements. The exact executed source is archived with the result, avoiding any claim that a different revision was measured. The frozen sample sizes, numerical method, scoring formulas and physical mapping settings remain explicit in the provenance.

All evidence is finite-sample. Physical metrics are pre-layout synthesis and ideal-interconnect STA, with no post-route, power or formal worst-case numerical claim.

## NumPy distribution update

The repository wheel was removed from both main trees. Existing NumPy is reused; a missing dependency is installed as a compatible binary from the pinned requirement through pip, with site mirror/offline-cache settings respected. The Docker wrapper delegates preparation to the same code and can use an external shared wheelhouse. No FFT numerical or hardware measurements were rerun for this packaging-only change.

82 operator regressions passed on the host. A fresh native Python 3.12 virtual environment, with no repository wheel and initially no NumPy, installed NumPy 2.2.6 from an external offline cache and then reused it without reinstalling. The real Docker environment check also passed using the external-cache option.
