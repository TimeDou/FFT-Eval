"""Targeted public reset-abort tests using the unmodified public simulator."""
from pathlib import Path
import sys,json,os
import numpy as np
work=Path(sys.argv[1]);sys.path.insert(0,str(work.parent/'fft64_benchmark/tools'))
pre=json.loads((work/'asic/preflight.json').read_text())
os.environ['FFT_TECH_DIR']=str(Path(next(iter(pre['libraries']))).parent)
from model import evaluation_frames,quality
from evaluate import used_cell_models
from simulate import simulate,decode
x,_=evaluation_frames(746213)
offsets=[0,1,10,31,32,33,63,64,65,66,95,96,97,127,128,129,159,160,161,191,192,193,194,195,224,225,226,240,256,257,258]
ev=[];epochs=[]
for j,offset in enumerate(offsets):
 begin=len(ev);ev +=[[1,0,0,0,0]]*3+[[0,0,0,0,0]]*2
 for c in range(offset):
  ev.append([0,1,int(c==0),*map(int,x[j,c])]if c<64 else[0,0,0,0,0])
 ev +=[[1,0,0,0,0]]*2
 start=len(ev)-begin
 ev.extend([0,1,int(c==0),*map(int,z)]for c,z in enumerate(x[j+40]))
 ev +=[[0,0,0,0,0]]*400
 epochs.append((begin,len(ev),start,offset,j+40))
ev=np.asarray(ev,dtype=np.int64)
source=(work/'rtl_sim/source.sv').read_text();mapped=(work/'asic/mapped.v').read_text();gate_source=used_cell_models(mapped)+'\n'+mapped
out=work/'agent_reset_stress'
r=simulate(source,ev,out/'rtl','vcs',reuse_compiled_from=work/'rtl_sim')
outputs=[]
for begin,end,start,offset,j in epochs:
 rr=r[begin:end].copy();rr[:,0]-=begin
 yy,lat=decode(rr,ev[begin:end],dict(frame_starts=[start],ignore_before_cycle=start))
 outputs.append(yy[0])
q=quality(x[[p[4]for p in epochs]],np.asarray(outputs));assert q['feasible'],q
for mode in [0,1,20261121]:
 g=simulate(gate_source,ev,out/'mapped','vcs',initialization=mode,reuse_compiled_from=work/'mapped_sim')
 assert np.array_equal(r[:,1:3],g[:,1:3]),'reset control-cycle mismatch'
 assert np.array_equal(r[r[:,1]==1,3:5],g[g[:,1]==1,3:5]),'reset valid payload mismatch'
result=dict(status='PASS',tested_abort_offsets=offsets,new_frame_immediately_after_reset=True,epochs=len(epochs),quality=q,rtl_mapped_cycle_and_payload_equal=True,gate_initial_state_modes=[0,1,20261121],coverage='Additional public tests, including reset during active output and pipeline boundaries')
(out/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
