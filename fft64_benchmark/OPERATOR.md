# 出题方部署

出题方在私有评测仓库调用根目录 `run_synopsys.sh`、`run_synopsys_docker.sh` 或 `run_evaluation.sh`。不要将准确校准 RTL、隐藏协议状态、Agent 结果及 Git 凭据交给受测 Agent。公开包只包含题面、接口、库和公开开发工具。

每个后端先对准确基线执行同一长帧规范，冻结校准后再评价候选。默认正式目标为 `architecture`，按文档 60/30/10 计算。参数在 `profiles/policy.json`，不是旧版吞吐/面积比评分。

Hidden numerical 为 8,192 个独立非零帧加 directed cases；必选连续服务和每个被测 II 均为 1,024 帧。映射使用代表性子集。最小非零帧 SQNR 与最大逐帧延迟决定质量和协议可行性。

DSBench Code Grade 在对应后端完成校准后生成：

```bash
python3 grading/make_grader.py --profile architecture --out /private/grading_files \
  --calibration /private/evaluation/calibration.json
```

打包脚本绑定校准所用输入种子及规模。校准文件保留兼容名称 `area_reference.json`，内容是所选 profile 的完整参数，不代表只按面积评分。附件只交给评分端，不放入 Agent checkout。

所有结果属于 pre-layout synthesis / ideal-interconnect STA；没有 P&R、功耗或 formal worst-case 数值保证。工具或许可证故障标记为未评分，不将其当成有效零分。
