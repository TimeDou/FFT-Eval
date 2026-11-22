"""Collect independently verified results on the private result branches.

Does not edit Agent workspaces, benchmark policy, or evaluator implementation.
Push is a separate explicit command after archive replay and commit inspection.
"""
from pathlib import Path
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT=Path(Path('/tmp/fft_final_agent_review_path.txt').read_text().strip())
BASE=Path(__file__).resolve().parents[2]
DEST=BASE/'DSBench'
SCRIPTS=Path(__file__).resolve().parent
ALLOWED={'.json','.csv','.rpt','.log','.sdc','.tcl','.npz','.v','.ys','.script','.md'}
IGNORE_DIRS={'csrc','simv.daidir','dc_work','obj_dir','obj','__pycache__','.venv','venv'}
IGNORE_NAMES={'simv','vectors.txt','output.txt','source.sv','staged.sv','tb.sv','mapped.ddc','lock'}


def read(path):return json.loads(path.read_text())
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()


def compact(source,target):
    for directory,dirs,files in os.walk(source):
        dirs[:]=[d for d in dirs if d not in IGNORE_DIRS]
        for name in files:
            p=Path(directory)/name;relative=p.relative_to(source)
            if name in IGNORE_NAMES or p.suffix not in ALLOWED:continue
            if name=='mapped.v'and'frequency_certificates'in relative.parts:continue
            if 'submission'in relative.parts:continue
            copy(p,target/relative)


def manifest(directory,paths):
    files={}
    for relative in paths:
        base=directory/relative
        candidates=[base]if base.is_file()else sorted(p for p in base.rglob('*')if p.is_file())
        for p in candidates:
            if '__pycache__'in p.parts or p.suffix=='.pyc':continue
            files[str(p.relative_to(directory))]=dict(bytes=p.stat().st_size,sha256=sha(p))
    return dict(files=dict(sorted(files.items())),
        scope='Current measured submission, original visible conversation, public exploration and independent private evidence; historical pilot excluded')


def stage(repo,paths):
    # Explicit paths include the archived command logs normally ignored by Git.
    names=[]
    for path in paths:
        base=repo/path
        if base.is_file():names.append(str(base.relative_to(repo)))
        elif base.is_dir():
            names.extend(str(p.relative_to(repo))for p in base.rglob('*')if p.is_file()
                         and'__pycache__'not in p.parts and p.suffix!='.pyc')
    listing=ROOT/'git_stage_paths.txt'
    listing.write_bytes(b'\0'.join(x.encode()for x in sorted(set(names)))+b'\0')
    git(repo,'add','-f','--pathspec-from-file='+str(listing),'--pathspec-file-nul')
    git(repo,'add','-u')


