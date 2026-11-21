# 在本机 Synopsys 容器中开发

## 部署目录

```text
workspace/
├── FFT-Bench/         # 本仓库
├── Synopsys/          # 容器内挂载为 /mnt/mydata
└── port.txt           # 只含 SSH 端口数字
```

例如容器通过 `ssh -p 1234 root@localhost` 访问时，在 `port.txt` 中写入 `1234`。脚本自动读取该文件，默认使用 `root@localhost` 和密码 `passwd`。可用环境变量 `FFT_SSH_PASSWORD` 设置其他密码；密码不会写入运行记录。宿主机需要 Python 3.10+ 和 OpenSSH 客户端，不需要安装 NumPy、VCS、Yosys 或 Icarus，也不需要 `sshpass`。

容器内需要可用的 VCS、Design Compiler、PrimeTime，以及 Python 3.10+。从 Liberty 生成 DB 时还需要 Library Compiler。脚本优先复用已带 NumPy 的解释器，再尝试用现有 Python 安装缺少的 NumPy 二进制包；不会构建 EDA 工具或 Python。已有环境配置和许可证设置优先保留。

旧镜像的系统 Python 可能低于要求。部署方可以显式准备一个独立的预编译解释器：

```bash
bash check_env.sh --prepare-python
```

已有合适的解释器时不下载；缺少时仅为 Linux x86_64 容器下载并校验固定 SHA-256 的二进制 Python，放在 `Synopsys/.fft64/runtime/python/`，不改变容器系统 Python。离线部署可再指定 `--python-archive /host/path/to/archive.tar.gz`，以及通过 `--remote-profile` 配置 pip 的外部离线轮子目录或包镜像。运行来源记录在共享 runtime 的 `python_source.json`。

## 一键检查

在 `FFT-Bench/` 中运行：

```bash
bash check_env.sh
```

返回码为 0 且 `environment.json` 的 `status=READY`，表示以下检查全部通过：

1. 读取端口、SSH 登录，共享目录在宿主机与容器之间双向读写。
2. 找到容器内 Python、NumPy、VCS/DC/PT；准备 ASAP7 RVT/TT 组合及时序库的 DB。
3. 使用 VCS 实际编译、运行一个小型时序电路。
4. 对该电路执行 DC 映射和 PrimeTime setup/hold STA。
5. 在三种时刻零寄存器初态下比较映射网表和 RTL。

每次完整检查都会实际调用 VCS/DC/PT，不用已有映射结果替代许可证与执行检查；首次运行还可能需要编译库。结果和原始工具日志位于终端打印的 `Host results` 路径，默认是本仓库 `runs/synopsys_*/` 下的链接。例如固定结果名称：

```bash
bash check_env.sh --out runs/environment
cat runs/environment/environment.json
```

`--inspect-only` 只检查安装项，不验证许可证或实际工具执行；其成功状态为 `INSTALLED`，不能代替 `READY`。检查失败返回非零。端口、SSH 或挂载错误直接在终端显示；任务启动后的详情保存在 `environment.json`、`ssh.log` 和相应工具日志中。

## Agent 的开发命令

```bash
# 公开数值、协议和持续服务测试
bash run_synopsys_debug.sh submission --quick --out runs/candidate_a_quick

# 完整映射、STA、代表性映射网表检查；面积诊断
bash run_synopsys_debug.sh submission --profile area --out runs/candidate_a_ppa

# 默认综合指标：额外包含完整 II 测量与频率认证，耗时较长
bash run_synopsys_debug.sh submission --profile architecture --out runs/candidate_a_full
```

这些命令使用容器内的商业工具和公开测试数据。没有匹配的冻结校准时仍会提供数值、协议、面积和时序反馈，但不产生有效的正式分数。环境检查使用的小型电路不参与 FFT 评分。

脚本将公开评测工具与当前提交复制到独立目录后运行。宿主机的结果链接指向 `Synopsys/.fft64/jobs/<job>/output/`，无需复制大型波形或向量文件即可读取反馈。容器内路径会一并打印。库 DB 和满足相同物理流程身份的映射缓存可复用。

修改设计时使用新的结果目录。若输入、工具和配置均未改变，可显式恢复相同任务：

```bash
bash run_synopsys_debug.sh submission --profile architecture \
  --out runs/candidate_a_full --resume
```

输入身份不一致会拒绝恢复，并保留已有结果。

## 直接调用工具进行调试

```bash
bash synopsys.sh exec -- bash -c 'command -v vcs; command -v dc_shell; command -v pt_shell'
bash synopsys.sh exec -- vcs -ID

# 宿主机 Synopsys/debug.tcl 对应容器内 /mnt/mydata/debug.tcl
bash synopsys.sh exec -- dc_shell -f /mnt/mydata/debug.tcl
```

`exec` 默认工作目录为 `/mnt/mydata`，可通过 `--cwd` 指定容器内其他目录。它不要求先通过 Python 或数值环境检查。

非标准部署可在 `synopsys.sh`、`check_env.sh` 或 `run_synopsys_debug.sh` 中指定 `--port`、`--port-file`、`--shared-dir`、`--mount`、`--ssh-host`、`--remote-python` 或 `--remote-profile`。例如：

```bash
bash check_env.sh --remote-python /opt/dsbench/bin/python3
```

`--remote-profile` 是容器内 shell 配置文件路径。容器重新创建并更换 SSH 主机密钥时，脚本会报告密钥不匹配；只更新该容器对应的已知主机记录后重试。

## 评测部署

每个被测 Agent 使用独立的开发容器和 `Synopsys/` 目录。该目录及容器内只放公开开发工具与该 Agent 的文件。正式隐藏评测使用独立的 FFT-Eval 环境；具备容器 root SSH 权限的 Agent 不应与隐藏数据或其他 Agent 的结果共用文件系统。
