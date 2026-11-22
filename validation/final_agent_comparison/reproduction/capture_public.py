"""Preserve compact public search evidence and tested submission snapshots."""
from pathlib import Path
import json
import os
import shutil

IGNORE_DIRS={'csrc','simv.daidir','dc_work','obj_dir','obj','__pycache__','.venv','venv'}
IGNORE_NAMES={'simv','vectors.txt','output.txt','source.sv','staged.sv','tb.sv','mapped.ddc','lock'}
SUFFIXES={'.json','.csv','.rpt','.log','.sdc','.tcl','.npz','.sv','.v','.py','.ys','.script','.md'}


def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)


def compact(source,target):
    for folder,dirs,files in os.walk(source):
        dirs[:]=[d for d in dirs if d not in IGNORE_DIRS]
        current=Path(folder)
        for name in files:
            p=current/name;rel=p.relative_to(source)
            if name in IGNORE_NAMES or p.suffix not in SUFFIXES:continue
            if name=='mapped.v'and'frequency_certificates'in p.parts:continue
            # Keep complete 321-II summary/identity, not duplicate chunk builds.
            if any(part.startswith('intervals_')for part in rel.parts):continue
            copy(p,target/rel)


def main():
    root=Path(Path('/tmp/fft_final_agent_review_path.txt').read_text().strip())
    campaign=json.loads((root/'campaign.json').read_text())
    totals=[]
    for case in campaign['cases']:
        source=Path(case['original_workspace']);target=root/'public_evidence'/case['id']
        count=0
        for directory in sorted((source/'runs').iterdir()):
            if not directory.is_dir():continue
            result=directory/'result.json'
            if not result.exists()and directory.name!='environment':continue
            compact(directory.resolve(),target/'runs'/directory.name)
            job=directory.resolve().parent
            snapshot=job/'submission'
            if snapshot.is_dir():
                shutil.copytree(snapshot,target/'snapshots'/directory.name/'submission',dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns(*IGNORE_DIRS))
            count+=1
        # Agent-authored experiment source, scripts and measured CSV/JSON logs.
        for name in ['work','experiments']:
            folder=source/name
            if folder.is_dir():compact(folder,target/'development'/name)
        files=[p for p in target.rglob('*')if p.is_file()]
        totals.append(dict(agent=case['id'],public_runs=count,files=len(files),bytes=sum(p.stat().st_size for p in files)))
    (root/'public_capture.json').write_text(json.dumps(dict(status='COMPLETE',cases=totals,
        scope='All recorded public run summaries, full 321-II aggregate/identity, tool logs/reports/netlists, exact tested submission snapshots and authored experiment scripts. Reconstructible builds and per-cycle vectors/output omitted; originals remain in each workspace.'),indent=2)+'\n')
    print(json.dumps(totals,indent=2))


if __name__=='__main__':main()
