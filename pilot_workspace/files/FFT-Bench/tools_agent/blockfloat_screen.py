#!/usr/bin/env python3
import sys,math,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'fft64_benchmark/tools'))
from model import evaluation_frames,quality
x,_=evaluation_frames(20261118)
reverse=[int(f'{i:06b}'[::-1],2) for i in range(64)]
rows=[]
for W in [18,17,16,15]:
 for tf in [10,9,8]:
  a=x[:,reverse,:].copy();ex=np.zeros(len(x),dtype=np.int64);overflow=False
  for stage in range(6):
   h=1<<stage; mag=np.max(np.where(a<0,-a-1,a),axis=(1,2))
   if stage==0:shift=np.full(len(x),max(0,17-W))
   elif stage==1:shift=(mag >=(1<<(W-2))).astype(np.int64)
   else:shift=(mag>=(1<<(W-3))).astype(np.int64)+(mag>=(1<<(W-2))).astype(np.int64)
   ex+=shift
   for start in range(0,64,h*2):
    for j in range(h):
     k=j*(32//h);cr=round(math.cos(math.pi*k/32)*(1<<tf));ci=round(-math.sin(math.pi*k/32)*(1<<tf))
     b=a[:,start+j+h,:].copy();aa=a[:,start+j,:].copy()
     if k==0:t=b
     elif k==16:t=np.stack([b[:,1],-b[:,0]],-1)
     else:t=np.stack([(b[:,0]*cr-b[:,1]*ci+(1<<(tf-1)))>>tf,(b[:,0]*ci+b[:,1]*cr+(1<<(tf-1)))>>tf],-1)
     u=aa+t;v=aa-t
     for z in [u,v]:
      sh=shift[:,None];base=z>>sh
      mask=(1<<sh)-1;rem=z&mask;half=(1<<sh)>>1
      z[:]=base+((sh!=0)&((rem>half)|((rem==half)&((base&1)!=0))))
      if z.min()<-(1<<(W-1)) or z.max()>=(1<<(W-1)):overflow=True
     a[:,start+j,:]=u;a[:,start+j+h,:]=v
  y=a*(1<<ex[:,None,None]);q=quality(x,y)
  row=dict(width=W,twfrac=tf,min_sqnr_db=q['minimum_frame_sqnr_db'],feasible=q['feasible']and not overflow,overflow=overflow,exponents=np.unique(ex).tolist());rows.append(row);print(json.dumps(row),flush=True)
Path('runs/blockfloat_screen.json').write_text(json.dumps(rows,indent=2))
