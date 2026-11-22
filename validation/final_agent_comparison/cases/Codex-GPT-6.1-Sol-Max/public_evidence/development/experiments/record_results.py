from pathlib import Path
import csv,json,hashlib
root=Path.cwd();fields='id,architecture,precision_policy,source_hash,recipe_hash,mapped_hash,backend,library_id,area_um2,worst_sqnr_db,verified_ii_cycles,certified_period_ns,maximum_first_cycles,maximum_completion_cycles,area_score,throughput_score,latency_score,total_score,score_valid,scoring_scope,timing_pass,protocol_pass,status,notes'.split(',')
# Each row records exactly one public run, and partial runs retain empty score fields.
runs=[('quick_F001','folded_1bf','Q13_T13_truncate'),('quick_F002','folded_1bf','Q13_T13_round'),('area_F002','folded_1bf','Q13_T13_round'),('quick_F003','folded_2bf','Q14_T11_round'),('arch_F003','folded_2bf','Q14_T11_round'),('quick_F004','folded_2bf_3mul','Q14_T11_round'),('area_F004','folded_2bf_3mul','Q14_T11_round'),('quick_S001','R2SDF','Q14_T11'),('arch_S001','R2SDF','Q14_T11'),('quick_S002','R2SDF_early_reorder','Q14_T11'),('quick_S003','R2SDF_early_reorder','Q14_T9'),('arch_S003','R2SDF_early_reorder','Q14_T9'),('arch_C001','R2SDF_early_reorder','Q14_T9_timing1000ps'),('quick_R001','R22SDF','Q14_T9'),('arch_R001','R22SDF','Q14_T9'),('quick_R002','R22SDF_staged','Q14_Q13_Q12_T9_round'),('quick_R003','R22SDF_staged','Q14_Q13_Q12_T9_RNE'),('arch_C002','R22SDF','Q14_T9_timing700ps'),('arch_C003','R22SDF_staged','Q14_Q13_Q12_T9_RNE_timing500ps'),('quick_R004','R22SDF_staged_pipeline_3mul','Q14_Q13_Q12_T9_RNE'),('arch_C004','R22SDF_staged_pipeline_3mul','Q14_Q13_Q12_T9_RNE_timing500ps'),('quick_R005','R22SDF_onehot_reorder','Q14_Q13_Q12_T9_RNE'),('arch_C005','R22SDF_onehot_reorder','Q14_Q13_Q12_T9_RNE_timing500ps'),('quick_R006','R22SDF_reorder_Q10','Q14_Q13_Q12_Q10_T9_RNE'),('quick_R006_independent','R22SDF_reorder_Q10','Q14_Q13_Q12_Q10_T9_RNE'),('quick_R007_independent','R22SDF_reorder_Q11','Q14_Q13_Q12_Q11_T9_RNE'),('arch_C006','R22SDF_reorder_Q10','Q14_Q13_Q12_Q10_T9_RNE_timing500ps'),('arch_C007','R22SDF_reorder_Q11','Q14_Q13_Q12_Q11_T9_RNE_timing500ps')]
rows=[]
for name,arch,prec in runs:
 path=root/'runs'/name/'result.json'
 if not path.exists():continue
 d=json.loads(path.read_text());r={k:''for k in fields};p=d.get('ppa',{});g=d.get('grade',{});l=d.get('latency',{});q=d.get('quality',{});source=d.get('source',{});impl=source.get('implementation',{})
 r.update(id=name,architecture=arch,precision_policy=prec,source_hash=source.get('source_sha256',''),mapped_hash=p.get('imported_sha256')or p.get('mapped_sha256',''),backend=d.get('backend',''),library_id='ASAP7_RVT_TT_comb_a470018fb07a_SEQ_57a0b403485b' if p else '',area_um2=p.get('area_um2',''),worst_sqnr_db=q.get('minimum_frame_sqnr_db',''),verified_ii_cycles=d.get('throughput_check',{}).get('verified_frame_ii_cycles',''),certified_period_ns=p.get('fmax_certificate',{}).get('passing_period_ns',''),maximum_first_cycles=l.get('maximum_first_output_latency_cycles',''),maximum_completion_cycles=l.get('maximum_frame_completion_cycles',''),score_valid=g.get('score_valid',False),scoring_scope=g.get('scoring_scope',''),timing_pass=p.get('timing_pass',''),protocol_pass=d.get('protocol_pass',''),status=d.get('status',''),notes='profile='+d.get('profile','')+'; seed='+str(d.get('seed',''))+'; random_frames='+str(d.get('independent_random_nonzero_frames',''))+'; report=runs/'+name+'/result.json')
 if g.get('score_valid'):
  r['area_score']=g.get('components',{}).get('area','')
  if d.get('profile')=='architecture' and d.get('status')=='COMPLETE':
   r.update(throughput_score=g.get('components',{}).get('throughput',''),latency_score=g.get('components',{}).get('latency',''),total_score=g.get('score',''))
 if not impl and p:
  r['recipe_hash']=hashlib.sha256((root/'fft64_benchmark/flow/templates/dc_opt.tcl').read_bytes()).hexdigest()
 if impl:
  # The producer manifest and recipe hashes remain independently inspectable.
  r['recipe_hash']=impl.get('producer',{}).get('recipe_sha256',{}).get('dc_opt.tcl','')
 rows.append(r)
with(root/'submission/measurements.csv').open('w')as f:
 w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
for r in rows:
 if r['area_um2'] or r['total_score']:print(r['id'],r['status'],'area',r['area_um2'],'II',r['verified_ii_cycles'],'P',r['certified_period_ns'],'score',r['total_score'])
