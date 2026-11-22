# FFT64-Quant: Architecture, Precision and Synthesis-Flow Co-Design

Technical report

## 1. Purpose and design problem

FFT64-Quant evaluates an EDA Agent's ability to design and improve a complete fixed-point FFT processor. The Agent receives a mathematical and cycle-accurate contract, architecture guidance, standard-cell libraries and public measurement tools. It constructs its own RTL; a working FFT implementation is not provided in the public task.

The problem has three coupled design dimensions: FFT architecture and scheduling; numerical precision and quantization; and synthesis optimization, Boolean rewriting and technology mapping. A successful design must satisfy the same numerical and transaction requirements as competing designs. Its hardware quality is determined by independent measurements of the complete circuit, including storage, arithmetic, control and reordering.

This report defines the task and measurement method. It reports no winning implementation, area improvement, post-route result or measured silicon frequency. The machine-readable specification and scoring policy accompany the report; their content hashes identify the configuration used for each experiment.

## 2. FFT computation and hardware alternatives

The required transform is the forward, unscaled complex discrete Fourier transform:

$$
X[k]=\sum_{n=0}^{63}x[n]\,e^{-j2\pi nk/64},\qquad 0\leq k<64.
$$

A radix-2 decomposition has six algorithmic stages with 32 butterfly operations per stage: 192 butterfly operations per transform. This operation count does not specify the number of physical butterfly units. Hardware can reuse an arithmetic unit over time or implement many operations concurrently. Input/output permutation, memory access conflicts and scheduling must be included in the implementation.

| Architecture | Organization | Main trade-off |
|---|---|---|
| R2SDF | One pipeline with delay feedback | Regular streaming; feedback storage and stage arithmetic |
| R2-squared SDF | Paired radix-2 stages with specialized rotations | Fewer nontrivial rotations; alignment and coefficient control |
| R4MDC or other MDC | Parallel paths and commutators | More internal parallelism; routing, buffering and serial I/O adaptation |
| Folded or iterative | One or a few reused butterfly units | Less duplicated arithmetic; memory ports, scheduling and latency |
| Fully parallel | Many spatial arithmetic units | Shorter computation at potentially much higher complete area |

All architectures have the same one-complex-sample-per-cycle external interface. More internal parallelism therefore does not, by itself, establish a throughput advantage. Required buffering and natural-order output conversion count toward area and latency.

Quantization also interacts with architecture. Stage-dependent data widths affect arithmetic, registers and feedback storage; twiddle precision affects rotation cost and error. Trivial rotations by 1, -1, j and -j can be specialized exactly. Quantization errors must be assessed at the complete FFT output rather than added as independent local error budgets.

## 3. Functional and numerical contract

| Item | Requirement |
|---|---|
| Transform | 64-point complex forward FFT, unscaled, natural-order input and output |
| Input format | Signed 16-bit real and imaginary components, each with 15 fractional bits |
| Tested input domain | Each component in [-0.5, 0.5]; nonzero frames have complex RMS at least 1/32 |
| Output format | Signed 24-bit real and imaginary components, each with 15 fractional bits |
| Input frame | 64 consecutive valid input cycles, one complex sample per cycle |
| Mandatory service | Accept frames whose starts are 384 cycles apart, and legal longer gaps, without backpressure |
| Output frame | 64 consecutive valid frequency bins; out_start marks the first bin |
| Clock and reset | Single rising-edge clock; synchronous active-high reset aborts inflight work |
| Timing | 10 ns target clock, setup and hold both passing |
| Latency | First output between cycles 63 and 300; last output no later than cycle 364 |
| Numerical quality | Every evaluated nonzero frame has SQNR at least 50 dB; zero input produces exact zero |

The first input edge is cycle 0. Inputs are sampled at rising edges; outputs are observed after their corresponding edges. A valid first output cannot precede the last required input. Reset is tested during input capture, processing and output, and later transactions must recover correctly. The RTL interface document specifies the exact port names and behavior.

The numerical reference is a float64 FFT of the same already-quantized input. Input quantization is not counted a second time as circuit error. For each nonzero frame f:

$$
\mathrm{SQNR}_f=10\log_{10}\!\left(\frac{\sum_k|X_f[k]|^2}{\sum_k|\hat{X}_f[k]-X_f[k]|^2}\right).
$$

