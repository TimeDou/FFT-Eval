# FFT64 Quantization and Architecture Benchmark

这是一个完整 FFT 电路优化题。Agent 选择架构、实现定点运算并调整量化与资源组织，在满足 SQNR、吞吐和延迟要求后优化吞吐量/面积效率。默认采用 **Open 模式：提供架构说明和接口，不提供 FFT 实现**。

从 [TASK_ZH.md](TASK_ZH.md) 或 [TASK_EN.md](TASK_EN.md) 开始。机器规格见 [SPEC.json](SPEC.json)，接口见 [INTERFACE.md](INTERFACE.md)。本目录不含参考答案、解题记录或隐藏测试种子。

## 环境

正式流程使用 ASAP7 RVT/TT、VCS、Design Compiler 和 PrimeTime。组合与时序 Liberty、门级功能模型和 Python 依赖随题提供。支持 Python 3.10+；随包离线 NumPy wheel 对应平台的 Python 3.12 / Linux x86-64 / GLIBC 2.17。

```bash
bash setup.sh --check-only  # 只检测，不安装、不构建
bash setup.sh               # 自动选择，并准备缺少的依赖
```

默认 `auto` 的优先顺序是：**已有 VCS/DC/PrimeTime → 已有开源工具链 → 最后才构建缺少的开源组件**。所有入口都会加载手册规定的 `/etc/profile.d/eda-env.sh`，优先使用 `/opt/dsbench/bin/python3`，并识别 `VCS_HOME/DC_HOME/PT_HOME`。平台已有工具可直接使用，agent 无需先安装 Yosys 或 Icarus。

Synopsys 已有而 ASAP7 DB 尚未准备时，只调用 Library Compiler 转换随题 Liberty；也可通过 `FFT_LC_BIN` 指定编译器，或直接提供 `tech/db/` 中的两份 DB。库配置仍不满足时，自动模式可复用已就绪的开源流程，但不为这个问题新建一套 Yosys。实际工具执行中的许可证错误会明确报告。`--quick` 只需 RTL 仿真器，不要求 DC/PT 或 DB 已准备好。

开源流程需要 Yosys、ABC、OpenSTA、Icarus、Verilator 及 C++ 构建工具。已有组件直接复用，缺少组件才尝试安装到独立的 `FFT_TOOLS_PREFIX`；不覆盖系统工具。构建日志、固定源码版本和实际 commit 保留在该目录。缺少基础编译依赖或网络时会报告原因。

可用 `bash setup.sh commercial` 或 `bash setup.sh local` 显式选流程；`--no-build` 禁止自动编译 EDA 工具。例如已有 ABC/OpenSTA 不在 PATH 时：

```bash
export FFT_ABC=/path/to/abc
export FFT_STA=/path/to/sta
bash setup.sh --no-build
```

`FFT_PYTHON` 可指定解释器。已经有 NumPy 时不重复安装；DSBench 的 Python 3.12 可使用随题离线 wheel。

## 做题与自测

1. 创建工作目录，例如 `/workspace/submission/`，在其中编写 `rtl/`、`DESIGN_PLAN.md` 和 `measurements.csv`。
2. `interface/fft64_top.sv` 仅是可复制的端口模板；需要自行实现 FFT。
3. 用公开输入快速检查，再为有希望的候选运行完整评估。

```bash
# 仅 RTL 数值和协议检查
bash run_preview.sh /workspace/submission /workspace/run_quick --quick

# 自动使用已有 Synopsys，否则使用已有开源工具
bash run_preview.sh /workspace/submission /workspace/run_full

# 只使用现有环境，禁止自动编译 EDA 工具
bash run_preview.sh /workspace/submission /workspace/run_existing --no-build

# 需要时显式指定开源流程
bash run_preview.sh /workspace/submission /workspace/run_local --backend local
```

终端只返回简短结果。`summary.json` 是便于阅读的反馈，`result.json` 和子目录保留逐帧质量、周期记录、网表与工具日志。每个候选使用独立输出目录；相同 RTL 的重复测量可复用映射与编译缓存。

反馈包含实际选择的 `backend`，检测详情在输出目录的 `environment_selection.json`。有已校准的面积参考时，设置 `FFT_CALIBRATION=/path/to/area_reference.json`，自动模式使用该参考指定的后端。未校准时仍报告实测面积和时序，面积比和正式得分留空。

不运行 RTL 时，也可用 `tools/check_numeric.py` 检查自己导出的整数输出 JSON；它只检查数值，不替代完整电路评估。

## 评分与平台使用

通过全部所选模式的硬件约束即 `resolved=true`，没有分数门槛。默认 `area` 只按完整映射面积评分；`--profile architecture` 使用 60% 面积、30% 经连续帧和时钟扫描验证的吞吐量、10% 首输出延迟。两个模式的标尺独立冻结，SQNR 达标不加分。详见 [SCORING.md](SCORING.md)。

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
