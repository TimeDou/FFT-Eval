# Codex-GPT-6.1-Sol-Max：FFT64-Quant v0.5 长帧验证

参考提交通过新规范，`resolved=true`，综合分数 **0.504748**。最低 SQNR **55.197422dB**，最大首输出延迟 **256 cycles**，实测最小 II **320 cycles/frame**。本分支是此前作者参考设计的迁移与重新验证，不冒充一次独立的新 Agent rollout，也不声称全局最优。

## 完整对照

同一 N=64、外部 P=1、ASAP7 RVT/TT、10ns 目标、VCS/DC/PrimeTime，全部通过必选规格。

| 设计 | Area µm² | 最大首输出 cycles | 实测 II | 认证周期 ns | 最低 SQNR dB | 综合分数 |
|---|---:|---:|---:|---:|---:|---:|
| 准确定点 R2SDF（逐帧隔离） | 3644.52 | 133 | 197 | 4.363281 | 70.292 | 0.202616 |
| 准确定点复用 radix-2 | 2437.28 | 256 | 320 | 3.839600 | 70.292 | 0.099199 |
| 量化 banking 参考提交 | 1614.78 | 256 | 320 | 3.820557 | 55.197 | 0.504748 |

每份设计均执行 8,192 个独立非零随机帧加 192 个 directed cases，共 8,384 帧数值测试。随机部分对应 524,288 个复数样本；加上 directed cases 共 536,576 个。FFT length 始终 64。

必选服务是 1,024 个连续帧、II=384，另有混合间隔、长空闲和复位。整数 II=64…384 的每一个点都执行 1,024 帧，合计 328,704 个帧事务；同一个 1,024 帧随机输入集合在不同 II 复用，不把这些重复事务称为独立随机样本。参考提交有 65 个通过点、256 个失败点，失败点完整保留。较短 II 失败不会否决必选服务。

每个完成帧的首输出与完成延迟都被测量，取最大值，不只看第一帧。逐 II/逐帧延迟保存在 `evaluation/designs/*/throughput/per_frame_latencies.npz`，未通过 II 的行用 -1 标注，失败原因及已观测极值另存 JSON/CSV。SQNR 采用所有适用测试的最低非零帧值，不用平均 dB。结果是有限样本证据，不是 formal worst-case error guarantee。

## 评分与 PPA

正式分数为 `0.6*S_A+0.3*S_T+0.1*S_L`。本平台准确参考面积 2437.28028µm²、面积目标 1218.64014µm²；吞吐参考为强制服务速率 260416.667 FFT/s，吞吐目标 2326754.496 FFT/s；延迟参考 300 cycles、目标 66.5 cycles。权重、比例及样本规模在本轮候选评测前冻结。

参考提交分项为 Area **0.674934**、Throughput **0.269814**、Latency **0.188437**。SQNR 达标不额外加分。10ns 下已验证服务为 312,500 FFT/s；认证周期 3.820556641ns 下吞吐估计为 817943.639 FFT/s（52.348393 M complex samples/s）。频率只通过吞吐计分，延迟分使用共同 10ns 时钟。

面积来自源码、库和物理流程均匹配的既有 DC 映射缓存；新的大样本数值、长服务、全部 II、代表性映射回放和时钟扫描均重新执行。没有将旧的数百帧结果重标为本轮结果。

商业映射验证使用三种时刻零初态（0、1、固定随机种子）。必选服务的代表性子集为 64 个随机帧加全部 directed cases，再加混合间隔尾部，共 272 个完整帧；最短通过 II 另测 128 帧加 16 帧尾部。与普通四态 RTL 对照输出内容及 valid/start 周期。没有声称对 8,384 帧都进行了映射网表仿真。

R2SDF 准确参考采用逐帧隔离控制，其实测 II=197 不是所有 R2SDF 架构的极限。原始 CSV、每帧误差、每个 II 的成功/失败、工具/库/RTL 哈希、源快照和一致性收据在 `evaluation/`。

## 复现

使用私有仓库的 `main` 评测器，对本分支 `submission/` 执行：

```bash
bash run_synopsys_docker.sh submission --agent Codex-GPT-6.1-Sol-Max --origin migrated-author-reference \
  --seed 2026112105 --scale 1 --jobs 2 --out /mnt/mydata/eval/agent_replay
```

本轮实际执行的不可变源码另存于 `evaluation/exact_campaign_source.tar.gz`，配套源文件哈希见 `source_snapshot.json`；标准单元库使用主分支的相同哈希版本，工具及 NumPy/Python 身份见 `platform_identity.json`。当前主分支后来补充了开源回退、部署提示及可选 II 声明的容错，这些未用于伪造或替换实测数据。

公开工具的实际 1,024+192 帧数值和 1,024 帧服务测试，以及开源 Yosys/ABC + Icarus/Verilator + OpenSTA 的公共诊断和独立时钟扫描，保存在 `evaluation/checks/`。开源数据不作为本商业分数的分母。所有物理数据是 pre-layout synthesis / ideal-interconnect STA，没有 P&R、功耗或真实芯片 Fmax 结论。

最终 75 项回归在宿主机与本机原生 Synopsys 容器 Python 上通过；新的商业/开源环境选择入口也都通过实际环境检测。单元测试中的合成测量夹具不替代上面实际的长帧仿真和 ASIC 数据。

实测全部结束后，旧快照仍在压缩大量逐周期文本；只停止了该冗余压缩，并用新版打包器生成约 19MB 的反馈包。原始测量目录完整保留，未中断任何实验。旧包装进程退出码为 143，恢复后的打包状态为 COMPLETE，见 `evaluation/checks/packaging_recovery.json`。
