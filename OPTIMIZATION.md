# Agent 可控综合流程：构建、导出与独立评测

本 benchmark 允许 Agent 同时探索 **RTL 架构与精度**和 **EDA 综合优化策略**。系统提供默认脚本，Agent 可在独立的公开开发环境中替换优化命令、参数和执行顺序。**正式评测不会执行所提交的任意 Tcl、Yosys 或 ABC 脚本；它评估 Agent 已导出的完整标准单元网表。**

## 1. 初始化可编辑模板

在 `FFT-Bench/` 根目录运行：

```bash
bash build_implementation.sh submission --init-flow
```

命令仅创建缺失文件，不覆盖已有修改，也不要求本机安装 EDA 工具。

| 文件 | 执行阶段 | 可探索的选择 |
|---|---|---|
| `submission/flow/dc_opt.tcl` | DC 完成 elaboration、link 和初始约束后 | `compile`/`compile_ultra`、effort、flattening、retiming、resource sharing、incremental compile 等 |
| `submission/flow/yosys_opt.ys` | Yosys 已读取 RTL 和 Liberty 后 | `synth`、`opt`、FSM/memory 优化及 pass 顺序 |
| `submission/flow/abc_opt.script` | FF 映射后、组合逻辑技术映射时 | `balance`、`rewrite`、`refactor`、`resyn2` 风格序列和映射策略 |
| `submission/flow/pnr_opt.tcl` | 可选 Innovus 初始化之后 | 布局布线及物理优化；**不参与当前评分** |

`resyn2` 并非可移植的 Yosys 顶层命令；可用 ABC 的一组 `balance`、`rewrite`、`refactor` 等命令构造相应序列。不同 ABC 版本对别名和命令的支持可能不同，请以容器内实际工具为准。ABC 模板最终必须完成合法标准单元映射；`{D}` 在公开构建时被替换为由 `--abc-delay-ps` 指定的目标。

DC 驱动通过 `FFT_AGENT_DC_RECIPE` 加载 Agent 的 Tcl；辅助文件可相对于该脚本所在目录引用。公开构建脚本维护工作目录、时序约束的初始加载、最终层次展开与网表导出。Agent 可以改变综合阶段的优化目标，**不得通过修改最终测量 SDC、Liberty、数值参考或评分公式改变成绩**。

## 2. 在 Synopsys 容器中构建

使用同级 `Synopsys/`（对应容器 `/mnt/mydata`）和 `port.txt`：

```bash
bash synopsys.sh build submission --export --out runs/dc_build
bash run_synopsys_debug.sh submission --profile area --out runs/dc_check
```

第一条命令在容器内运行 Agent 的优化脚本，并将 `mapped.v`、manifest 及 recipe 副本导出到 `submission/implementation/`。第二条命令在**可信评测流程**中导入并重新测量这些单元。完整 `architecture` profile 还包括长帧 II 测试和频率认证，耗时更长。

也可直接在容器内进行自定义调试：

```bash
bash synopsys.sh exec -- dc_shell -f /mnt/mydata/debug.tcl
```

只在 Agent 自己的工作目录中操作，不要修改全局库、工具配置或其他 Agent 的目录。

## 3. 使用 Yosys/ABC 构建

工具直接安装在本机时：

```bash
bash build_implementation.sh submission --backend local \
  --abc-delay-ps 10000 --out runs/yosys_build --export

bash fft64_benchmark/run_preview.sh submission runs/yosys_check \
  --backend local --profile area --no-build
```

也可将 Yosys/ABC 生成的合法 ASAP7 RVT/TT 网表交由 Synopsys 开发评价端测量：

```bash
bash run_synopsys_debug.sh submission --profile area --out runs/imported_check
```

这种跨工具构建**不会**改变最终的库和测量约束。公开预览在两个后端上都使用已公布的归一化函数与锚点，无需私有校准；同一个导出网表由不同 STA 后端得到的原始 PPA 和分数不得直接混排。正式隐藏评分还需匹配其测量平台和输入协议的校准。

## 4. 导出产物与正式评分边界

自定义综合的交付结构为：

```text
submission/
├── rtl/                  # 产生该实现的完整 RTL
├── flow/                 # 自定义优化 recipe 及辅助文件
└── implementation/
    ├── mapped.v          # 扁平化的结构化 ASAP7 标准单元网表
    ├── manifest.json     # RTL、网表、库和 recipe 的一致性信息
    └── recipes/          # 构建时使用的 recipe 副本
```

评测器检查 manifest 与当前 RTL、网表、固定库哈希的**一致性**，限制导入的结构化内容，独立统计映射单元面积、运行固定约束 STA，并在代表性测试上对比 RTL 与网表。正式隐藏环境不运行 Agent 的优化脚本，也不采用 Agent 自报的面积、频率或 SQNR。

**边界说明：** Agent 可自行编辑或生成 manifest，其哈希验证不构成可信的工具执行证明。因此，结果可信性主要来自评测器对导入网表的独立检查；如果实验要求证明某个 recipe 确实生成了网表，应另由可信构建环境保存带工具身份的执行记录。

对 RTL 或 recipe 作出更改后，应重新导出网表，使用新的构建与评测输出目录；不要将不同候选的报告或缓存混用。没有自定义 recipe 和网表时，正式评测采用冻结的默认综合流程。只有提交 recipe 而没有完整导出实现时，完整评价会拒绝继续，`--quick` 仍可进行 RTL-only 开发检查。

## 5. 评价范围与公平性

- **强制可行性：** FFT、逐帧 SQNR、输入/输出协议、复位、384-cycle 服务、10 ns 时序、RTL/网表一致性。
- **硬件质量：** 完整映射面积、经长时间验证的 II、STA 认证周期和最大首输出延迟。
- **固定测量条件：** ASAP7 RVT/TT、数值参考、正式 SDC、结果统计和评分标尺。
- **允许的优化：** 精确布尔重写、常数特化、资源共享、合法流水与复用，以及显式定点量化。
- **禁止的优化：** 任意门级 ALS/逻辑破坏、依赖测试数据的作弊实现、修改评分或隐藏检查。

准确参考设计使用冻结的默认映射 recipe 验证平台和协议，**其面积、吞吐率和延迟不设定归一化锚点**。候选可以使用其他 recipe，额外收益可以进入同一后端的硬件质量评分。完整公开 `architecture` 评测返回分项及总分，供 Agent 比较 RTL、精度和综合策略；`area` profile 仅作诊断。这一设置与仅优化 RTL 的固定 flow 实验不同，分析实验结果时应明确标记。

## 6. 可选物理设计与复现

`pnr_opt.tcl` 只是开发模板。需要匹配的 ASAP7 LEF、RC、site 和供电规划，且物理规模与单位必须经过验证；当前官方指标仍为 **pre-layout synthesis 与 ideal-interconnect STA**，没有 post-route PPA 或功耗分数。

独立输出目录是复现实验的基本要求。构建可在输入身份完全一致时复用产物；远程任务可用 `--resume` 恢复相同快照。工具、RTL、recipe 或库改变后需更换目录；`--export` 会在构建结果内备份被替换的旧实现。
