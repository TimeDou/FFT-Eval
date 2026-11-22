# FFT64-Quant：EDA Agent 设计任务

## 任务目标

根据公开规格，从零开发一套完整、可综合的 **64 点定点复数 FFT 处理器**。本任务不提供现成 FFT RTL。Agent 需要在满足全部强制约束后，自主探索 FFT 架构、内部数值精度、RTL 组织和可选综合策略，以真实测量结果改进硬件质量。评测对象是**整个电路**，包含运算单元、寄存器、缓冲、控制和数据重排序，而非单个蝶形运算。

## 强制功能与硬件规格

- **变换：** 64 点、正向、不缩放的复数 FFT；输入按自然采样顺序，输出按自然频率顺序。
- **数据格式：** 输入实部/虚部各 signed 16-bit，输出各 signed 24-bit，均有 15 位小数。被测输入分量位于 [-0.5, 0.5]，非零帧复数 RMS ≥1/32。
- **输入服务：** 每周期接收一个复数输入，连续 64 个有效周期构成一帧；必须在无反压条件下持续支持相邻帧起点间隔不小于 384 cycles 的合法输入。
- **输出和延迟：** 每帧连续输出 64 个频点，首频点用 `out_start` 标记。以首输入为 cycle 0，首输出不得早于最后一个必需输入，且不晚于 cycle 300；最后一个输出不晚于 cycle 364。
- **时钟与复位：** 单一上升沿时钟；同步高有效复位丢弃未完成帧；映射网表必须满足 10 ns 时序要求。
- **数值精度：** 以**同一已量化输入帧**的 float64 FFT 为参考，每个被测非零帧 SQNR ≥50 dB；全零帧必须精确输出零。不得通过后处理拟合增益、相位、缩放或输出排列来提高分数。

其中 X 为同输入的 float64 参考，X-hat 为硬件输出；每个完整复数帧的 SQNR 定义为：
\[
\mathrm{SQNR}_f=10\log_{10}\frac{\sum_{k=0}^{63}|X_f[k]|^2}{\sum_{k=0}^{63}|\hat X_f[k]-X_f[k]|^2}.
\]

384 cycles/frame 是**必须达到的最低服务能力**，不是对设计最大吞吐率的限制。更短的帧启动间隔只有经过评测器验证，才可能提高吞吐率评分。以 [SPEC.json](SPEC.json) 和 [INTERFACE.md](INTERFACE.md) 为准。

## 可探索的设计空间

允许使用 R2SDF、R2²SDF、R4MDC、folded/iterative 或其他符合规格的 FFT 架构；可以调整中间数据/旋转系数位宽、舍入与截断、保护位、存储组织、流水调度、常数乘法专用化与资源复用。

同时允许自主选择综合命令、优化参数、布尔重写及技术映射策略。执行 `bash build_implementation.sh submission --init-flow` 可获得 DC、Yosys/ABC 的可编辑模板。修改后须导出 `submission/implementation/mapped.v` 和 `manifest.json`。评测器会**直接导入该标准单元网表并独立计面积、做 STA、检查 RTL/网表一致性**；正式隐藏评分**不会执行** Agent 的 Tcl/Yosys/ABC 脚本，也不接受自报 PPA。操作方法见 [OPTIMIZATION.md](../OPTIMIZATION.md)。

禁止门级 ALS、任意逻辑近似剪枝/替换、无关的近似 compressor、仿真专用查表实现、未计面积的外部存储，以及改变规定 FFT 功能、外部数据格式或流式协议。允许的数值近似仅限明确的定点精度和量化操作。可选 P&R 模板不进入当前布局前评分。

## 建议执行流程

1. 阅读 [SPEC.json](SPEC.json)、[INTERFACE.md](INTERFACE.md)、[ARCHITECTURE_GUIDE.md](ARCHITECTURE_GUIDE.md)、[SCORING.md](SCORING.md) 和 [EVALUATION.md](EVALUATION.md)。
2. 自行建立 `submission/DESIGN_PLAN.md`，比较至少两种架构，并提出可通过测量验证的假设。
3. 在 `submission/rtl/` 下实现正确的基线，优先通过公开数值、协议及复位测试。
4. 自主调整 RTL、精度或综合 recipe，对有希望的候选进行完整映射面积与时序测量。
5. 对候选开展持续多帧和 II 测试，将实验结果、失败原因及后续决策记录在 `measurements.csv`。
6. 提交**已经验证**的最佳电路；若使用自定义综合，确保导出网表与最终 RTL、recipe 一致。

若存在同级 `Synopsys/` 和 `port.txt`，从 **FFT-Bench 仓库根目录**执行：

```bash
bash check_env.sh
bash run_synopsys_debug.sh submission --quick --out runs/quick
bash run_synopsys_debug.sh submission --profile area --out runs/area
bash run_synopsys_debug.sh submission --profile architecture --out runs/full
```

也可以使用 `bash synopsys.sh exec -- <命令>` 直接在容器内调试；详见 [REMOTE_SYNOPSYS.md](../REMOTE_SYNOPSYS.md)。使用本机已安装工具时可改用 `fft64_benchmark/run_preview.sh`。不同候选应使用独立输出目录；快速检查通过不代表全部硬件要求已通过。

## 测量、评分与交付

`resolved=true` 仅取决于 FFT、SQNR、协议、复位、II=384 服务、首/末输出延迟、映射网表一致性和 10 ns setup/hold 时序是否通过；**没有最低面积改善比例要求**。默认 `architecture` 分数由完整映射面积（60%）、实测可持续吞吐率（30%）和最大观测首输出延迟（10%）构成。SQNR 达标后不再额外加分。

数值可行性使用所有非零测试帧中的**最低 SQNR**，延迟使用**逐帧最大观测值**；吞吐率使用 64–384 cycles 中经过连续多帧验证的最小整数 II，而不是 Agent 自报值。公开数值测试包含至少 1,024 个非零随机帧，隐藏测试包含至少 8,192 个，均另加定向样例。每个 II 至少连续运行 1,024 帧，选中的最短通过 II 再经代表性网表验证。这些结论是有限样本证据，不是形式化保证。正式分数必须使用同一后端、profile 和冻结校准。

提交内容：

- `submission/rtl/`：完整可综合 RTL，顶层 `fft64_top`；
- `submission/DESIGN_PLAN.md`：关键假设、实验与设计决策；
- `submission/measurements.csv`：实际测量及其来源；
- `submission/design_config.json`（可选）：RTL 文件列表及不具评分权威性的 II 提示；
- `submission/flow/` 和 `submission/implementation/`（自定义综合时）：recipe、完整映射网表和 manifest。

成绩由可信评测器决定。不得修改评分规则、隐藏数据或校准结果，不得编造实验数据，也不得根据隐藏反馈事后更换提交设计。
