# 本轮最终 Agent 电路比较

阅读 [RESULTS.md](RESULTS.md)；原始指标位于 [final_metrics.csv](final_metrics.csv)。

`cases/<Agent>/` 包含精确的最终提交、真实独立隐藏评测记录、公开探索证据、可见聊天 JSON 和计时来源。对单个 case 可在其原始 Agent 分支运行 `python3 agent_evaluation/verify_evidence.py`；此处也可在 NumPy 可用时运行 `python3 cases/<Agent>/agent_evaluation/verify_evidence.py`。

`published_branches.json` 固定对应的私有分支 commit。`provenance/` 保存共同协议、校准身份、工具/库及执行记录；文件中的原始容器绝对路径是来源记录，不要求归档后仍是运行路径。`reproduction/` 是本次收集分析脚本，其原 campaign 路径需按本地部署设置；不应将其误作可替代正式 EDA 评测的脚本。

完整 321-II 汇总、分批日志、时序扫描 trace、netlist、隐藏实际输出 NPZ 均保留；重复编译产物和逐周期 text 未入库，原件仍在 provenance 指向的本地 campaign。

后续参测模型的结果、总体模型能力结论、最终排名和统计显著性仍为空，不以 PENDING 记零分。
