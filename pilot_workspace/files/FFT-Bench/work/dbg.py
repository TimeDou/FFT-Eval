import numpy as np, subprocess, sys, os
W='/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/work'
RTL='/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/submission/rtl'
srcs=sorted(os.path.join(RTL,f) for f in os.listdir(RTL) if f.endswith('.v'))
subprocess.run(['iverilog','-g2012','-o',W+'/sim.vvp','-s','tb']+srcs+[W+'/tb.v'],check=True)

def run(frames):
    ev=[[1,0,0,0,0]]*4+[[0,0,0,0,0]]*10
    starts=[]
    for x in frames:
        starts.append(len(ev))
        ev+=[[0,1,int(k==0),int(z[0]),int(z[1])] for k,z in enumerate(x)]
        ev+=[[0,0,0,0,0]]*300
    ev+=[[0,0,0,0,0]]*40
    np.savetxt(W+'/vec.txt',np.asarray(ev,dtype=np.int64),fmt='%d')
    subprocess.run(['vvp',W+'/sim.vvp','+VECTORS='+W+'/vec.txt','+OUTPUT='+W+'/out.txt'],check=True)
    raw=np.loadtxt(W+'/out.txt',dtype=np.int64,ndmin=2)
    os_=np.flatnonzero(raw[:,2]==1)
    return [raw[o:o+64,3:5] for o in os_], [int(o-s) for o,s in zip(os_,starts)]

tests=[]
x=np.zeros((64,2),dtype=np.int64); x[:,0]=1000; tests.append(('DC1000',x))
x=np.zeros((64,2),dtype=np.int64); x[0,0]=16384; tests.append(('impulse',x))
t=np.arange(64)
x=np.zeros((64,2),dtype=np.int64); x[:,0]=np.rint(8192*np.cos(2*np.pi*5*t/64)); x[:,1]=np.rint(8192*np.sin(2*np.pi*5*t/64)); tests.append(('tone5',x))
outs,lats=run([tt[1] for tt in tests])
for (name,x),z,lat in zip(tests,outs,lats):
    ref=np.fft.fft((x[:,0]+1j*x[:,1])/32768)
    pred=(z[:,0]+1j*z[:,1])/32768
    err=np.abs(pred-ref)
    print(f"--- {name} lat={lat}")
    print("  ref[0:6] ", np.round(ref[:6],4))
    print("  got[0:6] ", np.round(pred[:6],4))
    print("  maxerr", err.max(), "argmax", err.argmax())
    # check permutation: compare sorted magnitudes
    print("  |ref| sorted[:6]", np.round(np.sort(np.abs(ref))[:4],4), " |got| sorted[:4]", np.round(np.sort(np.abs(pred))[:4],4))
