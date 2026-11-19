# FFT64 Quantization and Architecture Benchmark

这是一个完整 FFT 电路优化题。Agent 选择架构、实现定点运算并调整量化与资源组织，在满足 SQNR、吞吐和延迟要求后降低面积。默认采用 **Open 模式：提供架构说明和接口，不提供 FFT 实现**。

从 [TASK_ZH.md](TASK_ZH.md) 或 [TASK_EN.md](TASK_EN.md) 开始。机器规格见 [SPEC.json](SPEC.json)，接口见 [INTERFACE.md](INTERFACE.md)。本目录不含参考答案、解题记录或隐藏测试种子。

## 环境

正式流程使用 ASAP7 RVT/TT、VCS、Design Compiler 和 PrimeTime。组合与时序 Liberty、门级功能模型和 Python 依赖随题提供。支持 Python 3.10+；随包离线 NumPy wheel 对应平台的 Python 3.12 / Linux x86-64 / GLIBC 2.17。

```bash
bash setup.sh commercial
```

脚本会检查工具并在需要时调用 Library Compiler 生成 `tech/db/`。工具或许可证未就绪时会说明缺少什么。尚未准备商业环境时，也可以用 Yosys、ABC、OpenSTA、Icarus 和 Verilator 执行本机流程：

```bash
export FFT_ABC=/path/to/abc
export FFT_STA=/path/to/sta
bash setup.sh local
```

默认调用 `python3`；可以用 `FFT_PYTHON` 指定解释器。在 DSBench 上会优先使用 `/opt/dsbench/bin/python3`。

## 做题与自测

1. 创建工作目录，例如 `/workspace/submission/`，在其中编写 `rtl/`、`DESIGN_PLAN.md` 和 `measurements.csv`。
2. `interface/fft64_top.sv` 仅是可复制的端口模板；需要自行实现 FFT。
3. 用公开输入快速检查，再为有希望的候选运行完整评估。

```bash
# 仅 RTL 数值和协议检查
bash run_preview.sh /workspace/submission /workspace/run_quick --quick

# 完整 VCS → DC → PrimeTime → 映射网表仿真
bash run_preview.sh /workspace/submission /workspace/run_full

# 同样的测试，在本机开源工具上运行
bash run_preview.sh /workspace/submission /workspace/run_local --backend local
```

终端只返回简短结果。`summary.json` 是便于阅读的反馈，`result.json` 和子目录保留逐帧质量、周期记录、网表与工具日志。每个候选使用独立输出目录；相同 RTL 的重复测量可复用映射与编译缓存。

有已校准的面积参考时，设置 `FFT_CALIBRATION=/path/to/area_reference.json`。未校准时仍报告实测面积和时序，面积比和正式得分留空。

不运行 RTL 时，也可用 `tools/check_numeric.py` 检查自己导出的整数输出 JSON；它只检查数值，不替代完整电路评估。

## 评分与平台使用

先通过全部硬件约束，再按完整映射面积排名。拟定通过目标为 `A/A_ref ≤ 0.80`；连续分数为 `max(0, 1-A/A_ref)`。商业平台的准确参考面积须在正式测试前完成校准。

出题人部署、校准和 DSBench Code Grade 的操作见 [OPERATOR.md](OPERATOR.md)。本题采用 pre-layout 标准单元面积和理想互连 STA；P&R 模板是可选扩展，不参与当前评分。

## 文件

| 路径 | 内容 |
|---|---|
| `TASK_*.md`、`SPEC.json` | 题面和数值/服务规格 |
| `ARCHITECTURE_GUIDE.md` | 架构选择及定点设计背景 |
| `INTERFACE.md`、`interface/` | 明确的端口和周期约定 |
| `AGENT_WORKFLOW.md`、`DESIGN_PLAN_TEMPLATE.md` | 简短的设计与实验记录建议 |
| `tools/`、`run_preview.sh` | 数据、仿真、综合、STA 和统一反馈 |
| `flow/`、`tech/` | 固定工艺与 EDA 配置 |
| `grading/` | 生成独立评分附件的工具与入口 |
| `public_data/` | 公开的快速数值测试输入 |

ASAP7 与 NumPy 保留各自的原始许可证。工具代码沿用并整理了工作区原有 FFT 实验基础设施；没有第三方 FFT RTL 或优化答案随题下发。
