"""Original fixed-point models and independent test families for this task."""
import numpy as np

N=64
F=15

def reference(x):
    x=np.asarray(x);return np.fft.fft((x[...,0]+1j*x[...,1])/(1<<F),axis=-1)

def quality(x,z):
    ref=reference(x);z=np.asarray(z);pred=(z[...,0]+1j*z[...,1])/(1<<F)
    sse=np.sum(abs(pred-ref)**2,axis=-1);energy=np.sum(abs(ref)**2,axis=-1)
    nz=energy>0;nmse=np.zeros_like(energy);nmse[nz]=sse[nz]/energy[nz]
    q=-10*np.log10(np.maximum(nmse[nz],1e-300))
    return dict(frames=len(x),minimum_frame_sqnr_db=float(q.min())if len(q)else None,
                pooled_sqnr_db=float(-10*np.log10(max(float(sse.sum()/energy.sum()),1e-300)))if energy.sum()else None,
                worst_frame_nmse=float(nmse.max()),zero_frame_exact=bool(np.all(z[~nz]==0)),
                failed_frames=np.flatnonzero(nz&(nmse>1e-5)).tolist(),
                feasible=bool(np.all(nmse[nz]<=1e-5)and np.all(z[~nz]==0)))

def make_frames(seed=20261116,scale=1):
    rng=np.random.default_rng(seed);out=[];labels=[]
    def add(name,a):
        a=np.rint(np.asarray(a)*(1<<F)).astype(np.int64)
        if a.ndim==2:a=a[None]
        assert a.min()>=-16384 and a.max()<=16384
        rms=np.sqrt(np.mean(np.sum((a/(1<<F))**2,axis=-1),axis=-1))
        keep=(rms>=1/32)|(rms==0)
        for z in a[keep]:out.append(z);labels.append(name)
    for amp in [.0625,.125,.5]:add('uniform_'+str(amp),rng.uniform(-amp,amp,(8*scale,N,2)))
    for sig in [.03125,.125,.3]:add('gaussian_'+str(sig),np.clip(rng.normal(0,sig,(8*scale,N,2)),-.5,.5))
    t=np.arange(N)
    for k in [0,1,7,15,16,31,32,63,3.25,17.5]:
        for amp in [.0625,.25,.5]:
            zz=amp*np.exp(2j*np.pi*(k*t/N+rng.uniform(0,1)))
            add('tone',np.stack([zz.real,zz.imag],-1))
    for p in [0,1,17,63]:
        for z in [[.25,0],[0,-.25],[.5,.5]]:
            a=np.zeros((N,2));a[p]=z;add('impulse',a)
    for _ in range(8*scale):
        f=np.zeros(N,dtype=complex);idx=np.r_[np.arange(1,13),np.arange(N-12,N)]
        f[idx]=rng.choice([-3,-1,1,3],len(idx))+1j*rng.choice([-3,-1,1,3],len(idx))
        a=np.fft.ifft(f);a*=.45/max(abs(a.real).max(),abs(a.imag).max())
        add('QAM_OFDM',np.stack([a.real,a.imag],-1))
        a=np.sum([rng.uniform(.03,.15)*np.exp(2j*np.pi*(rng.uniform(0,N)*t/N+rng.uniform(0,1)))for j in range(4)],axis=0)
        a*=.45/max(abs(a.real).max(),abs(a.imag).max());add('multitone',np.stack([a.real,a.imag],-1))
    add('DC_corner',np.full((N,2),.5));add('negative_DC_corner',np.full((N,2),-.5))
    add('Nyquist',np.column_stack([.5*(-1.)**t,.5*(-1.)**t]))
    # Explicit near-minimum-RMS rounding boundaries: an agent cannot rely on
    # random quantization errors cancelling inside an otherwise biased FFT.
    for raw in [1025,1026,1028,1030,1031,-1025,-1026,-1028,-1030]:
        a=np.zeros((N,2));a[:,0]=raw/(1<<F);add('quantization_boundary_DC',a)
        a[:,0]*=(-1.)**t;add('quantization_boundary_Nyquist',a)
    # Both I/Q components near the smallest valid complex RMS, with changing
    # signs. DC-only witnesses cannot reveal combined input/coefficient error.
    for raw in [725,726,727,730,1031]:
        a=rng.choice([-raw,raw],(8*scale,N,2))/(1<<F)
        add('complex_sign_quantization_boundary_'+str(raw),a)
    add('zero',np.zeros((N,2)))
    return np.asarray(out),labels


def evaluation_frames(seed, random_frames=1024):
    """Independent nonzero 64-point frames, followed by directed cases.

    Count means FRAMES, never FFT length. Rejection happens after quantization
    so every scored nonzero frame satisfies the declared complex RMS domain.
    """
    if type(random_frames)is not int or random_frames<1024:
        raise ValueError('Numerical evaluation needs at least 1024 independent random frames')
    rng=np.random.default_rng(seed);frames=[];labels=[]
    while len(frames)<random_frames:
        family=int(rng.integers(0,6))
        if family==0:a=rng.uniform(-.5,.5,(64,2))
        elif family==1:a=rng.uniform(-.0625,.0625,(64,2))
        elif family==2:a=np.clip(rng.normal(0,.125,(64,2)),-.5,.5)
        elif family==3:a=np.clip(rng.normal(0,.03125,(64,2)),-.5,.5)
        elif family==4:a=np.clip(rng.normal(0,.3,(64,2)),-.5,.5)
        else:
            raw=int(rng.choice([725,726,727,730,1031]));a=rng.choice([-raw,raw],(64,2))/32768
        x=np.rint(a*32768).astype(np.int64)
        if np.sqrt(np.mean(np.sum((x/32768)**2,axis=-1)))<1/32:continue
        frames.append(x);labels.append('independent_random_'+str(family))
    directed,names=make_frames(seed^0x6a09e667,1)
    for x,label in zip(directed,names):
        if label in {'tone','impulse','DC_corner','negative_DC_corner','Nyquist','zero'}or label.startswith('quantization_boundary'):
            frames.append(x);labels.append('directed_'+label)
    # Every integer-frequency bin, including extrema and low-amplitude tones.
    t=np.arange(64)
    for k in range(64):
        for amplitude in [.0625,.5]:
            z=amplitude*np.exp(2j*np.pi*(k*t/64+rng.uniform(0,1)))
            frames.append(np.rint(np.column_stack([z.real,z.imag])*32768).astype(np.int64))
            labels.append('directed_frequency_sweep')
    out=np.asarray(frames,dtype=np.int64)
    assert out.shape==(len(out),64,2) and out.min()>=-16384 and out.max()<=16384
    return out,labels


def quality_union(*qualities):
    """Hard SQNR uses the minimum over applicable, successfully decoded tests."""
    items=[q for q in qualities if q]
    minima=[q['minimum_frame_sqnr_db']for q in items if q.get('minimum_frame_sqnr_db')is not None]
    return dict(frames=sum(q['frames']for q in items),
                minimum_frame_sqnr_db=min(minima)if minima else None,
                worst_frame_nmse=max(q['worst_frame_nmse']for q in items),
                zero_frame_exact=all(q['zero_frame_exact']for q in items),
                feasible=all(q['feasible']for q in items),
                aggregation='minimum SQNR and maximum NMSE, never average frame dB',
                failed_frames=[dict(test=i,indices=q.get('failed_frames',[]))for i,q in enumerate(items)if not q['feasible']])
