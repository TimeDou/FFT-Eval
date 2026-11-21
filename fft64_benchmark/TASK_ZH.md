# EDA Agent 任务：FFT64 架构与数值精度联合设计

## 1. 任务目标

从零设计一套**完整、可综合的 64 点复数 FFT 处理器**，在满足功能与硬件规格的条件下改善面积、可持续吞吐率和首次输出延迟。本任务不提供完成的 FFT RTL。需要优化的是整个处理器，而非单个蝶形运算或乘法器；缓冲、寄存器、控制、数据交换和重排序均计入面积。

Agent 可自主比较不同架构和精度方案，并根据实际测量调整设计。**无需证明全局最优；测量后的设计决策比冗长报告更重要。**

## 2. 必须满足的规格

- **变换：** 64 点复数正向 FFT，不归一化，输入自然顺序，输出自然频率顺序。
- **输入：** 每个有效周期接收一个复数，连续 64 个周期构成一帧；每个实部/虚部分量为带 15 个小数位的 signed 16-bit，范围 [-0.5, 0.5]。被测非零帧的复数 RMS 不低于 1/32。
- **输出：** 连续 64 个有效周期，各分量为带 15 个小数位的 signed 24-bit；首频点用 `out_start` 标记。
- **时钟：** 单一上升沿时钟；必须满足 10 ns 时序约束。
- **最低服务能力：** 必须支持每 384 cycles 开始一帧及更长的合法间隔，无输入反压。
- **延迟：** 从首输入周期（cycle 0）起算，首输出不晚于 cycle 300，最后一个输出不晚于 cycle 364；首输出不能早于最后一个必需输入。
- **复位：** 同步高有效复位丢弃未完成帧，复位后的新帧须正确处理。

384 cycles/frame 是**最低服务规格**，并不代表流水 FFT 的最大固有吞吐能力。若通过更短的帧启动间隔测试，可以获得更高的吞吐率评分。

## 3. 数值约束

准确参考使用**同一组已量化输入样本**的 float64 FFT。逐个非零帧计算：

\[
\mathrm{SQNR}_f=10\log_{10}\frac{\sum_{k=0}^{63}|X_f[k]|^2}{\sum_{k=0}^{63}|\hat X_f[k]-X_f[k]|^2}.
\]

所有非零测试帧必须满足 **SQNR ≥ 50 dB**，全零帧必须严格输出零。不能在测试后拟合增益、相位、输出顺序或缩放。有限的公开/隐藏样本测试不构成全输入域的形式化精度保证。

## 4. 设计自由度与限制

**允许：** R2SDF、R2²SDF、R4MDC、folded/iterative 等可行架构；各 stage 的数据与 twiddle 精度；明确的 truncation/rounding；guard bits、量化边界；不改变规定数值语义的存储 bank、常数旋转专用化、资源复用和合法流水设计。

**禁止：** 门级 ALS、与量化无关的任意逻辑近似剪枝/替换、近似 compressor、仿真专用/查表作弊实现，以及更改外部 FFT 功能、数值格式、输出顺序和时钟协议。

面积必须来自**完整 top module 的标准单元映射**；不存在免费 SRAM。

## 5. 建议工作过程

如果仓库同级存在 `Synopsys/` 与 `port.txt`，应使用提供的 SSH 入口，不要在宿主机重复搭建 EDA 环境。在仓库根目录运行 `bash check_env.sh`，然后使用 `bash run_synopsys_debug.sh submission --quick --out runs/quick`。`--profile area` 提供映射与 STA 反馈，`--profile architecture` 执行完整吞吐率与频率评价。也可用 `bash synopsys.sh exec -- <命令>` 在容器中直接调试。详见仓库根目录的 `REMOTE_SYNOPSYS.md`。

工具直接安装在当前环境中时，在**仓库根目录**执行：

```bash
bash fft64_benchmark/setup.sh --check-only
bash fft64_benchmark/run_preview.sh submission runs/quick --quick --no-build
bash fft64_benchmark/run_preview.sh submission runs/full --no-build
```

1. 阅读 `fft64_benchmark/SPEC.json`、`fft64_benchmark/INTERFACE.md` 与 `fft64_benchmark/ARCHITECTURE_GUIDE.md`。
2. 自行创建 `submission/DESIGN_PLAN.md`，比较至少两种架构思路，并给出可测量的假设。
3. 先建立正确、具有足够精度的硬件实现，再尝试精度缩减。
4. 对候选执行数值、协议、完整映射面积和时序评价。
5. 在每次重要实验后记录实际结果、采纳或拒绝的理由以及下一次实验；将明细保存在 `measurements.csv`。
6. 提交满足全部硬约束且硬件分数较好的设计。

评测优先使用可用的 Synopsys 工具，否则使用已安装的开源仿真、综合和 STA 工具。没有同平台冻结校准时，公开预览可提供开发反馈，但不能视为正式分数。

## 6. 通过与评分

`resolved` 仅表示必选功能、SQNR、协议、复位、时序和映射网表要求全部通过，**不要求最低面积降幅或最低得分**。

默认 `architecture` 分数：完整映射面积 **60%**、已验证可持续吞吐率 **30%**、实测最大首输出延迟 **10%**。SQNR 达标即可，不额外奖励更高精度。吞吐率使用 64–384 全部整数 II 中**至少 1,024 个连续帧验证通过的最小值**，并对选中 II 做映射网表抽样确认；`design_config.json` 的 II 仅作提示，不决定评分。可选的更短 II 失败不会否决 384-cycle 必选服务。

数值数据：公开至少 1,024 个非零随机帧、隐藏至少 8,192 个非零随机帧，均另含定向边界案例。可行性以非零帧**最小 SQNR**及逐帧**最大延迟**判断。详情见 [SCORING.md](SCORING.md) 和 [EVALUATION.md](EVALUATION.md)。

## 7. 提交文件

- `submission/rtl/`：自包含可综合 RTL，顶层为 `fft64_top`
- `submission/DESIGN_PLAN.md`：重要设计假设与更新记录
- `submission/measurements.csv`：主要候选的实际测量
- `submission/design_config.json`（可选）：RTL 列表与帧间隔提示

正式评分以评测器实测为准；提交后不得根据隐藏反馈重新切换候选设计。
