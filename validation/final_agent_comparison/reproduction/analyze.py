"""Report measured final-design differences; leave future-model conclusions open."""
from pathlib import Path
import csv
import json
import sys

ROOT=Path(Path('/tmp/fft_final_agent_review_path.txt').read_text().strip())
sys.path.insert(0,str(ROOT/'engine_private/fft64_benchmark/tools'))
from scoring import score_result


def read(path):return json.loads(Path(path).read_text())


def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='')as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
    state=read(ROOT/'evaluation/status.json')
    assert state['status']=='COMPLETE'
    campaign=read(ROOT/'campaign.json');reference=read(ROOT/'evaluation/calibration.json')
    rows=[];quality=[];public_comparison=[];timing=[]
    for case in campaign['cases']:
        choices=list((ROOT/'evaluation/candidates'/case['id']/'runs').glob('*/result.json'))
        assert len(choices)==1
        result=read(choices[0]);grade=result['grade'];perf=grade['performance'];ppa=result['ppa']
        assert result['status']=='COMPLETE'and grade['resolved']and grade['score_valid']and grade['official_score']
        assert grade['scoring_scope']=='hidden_evaluation'
        assert result['source']['source_sha256']==case['source_sha256']
        assert result['source']['implementation']['mapped_sha256']==case['exported_mapped_sha256']
        assert abs(score_result(result,reference)['score']-grade['score'])<1e-12
        observations=read(choices[0].parent/'throughput/long_intervals/probe_results.json')
        assert len(observations)==321 and {r['frame_ii_cycles']for r in observations}==set(range(64,385))
        assert all(r['tested_frames']>=1024 for r in observations)
        conversation=read(ROOT/'conversations'/case['id']/'metadata.json')
        seq=ppa['register_area_um2'];area=perf['area_um2'];throughput=perf['effective_throughput_ffts_per_second']
        completion=max(result['latency']['frame_completion_cycles'])
        completion=max(completion,result['throughput_check'].get('maximum_frame_completion_cycles',completion))
        row=dict(agent=case['id'],status='VERIFIED',area_um2=area,sequential_cell_area_um2=seq,
            combinational_cell_area_um2=area-seq,cells=ppa['cells'],certified_period_ns=perf['certified_period_ns'],
            certified_fmax_MHz=perf['certified_setup_fmax_MHz'],verified_frame_ii=perf['verified_frame_II_cycles'],
            throughput_ffts_per_second=throughput,throughput_at_10ns_ffts_per_second=1e8/perf['verified_frame_II_cycles'],
            throughput_per_area=throughput/area,first_output_cycles=perf['first_output_cycles'],completion_cycles=completion,
            first_output_ns_at_10ns=10*perf['first_output_cycles'],
            first_output_ns_at_certified_period=perf['first_output_cycles']*perf['certified_period_ns'],
            minimum_hidden_sqnr_db=result['quality']['minimum_frame_sqnr_db'],sqnr_margin_db=result['quality']['minimum_frame_sqnr_db']-50,
            area_component=grade['components']['area'],throughput_component=grade['components']['throughput'],
            latency_component=grade['components']['latency'],score=grade['score'],score_valid=True,
            user_reported_dialogue=case['user_reported_dialogue_duration'],
            user_reported_dialogue_seconds=case['user_reported_dialogue_seconds'],
            logged_message_interval_seconds=conversation['logged_task_wall_seconds'],
            engine_task_seconds=conversation.get('engine_task_duration_seconds'),
            private_validation_seconds=result.get('seconds'),source_sha256=case['source_sha256'],
            exported_mapped_sha256=case['exported_mapped_sha256'],result_directory=str(choices[0].parent))
        rows.append(row)
        timing.append({k:row[k]for k in ['agent','user_reported_dialogue','user_reported_dialogue_seconds',
            'logged_message_interval_seconds','engine_task_seconds','private_validation_seconds']})
        pub=read(ROOT/'public_evidence'/case['id']/'result.json');pperf=pub['grade']['performance']
        public_comparison.append(dict(agent=case['id'],public_score=pub['grade']['score'],private_score=grade['score'],
            public_minimum_sqnr_db=pub['quality']['minimum_frame_sqnr_db'],private_minimum_sqnr_db=row['minimum_hidden_sqnr_db'],
            area_difference=area-pperf['area_um2'],period_difference=perf['certified_period_ns']-pperf['certified_period_ns'],
            ii_difference=perf['verified_frame_II_cycles']-pperf['verified_frame_II_cycles'],
            first_cycle_difference=perf['first_output_cycles']-pperf['first_output_cycles'],
            source_and_export_match=True))
        frames=read(choices[0].parent/'per_frame_quality.json')
        families={}
        for frame in frames:
            name=frame['family'];d=families.setdefault(name,dict(frames=0,minimum_sqnr_db=None,maximum_nmse=0))
            d['frames']+=1
            value=frame.get('sqnr_db')
            if value is not None:d['minimum_sqnr_db']=value if d['minimum_sqnr_db']is None else min(value,d['minimum_sqnr_db'])
            if frame.get('nmse')is not None:d['maximum_nmse']=max(d['maximum_nmse'],frame['nmse'])
        quality.extend(dict(agent=case['id'],family=name,**values)for name,values in sorted(families.items()))
    analysis=ROOT/'analysis';analysis.mkdir(exist_ok=True)
    write_csv(analysis/'final_metrics.csv',rows)
    write_csv(analysis/'dialogue_times.csv',timing)
    write_csv(analysis/'public_vs_hidden.csv',public_comparison)
    write_csv(analysis/'quality_by_family.csv',quality)
    by_name={r['agent']:r for r in rows};a=by_name['Codex-GPT-6.1-Sol-Max'];b=by_name['Codex-GPT-6.2-Sol-Max']
    delta=dict(comparison='6.2 final circuit minus 6.1 final circuit',
        weighted_area_delta=.6*(b['area_component']-a['area_component']),
        weighted_throughput_delta=.3*(b['throughput_component']-a['throughput_component']),
        weighted_latency_delta=.1*(b['latency_component']-a['latency_component']),score_delta=b['score']-a['score'],
        relative_area_change=b['area_um2']/a['area_um2']-1,
        relative_throughput_change=b['throughput_ffts_per_second']/a['throughput_ffts_per_second']-1,
        sequential_area_saving=a['sequential_cell_area_um2']-b['sequential_cell_area_um2'],
        combinational_area_saving=a['combinational_cell_area_um2']-b['combinational_cell_area_um2'])
    assert abs(sum(delta[k]for k in ['weighted_area_delta','weighted_throughput_delta','weighted_latency_delta'])-delta['score_delta'])<1e-12
    write_csv(analysis/'weighted_difference.csv',[delta])
    future=['Claude-DS-Pro','Claude-Fable-5.2','Claude-Opus-5.5']
    roster=[{k:r[k]for k in ['agent','status','score','area_um2','certified_period_ns','verified_frame_ii',
                          'minimum_hidden_sqnr_db','user_reported_dialogue_seconds']}for r in rows]
    for name in future:roster.append({key:name if key=='agent'else'PENDING'if key=='status'else None for key in roster[0]})
    write_csv(analysis/'model_results.csv',roster)
    (analysis/'summary.json').write_text(json.dumps(dict(status='COMPLETE',completed_designs=rows,pending_models=future,
        general_model_capability_conclusions=None,overall_model_ranking=None,statistical_significance=None,
        scope='Three concrete final designs only; approved fixed score and common independent hidden protocol; additional model conclusions intentionally reserved'),indent=2)+'\n')
    table='\n'.join(f"| {r['agent']} | {r['area_um2']:.2f} | {r['certified_period_ns']:.6f} | {r['verified_frame_ii']} | {r['throughput_ffts_per_second']/1e6:.3f} | {r['first_output_cycles']} / {r['completion_cycles']} | {r['minimum_hidden_sqnr_db']:.4f} | **{r['score']:.6f}** | {r['user_reported_dialogue']} |"for r in rows)
    components='\n'.join(f"| {r['agent']} | {r['area_component']:.6f} | {r['throughput_component']:.6f} | {r['latency_component']:.6f} | {r['sequential_cell_area_um2']:.2f} | {r['combinational_cell_area_um2']:.2f} |"for r in rows)
    report='''# 本轮 FFT64 Agent 提交核验与比较

三份最终提交已按同一独立隐藏协议完成核验，均满足基本规格。下文比较的是这三次运行实际交付的电路；其他模型尚未完成，总体模型能力结论与最终排名留空。批准的评分规则、权重、归一化目标、RTL 和提交 recipe 均未因结果而修改。

## 实测结果与对话用时

统一条件为 FFT64、外部输入/输出 P=1、同一 ASAP7 RVT/TT 库、VCS/DC/PrimeTime、10 ns 强制时序与逐非零帧 SQNR≥50 dB。三份完整导出网表分别独立导入计面积、做 STA 和 RTL/门级行为检查。准确参考的已有有效校准经过平台/协议指纹匹配后复用；没有用 Agent 的公开结果替代私有候选复测。

每个候选测试 8192 个独立隐藏随机非零帧和 192 个定向帧，II=64…384 的全部 321 个整数值各运行 1024 连续 RTL 帧，最小通过 II 再经代表性门级确认。包含复位、间隙和三个门级初始状态检查。频率采用同一固定网表 STA 扫描的通过端点。质量是有限样本观测，门级覆盖是代表性子集，不是形式化最坏误差证明。

| 本轮提交 | 面积 μm² | 认证周期 ns | 最小验证 II | 认证能力 M FFT/s | 首 / 末输出 cycles | 最低隐藏 SQNR dB | 综合分数 | 用户提供对话用时 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
'''+table+'''

硬件吞吐为 1e9/(认证周期×验证 II)。延迟分项使用共同 10 ns 下的最大首输出 cycles；认证时钟的物理延迟另存于 CSV，没有再次奖励频率。全部 PPA 为布局前 cell area / ideal-interconnect STA；没有 post-route 或可靠功耗结果。

![完整面积、认证吞吐、首输出延迟和评分贡献](figures/hardware_and_score.png)

[矢量 PDF](figures/hardware_and_score.pdf)；[面积–吞吐权衡图](figures/area_throughput.pdf)。

对话用时来自用户提供，按原值存档，既不代替 EDA 运行时间，也不进入硬件分数。日志另存消息起止与平台任务计时：6.1 的 task_complete 为 2253.103 s；6.2 为 2247.314 s，比用户给出的 2235 s 多 12.314 s，两种口径均保留。Claude 的实际任务首条提示至末条答案为 6915.504 s；较早的本地设置和较晚的退出等待不计入该区间。

## 评分差异来自哪些硬件指标

| 本轮提交 | 面积分项 | 吞吐分项 | 延迟分项 | 全部顺序单元面积 μm² | 组合单元面积 μm² |
|---|---:|---:|---:|---:|---:|
'''+components+'''

顺序面积包含数据存储、流水及控制寄存器，不能全部称为 FFT delay storage。组合面积按总面积减去顺序面积得到，没有根据 flatten 后名称猜测 BU/乘法器归属。

在这三份已测电路中，6.2 的综合分最高且面积最小，6.1 的认证周期略短，二者都支持 II=64。Claude 的 SQNR 余量最大，但在已满足共同 50 dB 门槛的比较中，其面积、吞吐和延迟均落后于另两份提交；更高 SQNR 按规则不加分。

6.2 相对 6.1 的加权变化为：面积 +%.6f，吞吐 %.6f，延迟 %.6f，合计 +%.6f。面积减少 %.2f%%，吞吐减少 %.2f%%，首输出晚 3 cycles。组合逻辑面积少 %.2f μm²，顺序单元面积少 %.2f μm²，说明面积差异不能只归因于寄存器数量。

## 电路与搜索过程的区别

**Claude-DS-Flash：R2SDF DIF，保留较多数值精度。** 六级反馈延迟为 32/16/8/4/2/1，数据保持 15 位小数并逐级增加保护位，使用 Q10 twiddle 和 22-bit 的输出重排序存储。帧间采用零输入推进与刷新，当前控制和重排序实现使最小服务间隔为 129，而不是理想连续 SDF 的 64。它比较了两个完整 architecture 候选，最终更激进的时序映射增加面积但略提高综合分，选择与完整公开评分一致。

**Codex-GPT-6.1-Sol-Max：R2²SDF DIF，优先压短算术路径。** 两个非平凡复数旋转器各用三个实数乘法，注册系数及乘积，最终以单个 64-word、每分量 19-bit 的交替重排序存储输出自然频点。输入从 Q15 舍入到 Q14，后续逐级变为 Q13/Q12；Q9 系数和 nearest-even 窄化控制数值误差。DC 目标 500 ps，使用 timing-high-effort 和增量 hold 修复。它完成了 11 个 architecture 候选，选择的电路并非面积最小者，而是完整综合分最高者。更窄的最终重排序存储在该批完整映射中反而增加总面积，未被选为最终提交。

**Codex-GPT-6.2-Sol-Max：R2²SDF DIT，将重排序移到输入端。** 输入位交换延迟为 31、14、4，共 49 个 complex word，每分量 15-bit；DIT 后续自然输出频点。它使用给定输入范围的整数位冗余：signed 15-bit Q15 保留原有 15 个小数位，仅把正端点 +0.5 饱和减少一个输入 LSB；6.1 的 signed 15-bit Q14 则通过舍入少保留一个小数位。两者的舍入误差来源不同，不能只用相同的“15-bit”判断精度。6.2 在两个旋转器采用 Q9/Q10 系数、Q15→Q14→Q12 量化和绝对残余系数表示，DC 目标 640 ps 并做 area recovery。它比较了 10 个完整 architecture 候选；更快的 split-product/retiming 实现因面积或延迟代价没有成为最终选择。

从 RTL 看，仅重排序数据存储的声明容量为 6.1 的 64×2×19=2432 bits 与 6.2 的 49×2×15=1470 bits。这能解释一部分结构差异，但其反馈网络顺序、量化位置、系数表示、控制和综合 recipe 也不同，不能把整个面积变化归因于单个因素。6.2 自己的公开对照中，去掉前两级输入交换的输出寄存器保持认证周期与 SQNR，面积减少 17.46684 μm²、首输出提前 2 cycles，是较清楚的局部流水优化证据。其文档给出的解析误差推导另行保留，不作为本次独立完成了 formal guarantee 的证据。

## 记录一致性与适用范围

三份最终 RTL 和导出输入网表均与选择的公开记录身份匹配，所选分数是各自已完成、可行 architecture 公开候选中的最高值。公开与私有最低 SQNR 的差别来自输入样本不同；完整硬件指标的对照见 public_vs_hidden.csv。导出网表哈希与评测器规范化后的网表哈希分别记录，不能把合法导入/命名规范化造成的差异误判成换设计。

聊天记录已按本轮会话导出为可读 JSON，包含用户/助手可见消息及工具调用/返回，另有原始日志哈希、模型标识和计时来源。内部推理、系统上下文和 provider 请求镜像不作为聊天导出。三次用户提示在去掉粘贴格式的空白和反斜杠后完全一致。日志和运行用时用于观察过程，不能控制工具并发、服务延迟或所有外部资源差异，故不据此单独归因模型能力。

## 后续模型与待补结论

| 模型 | 状态 | 结果 |
|---|---|---|
| Claude-DS-Pro | PENDING | |
| Claude-Fable-5.2 | PENDING | |
| Claude-Opus-5.5 | PENDING | |

总体模型能力结论：

最终模型排名：

统计显著性与重复运行结论：

'''
    report=report%(delta['weighted_area_delta'],delta['weighted_throughput_delta'],delta['weighted_latency_delta'],
        delta['score_delta'],-100*delta['relative_area_change'],-100*delta['relative_throughput_change'],
        delta['combinational_area_saving'],delta['sequential_area_saving'])
    (analysis/'RESULTS.md').write_text(report)
    print('Verified final metrics and report generated. General-model conclusions remain empty.')


if __name__=='__main__':main()
