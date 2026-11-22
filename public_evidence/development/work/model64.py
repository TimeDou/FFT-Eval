import numpy as np, sys
sys.path.insert(0,'/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/fft64_benchmark/tools')
from model import evaluation_frames, quality

N=64; ns=6
Ms=[N//2**(s+1) for s in range(ns)]

def mkcoef(CFRAC):
    return [[(int(round(np.cos(-2*np.pi*j/(2*M))*(1<<CFRAC))),int(round(np.sin(-2*np.pi*j/(2*M))*(1<<CFRAC)))) for j in range(M)] for M in Ms]

def rnd(p, CFRAC):
    return (p + (1<<(CFRAC-1))) >> CFRAC     # arithmetic shift on python ints is floor => matches >>> for negatives

def sim_frames(frames, CFRAC=12, TRUNC=None, T=200):
    """frames: (F,64,2) int. returns (F,64,2) outputs at 15 frac."""
    COEF=mkcoef(CFRAC)
    F=len(frames)
    out=np.zeros((F,64,2),dtype=np.int64)
    for fi in range(F):
        x=frames[fi]
        dly=[[0j]*M for M in Ms]
        # use integer pairs to model exactly
        dlyR=[[0]*M for M in Ms]; dlyI=[[0]*M for M in Ms]
        oR=[];oI=[]
        for sc in range(T):
            vR=int(x[sc,0]) if sc<N else 0
            vI=int(x[sc,1]) if sc<N else 0
            for s in range(ns):
                M=Ms[s]; ph=(sc//M)&1; addr=sc&(M-1)
                dR=dlyR[s][addr]; dI=dlyI[s][addr]
                if ph==0:
                    nR,nI=dR,dI
                    dlyR[s][addr]=vR; dlyI[s][addr]=vI
                else:
                    yR=dR+vR; yI=dI+vI
                    dR2=dR-vR; dI2=dI-vI
                    cr,ci=COEF[s][addr]
                    zR=rnd(dR2*cr-dI2*ci, CFRAC)
                    zI=rnd(dR2*ci+dI2*cr, CFRAC)
                    nR,nI=zR,zI
                    dlyR[s][addr]=yR; dlyI[s][addr]=yI
                vR,vI=nR,nI
            oR.append(vR); oI.append(vI)
        L=63
        for t in range(64):
            j=63-int(f'{t:06b}'[::-1],2)
            out[fi,j,0]=oR[L+t]; out[fi,j,1]=oI[L+t]
    return out

frames,labels=evaluation_frames(20261118, 1024)
print("frames",frames.shape)
z=sim_frames(frames)
q=quality(frames,z)
print("SQNR min %.2f pooled %.2f feasible %s zero_exact %s"%(q['minimum_frame_sqnr_db'],q['pooled_sqnr_db'],q['feasible'],q['zero_frame_exact']))
# worst frame label
q2=quality(frames,z)
