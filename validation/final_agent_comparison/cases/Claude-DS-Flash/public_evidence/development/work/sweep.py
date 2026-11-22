import sys, numpy as np, os, shutil
sys.path.insert(0,'/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/fft64_benchmark/tools')
from model import evaluation_frames, quality
from simulate import simulate, decode
from throughput import stream_schedule
src=open(sys.argv[1]).read()
frames,_=evaluation_frames(20261118,1024)
frames=frames[:int(sys.argv[3]) if len(sys.argv)>3 else 96]
for iv in [int(x) for x in sys.argv[2].split(',')]:
    d='/tmp/sw%d'%iv
    shutil.rmtree(d,ignore_errors=True); os.makedirs(d,exist_ok=True)
    ev,meta,i2=stream_schedule(frames,iv,11,tail=True,reset_probes=True)
    try:
        raw=simulate(src,ev,d+'/sim','iverilog')
        g,lat=decode(raw,ev,meta)
        q=quality(i2,g)
        print("II",iv,"SQNR %.2f"%q['minimum_frame_sqnr_db'],"feasible",q['feasible'],"lat",lat['maximum_first_output_latency_cycles'],"compl",lat['maximum_frame_completion_cycles'])
    except Exception as e:
        print("II",iv,"FAIL:",str(e)[:150])
