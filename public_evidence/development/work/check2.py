import numpy as np
exec(open('model_sdf.py').read().split('rng=np.random')[0])
rng=np.random.default_rng(1)
x=(rng.integers(-1000,1000,N)+1j*rng.integers(-1000,1000,N)).astype(complex)
outs=sim_frame(x)
ref=np.fft.fft(x)
for L in range(55,70):
    errs=[]
    for t in range(64):
        v=outs[L+t]
        # try mapping: t -> k  under bit reversal
        e1=abs(v-ref[t]); e2=abs(v-ref[int(f'{t:06b}'[::-1],2)])
        errs.append(min(e1,e2))
    print(L, max(errs), np.mean(errs))
