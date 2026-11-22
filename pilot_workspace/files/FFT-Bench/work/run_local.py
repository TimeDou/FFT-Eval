import numpy as np, subprocess, sys, os
sys.path.insert(0,'/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/fft64_benchmark/tools')
from model import evaluation_frames

RTL='/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/submission/rtl'
W='/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/work'

def build():
    srcs=sorted(os.path.join(RTL,f) for f in os.listdir(RTL) if f.endswith('.v'))
    r=subprocess.run(['iverilog','-g2012','-o',W+'/sim.vvp','-s','tb']+srcs+[W+'/tb.v'],capture_output=True,text=True)
    if r.returncode!=0: print(r.stdout,r.stderr); sys.exit(1)

def run(events, tag='t'):
    np.savetxt(W+'/vec.txt', np.asarray(events,dtype=np.int64), fmt='%d')
    r=subprocess.run(['vvp',W+'/sim.vvp','+VECTORS='+W+'/vec.txt','+OUTPUT='+W+'/out.txt'],capture_output=True,text=True)
    if r.returncode!=0: print(r.stdout[-3000:], r.stderr[-3000:]); sys.exit(1)
    raw=np.loadtxt(W+'/out.txt',dtype=np.int64,ndmin=2)
    return raw

def schedule(frames, II=384, gap0=20):
    ev=[]
    ev += [[1,0,0,0,0]]*4
    ev += [[0,0,0,0,0]]*gap0
    starts=[]
    for x in frames:
        starts.append(len(ev))
        ev += [[0,1,int(k==0),int(z[0]),int(z[1])] for k,z in enumerate(x)]
        ev += [[0,0,0,0,0]]*(II-64)
    ev += [[0,0,0,0,0]]*40
    return np.asarray(ev,dtype=np.int64), starts

frames,labels=evaluation_frames(20261118,1024)
nframes=int(sys.argv[1]) if len(sys.argv)>1 else 64
frames=frames[:nframes]
build()
ev,starts=schedule(frames,384)
raw=run(ev)
# decode
valid=raw[:,1]==1
ostart=np.flatnonzero(raw[:,2]==1)
assert len(ostart)==len(frames), (len(ostart),len(frames))
groups=[]
for o,i in zip(ostart,starts):
    assert np.all(raw[o:o+64,1]==1), "noncontiguous"
    groups.append(raw[o:o+64,3:5])
groups=np.asarray(groups)
lat=[int(o-i) for o,i in zip(ostart,starts)]
print("first-output latency: min %d max %d ; completion max %d"%(min(lat),max(lat),max(o+63-i for o,i in zip(ostart,starts))))
sq=[]
for fr,z in zip(frames,groups):
    ref=np.fft.fft((fr[:,0]+1j*fr[:,1])/32768)
    pred=(z[:,0]+1j*z[:,1])/32768
    s=np.sum(np.abs(ref)**2); e=np.sum(np.abs(pred-ref)**2)
    sq.append(10*np.log10(s/e) if e>0 else 999)
sq=np.array(sq)
print("SQNR: min %.2f dB  mean %.2f dB   (worst frame idx %d)"%(sq.min(),sq.mean(),sq.argmin()))
bad=np.flatnonzero(sq<50)
print("frames < 50dB:",bad[:10], "count",len(bad))