Numerical feasibility uses the minimum frame SQNR, not average frame dB or a pooled error ratio. No fitted output gain, phase, permutation or scale is allowed. SQNR is a feasibility constraint; exceeding 50 dB earns no additional score. All conclusions concern finite tested inputs and do not establish a formal worst-case error guarantee.

## 4. Agent design space

Agents may choose the FFT architecture, scheduling, memory banking, resource sharing, exact constant specialization and legal pipelining or retiming. Numerical approximation is limited to explicit fixed-point precision and quantization operations, including stage or instruction widths, twiddle precision, truncation, rounding and quantization boundaries. The external transform and interface remain fixed.

Gate-level approximate logic synthesis, arbitrary approximate Boolean pruning, unrelated approximate compressors, simulation-only implementations, input-data lookup cheats and uncounted external memories are excluded. Standard-cell storage has a real mapped cost; there is no free SRAM model.

Agents can also optimize EDA recipes. The provided templates are starting points, not a closed set of presets. Candidate changes may include compile effort, area/timing optimization targets, resource sharing, hierarchy, exact Boolean rewriting and mapping strategy. Commands supported by the installed tool must be checked in that environment. ABC rewrite/resyn2-style sequences belong in the ABC script rather than as Yosys top-level passes.

## 5. Agent-controlled synthesis and independent measurement

Public construction and final measurement have different roles:

| Step | Executed operation | Result |
|---|---|---|
| Public construction | Agent edits DC, Yosys or ABC optimization recipes and runs available tools | Complete mapped standard-cell netlist, manifest, recipe copies and development reports |
| Independent import | Evaluator reads the structural netlist with the supplied library | Legal-cell checks and a canonical representation of the same mapped circuit |
| Hardware measurement | Evaluator counts cells and applies its own timing constraints | Complete mapped area and setup/hold results |
| Behavioral verification | Evaluator compares RTL and mapped transactions on representative inputs | Output values, valid/start cycles, reset recovery and selected-II confirmation |
| Scoring | Evaluator combines validated measurements with frozen calibration | Feasibility and, when calibrated, continuous hardware score |

The editable files are flow/dc_opt.tcl, flow/yosys_opt.ys and flow/abc_opt.script. DC begins after elaboration, link and initial constraint loading; Yosys begins after reading the RTL and libraries. The wrapper completes structural export. A candidate may use a different synthesis target to guide optimization, but final library and STA constraints are chosen by the evaluator.

The submission includes RTL and, for custom synthesis, implementation/mapped.v and implementation/manifest.json with the corresponding flow files. An exported implementation is imported without resynthesis or automatic hold repair. This preserves the submitted mapping, including implementations produced by Yosys and later measured with DC/PrimeTime. A custom implementation must pass final setup and hold checks itself. Without a custom recipe or export, the provided default synthesis applies; default DC mapping includes incremental hold repair.

The private evaluator never executes candidate Tcl, Yosys or ABC recipes, and never adopts candidate-reported area, SDC, frequency or SQNR. It uses the trusted cell models, libraries, numerical reference and measurement scripts. RTL/manifest checks are followed by independent cell, timing and behavior verification.

Manifest hashes establish content consistency, not independently authenticated build provenance. An Agent can write its own manifest. If a research claim requires proving that a particular recipe actually generated a netlist, a controlled build service or operator-held execution record must bind the source, recipe, tool binaries, commands and output. Hash checks alone do not provide that proof.

Public SSH containers are development environments. Hidden seeds, calibration, accurate reference RTL and other Agents' submissions must be stored outside their accessible filesystems. The development transport and private grading transport have separate roles.

## 6. Verification workload

The FFT length remains 64 in every test. Increasing the number of frames increases the number of independently observed transforms; it does not change FFT length.

