# FFT64-Quant | EDA Agent Benchmark

本任务要求 Agent **从零设计并优化一个完整的 64 点定点复数 FFT**。不提供已经实现的 FFT RTL；Agent 可以探索 SDF、MDC、folded 等架构，以及明确的截断、舍入和精度分配策略。任务重点是满足功能与数值约束后，基于**完整硬件测量**自主改进面积、持续吞吐率和首次输出延迟。

## 开始任务

从本仓库根目录执行：

```bash
bash fft64_benchmark/setup.sh --check-only
bash fft64_benchmark/run_preview.sh submission runs/quick --quick --no-build
bash fft64_benchmark/run_preview.sh submission runs/full --no-build
```

先阅读 [中文任务](fft64_benchmark/TASK_ZH.md) / [English task](fft64_benchmark/TASK_EN.md)、[机器规格](fft64_benchmark/SPEC.json) 和 [背景报告](docs/FFT64-Quant.pdf)。平台优先使用可用的 Synopsys 工具；否则使用已安装的开源仿真、综合和 STA 工具。首次测量前建议 `--check-only`，避免不必要的软件重装。

## 通过与评分

所有必选规格通过即 `resolved=true`，**不要求最低面积节省比例**。默认 `architecture` 分数为：完整映射面积 60%、经过连续帧验证的有效吞吐率 30%、实测最大首输出延迟 10%。非零帧 SQNR 必须不低于 50 dB，但更高 SQNR 不加分。没有同后端的有效校准时，只能提供开发反馈，不能宣称官方有效分数。

详细定义请见 [SCORING.md](fft64_benchmark/SCORING.md) 和 [EVALUATION.md](fft64_benchmark/EVALUATION.md)。

## 提交内容

- `submission/rtl/`：自包含、可综合的 `fft64_top` 及其模块
- `submission/DESIGN_PLAN.md`：当前设计假设、关键决策及其测量依据
- `submission/measurements.csv`：主要候选的实际测量结果
- `submission/design_config.json`：可选配置说明；`frame_ii_cycles` 只是提示，**不决定官方吞吐率分数**

Agent 的成绩由可信评测结果决定，不因尝试次数或报告篇幅增加而加分。公开仓库不含准确校准 RTL、隐藏测试种子或出题方结果；这些仅保存在隔离的 FFT-Eval 私有环境中。
