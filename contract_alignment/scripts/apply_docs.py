"""Align supplied startup prose and shared public/private task contracts."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT/'DSBench/FFT-Bench'
PRIVATE = ROOT/'DSBench/FFT-Eval'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def insert_before(path, marker, text):
    source = path.read_text()
    assert source.count(marker) == 1
    path.write_text(source.replace(marker, text+'\n\n'+marker))


def prompt_section(text, language):
    lines = text.splitlines()
    assert lines[0].startswith('# ')
    return '## '+language+' — '+lines[0][2:]+'\n'+'\n'.join(
        '#'+line if line.startswith('## ') else line for line in lines[1:])


def main():
    supplied = ROOT/'DSBench/chat-new-markdown/START_CN.md'
    chinese = supplied.read_text().strip()
    old = '每个实部和虚部分量输入为有符号 16-bit、输出为有符号 24-bit，均具有 15 fractional bits。'
    assert chinese.count(old) == 1
    chinese = chinese.replace(old, old+'输入分量范围为 [-0.5, 0.5]，非零帧的 complex RMS 至少为 1/32；数值参考是同一已量化输入的 float64 FFT。')
    english = (Path(__file__).parent/'start_en.txt').read_text().strip()
    prompt = ('# Agent startup prompts\n\nUse the same language-equivalent prompt, public policy, '
              'tools and execution budget for every Agent in a comparison. Start a fresh conversation '
              'in the FFT-Bench repository root. Choose one complete prompt below.\n\n'
              +prompt_section(chinese,'中文')+'\n\n---\n\n'+prompt_section(english,'English')+'\n')
    (PUBLIC/'START_PROMPT.md').write_text(prompt)
    specpath = PUBLIC/'fft64_benchmark/SPEC.json'
    spec = json.loads(specpath.read_text())
    before = json.loads(specpath.read_text())
    score = spec['scoring']
    score['area'] = ('clip((A_half-A_ideal)/(A+A_half-2*A_ideal),0,1); public A_ideal=500 um2 and '
                     'A_half=4000 um2; accurate baseline area does not set the score scale')
    score['architecture'] = ('0.60*S_A + 0.30*S_T + 0.10*S_L; published rational-area, logarithmic-throughput '
                             'and linear-latency functions and fixed numeric anchors in profiles/policy.json and SCORING.md')
    score['latency_score'] = ('clip((300-L)/(300-63),0,1); L is maximum observed first-output cycles at the common 10 ns clock')
    score['missing_calibration'] = ('complete public previews compute component and combined scores from fixed public anchors without private calibration; '
                                     'official hidden grading requires matching platform/protocol validation; otherwise the hidden score is invalid')
    assert {k:v for k,v in spec.items()if k!='scoring'} == {k:v for k,v in before.items()if k!='scoring'}
    specpath.write_text(json.dumps(spec, indent=2)+'\n')
    insert_before(PUBLIC/'fft64_benchmark/TASK_EN.md', 'The public evaluation uses at least',
        'The ideal anchors form an intentionally demanding scoring scale, not a claim that one physical circuit achieves all three. '
        'Area credit stays positive above the half-credit anchor; throughput credit is logarithmic; each component saturates at one. '
        'Compare weighted component changes (0.60 ΔS_A, 0.30 ΔS_T, 0.10 ΔS_L), and select the highest verified combined score. '
        'Use the area profile to screen candidates, not to choose the final architecture winner.')
    insert_before(PUBLIC/'fft64_benchmark/TASK_ZH.md', '数值可行性使用所有非零测试帧中的',
        '理想锚点是一组刻意设得很高的评分标尺，不代表某个物理电路已经同时达到三项目标。面积超过半分锚点仍有正分，吞吐率采用对数归一化，各分项达到 1 后不再增加得分。'
        '比较候选时，应查看 `0.60 ΔS_A`、`0.30 ΔS_T`、`0.10 ΔS_L` 及综合分数变化。`area` profile 用于筛选，最终选择应依据完整 `architecture` 预览。')
    insert_before(PUBLIC/'fft64_benchmark/SCORING.md', '## Public feedback and final hidden grading',
        'When comparing candidates, use the weighted changes 0.60 ΔS_A, 0.30 ΔS_T and 0.10 ΔS_L. '
        'Raw percentage improvements are not interchangeable under these nonlinear functions. '
        'A throughput gain can be outweighed by an area penalty, and a component already at one earns no further credit. '
        'Choose the best complete architecture preview rather than the highest area-only diagnostic.')
    path = PUBLIC/'fft64_benchmark/EVALUATION.md'
    source = path.read_text().replace('selected profile, reference calibration, worst SQNR',
                                    'selected profile, private platform/protocol calibration when grading hidden data, worst SQNR')
    path.write_text(source)
    shared = ['START_PROMPT.md','REMOTE_SYNOPSYS.md','OPTIMIZATION.md',
              'fft64_benchmark/SPEC.json','fft64_benchmark/TASK_EN.md','fft64_benchmark/TASK_ZH.md',
              'fft64_benchmark/SCORING.md','fft64_benchmark/AGENT_WORKFLOW.md',
              'fft64_benchmark/DESIGN_PLAN_TEMPLATE.md','fft64_benchmark/TASK_ARCHITECTURE_EN.md',
              'fft64_benchmark/EVALUATION.md']
    for rel in shared:
        shutil.copy2(PUBLIC/rel, PRIVATE/rel)
    recordpath = PUBLIC/'fft64_benchmark/profiles/PRE_REGISTERED.json'
    record = json.loads(recordpath.read_text())
    record['specification_sha256'] = sha(specpath)
    recordpath.write_text(json.dumps(record, indent=2)+'\n')
    shutil.copy2(recordpath, PRIVATE/'fft64_benchmark/profiles/PRE_REGISTERED.json')
    supplied_files = {p.name:sha(p) for p in sorted(supplied.parent.iterdir())if p.is_file()}
    provenance = dict(supplied_files=supplied_files,
        supplied_replacement_applied='START_CN.md incorporated in START_PROMPT.md; missing numeric range/reference sentence supplied from SPEC; matching English translation included',
        unavailable_replacements='SYNC_MAP lists revised/FFT-Bench files, but no revised/ directory or Markdown replacement files other than START_CN.md is present',
        shared_files={rel:sha(PUBLIC/rel)for rel in shared},
        specification_sha256=sha(specpath),policy_sha256=sha(PUBLIC/'fft64_benchmark/profiles/policy.json'),
        scoring_source_sha256=sha(PUBLIC/'fft64_benchmark/tools/scoring.py'))
    (Path(__file__).parent/'source_alignment.json').write_text(json.dumps(provenance, indent=2)+'\n')
    print('Shared contracts aligned; FFT numerical/hardware/protocol specifications and scoring executable unchanged.')


if __name__ == '__main__':
    main()