def build_agent(case,row,campaign):
    name=case['id'];repo=DEST/('FFT-Eval-agent-'+name)
    assert git(repo,'branch','--show-current')=='agents/'+name
    assert git(DEST/'FFT-Eval','rev-parse','main')==campaign['evaluator_commit']
    archive=repo/'archive/pilot_before_score_aware_restart'
    if archive.exists():
        # Resume our own interrupted collection only; never mask unrelated edits.
        existing=read(repo/'run_metadata.json')
        assert existing['original_campaign']==str(ROOT) and existing['source_sha256']==case['source_sha256']
        old=read(archive/'ARCHIVE_CONTEXT.json')['previous_result_commit']
    else:
        assert not git(repo,'status','--porcelain'),name+' worktree must be clean'
        old=git(repo,'rev-parse','HEAD')
        git(repo,'merge','--no-edit','main')
        archive.mkdir(parents=True)
        for relative in ['submission','agent_evaluation','pilot_workspace','AGENT_RESULT.md']:
            p=repo/relative
            if p.exists():shutil.move(str(p),str(archive/relative))
        save(archive/'ARCHIVE_CONTEXT.json',dict(previous_result_commit=old,
            scope='Historical pilot preserved verbatim; not a result of this score-aware final run',
            policy_warning='Historical scores and normalization are not comparable to the current run'))
    shutil.copytree(ROOT/'submissions'/name,repo/'submission',dirs_exist_ok=True)
    shutil.copytree(ROOT/'conversations'/name,repo/'conversation',dirs_exist_ok=True)
    public=ROOT/'public_evidence'/name
    shutil.copytree(public/'runs',repo/'runs',dirs_exist_ok=True)
    (repo/'public_evidence').mkdir(exist_ok=True)
    for relative in ['snapshots','development']:
        if (public/relative).exists():shutil.copytree(public/relative,repo/'public_evidence'/relative,dirs_exist_ok=True)
    for p in public.iterdir():
        if p.is_file():copy(p,repo/'public_evidence'/p.name)
    run=Path(row['result_directory']);evidence=repo/'agent_evaluation'
    compact(run,evidence/'measurement')
    copy(ROOT/'evaluation/calibration.json',evidence/'calibration.json')
    for rel in ['environment.json','platform_identity.json','calibration_location.json','protocol.json']:
        copy(ROOT/'evaluation'/rel,evidence/'environment'/rel)
    for rel in ['calibration_reuse_check.json','official_command.json','process_resources.json',
                'frequency_prefetch.json','private_protocol.json']:
        if (ROOT/rel).is_file():copy(ROOT/rel,evidence/'environment'/rel)
    result=read(run/'result.json')
    save(evidence/'grade.json',result['grade'])
    # The official Operator writes code_result beside each candidate's runs.
    grade_file=ROOT/'evaluation/candidates'/name/'code_result.json'
    if grade_file.exists():copy(grade_file,evidence/'code_result.json')
    numeric=evidence/'numeric_evidence'
    copy(ROOT/'numerical_replay/inputs.npz',numeric/'inputs.npz')
    copy(ROOT/'numerical_replay'/(name+'.npz'),numeric/'outputs.npz')
    copy(ROOT/'numerical_replay'/(name+'.json'),numeric/'observation.json')
    meta=dict(case,agent=name,evaluator_commit=campaign['evaluator_commit'],
        policy_sha256=campaign['policy_sha256'],dialogue_metadata=read(repo/'conversation/metadata.json'),
        measured_metrics=row,original_campaign=str(ROOT),
        verification_scope='Actual independent hidden numerical, exhaustive long-II, mapped subset and fixed-netlist STA; empirical pre-layout only',
        general_model_capability_conclusions=None,final_model_ranking=None)
    save(repo/'run_metadata.json',meta)
    save(evidence/'provenance.json',dict(case,private_run_path=str(run),
        evaluator_commit=campaign['evaluator_commit'],policy_sha256=campaign['policy_sha256'],
        normalized_mapped_sha256=result['ppa']['mapped_sha256'],
        exported_and_normalized_hashes_are_distinct=True,
        omitted_artifacts='Reconstructible compiler objects, duplicate staged source, binary build databases, and per-cycle text traces. Original traces remain at the recorded campaign path. Actual hidden input/output arrays are retained as compressed NPZ.',
        source_was_not_modified=True))
    copy(SCRIPTS/'verify_evidence.py',evidence/'verify_evidence.py')
    audit=read(ROOT/'public_search_audit.json')
    save(evidence/'public_search_audit.json',audit)
    report=f'''# {name}: 本轮最终 FFT64 提交

原样提交位于 [submission/](submission/)。本轮独立隐藏评测通过；对应电路和综合 recipe 未由核验者修改。以下是一次运行的实测设计结果，不是模型总体能力结论。

| 指标 | 本轮实测 |
|---|---:|
| 基本规格 / 有效正式评分 | PASS / true |
| 综合硬件分数 | **{row['score']:.9f}** |
| 完整 mapped area | {row['area_um2']:.6f} μm² |
| 顺序 / 组合单元面积 | {row['sequential_cell_area_um2']:.6f} / {row['combinational_cell_area_um2']:.6f} μm² |
| 认证周期 / 频率 | {row['certified_period_ns']:.12f} ns / {row['certified_fmax_MHz']:.6f} MHz |
| 最小连续帧验证 II | {row['verified_frame_ii']} cycles/frame |
| 认证时钟的持续能力 | {row['throughput_ffts_per_second']:.6f} FFT/s |
| 最大首输出 / 整帧完成 | {row['first_output_cycles']} / {row['completion_cycles']} cycles |
| 最低隐藏逐帧 SQNR | {row['minimum_hidden_sqnr_db']:.9f} dB |
| 面积 / 吞吐 / 延迟分项 | {row['area_component']:.9f} / {row['throughput_component']:.9f} / {row['latency_component']:.9f} |
| 用户提供对话用时 | {case['user_reported_dialogue_duration']} ({case['user_reported_dialogue_seconds']} s) |

FFT64，外部 P=1，ASAP7 RVT/TT，VCS/DC/PrimeTime，布局前完整 cell area 与 ideal-interconnect STA。强制时钟 10 ns、逐非零帧 SQNR≥50 dB；更高 SQNR 不奖励分数。额外的频率扫描始终使用同一网表。首输出延迟分项使用共同 10 ns 时钟。

隐藏数值测试为 8192 个独立随机非零帧及 192 个定向帧。321 个整数 II（64–384）各验证 1024 连续 RTL 帧，并对所选最小 II 做代表性 mapped 检查；包含复位、间隙及 0/1/20261121 三种门级初始状态。结果不构成 formal worst-case error guarantee，也没有 post-route 或可靠功耗结论。

- [完整原生 measurement/result.json](agent_evaluation/measurement/result.json) 与 [grade.json](agent_evaluation/grade.json)。
- [全部 II 观测](agent_evaluation/measurement/throughput/long_intervals/probe_results.json)。
- [真实隐藏输入/输出与 replay 说明](agent_evaluation/numeric_evidence/observation.json)。
- [完整可见聊天 JSON](conversation/conversation.json)、[计时及日志来源](conversation/metadata.json)、[初始提示](conversation/initial_prompt.txt)。
- [Agent 原始设计说明](submission/DESIGN_PLAN.md)、[公开探索记录](runs/)、[对应受测快照与探索源码](public_evidence/)。
- [本轮身份与时长](run_metadata.json)、[文件哈希](CURRENT_RUN_MANIFEST.json)。
- [先前 pilot 原样存档](archive/pilot_before_score_aware_restart/)，旧分数不与本轮混用。

对话导出包括可见消息及工具调用/结果，省略内部推理和系统上下文。用户提供的用时与日志的消息区间、平台任务计时分别保留；6.2 的平台任务计时为 2247.314 s，与用户给出的 2235 s 相差 12.314 s。硬件评分不含对话或 EDA 用时。

在仓库根目录安装 NumPy 后可执行以下证据复核；该命令重新生成输入并重算已保存输出的质量和评分，不重新运行商业 EDA：

```bash
python3 agent_evaluation/verify_evidence.py
```

跨设计比较见私有仓库分支 `validation/final-agent-comparison` 的 `validation/final_agent_comparison/RESULTS.md`。后续模型结果、总体模型结论和最终排名仍留空。
'''
    (repo/'AGENT_RESULT.md').write_text(report)
    paths=['submission','conversation','runs','public_evidence','agent_evaluation','run_metadata.json','AGENT_RESULT.md']
    save(repo/'CURRENT_RUN_MANIFEST.json',manifest(repo,paths))
    completed=subprocess.run([str(BASE/'.venv/bin/python'),str(evidence/'verify_evidence.py')],
                             check=True,capture_output=True,text=True)
    receipt=read_json_text(completed.stdout)
    save(ROOT/'archive_verification'/('receipt_'+name+'.json'),receipt)
    stage(repo,paths+['CURRENT_RUN_MANIFEST.json','archive/pilot_before_score_aware_restart'])
    git(repo,'commit','-m','Archive verified score-aware final design and visible conversation')
    return dict(agent=name,branch='agents/'+name,commit=git(repo,'rev-parse','HEAD'),
        previous_result_commit=old,archive_replay=receipt)


