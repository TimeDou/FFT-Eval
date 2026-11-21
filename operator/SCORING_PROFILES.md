# Running the frozen scoring profiles

Default, compatible with the original fixed-service FFT64 task:

```bash
bash run_synopsys.sh /workspace/submission --profile area --out /workspace/eval/area
```

Architecture/throughput task:

```bash
bash run_synopsys.sh /workspace/submission --profile architecture --out /workspace/eval/architecture
```

For local SSH Docker replace `run_synopsys.sh` with `run_synopsys_docker.sh`. The host submission path is copied into a private shared snapshot; `--out` is a container path under the shared mount, for example `/mnt/mydata/eval/my_architecture_run`. No password is stored. Existing VCS/DC/PrimeTime/LC are used.

Architecture submissions declare an integer `frame_ii_cycles` in `design_config.json` (64–384, default 384). Baseline calibration searches all integers with a small qualification workload and strictly validates the selected interval on the full workload and three mapped initial states. Candidates strictly validate their declaration. The reported interval is an empirical achievable service bound, not a formal global minimum.

Both profiles use the same DC mapped netlist and area. A physical mapping cache is independent of scoring policy, profile and input seed. A content hash covers RTL, physical scripts, libraries, DC/PT launchers and formal mode. A file lock prevents duplicate mappings across profiles. Scored-run caches additionally include profile, policy, declared II, input protocol and evaluator identity. Different scoring calibrations never share normalization anchors. Specification upgrades automatically get a separate default protocol without deleting the old protocol.

The new common physical flow includes the documented DC `compile -incremental_mapping -only_hold_time` after area mapping. This is needed because the previous version left a 1.17ps input-to-register hold violation on the accurate folded implementation. Both accurate baselines and all candidates receive the same repair. New areas include the repair cells. Old checkpoints and v0.3 results remain intact.

`frequency_certificates/` records actual PrimeTime reconstraints and timing updates on a fixed mapped netlist. Every trial reports requested and actual period plus setup/hold slack. The final certificate uses a passing clock, with a measured failing clock less than 0.01ns faster. No single-clock slack-derived Fmax enters scoring.

Output includes separate area/throughput/latency components, calibration targets and their accurate-baseline source, verified II, certified period/frequency, effective FFTs/s and samples/s, first-output latency at the common 10ns clock, and latency at the certified clock. Raw strict simulations, failed II pilots, STA traces and hashes remain available. Area mode leaves frequency/throughput score fields blank because no capacity measurement is needed.

The normalization vector and weights were registered in `fft64_benchmark/profiles/` before measuring new candidates. Full equations are in [SCORING.md](../fft64_benchmark/SCORING.md). SQNR is a hard constraint, never a bonus. Feasible zero-score designs pass. Missing tools/calibration/certification remain unscored.

To collect a completed run into a small, portable report without changing its raw experiment:

```bash
python3 operator/collect_native_results.py /host/shared/eval/run \
  --shared-dir /host/shared --container-share /mnt/mydata \
  --out operator/results/my_new_run
```

All physical measurements here are synthesis cell area and ideal-interconnect STA, not post-route area/timing, power or silicon Fmax. The provided R2SDF reference is frame-isolated; its measured II must not be presented as a limit of the R2SDF architecture family.

The small DSBench attachment keeps the legacy filename `area_reference.json` for the selected profile calibration. The embedded `profile` and policy hash determine its meaning; an architecture calibration is not an area-profile denominator. Use `grading/make_grader.py --profile architecture --calibration ...` for that task.
