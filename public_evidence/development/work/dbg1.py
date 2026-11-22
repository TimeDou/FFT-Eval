import numpy as np
N=8
ns=int(np.log2(N))
Ms=[N//2**(s+1) for s in range(ns)]
CFRAC=20
def coefJ(s):
    M=Ms[s]
    return [(int(round(np.cos(-2*np.pi*j/(2*M))*(1<<CFRAC))),int(round(np.sin(-2*np.pi*j/(2*M))*(1<<CFRAC)))) for j in range(M)]
COEF=[coefJ(s) for s in range(ns)]
def stage1(x, M, coef):
    dly=[0j]*M; out=[]
    for sc in range(0,4*2*M):
        v = x[sc] if sc<len(x) else 0j
        ph=(sc//M)&1; addr=sc&(M-1); dout=dly[addr]
        if ph==0:
            out.append(dout); dly[addr]=v
        else:
            y=dout+v; d=(dout-v)
            re,im=coef[addr]
            def rnd(p):
                p=int(round(p/(1<<CFRAC)))
                return p
            z=complex(rnd(d.real*re-d.imag*im), rnd(d.real*im+d.imag*re))
            out.append(z); dly[addr]=y
    return out
rng=np.random.default_rng(3)
x=(rng.integers(-100,100,N)+1j*rng.integers(-100,100,N)).astype(complex)
M=N//2
o=stage1(x,M,COEF[0])
# expected DIF: y[n]=x[n]+x[n+M], z[n]=(x[n]-x[n+M]) W_2M^n
y=[x[n]+x[n+M] for n in range(M)]
z=[(x[n]-x[n+M])*np.exp(-2j*np.pi*n/(2*M)) for n in range(M)]
exp=y+z
print("expected first 2M:", [round(v.real,1) for v in exp[:2*M]])
print("got at 2M..4M:", [round(v.real,1) for v in o[2*M:4*M]])
print("o[0:4] ",[round(v.real,1) for v in o[0:4]])
print("z exp  ",[round(v.real,1) for v in z])
print("o[8:12]",[round(v.real,1) for v in o[8:12]])
print("o[4:8] z?")
for i in range(16):
    print(i, round(o[i].real,2), round(o[i].imag,2))
