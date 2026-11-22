import numpy as np
exec(open('dbg2.py').read().split('for N in [8]:')[0])
N=8; ns=3; Ms,COEF,CFRAC=build(N,ns)
rng=np.random.default_rng(3)
x=(rng.integers(-100,100,N)+1j*rng.integers(-100,100,N)).astype(complex)
o=sim(x,N,ns,Ms,COEF,CFRAC)
ref=np.fft.fft(x)
for i in range(0,26):
    print(i, round(o[i].real,1), round(o[i].imag,1))
print("ref:")
for i in range(8): print(i, round(ref[i].real,1), round(ref[i].imag,1))
