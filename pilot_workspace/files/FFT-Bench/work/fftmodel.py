import numpy as np, itertools, sys
sys.path.insert(0,'/mnt/DATA1/sj/FFT/Claude-DS-Flash/FFT-Bench/fft64_benchmark/tools')
from model import evaluation_frames, quality

N=64; F=15

def dr4(n):
    # base-4 digit reversal of a 3-digit base-4 number
    d0=n&3; d1=(n>>2)&3; d2=(n>>4)&3
    return (d0<<4)|(d1<<2)|d2

def tw(k, mod):   # e^{-j2pi k/mod}
    return np.exp(-2j*np.pi*k/mod)

def fft_r4_float(x, twbits=None):
    A=np.zeros(N,dtype=complex)
    for n in range(N): A[dr4(n)]=x[n]
    for s in range(3):
        m=4**s
        for b in range(0,N,4*m):
            for k in range(m):
                a0=A[b+k]; a1=A[b+k+m]; a2=A[b+k+2*m]; a3=A[b+k+3*m]
                w1=tw(k,4*m); w2=tw(2*k,4*m); w3=tw(3*k,4*m)
                a1*=w1; a2*=w2; a3*=w3
                t0=a0+a2; t1=a0-a2; t2=a1+a3; t3=a1-a3
                A[b+k]=t0+t2; A[b+k+m]=t1-1j*t3; A[b+k+2*m]=t0-t2; A[b+k+3*m]=t1+1j*t3
    return A

def tw_table(bits):
    # twiddle table of e^{-j2pi k/64} for k=0..63, quantized to `bits` fractional bits signed
    q=1<<bits
    out=[]
    for k in range(64):
        z=np.exp(-2j*np.pi*k/64)
        out.append((int(round(z.real*q)), int(round(z.imag*q))))
    return out

def rnd(v, fbits):
    # round to nearest, ties away, arithmetic shift right by (fbits-15)
    sh=fbits-15
    if sh<=0: return v<<(-sh)
    add=1<<(sh-1)
    return (v+add)>>sh

def fft_r4_fixed(xi, twbits=15, guard=1, dshift=0):
    """xi: int array (2,N) Q15. Returns int array (2,N) Q15 output.
    internal width: 15 frac bits + (6+guard) integer bits."""
    W=21+guard  # total bits (sign + 5+guard int + 15 frac)
    lo=-(1<<(W-1)); hi=(1<<(W-1))-1
    T=tw_table(twbits)
    def qmul(ar,ai,k):
        wr,wi=T[k%64]
        if k%64==0: return ar,ai
        # exact product Q(15+twbits) then round to Q15
        pr=ar*wr-ai*wi; pi=ar*wi+ai*wr
        return rnd(pr,twbits),rnd(pi,twbits)
    A=np.zeros((2,N),dtype=np.int64)
    for n in range(N):
        A[0,dr4(n)]=xi[0,n]; A[1,dr4(n)]=xi[1,n]
    for s in range(3):
        m=4**s
        for b in range(0,N,4*m):
            for k in range(m):
                i0=b+k; i1=b+k+m; i2=b+k+2*m; i3=b+k+3*m
                a0=(A[0,i0],A[1,i0]); a1=(A[0,i1],A[1,i1]); a2=(A[0,i2],A[1,i2]); a3=(A[0,i3],A[1,i3])
                base=16>>(2*s)   # twiddle index unit: W_64^{(k*unit)}
                a1=qmul(a1[0],a1[1],(k*base)%64)
                a2=qmul(a2[0],a2[1],(2*k*base)%64)
                a3=qmul(a3[0],a3[1],(3*k*base)%64)
                t0=(a0[0]+a2[0],a0[1]+a2[1]); t1=(a0[0]-a2[0],a0[1]-a2[1])
                t2=(a1[0]+a3[0],a1[1]+a3[1]); t3=(a1[0]-a3[0],a1[1]-a3[1])
                A[0,i0]=t0[0]+t2[0]; A[1,i0]=t0[1]+t2[1]
                A[0,i1]=t1[0]+t3[1]; A[1,i1]=t1[1]-t3[0]
                A[0,i2]=t0[0]-t2[0]; A[1,i2]=t0[1]-t2[1]
                A[0,i3]=t1[0]-t3[1]; A[1,i3]=t1[1]+t3[0]
    return A

if __name__=='__main__':
    # algorithm check (float)
    rng=np.random.default_rng(1)
    x=(rng.integers(-16384,16385,(64,2))).astype(np.int64)
    xc=(x[:,0]+1j*x[:,1])/32768
    ref=np.fft.fft(xc)
    got=fft_r4_float(xc)
    print("float alg max err:",np.abs(got-ref).max())

    frames,labels=evaluation_frames(20261118,1024)
    print("frames",frames.shape)
    for twb in [12,13,14,15,16]:
        worst=1e9
        for fr in frames[:400]:
            xi=fr.T.copy()
            out=fft_r4_fixed(xi,twbits=twb)
            z=out.T  # (64,2)
            e=np.sum(np.abs((z[:,0]+1j*z[:,1])/32768 - np.fft.fft((fr[:,0]+1j*fr[:,1])/32768))**2)
            s=np.sum(np.abs(np.fft.fft((fr[:,0]+1j*fr[:,1])/32768))**2)
            if s>0: worst=min(worst,10*np.log10(s/e) if e>0 else 999)
        print(f"twiddle bits={twb}: worst SQNR (400 frames) = {worst:.2f} dB")
