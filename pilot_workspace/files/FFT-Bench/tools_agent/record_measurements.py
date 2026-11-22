#!/usr/bin/env python3
"""Collect actual public tool receipts; never fill missing measurements with estimates."""
import csv,hashlib,json
from pathlib import Path
out=Path('submission/measurements.csv')
fields='id,architecture,precision_policy,source_hash,recipe_hash,mapped_hash,backend,library_id,area_um2,worst_sqnr_db,verified_ii_cycles,certified_period_ns,maximum_first_cycles,maximum_completion_cycles,timing_pass,protocol_pass,status,notes'.split(',')
rows=[]
candidates=[
 ('baseline22','22-bit Q15; Q14 coefficients; 4 products'),
 ('fused18','18-bit; stages2..5 RNE /2; Q9; 4 products'),
 ('fused18_3mul','18-bit; stages2..5 RNE /2; Q9 compact; 3 products'),
 ('fused18_compact','18-bit; stages2..5 RNE /2; Q9 compact; 4 products'),
 ('block16','16-bit adaptive block exponent; Q9; 3 products'),
 ('block15','15-bit adaptive block exponent; Q9; rounded Q14 input; 3 products'),
 ('block15_pipe1','15-bit adaptive block exponent; Q9; 3 products; 1 pipeline stage'),
 ('block15_pipe2','15-bit adaptive block exponent; Q9; 3 products; 2 pipeline stages'),
 ('block15_tight','15-bit block exponent; 3 products; DC 2ns target'),
 ('block15_pipe2_tight','15-bit block exponent; 3 products; 2 pipeline stages; DC 1.5ns target')]
def read(p):return json.loads(p.read_text())
for name,precision in candidates:
 architecture='folded radix2'+(' fused IO'if name!='baseline22'else'')
 local=Path('runs/local_'+('baseline'if name=='baseline22'else name)+'_public')
 if (local/'summary.json').exists():
  x=read(local/'summary.json');source=(local/'source.sv').read_text()
  # Match the evaluator's expanded-source convention, retaining this run's
  # exact archived source even if a later candidate changes declarations.
  h=hashlib.sha256((source+'\n').encode()).hexdigest()
  rows.append(dict(id=name+'_rtl',architecture=architecture,precision_policy=precision,source_hash=h,backend='Icarus RTL simulation',worst_sqnr_db=x['quality']['minimum_frame_sqnr_db'],maximum_first_cycles=x['first'],maximum_completion_cycles=x['completion'],protocol_pass=True,status='RTL_ONLY_PASS',notes='1216 public numerical frames with reset and variable gaps; no mapped claim'))
 runs=[f'area_{name}',f'arch_{name}']+(['final_architecture']if name=='block15_pipe2_tight'else[])
 for run in runs:
  d=Path('runs')/run;rp=d/'result.json'
  if not rp.exists():continue
  x=read(rp);pp=x.get('ppa',{});q=x.get('quality',{});lat=x.get('latency',{});cap=x.get('throughput_check',{});cert=pp.get('fmax_certificate',{})
  if not cert and(d/'agent_frequency_certificate.json').exists():cert=read(d/'agent_frequency_certificate.json')
  producer=x.get('source',{}).get('implementation',{}).get('producer',{})
  recipe=producer.get('recipe_sha256',{}).get('dc_opt.tcl')
  if not recipe:recipe=hashlib.sha256(Path('fft64_benchmark/flow/templates/dc_opt.tcl').read_bytes()).hexdigest()
  rows.append(dict(id=run,architecture=architecture,precision_policy=precision,source_hash=x.get('source',{}).get('source_sha256'),recipe_hash=recipe,mapped_hash=pp.get('mapped_sha256'),backend=x.get('backend'),library_id='ASAP7 RVT TT comb a470018fb07a + seq 57a0b403485b',area_um2=pp.get('area_um2'),worst_sqnr_db=q.get('minimum_frame_sqnr_db'),verified_ii_cycles=cap.get('verified_frame_ii_cycles'),certified_period_ns=cert.get('passing_period_ns'),maximum_first_cycles=lat.get('maximum_first_output_latency_cycles'),maximum_completion_cycles=lat.get('maximum_frame_completion_cycles'),timing_pass=pp.get('timing_pass'),protocol_pass=x.get('protocol_pass'),status=x.get('status'),notes='Public '+x.get('profile','')+' profile; mapped_pass='+str(x.get('mapped_simulation_pass'))+'; missing frozen calibration; no hidden score'))
 robustness=Path('runs/robustness_'+name)
 if (robustness/'summary.json').exists():
  x=read(robustness/'summary.json');h=hashlib.sha256(((robustness/'source.sv').read_text()+'\n').encode()).hexdigest()
  rows.append(dict(id='robustness_'+name,architecture=architecture,precision_policy=precision,source_hash=h,backend='Icarus RTL simulation',worst_sqnr_db=x['quality']['minimum_frame_sqnr_db'],maximum_first_cycles=x['first'],maximum_completion_cycles=x['completion'],protocol_pass=True,status='ADDITIONAL_PUBLIC_RTL_PASS',notes=str(x['quality']['frames'])+' self-generated public frames; seed 761239; includes maximum-growth and magnitude-boundary witnesses; not hidden evaluation'))
for fn,W,F,tf in [('precision_rne_screen.json',17,15,9),('precision_screen.json',19,12,14)]:
 p=Path('runs')/fn
 if p.exists():
  r=next(v for v in read(p)if v['width']==W and v['frac']==F and v['twfrac']==tf)
  rows.append(dict(id='model_rejected_W'+str(W)+'_F'+str(F),architecture='folded radix2 numerical model',precision_policy='W'+str(W)+' F'+str(F)+' TF'+str(tf),backend='NumPy fixed-point model',worst_sqnr_db=r['min_sqnr_db'],status='MODEL_REJECTED_SQNR',notes='1216 public input frames; precision screen only; not synthesized or claimed RTL result'))
with out.open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
