# 本机 Synopsys 完整验证（2026-11-21）

N64 FFT benchmark v0.3 已在本机 SSH Docker 中完整跑通。准确 R2SDF、准确复用 radix-2 与原有量化 banking 参考解均通过 **376 帧**的 RTL 数值/协议测试、DC 综合、PrimeTime STA，以及三种时刻零初态下的完整映射网表对照。

## 实测结果

| 设计 | 完整面积 µm² | STA 限制周期 ns | Fmax 估计 MHz | 最低逐帧 SQNR dB | 首输出/完成 cycles | 连续分数 | 基本规格 |
|---|---:|---:|---:|---:|---:|---:|---|
| 准确 R2SDF | 3644.52 | 4.3625 | 229.23 | 70.58 | 133/196 | 0.369820 | PASS |
| 准确复用 radix-2 | 2436.06 | 3.8301 | 261.09 | 70.58 | 256/319 | 0.500000 | PASS |
| 量化 banking radix-2 参考解 | 1614.78 | 3.8150 | 262.12 | 55.30 | 256/319 | 0.602319 | PASS |

所有设计均为 N=64、输入/输出 P=1，使用相同 ASAP7 RVT/TT 组合与时序库、10 ns 时钟、384 cycles 帧负载、50 dB 逐帧 SQNR 要求。参考解相对同平台准确复用 radix-2 的完整面积降低 **33.71%**。其首输出/完成延迟为 2560/3190 ns；目标时钟下服务速率均为 16.6667 M complex samples/s。

这些是实际 VCS/DC/PrimeTime 工具结果，面积为 pre-layout standard-cell area，频率为 ideal-interconnect STA 估计；没有完成 P&R 或功耗测量。STA 支持的速率估计另列在 CSV 中，不将共同负载当作架构固有最小 II。

## 一键运行

在 `fft64-solution` 分支的仓库根目录：

```bash
bash run_synopsys_docker.sh fft64_solution \
  --origin reference --seed 20261121 --scale 3 --jobs 2 \
  --out /mnt/mydata/eval/fft64_reference
```

默认宿主机共享目录是 `/home/sj/ALS/DP2.0/DSBench/Synopsys`，容器内为 `/mnt/mydata`。脚本通过 `root@localhost:1234` 登录；密码由 SSH 交互读取，不保存在代码中。输入目录可换成任何 agent 的本机提交目录，脚本会复制自包含 RTL 到独立源码快照。

首次运行复用预装 EDA 工具，仅准备独立 Python/NumPy 和对应 ASAP7 DB。源码快照、结果和工具缓存均放在共享目录。`--shared-dir`、`--container-share`、`--ssh-host`、`--ssh-port` 可覆盖默认位置；工具和许可证服务默认配置见 `docker_env.sh`。

在新版 DSBench 原生环境继续使用 `run_synopsys.sh`，无须 Docker 宿主机入口。工具版本变化后按新平台重新校准，不能沿用这里的面积分母。

## 评分

通过基本硬件规格即 `resolved=true`，没有 0.8 分数或面积比例门槛。定义

```text
E = (A_ref/A) * (II_ref/II_verified) * (T_ref/T_STA)
score = E / (1+E)
```

参考点来自两份已验证准确实现中，吞吐量/面积效率最高的一份真实设计；本次为准确复用 radix-2，其分数是 0.5。频率通过吞吐量计入一次，延迟保留为硬性规格并单独报告。当前 II_verified=384，因此没有给未验证的更短 II 额外奖励。详细定义见 [SCORING.md](../fft64_benchmark/SCORING.md)。

本次参考解的分数为 **0.602319**，`resolved=true`。准确 R2SDF 的 0.369820 同样是 PASS。工具/许可证故障报告为未评分，不能作为有效的零分设计。

## 实际修复与验证

1. 保留 `lc_shell`、`dc_shell` 的入口名称；旧 LC 文本启动器缺少 shebang 时通过 Bash 执行，保持 `$0`，解决 Python 直接启动时的 Exec format error。
2. 使用容器已有的 `27000@localhost` 许可证服务；VCS 使用 full64。两份 Liberty 已由实际 LC 转为 DB。
3. VCS 编译缓存改到每个运行目录，避免不同 RTL/netlist 或并行任务共享 csrc。即使旧 VCS 在 Fatal 后返回 0，也会根据日志判失败。
4. 对准确迭代基线出现的控制 X，提取 138-cell 控制网络并复现；SAT 证明 24 个控制寄存器在任意二值当前状态下均能复位归零。复位重汇合会产生 `q | ~q` 的四态 X 悲观性。正式流程从全 0、全 1 与种子 20261121 三种初态完整运行，之后不强制任何信号；每个初态都必须逐周期、逐有效样本匹配普通四态 RTL。数值和服务规格保持不变。
5. 两份准确基线可用独立进程并行运行；每个工具任务保留独立目录。映射、时序和质量数据缓存仍按完整来源与协议核对。

复位 SAT 只证明上述控制复位性质，不声称完成全 FFT 的形式化等价证明。早期失败记录、控制锥、SAT 日志和三初态诊断保存在 `results/synopsys_20261121_v03/diagnostics/`。

## 工具与重现记录

实际工具为 VCS L-2016.06 Full64、DC L-2016.03-SP1、PrimeTime M-2016.12-SP1、LC M-2016.12；运行环境为 Python 3.12.10、NumPy 2.2.6。Python 使用固定 [python-build-standalone 发布包](https://github.com/astral-sh/python-build-standalone/releases/tag/20250529)，下载地址及 SHA256 写入运行时来源记录。

57 项控制/打包/评分测试在宿主机和容器的 Python 下均通过；参考解原有 7 项回归、13 项环境测试、5 项缓存测试也通过。相同命令、相同输出目录重跑耗时 **7.80 s**，返回 `reused=true`，未重复运行 VCS/DC/PT。

完整小型证据位于 [results/synopsys_20261121_v03/](results/synopsys_20261121_v03/)：CSV/JSON、逐帧质量、DC/PT 报告、工具/库/RTL 哈希、源码快照来源、失败诊断及复用记录。大型日志与映射网表保留在共享目录的 `eval/official_v03_r2/`、`eval_state/`、`jobs/` 及对应反馈归档中。
