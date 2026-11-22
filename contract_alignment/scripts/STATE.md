# Contract-alignment task state

The user asked to merge the current ChatGPT review and replacement Markdown from DSBench/chat-new-markdown.

Completed:
- Inspected all supplied material. Only AUDIT_REPORT.md, SPEC_JSON_CHANGE_REQUEST.md, START_CN.md and SYNC_MAP.md exist. The fourteen replacement files under revised/FFT-Bench referenced by SYNC_MAP are absent. Do not claim they were copied verbatim.
- Retained supplied START_CN prose in START_PROMPT, with proper heading levels, one sentence defining existing input range/RMS/reference, plus full equivalent English translation. Fixed SPEC scoring descriptions, SSH/README/optimization wording, task explanations, weighted-delta workflow/measurement fields and design-plan template.
- Scoring implementation, policy, anchors, weights, numerical/hardware/protocol fields, PDF/report/builder bytes unchanged. SPEC only changes four descriptive scoring strings; PRE_REGISTERED now also binds its new SHA.
- Policy SHA stays 62311a56189365e4c4202522e2b74558dbc75c87259432c568a63bbcddd424aa; new SPEC SHA ddb6077e204fde38ea6bb22cd5a3279abe6939124c443f8253e16f3ecb62f011.
- 136 tests PASS (/tmp/fft_contract_alignment_tests.log); added stale-SPEC calibration rejection and extended registration binding. Shared documents/runtime byte identity and Markdown links checked, git diff --check passes.
- Public main committed/pushed 4a31a2a5fd4edefeae70d35a91b5b914c50e029d; private main committed/pushed 5d54b562c59f45aef0bfacf2fe2a140a6ad21040.
- Four idle Agent workspaces were safely fast-forwarded to public main; all clean, no submission. No reset/deletion this turn and no unrelated process touched.

Native validation RUNNING:
- DSBench/Synopsys/contract_alignment/run_20261122_094646 (also /tmp/fft_contract_alignment_validation_path.txt).
- Frozen exact Git source snapshots engine_private (5d54b56) and engine_public (4a31a2a). Original operator container SSH1234; child processes detached with native status/driver.log. Driver PID115669, prefetch115670, sampler119819 (container namespace).
- Three parallel jobs: accurate SDF hidden, accurate folded hidden, custom streaming fixture rebuilt/exported fresh under actual public code then full public preview without calibration. 8192+192 hidden /1024+192 public frames, every321II with1024 frames plus mapped/STA checks. Full scans take roughly30-40min.
- Fresh custom DC build/export PASS, all3 STA certifications PASS (4.36328125/3.839599609375/1.2021484375 ns). Remaining long II scans.
- Driver generates fresh matching calibration, actually regrades matching native controls through private operator.cached_evaluate, rejects old calibration without relabeling it, builds/verifies private Code Grade packet identical to public scorer/policy/SPEC. No need for extra 10min full evaluation replay; cached operator path is deliberately recorded.
- source snapshot preparation initially chmodded optional ZIP attributes to0; fixed using actual git ls-tree mode bits before starting any job. Notes recorded, no experiment affected.
- process_resources.json samples measurement/prefetch trees incl EDA subprocesses, explicitly not exact container/cgroup peak. Runtime engine code not modified.

Remaining:
1. Monitor native status until COMPLETE; diagnose actual failures without canceling valid tasks or duplicating searches. Check driver.log and logs if needed. Keep commentary updates <=60 seconds.
2. Wait for sampler to mark COMPLETE, record disk_usage.json (du -sb run/measurements/custom_build etc; exact local scope).
3. Run maintenance/contract_alignment/collect_evidence.py --run RUN --out DSBench/FFT-Eval-agent-comparison/contract_alignment. Private comparison branch validation/three-agent-comparison currently8c051fe. Collector preserves raw compact metrics/logs/netlists/codegrade+source review, writes human report andCSV+FILE_MANIFEST. Do not overwrite old score_aware_protocol or historical pilot grades. Verify manifest, force-add only intended ignored command logs, commit/push append.
4. Create updated public source ZIP from FFT-Bench HEAD with all tracked Git files and exact Git-blob verification; preserve existing old packages. Consider also private review bundle with FFT-Eval current main plus separate new native evidence for H4 review. Keep private data out of public archive. Give user links and distinguish private audit bundle.
5. Final verify remote/main cleanliness, four workspaces source sync, source hashes, report links. Do not repeat broad tests unless new runtime changes justify it.
6. Final Chinese response: fixed stated4issues, preserved provided prose; same policy/algorithm unchanged; real private identity/packet/old-calibration rejection verified;136 tests+native scopes. Explain onlySTART_CN replacement present, remaining14 bodies missing so not falsely claimed. Include new commit IDs and updated review packages/readable report. New workspaces ready; no old history deletion this turn.

Native completion: all3 cases COMPLETE, exact private cached-operator calibration PASS, new grader packet source/policy/SPEC identity PASS, actual old calibration rejection PASS. Complete native runtime2030.6s. Collect/archive/package remaining.
