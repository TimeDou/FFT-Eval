# 自主选择综合与实现策略

Agent 可以优化 RTL，也可以选择 EDA 工具的优化命令、顺序和参数。提供的脚本是一套可运行的默认方案，可以复制到自己的提交中修改或整体替换。

## 可编辑的接口

在仓库根目录初始化模板：

```bash
bash build_implementation.sh submission --init-flow
```

这条命令只创建缺少的文件，不覆盖已有脚本，也不要求宿主机安装 EDA 工具。

| 提交中的文件 | 调用时机 | 可以探索的内容 |
|---|---|---|
| `flow/dc_opt.tcl` | DC 完成 RTL elaboration、link 和默认约束后 | `compile` / `compile_ultra`、面积或时序导向、incremental compile、合法 retiming、资源共享、层次处理、app variables |
| `flow/yosys_opt.ys` | Yosys 已读入 RTL 与库后 | `synth`、`opt`、FSM、memory、资源共享与 pass 顺序 |
| `flow/abc_opt.script` | Yosys 完成 FF 映射、提取组合网络后 | `balance`、`rewrite`、`refactor`、`resyn2` 对应的命令序列、Liberty 映射与尺寸调整 |
| `flow/pnr_opt.tcl` | 可选 Innovus 流程完成设计及物理库初始化后 | floorplan、placement、CTS、routing 和各阶段优化 |

`rewrite`、`resyn2` 是 ABC 的布尔网络优化命令/脚本，而不是 Yosys 的顶层 pass。ABC 是否定义 `resyn2` 别名取决于启动配置；模板注释提供了展开后的命令序列。`{D}` 由构建脚本替换为 `-D <ps>`，取值由 `--abc-delay-ps` 指定。ABC 脚本需要保留最终的标准单元映射步骤。

不同工具安装可能支持不同命令。可以直接查看容器内工具帮助或运行自己的调试脚本：

```bash
bash synopsys.sh exec -- dc_shell -f /mnt/mydata/debug.tcl
```

提交中的 `flow/` 会随构建任务一起复制。DC 构建时的工作目录为构建目录；辅助脚本可使用 `[file join [file dirname $::env(FFT_AGENT_DC_RECIPE)] helper.tcl]` 定位。脚本可使用 `FFT_WORK`、`FFT_TASK_ROOT`、`FFT_TECH_DIR` 环境变量。可替换整个优化主体；最后的平坦化、合法 Verilog 命名和网表导出由 wrapper 完成。

## 在 Synopsys 容器中构建

修改 `submission/flow/dc_opt.tcl`，然后运行：

```bash
bash synopsys.sh build submission --export --out runs/dc_build
bash run_synopsys_debug.sh submission --profile area --out runs/dc_check
```

构建入口自动读取同级 `port.txt`，调用已有容器中的 DC。第一条命令执行 Agent 的优化脚本，并将生成的实现放入 `submission/implementation/`；第二条命令对该实现做公开数值、协议、面积、STA 和代表性映射网表验证。需要完整吞吐率与频率测量时再使用 `--profile architecture`。

若工具直接安装在当前环境中：

```bash
bash build_implementation.sh submission --backend commercial --out runs/dc_build --export
```

## 在 Yosys/ABC 环境中构建

修改 `flow/yosys_opt.ys`、`flow/abc_opt.script` 后运行：

```bash
bash build_implementation.sh submission --backend local \
  --abc-delay-ps 10000 --out runs/yosys_build --export

# 在同一开源环境中评价
bash fft64_benchmark/run_preview.sh submission runs/yosys_check \
  --backend local --profile area --no-build

# 或将生成的标准单元网表直接交给 Synopsys 测量
bash run_synopsys_debug.sh submission --profile area --out runs/synopsys_check
```

开源构建需要已有的 Python/NumPy、Yosys 和 ABC；开源完整评价另需仿真器和 OpenSTA。构建不要求安装 OpenSTA。跨环境时保留整个 `submission/`，包括 RTL、`flow/` 和 `implementation/`。商业评价会直接测量导入的网表，**不会重新综合成另一份网表**；因此可以评价开源优化产生的实际电路。

## 哪些结果参与评分

`implementation/` 包含平坦的 `mapped.v`、`manifest.json` 和所用 recipe 的副本。Manifest 绑定 RTL、映射网表及提供的组合/时序 Liberty 文件；构建目录另存命令、工具哈希、原始报告和执行时间。RTL 或 recipe 修改后应重新构建，并使用新的结果目录。

评测端从映射网表独立统计全部单元面积，使用统一库和约束执行 STA，并与提交 RTL 比较数值及周期行为。Agent 的 Tcl/YS/ABC 脚本在公开开发环境中执行；正式隐藏评测只接收其实现产物，不执行这些脚本，也不采用自报面积、时序或 SDC。

不提供自定义实现时，评测端使用默认综合模板。提交了自定义综合脚本却没有导出实现时，完整评价会提示先构建；`--quick` 仍可单独检查当前 RTL。

综合时可以用更紧的 delay target 等设置引导优化。最终的 ASAP7 RVT/TT、10 ns 必选时序、I/O 假设、SQNR、连续帧测试及评分公式对所有候选相同。Retiming 和流水调整仍须保持规定的时钟、同步复位和外部事务行为。精确布尔优化允许，门级 ALS 和任意近似逻辑剪枝仍不允许。

可以比较同一 RTL 在不同 recipe 下的面积、时序及构建耗时，并将 recipe 标识与测量记录一起保存。正式排名前由出题方冻结测量流程、默认准确参考、工具库与评分标尺；候选的优化 recipe 属于设计选择。开源与商业测量仍需各自校准，不能混用面积分母。

## 布局布线

当前评分依据 synthesis + ideal-interconnect STA。仓库提供可替换的 Innovus 主体，但运行它需要匹配 ASAP7 的 LEF、RC、site 和电源规划，并配置 `fft64_benchmark/flow/pnr_config.example.tcl` 所要求的内容。`FFT_PNR_OPT_FILE` 指向自己的 `pnr_opt.tcl`；`FFT_PNR_CONFIG` 指向已填写的物理配置。

这部分是可选开发接口，尚未在提供的容器和物理套件上完成验证，也不影响当前分数。拥有完整物理环境后，可以用相同方式开放 P&R recipe，再由统一 post-route 评测测量其收益。

## 保存和恢复

每个构建使用独立 `--out`。输入不变时，本地构建会复用完成的产物；SSH 任务可加 `--resume` 恢复相同快照。改变 RTL、recipe、库或工具后需新建输出目录。`--export` 替换旧实现前会将其备份到该次构建结果的 `export_backup/`。导出后提交目录内容已改变；再次使用 SSH `--resume` 时必须与原快照一致，否则使用新的输出目录。
