# 固定评价规格与评分

FFT 长度固定为 64；输入/输出外部并行度均为 1。输入实部和虚部为 signed 16-bit Q15，合法分量范围 [-0.5,+0.5]；非零帧 complex RMS≥1/32，全零帧另要求准确零输出。输出为 signed 24-bit Q15。数值参考是输入定点值对应的 double-precision、forward unscaled FFT，频点按 natural order 输出。

主误差指标是每个非零帧的 complex SQNR：

SQNR = 10 log10(sum |FFT_reference|² / sum |FFT_output − FFT_reference|²)。

所有有效帧中最低值须≥50 dB，额外精度不加分。输入/输出协议、复位、10 ns setup/hold、最大首输出 300 cycles、整帧完成 364 cycles、II=384 连续服务、代表性 RTL/mapped 一致性均为基本可行性要求；可行性不再设置分数门槛。

最终隐藏数值测试为 8192 随机非零帧+192 定向帧。所有 II=64…384 各验证 1024 连续 RTL 帧，最小通过值再经代表性 mapped 子集确认。逐帧 SQNR 取最低、首输出延迟取最大、II 取实际最小通过值，均不采信设计者自报值。门级检查使用三种初始状态，仍是有限样本行为验证。

独立评分器导入已提交网表，核对单元和面积、按统一约束做 STA，并做代表性 RTL/网表行为检查；不运行 Agent 的优化 recipe。所有设计使用 ASAP7 RVT/TT。面积为完整 mapped cell area；顺序面积包含数据存储、流水与控制，组合面积由总面积减顺序面积得到，未猜测 flatten 后算子归属。

统一 STA 假设包括 setup clock uncertainty 0.1 ns、clock/input transition 0.02 ns、外部 I/O delay 0、输出负载 1 fF；Liberty 时间单位为 ps。复位路径按固定流程排除于数据时序，复位行为另由协议测试验证。

综合分为 S = 0.60 S_A + 0.30 S_T + 0.10 S_L，各分项 clip 到 [0,1]：

- S_A = 3500 / (A + 3000)，A 单位 μm²；理想面积 500，半分锚点 4000。
- T = 1e9 / (p × II)，p 为固定网表的 STA 认证通过端点，单位 ns；T 单位 FFT/s。
- S_T = ln(T/T_min) / ln(240)，T_min=1e9/(384×10)，理想 T=62,500,000 FFT/s。
- S_L = (300−L)/237，L 是共同 10 ns 时钟下最大首输出 cycles，理想值 63，上限 300。

频率已经通过 T 进入评分，不再独立重复计分。认证周期来自同一固定网表的扫描；报告的是通过端点，扫描分辨率约 9.52 ps。不同 Agent 的 DC 目标值不直接当作认证周期。

全部结论限定为 pre-layout synthesis / ideal-interconnect STA。没有 post-route、可靠功耗或 energy 数据；经验样本误差不称为 formal worst-case guarantee。开发脚本中的 period estimate、局部面积及预测分数不替代完整资格评测。
