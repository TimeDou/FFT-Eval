# FFT64 四实验结果审核包

当前样本固定为 Claude-DS-Flash、Codex-GPT-6.1-Sol-Max、Codex-GPT-6.2-Sol-Max、Claude-Opus-5.5。Fable 因网络问题未开展，不列入评分。

建议先读 [RESULTS.md](RESULTS.md)，其中已包含详细策略分析，再读 [EXPLORATION_SUMMARY.md](EXPLORATION_SUMMARY.md) 和 [OPUS_ITERATIONS.md](OPUS_ITERATIONS.md)。STRATEGY_COMPARISON.md 是主报告策略章节的独立副本，无需重复阅读；精确数值在 CSV/JSON。

本包提供汇总数据、方法描述、结论和 PDF/PNG 图，方便审核、润色和总结。**不包含 RTL、mapped netlist、设计生成脚本、EDA recipe、原始聊天或隐藏输入/输出向量。** 原样设计及完整验证证据保存在私有 FFT-Eval 的各 Agent 分支，定位哈希见 provenance.json。

## 文件导航

- `RESULTS.md`：四份最终电路、评分差异、方法分析与可支持结论。
- `STRATEGY_COMPARISON.md`：按架构/状态、数值格式、旋转器/流水、技术库/综合逐项解释优劣；内容已收入主报告。
- `EXPLORATION_SUMMARY.md`：四个 Agent 如何提出假设、试验、接受/拒绝和停止的流程摘要。
- `exploration_records/<Agent>/DESIGN_PLAN.md` / `measurements.csv`：作者保存的原始探索文字和表格，代码块若存在则省略。
- `DOCUMENT_NOTES.md`：原始记录中需修正或限定的解释，包括 DS-Flash 的窄 buffer 数值格式问题。
- `strategy_evidence.csv` / `exploration_public_candidates.csv`：21 组有解释意义的对照、31 个完整公开评测点；原始来源哈希另存。
- `OPUS_ITERATIONS.md`：Opus 迭代、负结果和后期边际收益。
- `SCORING_AND_PROTOCOL.md`：固定评价规格、单位和公式。
- `final_metrics.csv/json`：独立核验后的最终指标；`public_vs_hidden.csv` 对比公开和隐藏结果。
- `quality_statistics.csv` / `quality_by_family.csv`：隐藏数值统计；主约束始终是最低逐帧 SQNR。
- `opus_public_iterations.csv/json`：8 次完整公开自测；确认运行与新实现分开标记。
- `opus_authored_experiments.csv`：37 行作者整理记录；`opus_development_trials.csv`：126 份开发摘要，未资格评测的分数为空。
- `dialogue_times.csv` / `opus_dialogue_time_metadata.json`：用户记录用时与原始日志时间口径。
- `figures/`：四设计硬件/评分、面积–吞吐权衡、Opus 收敛轨迹、时长和数值余量。
- `provenance.json`：固定代码和数据哈希、私有分支定位信息。

最终四个设计的成绩来自独立隐藏验证；Opus 中间点按用户授权采信自测，没有重新跑全部中间实验。运行时长不同、每模型单次运行，因此应把交付电路的比较与模型总体能力结论分开。

## 复现图表

安装 NumPy 和 Matplotlib，在本目录执行：

```bash
python3 reproduce_figures.py .
```

该脚本只读表格并绘图，不生成电路或调用 EDA。图表重新生成后，原始包中的文件哈希自然不再适用于新生成的文件。
