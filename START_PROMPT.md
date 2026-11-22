# Agent startup prompt

Use the same prompt and execution budget for every Agent. Start a new conversation in the FFT-Bench repository root.

## English

Read README.md, fft64_benchmark/TASK_EN.md, fft64_benchmark/SPEC.json and fft64_benchmark/SCORING.md. Design and optimize a complete FFT64 implementation in submission/. The default score is 0.60 S_A + 0.30 S_T + 0.10 S_L. Optimize the combined normalized hardware score rather than any single metric. All normalization functions and numeric targets are public in fft64_benchmark/profiles/policy.json. Use measured component scores, area, verified II, certified period and latency to guide revisions. Run check_env.sh and use the existing sibling Synopsys/ and port.txt environment. Preserve mandatory numerical, protocol, reset and timing specifications, and submit the best publicly verified candidate. The full architecture preview provides quantitative scoring feedback; hidden inputs are reserved for final evaluation.

## 中文

请阅读 README.md，以及 fft64_benchmark 下的 TASK_ZH.md、SPEC.json 和 SCORING.md，在 submission/ 中设计并优化完整 FFT64。默认目标为 0.60 S_A + 0.30 S_T + 0.10 S_L，请优化归一化综合硬件分数。归一化函数和全部数值目标已在 profiles/policy.json 公开。依据实测分项分数、面积、验证 II、认证周期与延迟选择下一轮优化。先运行 check_env.sh，使用同级 Synopsys/ 和 port.txt 所指定的已有环境。满足数值、协议、复位和时序约束，提交公开验证通过的最佳候选。完整 architecture 公开评测可直接给出评分反馈；隐藏输入仅用于最终评价。
