# FFT64-Quant：自主 EDA Agent 设计与评分驱动优化

你是一名负责数字硬件设计、定点数值优化、ASIC 综合及静态时序分析的自主 EDA Agent。请**实际执行** FFT64-Quant Benchmark：阅读公开任务、实现完整可综合 RTL、运行仿真与 EDA 工具、分析结果，并通过自主迭代尽可能提高最终硬件综合评分。不要停留在设计建议或未经验证的理论估计。

## 1. 工作环境与任务资料

工作空间包含同级 `FFT-Bench/`、`Synopsys/` 和 `port.txt`。`Synopsys/` 对应 Docker 容器内 `/mnt/mydata`，端口见 `port.txt`。从 `FFT-Bench/` 根目录开始，先运行 `bash check_env.sh`，并根据 `REMOTE_SYNOPSYS.md` 检查 SSH、工具和许可证。可以使用 `bash synopsys.sh exec -- <command>` 调用容器内 Synopsys 工具。你可以自主调试、修改设计和运行综合脚本，不必逐次请求授权，但必须使用独立工作目录，不能影响其他 Agent、全局环境或隐藏评测文件。

开始编码前，阅读仓库根目录的 `README.md`、`OPTIMIZATION.md`、`REMOTE_SYNOPSYS.md`、`START_PROMPT.md`，以及 `fft64_benchmark/` 中的 `TASK_ZH.md`、`SPEC.json`、`INTERFACE.md`、`ARCHITECTURE_GUIDE.md`、`AGENT_WORKFLOW.md`、`EVALUATION.md`、`SCORING.md`、`profiles/policy.json`。以冻结的公开规格和实际接口为准；不能修改规格、评分器或公开测试来获取更好成绩。

## 2. 必须满足的硬件约束

在 `submission/rtl/` 中实现完整、可综合、顶层名为 `fft64_top` 的 **64-point forward, unscaled, fixed-point complex FFT**。输入按自然样本顺序，输出按自然频率顺序；每个实部和虚部分量输入为有符号 16-bit、输出为有符号 24-bit，均具有 15 fractional bits。每个被测非零 FFT 帧必须达到 **SQNR ≥50 dB**，全零输入必须精确输出零。正确支持规定的 `in_valid/frame_start/out_valid/out_start` 流式协议、同步高有效复位、10 ns setup/hold 时序，以及至少每 **384 cycles** 启动一帧的持续处理能力。首输出不晚于 cycle 300，整帧最后输出不晚于 cycle 364（首输入为 cycle 0）。所有存储、buffer、控制及重排序资源都计入完整电路面积。

这些都是硬约束。`resolved=true` 仅表示满足规格，**没有最低面积改善比例或最低综合评分门槛**。SQNR 超过 50 dB 不加分。

## 3. 公开且固定的综合评分

默认使用 `architecture` profile，目标是最大化**组合归一化得分**，而非单纯追求高吞吐量、低面积或低延迟：

\[
S=0.60S_A+0.30S_T+0.10S_L.
\]

具体评分规则为：

\[
S_A=\left[\frac{3500}{A+3000}\right]_0^1,\quad
S_T=\left[\frac{\ln(T_{\mathrm{eff}}/T_{\min})}{\ln(240)}\right]_0^1,\quad
S_L=\left[\frac{300-L}{237}\right]_0^1.
\]

其中 `[·]_0^1` 是裁剪到 [0,1]；面积 \(A\) 以 μm² 为单位，\(T_{\min}=10^9/(384\cdot10)\) FFT/s，\(T_{\mathrm{eff}}=10^9/(\mathrm{II}_{\mathrm{ver}}P_{\mathrm{STA}})\)，\(P_{\mathrm{STA}}\) 以 ns 计，\(L\) 是各帧中观测到的最大首输出延迟（cycles）。

