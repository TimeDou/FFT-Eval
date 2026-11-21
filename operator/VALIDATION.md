# 验证状态

本机 SSH Docker 的完整 VCS → DC → PrimeTime → 映射网表流程已经通过：准确 R2SDF、准确复用 radix-2、量化 banking 参考解，各 376 帧、三种 gate 时刻零初态。全部数值、协议、截止时间、10 ns 时序及映射对照检查通过。连续评分与硬件通过状态分离，不设面积降幅门槛。

详细实测表和复现命令见 [LOCAL_SYNOPSYS.md](LOCAL_SYNOPSYS.md)，原始小型数据见 [results/synopsys_20261121_v03/](results/synopsys_20261121_v03/)。本机结果为 2016 年版本商业工具的 pre-layout/ideal-interconnect 测量；新版平台须重新校准。

57 项流程/工具入口/指标/评分/快照/仿真驱动回归在宿主机与容器中均通过。参考解另外 25 项已有检查通过。单元测试中的商业 PPA 夹具只验证流程；上述真实商业测量来自独立完整运行，不使用夹具值。

复现控制测试：`python3 -m unittest discover -s operator/tests -v`。Python 需 3.10+ 和 NumPy；容器可使用共享目录的 `runtime/python/bin/python3`。生产 Tcl 回归使用 `tclsh`。

早期失败实验保留：LC 启动/环境错误、迭代基线 reset X、隔离编译后的复现，以及后续控制锥 SAT 和三种二值初态验证。没有将失败点删除或当作有效面积收益。原来的 v0.2 开源结果和分数仍保留，不能与 v0.3 商业数据混用。
