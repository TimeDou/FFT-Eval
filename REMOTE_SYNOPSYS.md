# 通过 SSH 使用本机 Synopsys 容器

## 目录和连接方式

预期目录布局：

```text
workspace/
├── FFT-Bench/            # 公开 benchmark 仓库
├── Synopsys/             # 挂载到容器内 /mnt/mydata
└── port.txt              # 仅包含 SSH 端口号
```

运行脚本从相邻的 `port.txt` 读取端口，默认连接 `root@localhost`，此实验部署的默认登录密码为 `passwd`；可以使用 `FFT_SSH_PASSWORD` 覆盖密码。**不要将密码写入提交内容、日志或结果文档。** 宿主机需要 Python 3.10+ 和 OpenSSH 客户端；商用工具在容器中执行，宿主机不需要安装 VCS/DC/PT。

容器应具备可运行的 VCS、Design Compiler、PrimeTime、Python 3.10+ 和 NumPy，以及可用许可证。若须将 Liberty 转换为 DB，还需要 Library Compiler。缺少合适 Python 时，部署方可运行：

```bash
bash check_env.sh --prepare-python
```

该操作使用经过 SHA-256 校验的独立 Python 二进制运行时，不替换容器系统 Python；离线部署可以额外提供 `--python-archive` 与包源/离线 wheel 配置。准备过程及来源保存在共享 runtime 中。

## 预先验证环境

从 `FFT-Bench/` 运行：

```bash
bash check_env.sh --out runs/environment
cat runs/environment/environment.json
```

`status=READY` 且返回码为 0 表示 SSH、双向共享目录、Python/NumPy、VCS 仿真、DC 映射以及 PrimeTime setup/hold 测试均已完成。仅使用 `--inspect-only` 时，成功状态为 `INSTALLED`，**不表示许可证或 EDA 执行已经验证**。原始工具日志位于结果目录，缺失环境、许可证或其他工具故障不得归类为 Agent 设计失败。

## Agent 开发流程

```bash
# 公开数值、协议和持续服务检查
bash run_synopsys_debug.sh submission --quick --out runs/quick_a

# 完整映射面积和 STA；area 诊断 profile
bash run_synopsys_debug.sh submission --profile area --out runs/area_a

# 默认综合评分 profile；包括长时间 II 扫描与频率认证
bash run_synopsys_debug.sh submission --profile architecture --out runs/arch_a
```

这些命令将当前提交快照复制到共享挂载内的独立工作目录，并通过 SSH 在容器中执行公开评价。结果链接与日志可在宿主机查看。

完整公开 `architecture` 评测无需私有校准，即可按公开公式返回 `grade.components`、`grade.weighted_components` 和 `grade.score`。有效预览标记为 `score_valid=true`、`scoring_scope=public_preview`、`official_score=false`，可直接用于比较候选。`--quick` 或未完成的测量没有完整硬件分数。最终隐藏评分使用相同的公开归一化参数，另外要求匹配的平台/协议校准和独立隐藏测试；准确参考设计不改变评分标尺。

只在确认输入快照、工具及选项未改变时恢复任务：

```bash
bash run_synopsys_debug.sh submission --profile architecture \
  --out runs/arch_a --resume
```

更换 RTL、recipe 或相关配置时请使用新目录；身份不一致的恢复应被拒绝。

## 自定义优化流程

```bash
bash build_implementation.sh submission --init-flow
# 修改 submission/flow/dc_opt.tcl
bash synopsys.sh build submission --export --out runs/custom_build
bash run_synopsys_debug.sh submission --profile area --out runs/custom_check
bash run_synopsys_debug.sh submission --profile architecture --out runs/custom_architecture
```

`build` 在**公开开发容器**执行 Agent 的优化 recipe，导出 `submission/implementation/mapped.v` 和 manifest；后续公开或隐藏评价只导入网表并独立计面积、STA、验证行为，**隐藏评分不会执行提交的优化脚本**。Yosys/ABC 与可选未评分 P&R 的用法见 [OPTIMIZATION.md](OPTIMIZATION.md)。

## 直接使用工具

```bash
bash synopsys.sh exec -- bash -c 'command -v vcs; command -v dc_shell; command -v pt_shell'
bash synopsys.sh exec -- dc_shell -f /mnt/mydata/debug.tcl
```

`exec` 默认在 `/mnt/mydata` 工作，可用 `--cwd` 指定其他容器目录。部署变体可指定 `--port`、`--port-file`、`--shared-dir`、`--mount`、`--ssh-host`、`--remote-python` 或 `--remote-profile`。更换容器 SSH 主机密钥时，应验证新密钥来源后仅更新相应主机记录。

## 数据隔离

每个 Agent 必须拥有独立的 `submission/`、`runs/` 和共享挂载工作区。**拥有容器 root 权限的 Agent 不能与隐藏评测环境共用数据可见的文件系统**；FFT-Eval 的准确参考设计、隐藏种子与校准数据必须保持私有。
