# FFT-Bench：跨平台生成，统一 Synopsys 复测

这个分支用于出题人和实验人员统一复测设计。无论 RTL 是在 Yosys/Icarus/OpenROAD 还是 Synopsys 环境下生成，都用同一套 **VCS → DC → PrimeTime → mapped-netlist simulation** 获得最终分数。

`fft64_benchmark/` 是 agent 使用的纯题目目录；`operator/` 是复测及准确基线校准资源。给 agent 准备环境时只使用题目目录。优化后的参考解在另一个分支 `fft64-solution`，不放入本分支。

## 一键复测一个设计

将自包含的 RTL 提交目录同步到 Synopsys 平台，直接运行：

```bash
git clone --branch synopsys-eval git@github.com:TimeDou/FFT-Bench.git
cd FFT-Bench
bash run_synopsys.sh /workspace/submissions/agent_A \
  --origin open-source --agent agent_A --out /workspace/eval/agent_A
```

在 Synopsys 环境中生成的设计使用同一个命令，只需将来源标为 `--origin synopsys`。两类来源仅作为实验标签，不改变质量测试、面积参考或评分规则。

如果 agent 的结果保存在同仓库另一个分支，可用第二个普通 clone 保持评分器版本固定。这也兼容环境手册中的旧版 Git：

```bash
git clone --branch agent_A git@github.com:TimeDou/FFT-Bench.git ../agent_A
bash run_synopsys.sh ../agent_A/submission \
  --origin open-source --agent agent_A --out /workspace/eval/agent_A
```

这样可直接读取那个分支的设计，无需将 agent 的工具脚本合并进评分器分支，也不要求平台支持 `git worktree`。参考解分支可用同样方式读取。

提交目录沿用题目格式：`rtl/` 下为完整 RTL，顶层 `fft64_top`。多文件顺序可在 `design_config.json` 的 `rtl` 字段列出。读取的是源 RTL，不导入原平台的 mapped netlist、OpenROAD 面积、时序或自报分数；设计会在目标工具下重新编译和映射。

脚本自动加载平台 EDA profile，使用预装工具和 Python；只准备缺少的 NumPy/ASAP7 DB。**此入口固定使用商业流程，不回退到 Yosys，也不构建开源 EDA 工具。**

首次运行会在同一平台实测两份准确定点基线，取较小面积作为 `A_ref`。后续设计复用匹配的校准。通过全部硬件约束后，连续分数为 `clip(1-A/A_ref,0,1)`，通过目标为 `A/A_ref≤0.80`。这些仍是 pre-layout 面积与 ideal-interconnect STA，不称为 post-route。

DC 总面积按映射后每个 leaf instance 对应的 library cell area 累加；同一单元类型出现多次则按实例数计入，层级容器不重复计入。寄存器面积在同一遍历中统计，不依赖部分 DC 版本缺失的顶层 design `area` 属性。原始 `dc_area.rpt` 仍保留；机器结果的 `area_method` 标明统计方式。综合报错或面积/时序数据无效时停止，不生成有效评分。

## 多个 agent / 两组实验

准备 CSV，例如：

```csv
id,submission,origin,agent
oss_A,/workspace/submissions/oss_A,open-source,agent_A
oss_B,/workspace/submissions/oss_B,open-source,agent_B
syn_A,/workspace/submissions/syn_A,synopsys,agent_A
```

```bash
bash run_synopsys.sh --manifest /workspace/designs.csv \
  --jobs 2 --out /workspace/eval/comparison
```

相对路径按 CSV 所在目录解释。也可用 `--batch /workspace/submissions` 扫描直接子目录。并发默认 1，`--jobs` 最多 8；根据平台许可证与资源调整。

## 输出与恢复

- `scores.csv` / `summary.json`：各设计来源、agent、面积、SQNR、时序、物理延迟、分数和状态。
- `code_result.json`：单设计的 `resolved/score/reason`；批量运行则放在各候选目录。
- `candidates/`：实际使用的 RTL 快照、逐帧质量、映射网表、STA、仿真日志。
- `calibration.json`：本平台的准确参考面积和对应测量。
- `protocol.json`：本次全部设计共用的质量测试协议。
- `<输出目录>_feedback.tar.gz`：可回传分析的结果包，含校准诊断日志。

重复同一命令可恢复：成功完成、同源同协议同工具的点直接复用；未完成或基础设施错误的点重试。变更 RTL 会使用独立目录，不覆盖旧点。工具/许可证/库错误标为未评分，不当作已测得的零面积或有效零收益。

评分器或综合脚本更新会改变平台指纹，自动建立新的校准/候选缓存目录，不复用旧版本的失败结果或面积分母。无需删除 `.eval_state/`；旧记录保持可查。

`.eval_state/` 缓存平台校准和默认公共实验协议，不进入 Git。默认协议首次创建后在本平台所有设计间复用。跨服务器同步时显式使用同一 `--protocol /path/protocol.json`；首次也可用 `--seed 12345` 指定可复现的实验种子。实际最终测试协议应由出题人保存，和 agent 的公开开发输入分开。

只检查环境：

```bash
bash run_synopsys.sh --check-only --out /workspace/eval/environment
```

手册中的平台已有 VCS/DC/PrimeTime，但没有默认工艺库。若缺 DB，可设置 `FFT_LC_BIN`，或提前将匹配的两份 DB 放到 `fft64_benchmark/tech/db/`。脚本会给出实际缺项及反馈包。

Synopsys 工具入口可能是指向共享 `snps_shell` 的软链接。调用路径必须保留 `lc_shell`、`dc_shell` 等入口名称；不要把 `readlink -f` 的结果设置成工具命令。库编译失败时，反馈包的 `setup/library_compile.log` 和 `.log.json` 保存完整输出及实际 argv。

## 分支

- `main`：原始版本，保持不变。
- `synopsys-eval`：更新后的纯 benchmark、统一商业复测入口及准确校准资源。
- `fft64-solution`：基于本分支的参考解、重新生成的候选、实测结果与复现脚本。

源码和小型科学结果通过 Git 同步。许可证、编译后的 DB、工具安装及大型编译缓存保持平台本地。
