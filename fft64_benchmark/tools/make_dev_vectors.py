#!/usr/bin/env python3
"""Produce small deterministic PUBLIC FFT64 development input frames.

Not a final graded dataset and not a substitute for hidden low-RMS/sign tests.
"""
import argparse, json
from pathlib import Path
import numpy as np

N=64
SCALE=1<<15
LIM=1<<14

def q(z):
    return np.clip(np.rint(z*SCALE), -LIM, LIM).astype(np.int64)

def valid_or_raise(c):
    codes=q(c.real)+1j*q(c.imag)
    x=codes/SCALE
    rms=np.sqrt(np.mean(np.abs(x)**2))
    if rms<1/32 and rms>0:
        raise ValueError(f'Generated nonzero frame below RMS limit: {rms}')
    return np.stack([q(c.real),q(c.imag)],axis=-1).tolist()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',default='public_data/dev_inputs.json')
    ap.add_argument('--seed',type=int,default=20261118)
    args=ap.parse_args()
    r=np.random.default_rng(args.seed)
    t=np.arange(N)
    cases={}
    cases['zero']=np.zeros(N,dtype=complex)
    cases['impulse']=np.eye(1,N,0).reshape(-1).astype(complex)*0.25
    cases['dc_complex']=np.full(N,0.105-0.08j)
    cases['nyquist_complex']=((-1.0)**t)*(0.08+0.11j)
    cases['tone_7']=0.21*np.exp(2j*np.pi*7*t/N)
    cases['two_tones']=0.14*np.exp(2j*np.pi*3*t/N)+0.11j*np.exp(2j*np.pi*21*t/N)
    cases['low_rms_mixed_sign']=0.035*np.exp(2j*np.pi*9*t/N)+0.012*np.exp(-2j*np.pi*5*t/N)
    for i in range(12):
        z=(r.uniform(-0.22,0.22,N)+1j*r.uniform(-0.22,0.22,N))
        cases[f'uniform_{i:02d}']=z
    for i in range(8):
        z=r.normal(0,0.13,N)+1j*r.normal(0,0.13,N)
        cases[f'gaussian_{i:02d}']=np.clip(z.real,-0.5,0.5)+1j*np.clip(z.imag,-0.5,0.5)
    for i in range(8):
        z=(2*r.integers(0,2,N)-1)+1j*(2*r.integers(0,2,N)-1)
        cases[f'qpsk_{i:02d}']=0.18*z
    out={'schema':'fft64_inputs','reference':'float64_fft_of_same_quantized_input','frames':[]}
    for name,z in cases.items():
        out['frames'].append({'id':name,'inputs_iq':valid_or_raise(z)})
    p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2)+'\n')
    print('Wrote',len(out['frames']),'public input frames to',p)
if __name__=='__main__':main()
