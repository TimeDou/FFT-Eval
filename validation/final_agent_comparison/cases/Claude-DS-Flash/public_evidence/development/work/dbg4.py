import sys, numpy as np, os, shutil
sys.path.insert(0,'/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/fft64_benchmark/tools')
from model import evaluation_frames, reference
from simulate import simulate, decode
from throughput import stream_schedule
src=open('/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/submission/rtl/fft64_top.sv').read()
frames,labels=evaluation_frames(20261118,1024)
frames=frames[:2]
ev,meta,i2=stream_schedule(frames,384,11,tail=False,reset_probes=False)
shutil.rmtree('/tmp/lt2',ignore_errors=True); os.makedirs('/tmp/lt2',exist_ok=True)
raw=simulate(src,ev,'/tmp/lt2/sim','iverilog')
g,lat=decode(raw,ev,meta)
ref=reference(i2)
for f in range(2):
    print("frame",f)
    pred=g[f][:,0]+1j*g[f][:,1]
    r=ref[f]
    err=np.abs(pred-r)
    print(" err per idx:", np.round(err[:16],0))
    print(" |ref|:", np.round(np.abs(r[:8]),0))
    print(" pred:", pred[:8])
    print(" ref :", r[:8])
