import numpy as np, sys
sys_path_work='/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/work'
sys.path.insert(0,'/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/fft64_benchmark/tools'); sys.path.insert(0,sys_path_work)
from model import evaluation_frames
from fftmodel import dr4, tw_table

def rnd_sh(v, sh):
    if sh<=0: return v<<(-sh)
    return (v+(1<<(sh-1)))>>sh

def fft_r4_fixed(xi, twbits=15, trun=False):
    N=64; T=tw_table(twbits)
    def qmul(ar,ai,k):
        k%=64
        if k==0: return ar,ai
        wr,wi=T[k]
        pr=ar*wr-ai*wi; pi=ar*wi+ai*wr
        if trun: return pr>>twbits, pi>>twbits
        return rnd_sh(pr,twbits), rnd_sh(pi,twbits)
    A=np.zeros((2,N),dtype=np.int64)
    for n in range(N):
        A[0,dr4(n)]=xi[0,n]; A[1,dr4(n)]=xi[1,n]
    for s in range(3):
        m=4**s
        for b in range(0,N,4*m):
            for k in range(m):
                i0=b+k; i1=b+k+m; i2=b+k+2*m; i3=b+k+3*m
                a0=(A[0,i0],A[1,i0]); a1=(A[0,i1],A[1,i1]); a2=(A[0,i2],A[1,i2]); a3=(A[0,i3],A[1,i3])
                base=16>>(2*s)
                a1=qmul(*a1,(k*base)%64); a2=qmul(*a2,(2*k*base)%64); a3=qmul(*a3,(3*k*base)%64)
                t0=(a0[0]+a2[0],a0[1]+a2[1]); t1=(a0[0]-a2[0],a0[1]-a2[1])
                t2=(a1[0]+a3[0],a1[1]+a3[1]); t3=(a1[0]-a3[0],a1[1]-a3[1])
                A[0,i0]=t0[0]+t2[0]; A[1,i0]=t0[1]+t2[1]
                A[0,i1]=t1[0]+t3[1]; A[1,i1]=t1[1]-t3[0]
                A[0,i2]=t0[0]-t2[0]; A[1,i2]=t0[1]-t2[1]
                A[0,i3]=t1[0]-t3[1]; A[1,i3]=t1[1]+t3[0]
    return A

frames,labels=evaluation_frames(20261118,1024)
for twb in [9,10,11,12,13,14,15,16]:
    worst=1e9; wl=None
    for fr,lb in zip(frames,labels):
        out=fft_r4_fixed(fr.T.copy(),twbits=twb)
        z=(out[0]+1j*out[1])/32768
        ref=np.fft.fft((fr[:,0]+1j*fr[:,1])/32768)
        e=np.sum(np.abs(z-ref)**2); s=np.sum(np.abs(ref)**2)
        if s>0:
            q=10*np.log10(s/e) if e>0 else 999
            if q<worst: worst=q; wl=lb
    print(f"twb={twb}: worst SQNR = {worst:.2f} dB  [{wl}]")
