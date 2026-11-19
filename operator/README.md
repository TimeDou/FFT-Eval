# 统一复测资源

`evaluate_synopsys.py` 接受单个提交、目录批次或 CSV 清单，固定调用公开 benchmark 的商业后端。先在相同平台校准准确 SDF 与迭代式实现，再评分候选；生成设计的工具环境不参与最终面积分母。

`baselines/` 是出题人使用的高精度定点校准电路，不含数据精度缩减或优化参考解。它们和纯题目目录分开。数值参考仍为同一量化输入的 float64 FFT，准确定点基线不等同于零数值误差。

测试运行：

```bash
python3 -m unittest discover -s operator/tests -v
```

其中商业流程控制测试使用模拟结果，不产生真实商业 PPA。实际商业工具结果只由 `run_synopsys.sh` 在有许可证的目标平台测得。
