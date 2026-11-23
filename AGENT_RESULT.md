# Claude-Opus-5.5：最终 FFT64 实验

最终提交已独立通过同一隐藏协议，正式分数 **0.756862621**。面积 1970.57448 μm²，认证周期 0.526123046875 ns，验证 II=64，最大首/末输出 122/185 cycles，最低隐藏逐帧 SQNR 52.558071243 dB。

用户记录用时 **6h30m**。原始会话跨夜，含较长无事件间隔；原始时间、后段观察窗口及人工停止指令分别保留，不能据整个消息跨度估计计算耗时。

采用 R2³SDF DIF、范围感知位宽、两个常数 W8 旋转器和一个通用 W64 旋转器，结合精确极性编码、手动流水及综合恢复。全部 PPA 为 pre-layout / ideal-interconnect STA；质量和门级一致性是有限样本证据。

- [原样最终提交](submission/)，[作者设计说明](submission/DESIGN_PLAN.md)。
- [正式测量](agent_evaluation/measurement/result.json)、[评分](agent_evaluation/grade.json)、[全部 II 观测](agent_evaluation/measurement/throughput/long_intervals/probe_results.json)。
- [聊天 JSON](conversation/conversation.json)、[日志与计时来源](conversation/metadata.json)。聊天导出省略内部推理和 provider 请求内容。
- [37 行作者记录及中间数据](search_data/)、[公开评测原始证据](runs/)、[开发记录和源码](public_evidence/)。中间结果按用户要求采信自测，未独立重跑，不把开发估计当作正式分数。
- [运行元数据](run_metadata.json)、[归档哈希](CURRENT_RUN_MANIFEST.json)。

复核已保存的数值、输入身份、网表哈希和评分（需要 NumPy；不重新运行 EDA）：

```bash
python3 agent_evaluation/verify_evidence.py
```

当前四实验统一报告位于 `validation/final-agent-comparison` 分支的 `validation/four_agent_comparison/RESULTS.md`。审核包只包含总结、数值与图，不包括此处的 design 和聊天代码。
