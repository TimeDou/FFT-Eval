# 出题人使用说明

## 部署

将本目录放到 `/workspace/benchmark/`，运行 `bash setup.sh commercial`，然后保存 agent 初始环境。任务提示使用 `TASK_ZH.md` 或 `TASK_EN.md`，提交目录为 `/workspace/submission/`。

本目录可独立交给 agent；解题目录只用于出题人校准。当前仅提供架构说明与接口。若以后提供准确 RTL 起点，请作为 Assisted 模式另行统计。

## 校准面积

在出题人容器中准备两份准确实现，使用与正式评估相同的流程：

```bash
python3 tools/calibrate.py --backend commercial \
  --baseline /path/to/accurate_sdf \
  --baseline /path/to/accurate_iterative \
  --out /path/to/calibration_run
```

每份实现也使用 `rtl/` 布局和 `fft64_top` 接口。所有基线验证成功后，会生成 `area_reference.json`。审核实测结果与 0.80 通过目标，然后将这个文件作为该版本的面积参考。agent 可通过 `FFT_CALIBRATION` 使用它。

平台若没有默认的 Python 3.10+，将命令中的 `python3` 换成 `/opt/dsbench/bin/python3`。Liberty 原生单位为 ps/fF，随题 SDC 已按 10 ns、0.1 ns uncertainty、1 fF load 配置。

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