| Test | Workload | Interpretation |
|---|---|---|
| Public numerical | 1,024 independent nonzero random frames plus 192 directed frames | Public numerical development checks |
| Hidden numerical | 8,192 independent nonzero random frames plus 192 directed frames | Independent final numerical feasibility |
| Mandatory service | At least 1,024 consecutive frames at II=384, plus gap/reset probes | Long-stream protocol and maximum observed per-frame latency |
| Capacity scan | Every integer II from 64 through 384, each with 1,024 consecutive RTL frames | Smallest observed passing interval in the tested range |
| Mapped numerical/protocol | Representative subset, including 64 random and directed frames | Same RTL/netlist payload and transaction timing |
| Selected-II confirmation | 128 base frames with additional gap/reset probes | Representative mapped confirmation of the selected interval |
| Clock certification | Reconstraint and STA update on one fixed mapped netlist | Passing setup/hold endpoint and a passing/failing period bracket |

Random numerical families include bounded complex uniform and clipped Gaussian inputs and sign-sensitive low-RMS inputs. Directed cases include zero, DC, impulses, tones, multitone, OFDM-like inputs and quantization boundaries. Generation and rejection occur after input quantization so that tested nonzero frames satisfy the declared RMS domain. Public and hidden seeds are separate. The input-generator implementation defines the exact distributions.

The capacity scan selects 1,024 frames reproducibly and applies the same selected frames at every tested II. It probes all 321 integer intervals; a claimed frame interval is only a hint. Optional faster intervals may fail without invalidating mandatory II=384 service. The selected shortest passing interval receives additional mapped confirmation. This establishes empirical capacity over the tested streams, not a proof of globally minimal II.

To bound memory, at most eight II values are batched together. Regular schedules use preallocated arrays, preserving every input sample, reset cycle, frame start and trailing idle cycle. Batch size is an execution setting: it does not reduce the tested II set or frames per interval. Chunk-level checkpoints, input identities, resource records and progress files support recovery without silently reusing unrelated results.

Commercial gate tests compare RTL and mapped transactions from three time-zero binary register initialization modes: all zero, all one and a recorded random seed. There is no forcing or repair during normal operation. These tests help detect reset and unknown-state problems but are not a formal sequential-equivalence proof. Optional formal checking is reported separately. The large hidden RTL dataset must not be described as an equally large mapped-netlist test.

## 7. ASIC flow and measured quantities

All candidates in a scored campaign use the same ASAP7 RVT/TT combinational and sequential libraries and the same measurement assumptions: a 10 ns clock, 0.1 ns setup uncertainty, 0.02 ns clock/input transition, zero external I/O delay and 1 fF output load. Normal-operation frequency analysis excludes reset paths; reset remains a functional requirement. Library-native time and capacitance units are checked explicitly.

The commercial development backend uses VCS, Design Compiler and PrimeTime. The open-source development/operator backend uses Icarus or Verilator for simulation, Yosys/ABC for mapping and OpenSTA for timing. This is a pre-layout flow, not an OpenROAD place-and-route implementation. A backend is not switched after a tool or license failure during a run.

The official DSBench Code Grade attachment requires commercial calibration. The presence of a general open-source fallback does not make the official attachment a backend-switching grader. Separate backend calibrations and measurement identities are required; raw PPA and normalized scores from different backends must not be mixed.

Area is the sum of approved mapped library-cell areas over the complete top-level design. Registers, buffers, standard-cell memories, control, multiplexing, arithmetic and reordering are included. Imported library model redefinitions, foreign cells and unsupported clocks are rejected through the structural import and technology checks.

The certified period is the passing endpoint of a setup/hold STA scan on the same fixed mapped netlist. A passing/failing bracket is refined to at most 0.01 ns unless the configured scan floor is reached. A slack value from one 10 ns run is not, by itself, a certified maximum frequency.

$$
T_{\mathrm{eff}}=\frac{10^9}{II_{\mathrm{ver}}P_{\mathrm{STA}}}\quad\mathrm{FFTs/s},\qquad P_{\mathrm{STA}}\ \mathrm{in\ ns}.
$$

First-output latency is the maximum observed delay from a frame's first input to first valid output. Frame-completion latency is also checked per frame. The latency score uses cycles at the common 10 ns clock; frequency contributes to the score through effective throughput only once.

Current QoR is pre-layout mapped area and ideal-interconnect STA. Optional Innovus scripts require matched LEF, RC, site and power assets and do not contribute to the score. There is no post-route, power, energy or silicon-frequency claim.

## 8. Feasibility, calibration and hardware-quality score

