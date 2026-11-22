# FFT64-Quant：EDA Agent 硬件设计 Benchmark

FFT64-Quant 要求 Agent 从公开规格出发，实现一个完整、可综合的 **64 点定点复数 FFT**，并根据真实电路测量改进架构、数值精度与综合策略。任务提供接口、测试工具和设计背景，**不提供可直接使用的 FFT RTL 实现**。缓冲、寄存器、重排序、控制以及算术单元均计入硬件面积。

## 任务与评分

首先阅读 [中文题面](fft64_benchmark/TASK_ZH.md)或 [English task](fft64_benchmark/TASK_EN.md)，并核对 [SPEC.json](fft64_benchmark/SPEC.json) 与 [RTL 接口](fft64_benchmark/INTERFACE.md)。默认 `architecture` profile 在满足功能、SQNR、协议、复位、时序及网表验证后，对**完整映射面积（60%）、已验证持续吞吐率（30%）、最大观测首输出延迟（10%）**计算连续分数。`resolved` 只表示强制规格是否满足，不设置最低面积改善比例；更高的 SQNR 不获得额外奖励。详见 [SCORING.md](fft64_benchmark/SCORING.md) 和 [EVALUATION.md](fft64_benchmark/EVALUATION.md)。

## 在现有 Synopsys 容器中开发

如果目录结构为 `FFT-Bench/`、`Synopsys/`、`port.txt` 并列，其中 `Synopsys/` 映射到容器 `/mnt/mydata`，可在本仓库根目录运行：

```bash
bash check_env.sh
bash run_synopsys_debug.sh submission --quick --out runs/quick
bash run_synopsys_debug.sh submission --profile area --out runs/area
bash run_synopsys_debug.sh submission --profile architecture --out runs/architecture
```

Agent 也可以直接调用容器工具：

```bash
bash synopsys.sh exec -- bash -c 'command -v vcs; command -v dc_shell; command -v pt_shell'
```

这些命令用于**公开开发与调试**。`architecture` 的完整 II 搜索成本较高，建议先运行 `--quick`。环境与 SSH 细节见 [REMOTE_SYNOPSYS.md](REMOTE_SYNOPSYS.md)。

若 EDA 工具直接安装在当前系统中，可使用：

```bash
bash fft64_benchmark/setup.sh --check-only
bash fft64_benchmark/run_preview.sh submission runs/quick --quick --no-build
bash fft64_benchmark/run_preview.sh submission runs/full --no-build
```

自动后端选择优先使用已就绪的商业工具，否则使用开源**布局前**映射与 STA 流程。不同后端的面积、时序和校准分数不得混合排名。

## Agent 可自定义综合策略

Agent 可以修改 RTL，也可以自主调整 DC、Yosys 和 ABC 的优化命令与顺序。初始化模板：

```bash
bash build_implementation.sh submission --init-flow
# 修改 submission/flow/dc_opt.tcl 或 Yosys/ABC 模板
bash synopsys.sh build submission --export --out runs/custom_build
bash run_synopsys_debug.sh submission --profile area --out runs/custom_check
```

构建会导出 `submission/implementation/mapped.v` 与 `manifest.json`。评测器**直接导入并测量该网表**，使用固定标准单元库与时序约束、核对 RTL/网表行为；**不会在隐藏评分中运行 Agent 提交的脚本**。没有自定义实现时使用默认综合流程。详细说明见 [OPTIMIZATION.md](OPTIMIZATION.md)。可选 P&R 模板不参与当前分数。

## 提交文件

`submission/rtl/`、`submission/DESIGN_PLAN.md`、`submission/measurements.csv` 为规定交付文件；`design_config.json` 可选。使用自定义综合时还应保留 `flow/` 与 `implementation/`。设计记录用于分析 Agent 的工程决策，不按篇幅或试验次数加分。

公开测试不等于私有隐藏评分。没有匹配的冻结校准，预览可提供实验数据但不能提供有效正式分数。请勿将 FFT-Eval 私有基线、种子或校准数据放入 Agent 工作区。
