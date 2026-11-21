# FFT64 v0.4：通过条件与两个独立评分模式

通过与排名分开。`resolved=true` 表示所选模式的基本规格全部通过，**不设最低分数或最低面积降幅**。可行设计可得 0 分。SQNR 是硬约束，超过 50 dB 不加分；协议、复位、自然输出顺序、输出截止时间、完整 RTL/映射对照及 10 ns setup/hold 时序仍必须通过。

规则见 [profiles/policy.json](profiles/policy.json)。其权重、目标比例和扫描设置在新实验前已冻结，时间及 SHA-256 见 [PRE_REGISTERED.json](profiles/PRE_REGISTERED.json)。准确基线先在本平台校准，再评价候选；目标不随候选或 agent 结果调整。两种模式的分数不能相互排名。

## 默认模式：Area Profile

适合原有每 384 cycles 输入一帧的固定服务任务：

\[
S_A=\mathrm{clip}\left(\frac{A_{ref}-A}{A_{ref}-A_{target}},0,1\right),\quad
A_{target}=0.5A_{ref},\quad S=V S_A.
\]

`A` 为完整顶层 mapped cell area，含存储、控制、重排及寄存器。`A_ref` 为同一技术库和流程下，通过全部检查的两份准确定点基线中较小的面积。`V` 表示基本规格通过。

| 相对面积 | 分数 | 规格已满足时 resolved |
|---:|---:|---|
| 1.10 | 0.00 | true |
| 1.00 | 0.00 | true |
| 0.90 | 0.20 | true |
| 0.75 | 0.50 | true |
| 0.50 或更小 | 1.00 | true |

面积模式不奖励时序余量，不把单次 10 ns STA 的 slack 换算成 Fmax。频率在此模式只通过 10 ns 时序这个基本约束起作用。默认运行方式不变，也可显式指定：

```bash
bash run_synopsys.sh submission --profile area --out /workspace/eval/area
```

## 架构模式：Architecture–Throughput Profile

```bash
bash run_synopsys.sh submission --profile architecture --out /workspace/eval/architecture
```

在提交目录的 `design_config.json` 中声明可持续输入帧间隔：

```json
{"top":"fft64_top", "rtl":["rtl/fft64_top.sv"], "frame_ii_cycles":320}
```

范围为整数 64–384，省略时为 384。每帧仍连续输入 64 个复样本；无需调整顶层接口，也没有输出 backpressure。原有 384-cycle 工作负载始终测试。平台另在声明间隔下连续发送完整独立测试集，并增加混合间隔、长空闲和密集流复位测试。三种时刻零状态的 mapped 仿真均须与 RTL 对应。只声明较短 II 而无法持续服务，将不通过；有限测试证明的是**已验证的可达 II**，不是任意输入下的形式化最小 II。

准确基线的校准先用 16 帧探测 64–384 的每个整数 II，记录所有成功与失败间隔，再对最小可行候选做完整数据和映射验证；完整验证失败则继续尝试。候选正式评测使用其声明的 II。开发者可用 `tools/evaluate.py --profile architecture --auto-ii` 做同样的经验搜索。

对同一份映射网表，PrimeTime 在 0.25–10 ns 范围重新施加时钟并逐点更新 STA，以不超过 0.01 ns 的失败/通过区间定位 setup 边界。评分使用**实测 setup/hold 都通过的周期端点**，不使用负 slack 点，也不从固定时钟 slack 推算最高频率。如果 0.25 ns 也通过，仅报告达到扫描上限，不能声称找到真正峰值。证书与 mapped netlist hash 绑定，逐点 trace 保留。最高频率仍是本 pre-layout 模型下的认证可达频率估计，非 post-route 或芯片实测。

\[
T=F_{certified}/II_{verified}\quad (\mathrm{FFTs/s}),
\qquad T_{samples}=64T.
\]

\[
S=V(0.6S_A+0.3S_T+0.1S_L),
\]

\[
S_A=\mathrm{clip}\frac{A_{ref}-A}{A_{ref}-A_{target}},\quad
S_T=\mathrm{clip}\frac{T-T_{ref}}{T_{target}-T_{ref}},\quad
S_L=\mathrm{clip}\frac{L_{ref}-L}{L_{ref}-L_{target}}.
\]

每项 clip 到 [0,1]。频率只经吞吐量计分，不另设 Fmax 项。`L` 是包括密集流在内的最坏首输出 cycles 乘**共同的 10 ns 工作时钟**，避免再次奖励同一次频率提高。另报告在认证时钟下的物理延迟，二者明确区分。

架构模式有独立标尺。准确基线提供以下分量参考向量，它不冒充某一份真实电路：

| 项目 | 0 分参考 | 1 分目标 |
|---|---|---|
| Area | 准确基线的最大面积 | 准确基线最小面积的 50% |
| Throughput | 准确基线的最小已验证吞吐量 | 准确基线最大已验证吞吐量的 2 倍 |
| First-output latency @10 ns | 准确基线的最大首输出延迟 | `max(0.5 × 最小准确延迟, 630 ns)` |

采用分量参考使准确架构本身的面积/吞吐/延迟取舍也能得到不同分数；不会把所有准确候选都截成 0。两个模式可复用完全相同的原始物理测量，但校准文件、目标和评分缓存分开。target 是本版本的工程标尺，不是已证明可达的全局最优结果。

## 验证、缓存及测量口径

- 同一技术库、corner、10 ns 约束、I/O 和 hold 修复流程用于全部准确基线及候选。DC 总面积按每个 leaf cell 的 library area 累加。
- 普通四态 RTL；mapped VCS 从全 0、全 1 和种子 20261121 三种时刻零寄存器初态运行。不得在运行中 force 或修补信号。此方法与经验局限见既有验证记录。
- `scoring_version/profile/policy_sha256`、协议、工具、源码和 declared II 均参与相应缓存身份。修改 declared II 不会复用旧候选得分。准确基线和候选必须来自同一 flow。
- 未完成扫描、工具或许可证错误标记为未评分，不当作有效零收益。缺匹配校准时，硬件可行性单独报告，`score_valid=false`；正式入口自动校准。
- 开源环境可运行默认面积 preview；当前 architecture 正式认证依赖 PrimeTime，不会使用 OpenSTA 的单点 slack 冒充等价频率扫描。
- 所有面积、认证频率、吞吐量为 synthesis / ideal-interconnect STA 口径；没有 post-route、功耗或能量结论。

v0.2/v0.3 原始结果保留。v0.3 的 `E/(1+E)`、0.5 参考分及由单点 slack 推算频率的排名规则已被本版本取代，不与新分数混用。
