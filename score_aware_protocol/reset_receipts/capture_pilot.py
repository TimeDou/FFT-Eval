"""Archive reconstructible pilot evidence before clearing Agent workspaces."""
from pathlib import Path
import gzip
import hashlib
import json
import os
import shutil
import subprocess

BASE = Path('/mnt/DATA1/sj/ALS/DP2.0/DSBench')
NAMES = ['Claude-DS-Flash','Codex-GPT-6.1-Sol-Max','Codex-GPT-6.2-Sol-Max']
SKIP_DIRS = {'.git','__pycache__','csrc','simv.daidir','dc_work','obj','obj_dir','runtime','tech','physical_cache'}
SKIP_NAMES = {'simv','vectors.txt','output.txt','mapped.ddc'}
GENERATED_SUFFIXES = {'.o','.a','.so','.d','.vcd','.fst','.pyc','.bin','.npy'}


def main():
    for name in NAMES:
        source=Path('/home/sj/FFT')/name
        repo=BASE/('FFT-Eval-agent-'+name)
        target=repo/'pilot_workspace'
        if (target/'capture_manifest.json').exists():
            print('REUSED',name,flush=True)
            continue
        target.mkdir(parents=True,exist_ok=True)
        records=[]
        for origin in [source/'FFT-Bench',source/'Synopsys']:
            for directory,dirs,files in os.walk(origin,followlinks=False):
                parent=Path(directory)
                relative=parent.relative_to(source)
                removed=[]
                for item in list(dirs):
                    p=parent/item
                    if p.is_symlink() or item in SKIP_DIRS or item.startswith('Vfft'):
                        dirs.remove(item);removed.append(item)
                    elif origin.name=='FFT-Bench' and parent==origin and item in {'fft64_benchmark','docs'}:
                        dirs.remove(item);removed.append(item)
                    elif origin.name=='Synopsys' and item in {'fft64_benchmark','operator'} and 'jobs' in p.parts:
                        dirs.remove(item);removed.append(item)
                for item in removed:
                    records.append(dict(path=str(relative/item),action='excluded_directory',reason='Public dependency, duplicate benchmark snapshot, symlink or rebuildable simulator/cache directory'))
                for item in files:
                    p=parent/item;rel=p.relative_to(source)
                    if p.is_symlink():
                        records.append(dict(path=str(rel),action='symlink',target=os.readlink(p)));continue
                    size=p.stat().st_size
                    if item in SKIP_NAMES or p.suffix in GENERATED_SUFFIXES or (item.startswith('V') and p.suffix in {'.cpp','.h','.mk'}):
                        records.append(dict(path=str(rel),bytes=size,action='excluded_generated',reason='Rebuildable binaries, simulator sources, arrays or per-cycle text; final observed FFT outputs are retained separately'))
                        continue
                    # ELF output names need not carry a conventional suffix.
                    with p.open('rb') as f:head=f.read(4)
                    if head==b'\x7fELF':
                        records.append(dict(path=str(rel),bytes=size,action='excluded_generated',reason='Rebuildable ELF binary'));continue
                    dest=target/'files'/rel
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    sha=hashlib.sha256(p.read_bytes()).hexdigest()
                    compressed=size>512*1024 and p.suffix in {'.json','.log','.rpt','.txt'}
                    if compressed:
                        dest=dest.with_name(dest.name+'.gz')
                        with p.open('rb')as src,gzip.open(dest,'wb',compresslevel=6)as out:shutil.copyfileobj(src,out)
                        with gzip.open(dest,'rb')as f:assert hashlib.sha256(f.read()).hexdigest()==sha
                    else:shutil.copy2(p,dest)
                    records.append(dict(path=str(rel),bytes=size,sha256=sha,action='retained',
                         archive_path=str(dest.relative_to(target)),compressed=compressed))
        manifest=dict(agent=name,public_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source/'FFT-Bench',text=True).strip(),
                      original_directory=str(source),records=records,
                      scope='Pilot author-written sources, configurations, logs and measurements. Public tool dependencies, redundant source snapshots and rebuildable large simulation products are excluded. Final independent private evaluation and numerical observations already accompany this branch.')
        (target/'capture_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        (target/'README.md').write_text('# Pilot workspace evidence\n\nThis archive preserves the completed development process before the Agent workspace is reset. '
            'The branch retains the original benchmark and score. `capture_manifest.json` lists retained files and explicitly excluded rebuildable products. '
            'Large text reports are gzip-compressed with decompression SHA-256 checks. Final hidden measurements and observed FFT outputs remain in `agent_evaluation/`. '
            'This is a compact research record, rather than a byte-for-byte container or disk image.\n')
        print(name,'retained',sum(r['action']=='retained'for r in records),'files',flush=True)


if __name__=='__main__':main()
