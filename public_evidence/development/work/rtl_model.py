"""Bit-exact replica of generated fft64_top.sv."""
import math
N=64; NS=6; Ms=[32,16,8,4,2,1]
CFRAC=12
COEF=[[(int(round(math.cos(-2*math.pi*j/(2*M))*(1<<CFRAC))),int(round(math.sin(-2*math.pi*j/(2*M))*(1<<CFRAC)))) for j in range(M)] for M in Ms]
def sgn(v,bits):
    v&=(1<<bits)-1
    return v-(1<<bits) if v>>(bits-1) else v
LASTsc=132
W=[16+s for s in range(NS)]
Wo=[w+1 for w in W]

def run(inp,T,rst_first=5,taps=None):
    dly=[[[0,0] for _ in range(Ms[s])] for s in range(NS)]
    o=[[0,0] for _ in range(NS)]
    cp=[0]*6; sc=0; busy=0
    ram_re=[0]*64; ram_im=[0]*64
    seq=[]
    for t in range(T):
        re,im,iv,fs = inp[t] if t<len(inp) else (0,0,0,0)
        start=1 if (iv and fs) else 0
        rst=1 if t<rst_first else 0
        cur=(re if iv else 0, im if iv else 0)
        newo=[None]*NS; wrv=[None]*NS
        for s in range(NS):
            M=Ms[s]; w=W[s]; wo=Wo[s]
            ctl = sc if s==0 else cp[s-1]
            ph=(ctl>>(5-s))&1
            idx=ctl&(M-1)
            doR,doI=dly[s][M-1]
            cr,ci=COEF[s][idx]
            suR=sgn(doR+cur[0],wo+1); suI=sgn(doI+cur[1],wo+1)
            dfR=sgn(doR-cur[0],wo+1); dfI=sgn(doI-cur[1],wo+1)
            drR=sgn(dfR,wo); drI=sgn(dfI,wo)
            pr=sgn(drR*cr,wo+14); pi=sgn(drI*ci,wo+14)
            qr=sgn(drR*ci,wo+14); qi=sgn(drI*cr,wo+14)
            zRf=sgn(pr-pi+2048,wo+15)
            zIf=sgn(qr+qi+2048,wo+15)
            zR=sgn(zRf>>CFRAC,wo); zI=sgn(zIf>>CFRAC,wo)
            nxR=zR if ph else doR; nxI=zI if ph else doI
            wrR=sgn(suR,wo) if ph else sgn(cur[0],wo)
            wrI=sgn(suI,wo) if ph else sgn(cur[1],wo)
            newo[s]=(nxR,nxI); wrv[s]=(wrR,wrI)
            cur=(nxR,nxI)
        for s in range(NS):
            if rst:
                dly[s]=[[0,0] for _ in range(Ms[s])]
                o[s]=(0,0)
            else:
                nd=[[0,0]]+[list(dly[s][k]) for k in range(0,Ms[s]-1)]
                nd[0]=[wrv[s][0],wrv[s][1]]
                dly[s]=nd
                o[s]=newo[s]
        cp=[sc]+cp[:5]
        if rst: busy=0; sc=0
        elif start: busy=1; sc=1
        elif busy:
            if sc==LASTsc: busy=0; sc=0
            else: sc+=1
        if 63<=cp[5]<=126:
            wt=((cp[5]&63)-63)&63
            wad=(~int(f'{wt:06b}'[::-1],2))&63
            ram_re[wad]=sgn(o[5][0],22); ram_im[wad]=sgn(o[5][1],22)
        seq.append((o[5][0],o[5][1]))
        if taps is not None: taps.append([tuple(o[s]) for s in range(NS)])
    return seq,ram_re,ram_im
