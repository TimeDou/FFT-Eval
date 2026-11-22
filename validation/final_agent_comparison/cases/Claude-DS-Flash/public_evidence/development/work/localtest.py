import sys, numpy as np, os, shutil
sys.path.insert(0,'/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/fft64_benchmark/tools')
from model import evaluation_frames, quality, quality_union
from simulate import schedule, simulate, decode
from throughput import stream_schedule

src=open(sys.argv[1]).read()
outdir=sys.argv[2] if len(sys.argv)>2 else '/tmp/localtest'
interval=int(sys.argv[3]) if len(sys.argv)>3 else 384
nframes=int(sys.argv[4]) if len(sys.argv)>4 else 128
shutil.rmtree(outdir,ignore_errors=True)
os.makedirs(outdir,exist_ok=True)
frames,labels=evaluation_frames(20261118,1024)
frames=frames[:nframes]
events,meta,i2=stream_schedule(frames,interval,11,tail=True,reset_probes=True)
raw=simulate(src,events,outdir+'/sim','iverilog')
groups,lat=decode(raw,events,meta)
q=quality(i2,groups)
print("interval",interval,"frames",len(i2))
print("minSQNR %.2f dB pooled %.2f feasible %s zero %s"%(q['minimum_frame_sqnr_db'],q['pooled_sqnr_db'],q['feasible'],q['zero_frame_exact']))
print("lat first",lat['maximum_first_output_latency_cycles'],"completion",lat['maximum_frame_completion_cycles'])
print("first_output_latency set",lat['first_output_latency_cycles'][:5],"...")
