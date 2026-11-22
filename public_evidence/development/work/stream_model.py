import numpy as np
N=64; NS=6; Ms=[32,16,8,4,2,1]
CFRAC=12
def mkcoef():
    return [[(int(round(np.cos(-2*np.pi*j/(2*M))*(1<<CFRAC))),int(round(np.sin(-2*np.pi*j/(2*M))*(1<<CFRAC)))) for j in range(M)] for M in Ms]
COEF=mkcoef()
def rnd(p): return (p + (1<<(CFRAC-1)))>>CFRAC
def sim(x, T=None, clr_at_start=False, taps=None):
    """x: (L,2) int samples, streamed from position 0. Circular-buffer SDF model."""
    L=len(x)
    if T is None: T=L+200
    dR=[[0]*M for M in Ms]; dI=[[0]*M for M in Ms]
    out=[]
    for sc in range(T):
        if clr_at_start and (sc % 64)==0:
            dR=[[0]*M for M in Ms]; dI=[[0]*M for M in Ms]
        vR=int(x[sc,0]) if sc<L else 0
        vI=int(x[sc,1]) if sc<L else 0
        o=[None]*NS
        for s in range(NS):
            M=Ms[s]; ph=(sc//M)&1; addr=sc&(M-1)
            dR0=dR[s][addr]; dI0=dI[s][addr]
            if ph==0:
                nR,nI=dR0,dI0
                dR[s][addr]=vR; dI[s][addr]=vI
            else:
                yR=dR0+vR; yI=dI0+vI
                aR=dR0-vR; aI=dI0-vI
                cr,ci=COEF[s][addr]
                nR=rnd(aR*cr-aI*ci); nI=rnd(aR*ci+aI*cr)
                dR[s][addr]=yR; dI[s][addr]=yI
            vR,vI=nR,nI
            o[s]=(nR,nI)
        out.append(complex(vR,vI))
        if taps is not None: taps.append([tuple(o[s]) for s in range(NS)])
    return np.array(out)
def win(o,start):
    out=o[start+63:start+127]
    pred=np.zeros(64,dtype=complex)
    for t in range(64):
        j=63-int(f'{t:06b}'[::-1],2)
        pred[j]=out[t]
    return pred