def read_json_text(text):return json.loads(text)


def build_comparison(records,campaign):
    repo=DEST/'FFT-Eval-final-comparison'
    assert not git(repo,'status','--porcelain')
    assert git(repo,'rev-parse','HEAD')==campaign['evaluator_commit']
    target=repo/'validation/final_agent_comparison'
    assert not target.exists()
    shutil.copytree(ROOT/'analysis',target)
    save(target/'campaign.json',campaign)
    save(target/'published_branches.json',records)
    for rel in ['calibration_reuse_check.json','official_command.json','private_protocol.json',
                'public_search_audit.json','public_search_audit.csv','conversation_summary.json',
                'public_capture.json','process_resources.json','launcher_result.json']:
        if (ROOT/rel).is_file():copy(ROOT/rel,target/'provenance'/rel)
    for rel in ['status.json','calibration.json','environment.json','platform_identity.json','protocol.json']:
        copy(ROOT/'evaluation'/rel,target/'provenance'/rel)
    for case in campaign['cases']:
        name=case['id'];src=DEST/('FFT-Eval-agent-'+name);out=target/'cases'/name
        for rel in ['submission','conversation','agent_evaluation','runs','public_evidence']:
            shutil.copytree(src/rel,out/rel,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for rel in ['run_metadata.json','AGENT_RESULT.md','CURRENT_RUN_MANIFEST.json']:copy(src/rel,out/rel)
        copy(ROOT/'archive_verification'/('receipt_'+name+'.json'),out/'archive_verification.json')
    for p in SCRIPTS.glob('*.py'):copy(p,target/'reproduction'/p.name)
    (target/'README.md').write_text('''# 本轮最终 Agent 电路比较

阅读 [RESULTS.md](RESULTS.md)；原始指标位于 [final_metrics.csv](final_metrics.csv)。

`cases/<Agent>/` 包含精确的最终提交、真实独立隐藏评测记录、公开探索证据、可见聊天 JSON 和计时来源。对单个 case 可在其原始 Agent 分支运行 `python3 agent_evaluation/verify_evidence.py`；此处也可在 NumPy 可用时运行 `python3 cases/<Agent>/agent_evaluation/verify_evidence.py`。

`published_branches.json` 固定对应的私有分支 commit。`provenance/` 保存共同协议、校准身份、工具/库及执行记录；文件中的原始容器绝对路径是来源记录，不要求归档后仍是运行路径。`reproduction/` 是本次收集分析脚本，其原 campaign 路径需按本地部署设置；不应将其误作可替代正式 EDA 评测的脚本。

完整 321-II 汇总、分批日志、时序扫描 trace、netlist、隐藏实际输出 NPZ 均保留；重复编译产物和逐周期 text 未入库，原件仍在 provenance 指向的本地 campaign。

后续参测模型的结果、总体模型能力结论、最终排名和统计显著性仍为空，不以 PENDING 记零分。
''')
    save(target/'FILE_MANIFEST.json',manifest(target,[str(p.relative_to(target))for p in target.iterdir()]))
    stage(repo,['validation/final_agent_comparison'])
    git(repo,'commit','-m','Compare three independently verified final FFT64 designs with dialogue records')
    return dict(branch='validation/final-agent-comparison',commit=git(repo,'rev-parse','HEAD'))


def main():
    campaign=read(ROOT/'campaign.json')
    summary=read(ROOT/'analysis/summary.json')
    assert read(ROOT/'evaluation/status.json')['status']=='COMPLETE'
    assert all(r['status']=='VERIFIED'for r in summary['completed_designs'])
    by={r['agent']:r for r in summary['completed_designs']}
    records=[build_agent(case,by[case['id']],campaign)for case in campaign['cases']]
    comparison=build_comparison(records,campaign)
    save(ROOT/'publication.json',dict(agents=records,comparison=comparison,pushed=False))
    print(json.dumps(dict(agents=records,comparison=comparison),indent=2))


if __name__=='__main__':main()
