import numpy as np
def build(N, ns):
    Ms=[N//2**(s+1) for s in range(ns)]
    CFRAC=24
    COEF=[[(int(round(np.cos(-2*np.pi*j/(2*M))*(1<<CFRAC))),int(round(np.sin(-2*np.pi*j/(2*M))*(1<<CFRAC)))) for j in range(M)] for M in Ms]
    return Ms,COEF,CFRAC
def sim(x,N,ns,Ms,COEF,CFRAC,T=200):
    dly=[[0j]*M for M in Ms]
    outs=[]
    for sc in range(T):
        v = complex(x[sc]) if sc<N else 0j
        for s in range(ns):
            M=Ms[s]; ph=(sc//M)&1; addr=sc&(M-1); dout=dly[s][addr]
            if ph==0:
                nv=dout; dly[s][addr]=v
            else:
                y=dout+v; d=dout-v
                re,im=COEF[s][addr]
                z=complex(round((d.real*re-d.imag*im)/(1<<CFRAC)), round((d.real*im+d.imag*re)/(1<<CFRAC)))
                nv=z; dly[s][addr]=y
            v=nv
        outs.append(v)
    return outs
for N in [8]:
    ns=int(np.log2(N)); Ms,COEF,CFRAC=build(N,ns)
    rng=np.random.default_rng(3)
    x=(rng.integers(-100,100,N)+1j*rng.integers(-100,100,N)).astype(complex)
    o=sim(x,N,ns,Ms,COEF,CFRAC)
    ref=np.fft.fft(x)
    # search for output block of N consecutive samples matching a permutation
    for L in range(0,4*N):
        blk=o[L:L+N]
        idx=[]
        ok=True
        for v in blk:
            d=np.abs(ref-v); k=int(np.argmin(d))
            if d[k]>1e-3*max(1,abs(ref[k])): ok=False;break
            idx.append(k)
        if ok:
            print("N",N,"latency",L,"perm",idx)
            break
    else:
        print("N",N,"no match; outs:",[round(v.real,1) for v in o[N:3*N]])
        print("ref",[round(v.real,1) for v in ref])
