# 重新生成的 FFT64 参考解

当前 **v0.4 商业验证已完成**：参考解 `resolved=true`，面积模式 **0.674934**、架构模式 **0.502826**，验证 II=320。见 [SYNOPSYS_V04.md](SYNOPSYS_V04.md)。v0.3 商业与 v0.2 开源结果保留为历史记录，不与新分数混用。

本目录基于同仓库的 `fft64_benchmark/` 和 `synopsys-eval` 分支重新生成并验证。旧实验结果没有拷入本目录。RTL 生成器沿用原创实现，对新版本重新测量，并使用新的留出种子确认。

它是出题人的参考解，不是一次独立 agent 从零完成任务的 rollout。候选搜索是有限采样，不声称全局最优。

## 在 Synopsys 平台直接评分

```bash
git clone --branch fft64-solution git@github.com:TimeDou/FFT-Bench.git
cd FFT-Bench
bash run_synopsys.sh fft64_solution \
  --origin reference --agent author --out /workspace/eval/fft64_reference
```

也可以运行 `bash fft64_solution/run_platform.sh --out /workspace/eval/fft64_reference`。两种入口调用同一评分器、相同准确基线和相同实验协议；不另建一套参考解专用商业流程。

平台返回的 `<输出目录>_feedback.tar.gz` 包含真实 VCS/DC/PT 数据。源码生成时的开源面积和分数不会作为商业评分输入。

## 开源环境复现

在仓库根目录准备或检查已有工具，然后重新生成和测量：

```bash
bash fft64_benchmark/setup.sh local
bash fft64_solution/run_local.sh --workers 2
python3 fft64_solution/tools/report.py
```

如 Python、ABC 或 OpenSTA 不在默认路径，用 `FFT_PYTHON`、`FFT_ABC`、`FFT_STA` 指定；例如 `FFT_PYTHON=/path/to/python3`。脚本只依赖同仓库 benchmark 和指定的工具，不依赖原工作区路径。

## 结果与文件

- `rtl/`、`design_config.json`：选定的完整 RTL 和配置。
- `candidates/`：准确架构、精确 banking、量化、流水切分和失败候选。
- `DESIGN_PLAN.md`、`measurements.csv`、`RESULTS.md`：选择依据与实测数字。
- `results/`：新一轮的状态、逐帧质量、映射/STA、命令记录、源/库哈希和留出结果。
- `tools/`：生成、整数模型、求解和报告脚本。

Git 保存源码、CSV/JSON、网表、逐周期输出和关键工具报告。编译缓存、可再生成的输入向量及重复中间表示留在本机，按保存的种子、源码和命令即可重新生成。商业 PPA 与 post-route 状态单独报告；开源验证通过不代替真实商业执行。
