import sys, numpy as np, os, shutil
sys.path.insert(0,'/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/fft64_benchmark/tools')
from model import evaluation_frames, quality
from simulate import schedule, simulate, decode
src=open(sys.argv[1]).read()
frames,labels=evaluation_frames(20261118,1024)
n=int(sys.argv[2]) if len(sys.argv)>2 else 128
frames=frames[:n]; labels=labels[:n]
ev,meta=schedule(frames,11)
d='/tmp/num1'; shutil.rmtree(d,ignore_errors=True); os.makedirs(d,exist_ok=True)
raw=simulate(src,ev,d+'/sim','iverilog')
g,lat=decode(raw,ev,meta)
q=quality(frames,g)
print("minSQNR %.2f pooled %.2f feasible %s"%(q['minimum_frame_sqnr_db'],q['pooled_sqnr_db'],q['feasible']))
print("failed frames:",q['failed_frames'][:20])
for f in q['failed_frames'][:6]:
    r=np.fft.fft(frames[f][:,0]+1j*frames[f][:,1]); p=g[f][:,0]+1j*g[f][:,1]
    print(" frame",f,labels[f],"relmax %.2e"%(np.abs(p-r).max()/np.abs(r).max()))
print("lat",lat['maximum_first_output_latency_cycles'],"compl",lat['maximum_frame_completion_cycles'])
