"""Run an experimental DC+PT synthesis in the container. Development only.

python3 exp.py NAME RTL PERIOD_PS RECIPE_FILE
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path('/mnt/DATA1/sj/FFT/Claude-Opus-5.5/FFT-Bench')
SHARE = Path('/mnt/DATA1/sj/FFT/Claude-Opus-5.5/Synopsys/opus_work')


def run(name, rtl, period, recipe):
    d = SHARE / 'runs' / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    shutil.copy(rtl, d / 'rtl.v')
    shutil.copy(recipe, d / 'recipe.tcl')
    c = f'/mnt/mydata/opus_work/runs/{name}'
    cmd = (f'cd {c} && export EXP_RTL={c}/rtl.v EXP_OUT={c} EXP_PERIOD_PS={period} EXP_RECIPE={c}/recipe.tcl && '
           f'dc_shell -f /mnt/mydata/opus_work/dc_exp.tcl > dc.log 2>&1; '
           f'pt_shell -f /mnt/mydata/opus_work/pt_exp.tcl > pt.log 2>&1; echo done')
    subprocess.run(['bash', str(REPO / 'synopsys.sh'), 'exec', '--', 'bash', '-c', cmd],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return summarize(d)


def summarize(d):
    res = dict(name=d.name)
    try:
        a = (d / 'area.rpt').read_text()
        res['area'] = float(re.search(r'Total cell area:\s+([0-9.]+)', a).group(1))
        res['comb'] = float(re.search(r'Combinational area:\s+([0-9.]+)', a).group(1))
        res['seq'] = float(re.search(r'Noncombinational area:\s+([0-9.]+)', a).group(1))
    except Exception as exc:
        res['error'] = 'area: ' + str(exc)
    try:
        res.update(json.loads((d / 'pt.json').read_text()))
    except Exception as exc:
        res['pt_error'] = str(exc)
    try:
        refs = {}
        for line in (d / 'ref.rpt').read_text().splitlines():
            m = re.match(r'^(\S+_ASAP7_75t_R)\s+\S+\s+([0-9.]+)\s+(\d+)\s+([0-9.]+)', line)
            if m:
                refs[m.group(1)] = (int(m.group(3)), float(m.group(4)))
        res['nflops'] = sum(v[0] for k, v in refs.items() if k.startswith('DFF'))
        res['ninv'] = sum(v[0] for k, v in refs.items() if k.startswith('INV'))
        res['top_refs'] = sorted(refs.items(), key=lambda kv: -kv[1][1])[:10]
    except Exception as exc:
        res['ref_error'] = str(exc)
    errs = [l for l in (d / 'dc.log').read_text().splitlines() if l.startswith(('Error', 'EXP_FATAL'))] if (d / 'dc.log').exists() else ['no log']
    if errs:
        res['dc_errors'] = errs[:5]
    return res


if __name__ == '__main__':
    r = run(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4])
    out = REPO / 'work' / 'results' / (sys.argv[1] + '.json')
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(r, indent=1))
    print(json.dumps(r, indent=1))
