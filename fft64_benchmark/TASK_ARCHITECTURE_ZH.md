# FFT64 架构与吞吐优化任务

先阅读 `TASK_ZH.md`，沿用其数学 FFT、输入范围、50 dB SQNR、输出顺序、顶层接口、复位、10 ns 时序与输出截止要求。本任务明确使用 **v0.4 architecture profile**；无需 ALS。

在可行的 FFT 架构之间选择，并用精度/量化、常数专用化、存储/资源共享和合法流水优化提高得分。排名为 60% 完整映射面积、30% 已验证持续吞吐、10% 首输出延迟，精确定义和预先冻结的标尺见 `SCORING.md`。频率只通过吞吐量计分，SQNR 达标不额外加分。

在 `design_config.json` 声明 `frame_ii_cycles`（整数 64–384，默认 384）。平台会在该间隔下连续输入多帧，并测试混合间隔、长空闲及复位。不能将首次输出延迟或某一个成功的帧当作可持续启动间隔。每个输入帧仍按原接口连续输入 64 个样本。

```bash
bash run_preview.sh /workspace/submission /workspace/runs/architecture \
  --profile architecture --backend commercial
```

开发期可以加 `--auto-ii` 寻找通过小样本探测及完整验证的最短经验间隔，然后将最终声明写入配置；正式评测按声明验证。时钟频率来自固定 mapped netlist 的 PrimeTime setup/hold 扫描。只有开源工具时，默认面积 preview 仍可使用；不能把固定时钟 slack 或未验证 II 自报成正式架构分数，最终交给统一 Synopsys 入口复测。

提交 RTL、配置、设计计划和主要实测结果。选用本任务的出题人应在 agent 启动前固定 `--profile architecture`、校准和最终测试协议，不在看到 agent 结果后切换评分模式。
