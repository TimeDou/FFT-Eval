from pathlib import Path
import json,shutil,sys,hashlib,tempfile
root=Path.cwd();dst=root/'submission';candidates=[]
for name in ['F003','S001','S003','R001','C001','C002','C003','C004','C005','C006','C007']:
 path=root/'runs'/('arch_'+name)/'result.json'
 if not path.exists():continue
 r=json.loads(path.read_text());g=r.get('grade',{})
 if r.get('status')=='COMPLETE' and r.get('profile')=='architecture' and g.get('resolved') and g.get('score_valid') and g.get('scoring_scope')=='public_preview':
  candidates.append((g['score'],name,r,path))
if not candidates:raise RuntimeError('No complete feasible public architecture preview')
score,name,r,report=max(candidates,key=lambda x:x[0]);src=root/'experiments'/name
old=json.loads((dst/'frozen_selection.json').read_text())if(dst/'frozen_selection.json').exists()else{}
# Audit with the PUBLIC loader before copying. No EDA or recipe is executed.
sys.path.insert(0,str(root/'fft64_benchmark/tools'))
from evaluate import assemble
text,info=assemble(src)
assert info['source_sha256']==r['source']['source_sha256']
if info.get('implementation'):
 assert info['implementation']['mapped_sha256']==r['ppa']['imported_sha256']
if old.get('candidate')!=name:
 with tempfile.TemporaryDirectory(prefix='.freeze_',dir=root/'experiments')as tmp:
  tmp=Path(tmp)
  for n in ['rtl','flow','implementation']:
   if(src/n).exists():shutil.copytree(src/n,tmp/n)
  for n in ['rtl','flow','implementation']:
   if(dst/n).exists():shutil.rmtree(dst/n)
   if(tmp/n).exists():shutil.move(tmp/n,dst/n)
 shutil.copy2(src/'design_config.json',dst/'design_config.json')
 shutil.copy2(report,dst/'public_verification.json')
 payload=dict(candidate=name,score=score,public_report=str(report.relative_to(root)),report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),source_sha256=info['source_sha256'],mapped_sha256=info.get('implementation',{}).get('mapped_sha256',r['ppa']['mapped_sha256']),official_score=False)
 (dst/'frozen_selection.json').write_text(json.dumps(payload,indent=2)+'\n')
 verified=assemble(dst)[1]
 assert verified['source_sha256']==info['source_sha256']
 print('FROZEN',name,score)
else:print('UNCHANGED',name,score)
for _,n,v,_ in sorted(candidates,reverse=True):print(n,v['grade']['score'],v['grade']['performance'])
