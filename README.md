# FFT-Eval：FFT64-Quant 出题方评测仓库

本仓库用于出题方评测，不放入 Agent 工作区。`main` 保存评测实现、准确校准基线、技术库和复现脚本；各 Agent 的提交及结果由出题方导入独立分支。Agent 只获得公开 FFT-Bench，不能读取本仓库、其 Git 凭据或评测共享目录。分支本身不是访问权限边界。

规范依据是 [FFT64-Quant.pdf](docs/FFT64-Quant.pdf)，实现版本为 v0.5。FFT 始终为 64 点，增加的是独立输入帧数。

| 测试 | 实际配置 |
|---|---|
| Public numerical | 1,024 个独立非零随机帧 + directed cases |
| Hidden numerical | 8,192 个独立非零随机帧 + directed cases |
| Mandatory sustained service | 1,024 个连续帧，II=384，另测复位、混合间隔和长空闲 |
| Throughput | 穷举整数 II=64…384；每个 II 都测 1,024 个连续帧 |
| Mapped consistency | 64 个随机帧 + 全部 directed cases；最短通过 II 另测 128 帧；商业后端用三种时刻零初态 |

零输入必须输出精确零。SQNR 使用适用测试中所有非零帧的最小值；每帧与同一量化输入的 double-precision FFT 比较，不修正增益、相位或顺序。Latency 使用各连续测试中所有完成帧的最大首输出延迟。Throughput 使用长时间测试通过的最小 II，不按提交中的理论 II 打分。较短可选 II 失败会保留记录，但不会否决满足 II=384 的设计。

## 一键评测

已有 Synopsys 平台：

```bash
bash run_synopsys.sh /workspace/submission --jobs 2 --out /workspace/eval/agent_A
```

本机 SSH Docker（共享目录默认 `/home/sj/ALS/DP2.0/DSBench/Synopsys`，容器挂载 `/mnt/mydata`）：

```bash
bash run_synopsys_docker.sh /path/to/submission --jobs 2 --out /mnt/mydata/eval/agent_A
```

SSH 密码交互输入，不保存到仓库。该入口使用已有 VCS/DC/PrimeTime/LC，不构建开源工具。不要把评测 Docker 的 SSH 凭据或整个共享挂载交给受测 Agent。

自动选择已安装后端，或显式使用开源环境：

```bash
bash run_evaluation.sh /path/to/submission --backend auto --jobs 2 --out /path/to/eval
bash run_evaluation.sh /path/to/submission --backend local --jobs 2 --out /path/to/local_eval
```

自动选择优先商业工具，其次为已有 Yosys/ABC、Icarus/Verilator、OpenSTA。缺失工具或许可证故障不产生正式分数；可显式选择可用后端重新启动完整评测。一个评测运行内部不混用后端。OpenSTA 使用独立时钟扫描和独立准确校准，不把商业面积当作开源分母。这里仍是综合与 ideal-interconnect STA，没有 post-route/power 结论。

官方默认使用文档中的 `architecture` 综合分数：60% Area、30% Throughput、10% First-output latency。`--profile area` 仅保留为诊断模式。SQNR 是硬约束，不额外奖励。通过与分数分离，零分也可 `resolved=true`。

默认隐藏种子由出题方首次运行时生成并保存在本地状态中，之后同平台复用。跨平台同步用 `--protocol protocol.json`；复现实验可显式指定 `--seed`。正式比较前固定协议、准确参考和目标。单次完整 II 搜索覆盖 328,704 帧；运行较久属正常，不能用少量帧搜索冒充完整结果。

## 数据与恢复

输出包括 `code_result.json`、`scores.csv`、逐帧数值误差、连续服务记录、每个 II 的通过/失败和帧延迟、映射报告、时钟扫描及工具/库/源码哈希。大体积逐周期文本留在本地运行目录；反馈包保留概要和可复现元数据，不重复打包全部文本波形。

每 64 个 II 保存一个检查点。重跑同命令复用完成的校准、映射和长区间结果；未完成的点会重试，不当作零收益。每次 Docker 运行使用独立源码快照。

## 历史与 Agent 分支

迁移前所有 FFT-Bench 提交均已保留在本仓库主分支的历史中；原分支头另以 `archive/fft-bench/*` 标签保存，核对记录见 [HISTORY_MANIFEST.json](migration/HISTORY_MANIFEST.json)。旧提交只作历史记录，不作为新长帧规范下的实测结果。

Agent 分支例如 `Codex-GPT-6.1-Sol-Max`。该分支中的 `submission/` 是提交，`evaluation/` 是对应新规范的结果。当前参考解由此前作者参考设计迁移，不冒充一次新的独立 Agent rollout。

公开仓库重新建立干净单分支历史。旧克隆、缓存的 commit 地址和平台缓存无法靠删除 Git 分支撤回，正式测试应使用全新 clone。GitHub 历史对象的物理回收由托管平台管理；如果需要撤销已经公开的信息，应另建从未承载该信息的公开仓库。

## NumPy installation without vendored binaries

Existing NumPy is reused. Missing NumPy is installed once by the shared setup path using the pinned binary requirement; pip index/mirror/cache configuration remains available. The Docker wrapper delegates dependency preparation to that same setup path.

For an offline Docker, place a wheel matching its Python/platform in an external directory under the shared mount, then pass that host path:

```bash
bash run_synopsys_docker.sh /path/to/submission \
  --wheelhouse /home/sj/ALS/DP2.0/DSBench/Synopsys/runtime/wheelhouse \
  --out /mnt/mydata/eval/agent_A
```

This directory is accessed through the shared mount and is not copied into the repository or the source snapshot. The option configures pip for offline installation only when NumPy is absent. Prior experiment histories and archived source remain unchanged.
