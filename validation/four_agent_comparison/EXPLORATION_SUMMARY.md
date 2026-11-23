# 四个 Agent 的探索流程摘要

作者按任务要求保存的原始文字/表格在 `exploration_records/<实验标签>/DESIGN_PLAN.md`，原始测量表在同目录 measurements.csv。没有把含 RTL/网表的完整聊天放入此包；完整可见聊天保存在相应私有结果分支。

## DS-Flash：先修正确性，再做少量实现微调

R2SDF 初始假设 → 修正 delay depth、相位计数和帧间推进 → 平衡系数 mux 并提前注册 → 试 20-bit buffer（数值格式实施问题导致失败）→ AND-mask reset 与常数级专用化 → clock target sweep → 在两个完整 architecture 结果中选择最高分。

作者测量表有 11 行，完整 architecture 评测 2 次。它确实理解了综合评分，也比较了 700/550 ps 的面积–时序权衡；主要欠缺是架构与有效精度方向没有充分展开，而非“没有看见权重”。

## Codex 6.1：较广的架构与算术/数值路径

一 BU folded 的数值 screen（截断失败，舍入后通过）→ 两 BU / 四 bank folded → streaming SDF → 提早自然序输出、降低 twiddle precision → R2² pairing → 精度/nearest-even 分配 → 系数与三乘积流水 → one-hot reorder → 再窄化最终存储（面积/评分反而变差）→ 选择已完成最高分 C005。

作者测量表有 28 行，完整 architecture 评测 11 次。它保留了数值失败、面积 diagnostic、完整评分的区别，并没有选择面积最小或频率最高的任意单项结果。

## Codex 6.2：结构替换优先，随后联合量化与流水

R2² DIF + 输出 buffer baseline → DIT + 输入 49-word bit swaps → 三实乘法、分级量化及 clock steering → 利用输入幅度缩整数冗余、重新配置分数位与 twiddle → split-product 流水（更快却分数降低）→ 残余角表示 → retiming（同样因面积代价放弃）→ area recovery → 删除两个重排输出寄存器 → 提交最高分。

作者测量表有 22 行，完整 architecture 评测 10 次。它的主要成功来自结构/数据表示和按综合分拒绝过度流水，不能将所有改善归于某一条 DC 命令。

## Opus：更长的跨层迭代，最后进入局部收益平台

R2³SDF 架构选择 → 反馈和重排的数值模型 → 精确极性编码 → 范围感知位宽/分级精度 → 多种旋转器与流水 sweep → 控制器注册 → W8 手动流水及负号/选择合并 → 多个时序目标 → ungroup 与恢复 pass → 最终网表导出及重复确认。

作者表有 37 行，另保存 126 份开发摘要及一个初始原始开发点；8 次完整 architecture 评测对应 6 个不同实现。开发点不等于完整可行点，确认运行也不算新增改善。实际路径与后期收益详见 OPUS_ITERATIONS.md。

## 如何使用这些记录

`exploration_public_candidates.csv` 汇总四者全部已完成的公开 architecture 点；`strategy_evidence.csv` 给出有解释意义的配对差值。候选数量不是计算预算，也不是策略质量本身：Opus 在首次完整评分前已经做了较多开发优化，另外三者的 screen 和完整评测安排不同。对照的价值在于它们如何用观测修改假设、是否正确放弃无收益方向。
