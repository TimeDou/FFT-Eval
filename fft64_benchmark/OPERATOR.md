# 出题人使用说明

## 部署

将本目录放到 `/workspace/benchmark/`，先运行 `bash setup.sh --check-only` 查看已有工具，再运行 `bash setup.sh` 准备缺失依赖。脚本会加载平台已有环境，优先选 VCS/DC/PrimeTime；不要求 agent 重新构建 Yosys/Icarus。完成准备后保存初始环境。任务提示使用 `TASK_ZH.md` 或 `TASK_EN.md`，提交目录为 `/workspace/submission/`。

本目录可独立交给 agent；解题目录只用于出题人校准。当前仅提供架构说明与接口。若以后提供准确 RTL 起点，请作为 Assisted 模式另行统计。

## 校准面积

在出题人容器中准备两份准确实现，使用与正式评估相同的流程：

```bash
python3 tools/calibrate.py --backend commercial \
  --baseline /path/to/accurate_sdf \
  --baseline /path/to/accurate_iterative \
  --out /path/to/calibration_run
```

每份实现也使用 `rtl/` 布局和 `fft64_top` 接口。所有基线验证成功后，会生成 `area_reference.json`。准确参考点按吞吐量/面积效率选择，面积、period、II 来自同一份真实实现。所有硬件约束通过即通过；不存在 0.80 面积比例门槛。评分公式见 `SCORING.md`。agent 可通过 `FFT_CALIBRATION` 使用它。

平台若没有默认的 Python 3.10+，将命令中的 `python3` 换成 `/opt/dsbench/bin/python3`。Liberty 原生单位为 ps/fF，随题 SDC 已按 10 ns、0.1 ns uncertainty、1 fF load 配置。手册说明平台没有预置工艺库，因此仍需用随题 Liberty/DB，不需另装 EDA 软件。

正式测试时使用校准后固定的后端。自动选择是为了适配开发环境，评分不会因许可证或工具故障静默换成另一种面积流程。可设置 `FFT_NO_BUILD=1`，避免模型试验期间触发源码构建。

## DSBench Code Grade

在完成商业校准后，运行：

```bash
python3 grading/make_grader.py --out /path/to/grading_files \
  --calibration /path/to/area_reference.json
```

把生成的 `test_by_code.py` 用作 Code Grade，把 `fft64_grader.zip` 和 `area_reference.json` 放入 `/test_files`。附件只含评估代码、种子和面积参考；库与工具已经安装在环境中，附件总大小应小于 1 MB。

评分运行独立代码副本，读取 `/workspace/submission/`，结果写到 `/eval/code_result.json`，只有 `resolved`、`score`、`reason` 三项。详细结果在 `/eval/fft64_measurements/`。

在没有商业校准前，可生成不带面积参考的附件检查部署流程，但不能据此产生正式面积得分。公开 preview 与最终评估使用不同随机种子。每个模型的重复试验次数、时间与 CPU 配额应统一设置。

## 可选物理设计

`flow/pnr_config.example.tcl` 和 `flow/pnr_innovus.tcl` 是 Innovus 模板。需要匹配这套单元的 LEF、RC、SITE 和电源规划；填好配置并确认单位后，使用环境变量 `FFT_WORK`、`FFT_TASK_ROOT`、`FFT_PNR_CONFIG` 运行。此扩展不参与本版本 pre-layout 排名。
