# FFT64-Quant: Architecture and Precision Co-Design

实现并优化一个 64-point fixed-point complex FFT。你可以选择 SDF、MDC 或 folded 等结构，并优化精度、量化、常数乘法、缓存与流水。仓库不提供完成的 FFT RTL。

先阅读 [任务说明](fft64_benchmark/TASK_ZH.md)（[English](fft64_benchmark/TASK_EN.md)）、[完整规范](docs/FFT64-Quant.pdf) 和 [机器规格](fft64_benchmark/SPEC.json)。

```bash
bash fft64_benchmark/setup.sh --check-only
bash fft64_benchmark/run_preview.sh submission runs/numerical --quick --no-build
bash fft64_benchmark/run_preview.sh submission runs/hardware --no-build
```

优先复用已安装工具。数值快速评估仍使用至少 1,024 个独立非零帧，另有 directed cases，并测试 1,024 个连续服务帧；每帧始终 64 点。完整硬件评价包含面积、时钟扫描和长时间帧服务测试。正式隐藏评价由出题方单独执行；本仓库没有隐藏种子、准确参考 RTL 或其他 Agent 的结果。

目标为 Area 60%、Throughput 30%、最大首输出 Latency 10% 的综合评分，详见 [SCORING.md](fft64_benchmark/SCORING.md)。SQNR≥50dB 是硬约束，不因更高精度加分。全部必选规格通过即可，低分或零分也通过。没有正式校准时，本地工具报告硬件反馈和 score_valid=false。

提交 `submission/rtl/`、`design_config.json`、`DESIGN_PLAN.md` 和 `measurements.csv`。可用下面的启动 prompt：

> 阅读 fft64_benchmark/TASK_ZH.md、SPEC.json 和 ARCHITECTURE_GUIDE.md，在 submission/ 中实现并优化 FFT64。优先使用已安装工具，完成数值、连续协议和硬件验证；根据实测结果迭代设计，并提交 RTL、设计计划和测量记录。

NumPy 优先复用所选 Python 环境中已有的安装；缺失时通过 pip 安装固定版本，也支持仓库外的离线缓存。仓库不再分发 NumPy wheel，配置见 [依赖说明](fft64_benchmark/README.md#numpy-dependency)。
