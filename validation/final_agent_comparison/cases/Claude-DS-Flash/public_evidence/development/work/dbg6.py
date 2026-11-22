import sys, numpy as np, os, shutil
sys.path.insert(0,'/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/fft64_benchmark/tools')
from model import reference
from simulate import simulate, decode
from throughput import stream_schedule
src=open('/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/submission/rtl/fft64_top.sv').read()
N=64
t=np.arange(N)
tests={}
a=np.zeros((N,2)); a[:,0]=16384; a[:,1]=16384; tests['DC']=a
a=np.zeros((N,2)); a[0,0]=16384; tests['impulse']=a
z=16384*np.exp(2j*np.pi*(1*t/N)); a=np.column_stack([z.real,z.imag]); tests['tone1']=a
z=16384*np.exp(2j*np.pi*(8*t/N)); a=np.column_stack([z.real,z.imag]); tests['tone8']=a
a=np.zeros((N,2)); a[:,0]=np.where(t%2==0,16384,-16384); tests['nyq']=a
names=list(tests)
frames=np.array([np.rint(tests[k]).astype(np.int64) for k in names])
ev,meta,i2=stream_schedule(frames,384,11,tail=False,reset_probes=False)
shutil.rmtree('/tmp/lt4',ignore_errors=True); os.makedirs('/tmp/lt4',exist_ok=True)
raw=simulate(src,ev,'/tmp/lt4/sim','iverilog')
g,lat=decode(raw,ev,meta)
ref=reference(i2)
for f,k in enumerate(names):
    pred=g[f][:,0]+1j*g[f][:,1]
    r=ref[f]*32768
    err=np.abs(pred-r)
    print(k,"maxerr %.0f  relmax %.2e"%(err.max(), err.max()/max(1,abs(r).max())))
    if err.max()>2:
        idx=np.argsort(-err)[:6]
        for i in idx: print("   idx",i,"pred",pred[i],"ref",r[i])
