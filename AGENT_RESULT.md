# Codex-GPT-6.2-Sol-Max: 本轮最终 FFT64 提交

原样提交位于 [submission/](submission/)。本轮独立隐藏评测通过；对应电路和综合 recipe 未由核验者修改。以下是一次运行的实测设计结果，不是模型总体能力结论。

| 指标 | 本轮实测 |
|---|---:|
| 基本规格 / 有效正式评分 | PASS / true |
| 综合硬件分数 | **0.716134144** |
| 完整 mapped area | 2327.201280 μm² |
| 顺序 / 组合单元面积 | 1370.315880 / 956.885400 μm² |
| 认证周期 / 频率 | 0.640380859375 ns / 1561.570721 MHz |
| 最小连续帧验证 II | 64 cycles/frame |
| 认证时钟的持续能力 | 24399542.508578 FFT/s |
| 最大首输出 / 整帧完成 | 126 / 189 cycles |
| 最低隐藏逐帧 SQNR | 59.416946513 dB |
| 面积 / 吞吐 / 延迟分项 | 0.657005399 / 0.828377277 / 0.734177215 |
| 用户提供对话用时 | 37m15s (2235 s) |

FFT64，外部 P=1，ASAP7 RVT/TT，VCS/DC/PrimeTime，布局前完整 cell area 与 ideal-interconnect STA。强制时钟 10 ns、逐非零帧 SQNR≥50 dB；更高 SQNR 不奖励分数。额外的频率扫描始终使用同一网表。首输出延迟分项使用共同 10 ns 时钟。

隐藏数值测试为 8192 个独立随机非零帧及 192 个定向帧。321 个整数 II（64–384）各验证 1024 连续 RTL 帧，并对所选最小 II 做代表性 mapped 检查；包含复位、间隙及 0/1/20261121 三种门级初始状态。结果不构成 formal worst-case error guarantee，也没有 post-route 或可靠功耗结论。

- [完整原生 measurement/result.json](agent_evaluation/measurement/result.json) 与 [grade.json](agent_evaluation/grade.json)。
- [全部 II 观测](agent_evaluation/measurement/throughput/long_intervals/probe_results.json)。
- [真实隐藏输入/输出与 replay 说明](agent_evaluation/numeric_evidence/observation.json)。
- [完整可见聊天 JSON](conversation/conversation.json)、[计时及日志来源](conversation/metadata.json)、[初始提示](conversation/initial_prompt.txt)。
- [Agent 原始设计说明](submission/DESIGN_PLAN.md)、[公开探索记录](runs/)、[对应受测快照与探索源码](public_evidence/)。
- [本轮身份与时长](run_metadata.json)、[文件哈希](CURRENT_RUN_MANIFEST.json)。
- [先前 pilot 原样存档](archive/pilot_before_score_aware_restart/)，旧分数不与本轮混用。

对话导出包括可见消息及工具调用/结果，省略内部推理和系统上下文。用户提供的用时与日志的消息区间、平台任务计时分别保留；6.2 的平台任务计时为 2247.314 s，与用户给出的 2235 s 相差 12.314 s。硬件评分不含对话或 EDA 用时。

在仓库根目录安装 NumPy 后可执行以下证据复核；该命令重新生成输入并重算已保存输出的质量和评分，不重新运行商业 EDA：

```bash
python3 agent_evaluation/verify_evidence.py
```

跨设计比较见私有仓库分支 `validation/final-agent-comparison` 的 `validation/final_agent_comparison/RESULTS.md`。后续模型结果、总体模型结论和最终排名仍留空。
