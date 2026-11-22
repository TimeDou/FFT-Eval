#!/usr/bin/env python3
"""Additional self-generated PUBLIC-domain tests, independent of official vectors."""
import sys,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'fft64_benchmark/tools'))
from model import evaluation_frames,quality
from simulate import schedule,simulate,decode
name=sys.argv[1] if len(sys.argv)>1 else 'block15'
x,labels=evaluation_frames(761239,8192)
# Legal maximum-bin witnesses exercise complex component growth above 32.
t=np.arange(64);extra=[]
for k in range(64):
 c=np.cos(2*np.pi*k*t/64);s=np.sin(2*np.pi*k*t/64)
 extra.extend([np.stack([np.where(c>=0,16384,-16384),np.where(s>=0,16384,-16384)],-1),np.stack([np.where(c>=0,16384,-16384),np.where(s>=0,-16384,16384)],-1)])
rng=np.random.default_rng(382491)
for mag in [1024,1025,2047,2048,4095,4096,8191,8192,16383,16384]:
 for _ in range(8):extra.append(rng.choice([-mag,mag],(64,2)))
x=np.concatenate([x,np.asarray(extra)],axis=0)
e,m=schedule(x)
s=Path('experiments/'+name+'/rtl/fft64_top.sv').read_text()
d=Path('runs/robustness_'+name)
r=simulate(s,e,d,'iverilog');y,l=decode(r,e,m);q=quality(x,y)
(d/'summary.json').write_text(json.dumps(dict(quality=q,first=l['maximum_first_output_latency_cycles'],completion=l['maximum_frame_completion_cycles'],seed=761239,extra_growth_and_magnitude_frames=len(extra),coverage='Additional self-generated public vectors; not hidden evaluation'),indent=2))
print(name,q,flush=True)
