# FFT64 参考解：本机 Synopsys v0.3 结果

现有量化 banking radix-2 RTL 在本机 SSH Docker 中通过完整 VCS/DC/PrimeTime 流程。**376 帧**全部满足逐帧 SQNR≥50 dB、复位与帧协议、10 ns 时序及截止时间；全 0、全 1、种子 20261121 三种 gate 时刻零初态均与 RTL 对照一致。

| 指标 | 实测 |
|---|---:|
| 完整标准单元面积 | 1614.77874 µm² |
| 寄存器面积 | 804.23280 µm² |
| STA 限制周期 | 3.815013184 ns |
| STA Fmax 估计 | 262.1223 MHz |
| 目标时钟 / 已验证帧 II | 10 ns / 384 cycles |
| 目标时钟下服务速率 | 16.6667 M complex samples/s |
| 首输出 / 完成延迟 | 256 / 319 cycles（2560 / 3190 ns） |
| 最低逐帧 SQNR | 55.303911 dB |
| v0.3 连续分数 | 0.602318764 |
| resolved | true |

同平台准确复用 radix-2 的面积为 2436.05556 µm²，参考解面积下降 33.71%。两份准确基线和参考解均通过规格；v0.3 没有最低面积降幅或分数门槛。

评分为 `E/(1+E)`，其中 `E` 是相对准确参考点的吞吐量/面积效率，频率通过吞吐量计入一次。当前共同测试 II=384，不将该负载解释为最小固有 II。原有参考解不因这次评分规则更新而被宣称为新的全局最优解。

```bash
bash run_synopsys_docker.sh fft64_solution \
  --origin reference --seed 20261121 --scale 3 --jobs 2 \
  --out /mnt/mydata/eval/fft64_reference
```

详细复现方法、真实工具版本、修复分析及两份基线对照见 [operator/LOCAL_SYNOPSYS.md](../operator/LOCAL_SYNOPSYS.md)。完整小型原始数据在 [results/synopsys_v03_20261121/](results/synopsys_v03_20261121/)，最新商业状态在 [results/SYNOPSYS_LATEST.json](results/SYNOPSYS_LATEST.json)。

这是 pre-layout cell area / ideal-interconnect STA，未完成 P&R 或功耗测量。旧 [RESULTS.md](RESULTS.md)、`measurements.csv` 与 `results/status.json` 只记录历史 v0.2 开源实验，保留原始分数，不与本次商业数据混用。
