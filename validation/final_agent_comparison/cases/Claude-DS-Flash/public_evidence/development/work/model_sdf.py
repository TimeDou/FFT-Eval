import numpy as np
N=64
Ms=[32,16,8,4,2,1]
FRAC=15      # data fractional bits
CFRAC=12     # coefficient fractional bits

def coef(stage):
    # stage index 0..5, M=Ms[stage], twiddles W_{2M}^j, j=0..M-1
    M=Ms[stage]
    out=[]
    for j in range(M):
        ang=-2*np.pi*j/(2*M)
        # Q2.12 (14-bit signed, 12 frac)
        re=int(round(np.cos(ang)*(1<<CFRAC)))
        im=int(round(np.sin(ang)*(1<<CFRAC)))
        out.append((re,im))
    return out

COEF=[coef(s) for s in range(6)]

def sim_frame(x, verbose=False):
    """x: complex int array shape (64,) at 15 frac bits.  Returns output stream (list of complex ints) length ~200 and latency."""
    # each stage: delay line of M complex values, plus state
    dly=[[0j]*Ms[s] for s in range(6)]
    outs=[]
    for sc in range(0,260):
        v = complex(x[sc]) if sc<N else 0j
        for s in range(6):
            M=Ms[s]
            per=2*M
            ph=(sc//M)&1        # 0 = first half, 1 = second half
            addr=sc & (M-1)
            dout=dly[s][addr]
            if ph==0:
                nv=dout
                dly[s][addr]=v
            else:
                y=dout+v
                d=dout-v
                re,im=COEF[s][addr]
                zr=(d.real*re-d.imag*im)
                zi=(d.real*im+d.imag*re)
                # round: add 2^(CFRAC-1) then >> CFRAC (arithmetic)
                def rnd(p):
                    p=int(p)
                    p=(p + (1<<(CFRAC-1)))>>CFRAC
                    return p
                z=complex(rnd(zr),rnd(zi))
                nv=z
                dly[s][addr]=y
            v=nv
        outs.append(v)
    return outs

rng=np.random.default_rng(1)
x=(rng.integers(-1000,1000,N)+1j*rng.integers(-1000,1000,N)).astype(complex)
outs=sim_frame(x)
ref=np.fft.fft(x)
# find latency: first output index
for L in range(0,140):
    # assume output[t] = ref[perm[t]]*scale
    good=0
    idx=[]
    for t in range(64):
        v=outs[L+t]
        # find best match in ref
        d=np.abs(ref-v)
        k=int(np.argmin(d))
        if d[k]<1e-6*max(1,abs(ref[k])): good+=1
        idx.append(k)
    if good>=63:
        print("latency",L,"perm",idx[:16],"...","good",good)
        # check scale
        r=[]
        for t in range(64):
            k=idx[t]
            if abs(ref[k])>1: r.append(outs[L+t]/ref[k])
        print("scale",np.mean(r).real, np.mean(r).imag)
        print("perm full",idx)
        break
else:
    print("no latency found")
    print([abs(outs[i]) for i in range(60,80)])
