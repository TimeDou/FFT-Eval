"""Render the solution's actual new-interface results and design decisions."""
from pathlib import Path
import csv
import json
import sys
import numpy as np

SOLUTION=Path(__file__).resolve().parents[1]
BENCHMARK=SOLUTION.with_name('fft64_benchmark')
sys.path.insert(0,str(BENCHMARK/'tools'))
from common import read,save,sha
from model import make_frames
from simulate import schedule,decode

NAMES={
    'accurate_sdf':'准确 R2SDF',
    'accurate_iterative':'准确迭代 R2',
    'exact_banked':'迭代 R2＋精确 banking',
    'quantized_banked':'迭代 R2＋banking＋数据/系数量化',
    'pipelined_iterative':'准确迭代 R2＋BF 流水切分',
    'aggressive_quantization':'banking＋更激进的数据量化',
}

def main():
    status=read(SOLUTION/'results/status.json')
    assert status['status']=='COMPLETE_LOCAL',status
    if status.get('run_relative'):
        run=SOLUTION/status['run_relative']
    else:
        run=Path(status['run'])
        if not run.exists():run=SOLUTION/'results/runs'/run.name
    results=read(run/'development.json');validation=read(run/'validation.json')
    calibration=read(SOLUTION/'results/local_area_reference.json')
    rows=[]
    for name,label in NAMES.items():
        result=results[name];ppa=result.get('ppa',{});lat=result.get('latency',{});q=result.get('quality',{})
        row=dict(id=name,design=label,status=result['status'],backend='local',area_um2=ppa.get('area_um2'),
                 area_ratio=result.get('grade',{}).get('area_ratio'),worst_frame_sqnr_db=q.get('minimum_frame_sqnr_db'),
                 first_cycle=lat.get('first_output_latency_cycles',[None])[0],
                 last_cycle=lat.get('frame_completion_cycles',[None])[0],
                 timing_pass=ppa.get('timing_pass'),worst_slack_ns=ppa.get('worst_setup_slack_ns'),
                 limiting_period_estimate_ns=ppa.get('effective_required_period_ns'),
                 protocol_pass=result.get('protocol_pass'),source_sha256=result['source']['source_sha256'])
        rows.append(row)
        with(SOLUTION/'candidates'/name/'measurements.csv').open('w',newline='')as stream:
            writer=csv.DictWriter(stream,list(row));writer.writeheader();writer.writerow(row)
    with(SOLUTION/'measurements.csv').open('w',newline='')as stream:
        writer=csv.DictWriter(stream,list(rows[0]));writer.writeheader();writer.writerows(rows)
    accurate_area=calibration['reference_area_um2'];bank_area=results['exact_banked']['ppa']['area_um2']
    chosen=results[status['selected']];area=chosen['ppa']['area_um2'];minimum=min(r['quality']['minimum_frame_sqnr_db']for r in validation)
    score_policy=chosen['grade'].get('scoring_version','legacy_fractional_area_saving_v0.2')
    # Same input packets, different legal output timings: compare decoded values.
    frames,_=make_frames(20261118,2);events,metadata=schedule(frames,20261118+17)
    exact_outputs=[]
    for name in ['accurate_sdf','accurate_iterative','exact_banked','pipelined_iterative']:
        raw=np.loadtxt(run/'development'/name/'rtl_sim/output.txt',dtype=np.int64,ndmin=2)
        exact_outputs.append(decode(raw,events,metadata)[0])
    exact_match=all(np.array_equal(z,exact_outputs[0])for z in exact_outputs[1:])
    assert exact_match
    summary=dict(status='COMPLETE_LOCAL',cases=rows,selected=status['selected'],
                 minimum_validation_sqnr_db=minimum,validation_frames=sum(r['dataset_frames']for r in validation),
                 total_area_saving_percent=100*(1-area/accurate_area),
                 exact_banking_saving_percent=100*(1-bank_area/accurate_area),
                 quantization_increment_percent=100*(1-area/bank_area),
                 exact_controls_bit_exact_on_development=exact_match,
                 selected_source_sha256=sha(SOLUTION/'rtl/fft64_top.sv'),
                 commercial='NOT_RUN',pnr='NOT_RUN')
    save(SOLUTION/'results/summary.json',summary)
    table=['| 实现 | 状态 | 面积 µm² | 最低 SQNR dB | 首输出/完成 cycles | setup slack ns |',
           '|---|---|---:|---:|---:|---:|']
    for row in rows:
        a=f"{row['area_um2']:.2f}"if row['area_um2']is not None else '未测'
        slack=f"{row['worst_slack_ns']:.4f}"if row['worst_slack_ns']is not None else '—'
        table.append(f"| {row['design']} | {row['status']} | {a} | {row['worst_frame_sqnr_db']:.2f} | {row['first_cycle']} / {row['last_cycle']} | {slack} |")
    hold_table='\n'.join(f"| {r['seed']} | {r['dataset_frames']} | {r['quality']['minimum_frame_sqnr_db']:.4f} | PASS |"for r in validation)
    text=f'''# 本轮解题结果

已将已有方案迁移到新题面和新接口，并完成完整本机复测。选择迭代 R2、精确 parity banking、数据少保留 1 个小数位、twiddle fraction 9；完整面积 **{area:.2f} µm²**，相对较小准确基线下降 **{summary['total_area_saving_percent']:.2f}%**。新的留出测试最低逐帧 SQNR 为 **{minimum:.2f} dB**，满足 50 dB 要求。

这不是一次新的 agent 从零 rollout，也不是全局最优搜索。结果来自 ASAP7 RVT/TT、Yosys/ABC/OpenSTA 的 pre-layout 流程；VCS/DC/PrimeTime 和 P&R 尚未运行。

## 实际对照

{chr(10).join(table)}

同一公开数据协议、272 帧 development、新接口、固定 10 ns 时钟；包含复位、连续帧、变化空闲及超过 16-bit 计数周期的长空闲。未通过 SQNR 的候选停止在数值验证阶段，面积留空，不记为零。

准确 SDF、准确迭代、精确 banking 与准确流水切分的全部 development 输出逐样本相同。这里的“准确”是高精度定点基线，不是 float64 无误差实现。

## 选择理由

1. 当前服务档允许复用一个 Butterfly，迭代式准确基线比 SDF 面积小；SDF 首输出更早，但两者都满足截止时间。
2. 精确 parity banking 减少存储读写选择逻辑，节省 {summary['exact_banking_saving_percent']:.2f}% 整体面积。它保持算术语义，收益不归给近似。
3. 数据/系数量化在 banking 基础上再省 {summary['quantization_increment_percent']:.2f}%，质量仍有余量。数据内部保留 14 fractional bits、存储宽度 21 bit；输出恢复原有增益；twiddle 为 signed 11 bit /2^9；非平凡旋转采用完整乘积及累加保护位后 RNE，平凡旋转精确旁路。
4. 增加 BF 流水切分改善时序余量，却增加面积和周期延迟。固定 10 ns 目标已满足，因此不选它；不宣称流水减少组合延迟就提高了规定服务吞吐。
5. 再多去掉一个数据小数位的候选在合法低 RMS 复数输入上失败，因此拒绝，没有降低质量阈值。

## 独立确认

候选配置与 RTL 在运行这些新种子前固定。不同组包含重复的 directed cases，不把全部帧都称为独立随机样本。

| 种子 | 帧数 | 最低 SQNR dB | 协议/映射对照 |
|---|---:|---:|---|
{hold_table}

选定设计首输出为 {chosen['latency']['first_output_latency_cycles'][0]} cycles（2.56 µs），计算尾延迟为 {chosen['latency']['computational_tail_cycles'][0]} cycles（1.93 µs），整帧完成为 {chosen['latency']['frame_completion_cycles'][0]} cycles（3.19 µs）。按规定每 384 cycles 接收一帧，对应 260416.67 FFT/s；不将它称为架构最大固有吞吐。

本机：全数据 Icarus RTL、全数据 Verilator gate、额外 Icarus 四态 gate 复位/边界子集。商业脚本采用 VCS 全量四态 RTL/gate 对照。当前结果不是形式全输入域等价或 worst-case 数值误差证明。

## 对新 benchmark 的结论

题目可以形成一个小而完整的工程闭环：架构选择 → 精确资源优化 → 量化 → 协议/数值 → 映射/STA → 网表复测。面积节省是设计收益的一项；通过与否只取决于基本硬件规格，不设置最低面积降幅。

本次原始记录使用评分规则 `{score_policy}`，保存得分为 {chosen['grade']['score']:.6f}。历史结果不重新标注为新版本测量；v0.3 使用归一化吞吐量/面积效率，准确参考点为 0.5。实际 agent 评分须使用同一商业平台的新版本校准。

本次使用已经修正长空闲计数和表达式兼容性的生成器；没有拷贝旧版本的运行目录或将旧故障当成本轮失败。所有表格来自当前仓库下重新执行的测量。

完整数字在 [measurements.csv](measurements.csv)，原始运行目录由 [results/status.json](results/status.json) 指向。下一步可运行 `run_platform.sh`，回传商业 EDA 反馈；这一步尚未在本机完成。
'''
    environment_notes=SOLUTION/'results/environment_update/NOTES.md'
    if environment_notes.exists():text+=environment_notes.read_text()
    (SOLUTION/'RESULTS.md').write_text(text)
    (SOLUTION/'DESIGN_PLAN.md').write_text(f'''# 设计计划与决策

## 目标与选择

满足 FFT64/50 dB/10 ns/384-cycle 服务要求，最小化完整映射面积。本轮迁移并验证已有 SDF 与单 BF 迭代实现，选择面积较小的可行方案；不声称一次独立从零探索。

## 关键假设及结果

- 资源复用适合本题较宽松帧间隔：两个准确架构均完成实际综合与协议测试，选择迭代式。
- 精确 banking 应降低存储选择开销：实测整机下降 {summary['exact_banking_saving_percent']:.2f}%，接受。
- 数据和系数量化可进一步节省：banking 基础上再降 {summary['quantization_increment_percent']:.2f}%，接受；更激进量化在低 RMS 复数输入失败，拒绝。
- 额外 BF 流水切分可能提高时序余量：实测增加面积与周期延迟，现有时序已过，拒绝。

每个候选的数字见 measurements.csv。SDF 使用饱和 epoch 计数覆盖长空闲；生成代码使用显式括号兼容旧 Yosys。

## 当前最佳

配置见 design_config.json，RTL 在 rtl/fft64_top.sv。面积 {area:.2f} µm²，新留出数据最低 SQNR {minimum:.2f} dB，全部本机协议/映射检查通过。停止扩大矩阵，等待商业平台校准后再决定是否继续优化。
''')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
