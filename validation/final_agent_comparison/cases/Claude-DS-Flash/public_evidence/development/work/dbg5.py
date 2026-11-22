import sys, numpy as np, os, shutil
sys.path.insert(0,'/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/fft64_benchmark/tools')
from model import evaluation_frames, reference, quality
from simulate import simulate, decode
from throughput import stream_schedule
sys.path.insert(0,'.')
import importlib.util
spec=importlib.util.spec_from_file_location("m64","model64.py")
# reuse sim_frames from model64 without running its main
srcm=open('model64.py').read().split('frames,labels=evaluation_frames')[0]
ns={}; exec(srcm, ns)
sim_frames=ns['sim_frames']
src=open('/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/submission/rtl/fft64_top.sv').read()
frames,labels=evaluation_frames(20261118,1024)
frames=frames[:2]
ev,meta,i2=stream_schedule(frames,384,11,tail=False,reset_probes=False)
shutil.rmtree('/tmp/lt3',ignore_errors=True); os.makedirs('/tmp/lt3',exist_ok=True)
raw=simulate(src,ev,'/tmp/lt3/sim','iverilog')
g,lat=decode(raw,ev,meta)
m=sim_frames(frames)
print("model sqnr", quality(i2,m)['minimum_frame_sqnr_db'])
print("rtl   sqnr", quality(i2,g)['minimum_frame_sqnr_db'])
for f in range(2):
    d=np.abs(g[f]-m[f])
    print("frame",f,"maxdiff",d.max(),"ndiff",(d>0).sum())
    print(" rtl0",g[f][0],"model0",m[f][0])
    print(" rtl1",g[f][1],"model1",m[f][1])
    print(" rtl2",g[f][2],"model2",m[f][2])
