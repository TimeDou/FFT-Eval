#!/usr/bin/env python3
"""Independent fixed-point feasibility screen; does not replace RTL or EDA."""
import sys,math,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'fft64_benchmark/tools'))
from model import evaluation_frames,quality
x,_=evaluation_frames(20261118)
reverse=[int(f'{i:06b}'[::-1],2) for i in range(64)]
results=[]
for width,frac,scaling in [(22,15,6),(21,14,6),(20,13,6),(19,12,6),(20,15,4),(19,15,3),(18,15,2),(17,15,1)]:
 for tf in [14,12,11,10,9]:
  a=x[:,reverse,:].copy()
  shift=15-frac
  if shift:a=(a+(1<<(shift-1)))>>shift
  overflow=False
  for stage in range(6):
   h=1<<stage
   for start in range(0,64,h*2):
    for j in range(h):
     k=j*(32//h)
     cr=round(math.cos(math.pi*k/32)*(1<<tf));ci=round(-math.sin(math.pi*k/32)*(1<<tf))
     b=a[:,start+j+h,:].copy(); aa=a[:,start+j,:].copy()
     if k==0:t=b
     elif k==16:t=np.stack([b[:,1],-b[:,0]],-1)
     else:t=np.stack([(b[:,0]*cr-b[:,1]*ci+(1<<(tf-1)))>>tf,(b[:,0]*ci+b[:,1]*cr+(1<<(tf-1)))>>tf],-1)
     u=aa+t;v=aa-t
     if stage>=scaling:u=(u+1)>>1;v=(v+1)>>1
     if min(u.min(),v.min())<-(1<<(width-1)) or max(u.max(),v.max())>=(1<<(width-1)):overflow=True
     a[:,start+j,:]=u;a[:,start+j+h,:]=v
   # fixed width storage: checked above, never silently saturate
  y=a*(1<<(shift+max(0,6-scaling)))
  q=quality(x,y)
  row=dict(width=width,frac=frac,scale_from_stage=scaling,twfrac=tf,min_sqnr_db=q['minimum_frame_sqnr_db'],feasible=q['feasible'] and not overflow,overflow=overflow)
  results.append(row);print(json.dumps(row),flush=True)
Path('runs/precision_screen.json').write_text(json.dumps(results,indent=2))
