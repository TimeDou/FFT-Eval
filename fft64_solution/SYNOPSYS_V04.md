# FFT64 参考解：Synopsys v0.4 双模式结果

同一份量化 banking radix-2 RTL 在两个模式中均通过，SQNR 达标不加分：

| 指标 | 实测 |
|---|---:|
| 完整 cell area | 1614.77874 µm² |
| Register area | 804.23280 µm² |
| Area Profile | **0.674934，PASS** |
| Architecture Profile | **0.502826，PASS** |
| 经完整 RTL/mapped 验证的声明 II | 320 cycles/frame |
| 认证通过周期 / 频率 | 3.820556641 ns / 261.7420 MHz |
| 10 ns 下连续服务 | 312500 FFT/s，20 M complex samples/s |
| 认证时钟下持续吞吐估计 | 817943.639 FFT/s |
| 首输出 / 完成延迟 @10ns | 256 / 319 cycles，2560 / 3190 ns |
| 首输出延迟 @认证时钟 | 978.0625 ns |
| 最低逐帧 SQNR | 55.303911 dB |
| Worst hold slack @10ns | 0.037591587 ns |

这是评分机制及测量协议更新，RTL 未重新优化。参考解在新共用 hold 修复流程下无需额外单元，面积与 v0.3 相同；准确复用基线需修复，其面积变为 2437.28028µm²。两种模式采用同一份实际 mapped netlist，但有独立校准和不同权重，不能将两个分数作相对性能比较。

面积模式验证原来的 384-cycle 最小工作负载。架构模式额外在 320 cycles/frame 连续运行完整 376 帧和 16 帧混合间隔尾部，三个 mapped 时刻零初态均与 RTL 一致。故意声明 319 cycles/frame 时，仅输出 200/392 帧，按协议失败处理；不会因为某个面积或分数门槛而失败。

```bash
bash run_synopsys.sh fft64_solution --profile area --origin reference --out /workspace/eval/area
bash run_synopsys.sh fft64_solution --profile architecture --origin reference --out /workspace/eval/architecture
```

本机 SSH Docker 使用 `run_synopsys_docker.sh`。两个模式及准确架构对照、校准值、PDF/PNG 图、完整小型原始数据和版本说明见 [v0.4 实测报告](../operator/results/scoring_profiles_v04/README.md)；定义见 [SCORING.md](../fft64_benchmark/SCORING.md)。`design_config.json` 的 `frame_ii_cycles=320` 是本次实际验证的声明，面积模式不据此加吞吐分。

保留的 [SYNOPSYS_RESULTS.md](SYNOPSYS_RESULTS.md) 是 v0.3；`RESULTS.md`、`measurements.csv` 和原 `results/status.json` 为更早的开源结果。它们没有重标为新版本。所有当前物理数据属于 pre-layout synthesis / ideal-interconnect STA；没有 P&R、功耗或真实芯片 Fmax 结论，验证也不是形式化全输入保证。