Feasibility and optimization quality are separate. A demonstrated failure of a mandatory numerical, RTL, protocol, timing or mapped-netlist requirement is a design violation. A feasible design can receive a score of zero; there is no minimum area reduction or minimum quality score required for resolved=true.

For a feasible design, normalize measured area, throughput and first-output latency to [0,1]:

$$
S_A=\operatorname{clip}\!\left(\frac{A_{\mathrm{ref}}-A}{A_{\mathrm{ref}}-A_{\mathrm{goal}}},0,1\right),\qquad A_{\mathrm{goal}}=0.5A_{\mathrm{ref}}.
$$

$$
S_T=\operatorname{clip}\!\left(\frac{T_{\mathrm{eff}}-T_{\mathrm{req}}}{T_{\mathrm{goal}}-T_{\mathrm{req}}},0,1\right),\qquad T_{\mathrm{req}}=\frac{10^9}{384\cdot 10}.
$$

$$
S_L=\operatorname{clip}\!\left(\frac{300-L}{300-L_{\mathrm{goal}}},0,1\right).
$$

The general weighted hardware objective is:

$$
S=\alpha S_A+\beta S_T+\gamma S_L,\qquad \alpha+\beta+\gamma=1.
$$

The default architecture profile fixes alpha=0.60, beta=0.30 and gamma=0.10. The independent area diagnostic profile uses area alone. These profiles have distinct calibration and cannot be mixed in one ranking. The weights are not retuned after seeing evaluated Agent results.

Two accurate fixed-point designs, R2SDF and folded radix-2, are measured with the default mapping recipe before scoring. The area reference is their smaller validated area. The throughput goal is twice their higher verified throughput. The latency goal is the greater of half their shorter maximum first-output latency and 63 cycles. These component-wise anchors form an envelope; they need not be one physical circuit. Candidate synthesis recipes may differ, while the independent measurement method remains common.

Calibration binds the selected backend, libraries, tools, protocol, measurement scripts and policy. Changes require a matching calibration rather than silently applying an old denominator. Completed experiments retain their original source and policy identities. Report, policy and source hashes are consistency records; freezing those bytes is not a substitute for verifying their technical content.

## 9. Outcomes and reproducible evidence

The platform result has exactly resolved, score and reason. Detailed internal records retain score_valid, per-frame quality, measured II, certified period, full area, source/library/tool hashes and raw execution logs.

| Outcome | Meaning | Ranking treatment |
|---|---|---|
| Feasible | All mandatory hardware checks completed and passed | Score is valid only with matching frozen calibration |
| DESIGN_INVALID | Observed violation attributable to the design | Valid zero score |
| UNSCORED_INFRASTRUCTURE | Missing tools/calibration, license fault, timeout, crash or incomplete measurement | Exclude and diagnose; not a measured zero-performance design |
| INCOMPLETE | Quick-only or unfinished evaluation | No final score |

The three-field interface has no separate score_valid field. For infrastructure or incomplete results the reason prefix carries that distinction. The external ranking system must honor it and retain the detailed records. Benchmark code cannot, by itself, establish how an external service handles that result.

Submission-document completeness is reported separately and does not change electrical feasibility or the numerical hardware score. Design plans and measurement tables support analysis of Agent decision making; report length and experiment count earn no bonus.

Reproduction requires the final RTL, custom recipes and exported netlist when used, input-generator identities and seeds, backend and executable/library hashes, scoring calibration, measured transaction results, STA certificate and execution receipts. Regression fixtures, real tool smoke tests, complete FFT validation and formal proofs are different evidence levels. A source-only checkout does not contain every measurement stored in separate private result branches or directories.

Use the same frozen task, libraries, measurement flow, scoring targets and execution budget for all Agents in a campaign. The final question is whether the Agent can explain and improve a verified hardware implementation through architecture, numerical and EDA-flow choices under a common contract.

## 10. Files and reproduction

The report source is docs/FFT64-Quant.md. Run python3 docs/build_report.py with the optional documentation dependencies to regenerate docs/FFT64-Quant.pdf. SPEC.json and profiles/policy.json under fft64_benchmark contain the executable contract. Task, interface, optimization, evaluation and scoring Markdown files provide the corresponding development instructions. profiles/PRE_REGISTERED.json records report, report-source, builder and policy hashes.