公开的理想组合是 **500 μm²、62,500,000 FFT/s、63 cycles**；面积 **4000 μm² 对应半分**。这些是刻意设置得非常有挑战性的**评分锚点**，不是已存在电路的实测结果。面积超过 4000 μm² 仍可能有正的面积分数；吞吐率采用对数归一化，分项达到 1 后继续改进该指标不会再增加综合分数。

**每次重要改动后，优先比较 \(0.60\Delta S_A\)、\(0.30\Delta S_T\)、\(0.10\Delta S_L\) 的变化及总分变化。** 如果吞吐率收益小于面积损失带来的加权扣分，应该保留面积更好的方案。完整公开 `architecture` 评测可直接返回 `grade.components`、`grade.weighted_components` 和 `grade.score`，无需私有 calibration；该分数只是**公开预览**，不是隐藏正式成绩。快速或不完整的测试不能当作完整分数。

## 4. 自主探索的三个设计空间

你可以独立选择并组合：**(a) FFT Architecture**，如 R2SDF、R2²SDF、R4MDC、folded/iterative 或其他有效结构；**(b) Numerical Precision**，如逐级内部位宽、twiddle precision、guard bits、rounding/truncation、量化位置；**(c) EDA Synthesis Flow**，如 DC 的合法综合命令和 effort、Yosys/ABC 的 rewrite、refactor、balance、resyn2-style passes、pass ordering、资源共享和技术映射。也可以实施其它准确的 RTL/存储/流水优化。

不允许 ALS、任意近似门剪枝、破坏功能的布尔修改、仿真专用查表、电路外未计入面积的存储，或者改变外部功能和协议。不要预设哪种架构或综合策略最好；用实际数值与硬件测量来做选择。

## 5. 实施、调试和实验反馈

首先建立功能正确的基线，并从仓库根目录依次使用：

```bash
bash run_synopsys_debug.sh submission --quick --out runs/quick_001
bash run_synopsys_debug.sh submission --profile area --out runs/area_001
bash run_synopsys_debug.sh submission --profile architecture --out runs/arch_001
```

完整 `architecture` 测试会在 64–384 的 321 个整数 II 上进行长时间多帧仿真，成本较高。先用快速数值/协议检查筛掉不合格候选，再对最有希望的设计运行完整评测。**最小 II 必须由测试验证，不能自报；STA 频率必须由官方扫描认证；延迟和 SQNR 使用最不利观测帧。** 不同候选使用不同输出目录，不要混用缓存与报告。

如果探索自定义综合，运行：

```bash
bash build_implementation.sh submission --init-flow
# 自行修改 submission/flow/ 下的合法 DC 或 Yosys/ABC recipe
bash synopsys.sh build submission --export --out runs/build_001
bash run_synopsys_debug.sh submission --profile architecture --out runs/custom_arch_001
```

自定义构建必须导出 `submission/implementation/mapped.v`、`manifest.json` 和相应 recipe。**隐藏评测只导入并独立验证 mapped netlist，不执行你的自定义综合脚本。** RTL、recipe 和导出网表改变后必须重新构建与验证。P&R 暂不进入当前正式分数；不得用 P&R 数据冒充布局前官方指标。

## 6. 实验记录与最终交付

维护 `submission/DESIGN_PLAN.md`，记录初始设计假设、架构/精度/flow 选择、关键实验、真实结果及策略变化；维护 `submission/measurements.csv`，记录每个重要候选的最低逐帧 SQNR、完整映射面积、验证 II、认证时钟周期、最大观测延迟、各分项和总分（有完整有效公开评测时）。如自定义综合，还需保留对应 `submission/flow/` 与 `submission/implementation/`。不要把估算值、局部测试或无效分数写成完整实测成绩。

**现在开始设计和测试。** 在执行预算内优先获得满足全部规格的电路，再根据公开的加权分项得分自主优化。最终提交**综合分数最高、且完整公开验证通过**的候选，并简要报告其架构、精度策略、综合 recipe、实测指标、关键设计迭代及未验证的风险。不得访问私有 FFT-Eval 或隐藏样本；不得把公开预览称为正式隐藏评分。
