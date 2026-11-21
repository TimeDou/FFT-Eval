# FFT64-Quant v0.5 评分

以 `docs/FFT64-Quant.pdf` 第 2.4–2.5 节为依据。默认 `architecture`：

```
S_A = clip((A_ref - A)/(A_ref - A_goal), 0, 1)
S_T = clip((T_eff - T_req)/(T_goal - T_req), 0, 1)
S_L = clip((300 - max_first_output_cycles)/(300 - L_goal_cycles), 0, 1)
score = 0.6*S_A + 0.3*S_T + 0.1*S_L
```

`A_ref` 为同后端准确校准设计中最小完整面积，`A_goal=0.5*A_ref`。`T_req=1e9/(384*10)` FFT/s，`T_goal` 为准确校准最大实测吞吐的两倍。`L_goal` 为最短准确首输出延迟的一半，并不低于 63 cycles。目标比例、权重和输入规模在本轮候选评测前冻结，见 `profiles/policy.json` 与 `PRE_REGISTERED.json`。

`T_eff=1e9/(certified_period_ns * measured_II)`。在同一 mapped netlist 上重新施加时钟并更新 STA，使用 setup/hold 通过端点，失败/通过周期区间不超过 0.01 ns；不从单点 slack 推断 Fmax。商业和开源后端分别认证、分别校准。所有频率都是 pre-layout ideal-interconnect STA 估计。

II=64…384 的每个整数点至少测试 1,024 个连续帧。评分采用通过长测试及代表性映射一致性验证的最小 II。提交中的 `frame_ii_cycles` 可作说明，但不决定正式分数。可选较短 II 失败不导致满足 384-cycle 必选服务的设计被否决。所有失败点保留。

Latency 是连续测试中每帧首输出延迟的最大值，包含最后一帧；完成时间也逐帧检查。延迟项使用共同 10 ns 时钟，避免通过吞吐和延迟重复奖励频率。

Hidden numerical 至少 8,192 个独立非零随机帧，另加 directed cases；Public numerical 至少 1,024 个。FFT length 固定为 64。每个非零帧必须 SQNR≥50dB，所有适用测试的最小 SQNR 决定可行性；零帧精确输出零。更高 SQNR 不加分。映射仿真用代表性数值/协议子集，不能把该子集冒充 8,192 帧完整隐藏数值测试。

`resolved` 只取决于必选数值、协议、复位、时序和 RTL/mapped 一致性规格。硬件分数低或为零不影响通过。工具、校准或未完成测量不产生正式分数。`--profile area` 仅为开发诊断保留，不能与正式组合分数混排。

这是有限样本验证，不是 formal worst-case error guarantee。历史 v0.2–v0.4 结果未按新规范重标，保存在出题方历史归档中。
