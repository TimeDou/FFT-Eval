import numpy as np, sys, math
sys.path.insert(0,'/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/fft64_benchmark/tools')
from model import evaluation_frames, quality
N=64; NS=6; Ms=[32,16,8,4,2,1]
def rnd(p,f): return (p + (1<<(f-1)))>>f
def sgn(v,bits):
    v&=(1<<bits)-1
    return v-(1<<bits) if v>>(bits-1) else v
COEFS={}
def getcoef(CFRAC):
    if CFRAC not in COEFS:
        COEFS[CFRAC]=[[(int(round(math.cos(-2*math.pi*j/(2*M))*(1<<CFRAC))),int(round(math.sin(-2*math.pi*j/(2*M))*(1<<CFRAC)))) for j in range(M)] for M in Ms]
    return COEFS[CFRAC]
def run_frame(x, CFRAC=10, drop=0):
    """drop = number of LSBs removed when storing to the output buffer (0,2,4)"""
    COEF=getcoef(CFRAC)
    dR=[[0]*M for M in Ms]; dI=[[0]*M for M in Ms]
    out=np.zeros((64,2),dtype=np.int64)
    for sc in range(160):
        vR=int(x[sc,0]) if sc<64 else 0
        vI=int(x[sc,1]) if sc<64 else 0
        for s in range(NS):
            M=Ms[s]; ph=(sc//M)&1; addr=sc&(M-1)
            Wo=16+s+1
            dR0=dR[s][addr]; dI0=dI[s][addr]
            if ph==0:
                nR,nI=dR0,dI0
                dR[s][addr]=vR; dI[s][addr]=vI
            else:
                yR=sgn(dR0+vR,Wo); yI=sgn(dI0+vI,Wo)
                aR=sgn(dR0-vR,Wo); aI=sgn(dI0-vI,Wo)
                cr,ci=COEF[s][addr]
                nR=sgn(rnd(aR*cr-aI*ci,CFRAC),Wo); nI=sgn(rnd(aR*ci+aI*cr,CFRAC),Wo)
                dR[s][addr]=yR; dI[s][addr]=yI
            vR,vI=nR,nI
        if 63<=sc<=126:
            t=sc-63
            j=63-int(f'{t:06b}'[::-1],2)
            if drop: out[j,0]=rnd(vR,drop)*(1<<drop); out[j,1]=rnd(vI,drop)*(1<<drop)
            else: out[j,0]=vR; out[j,1]=vI
    return out
frames,_=evaluation_frames(20261118,1024)
frames=frames[:700]
for CFRAC,drop in [(10,0),(10,2),(10,3),(9,2),(10,4),(8,2)]:
    z=np.array([run_frame(f,CFRAC,drop) for f in frames])
    q=quality(frames,z)
    print("CFRAC=%d drop=%d (RAM %d bits): minSQNR %.2f dB feasible %s"%(CFRAC,drop,22-drop,q['minimum_frame_sqnr_db'],q['feasible']))
