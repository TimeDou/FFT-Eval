from pathlib import Path
import sys,json,hashlib,math,csv
root=Path.cwd();sub=root/'submission';sys.path.insert(0,str(root/'fft64_benchmark/tools'))
from evaluate import assemble,submission_completeness
source,info=assemble(sub);sel=json.loads((sub/'frozen_selection.json').read_text());r=json.loads((sub/'public_verification.json').read_text());g=r['grade'];p=r['ppa'];perf=g['performance']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert submission_completeness(sub)['status']=='COMPLETE'
assert r['status']=='COMPLETE' and r['profile']=='architecture' and r['backend']=='commercial'
assert g['resolved'] and g['score_valid'] and g['scoring_scope']=='public_preview' and not g['official_score']
assert sel['source_sha256']==info['source_sha256']==r['source']['source_sha256']
assert sel['report_sha256']==sha(sub/'public_verification.json')==sha(root/sel['public_report'])
assert r['quality']['feasible'] and r['quality']['zero_frame_exact'] and r['quality']['minimum_frame_sqnr_db']>=50
assert r['protocol_pass'] and r['mandatory_service']['status']=='PASS'
assert r['mandatory_service']['continuous_frames']>=1024
assert r['latency']['maximum_first_output_latency_cycles']<=300
assert r['latency']['maximum_frame_completion_cycles']<=364
assert p['timing_pass'] and min(p['worst_setup_slack_ns'],p['worst_hold_slack_ns'])>=0
assert r['mapped_simulation_pass'] and r['mapped_initial_state_modes']==[0,1,20261121]
c=r['throughput_check'];assert c['status']=='PASS' and c['mapped_pass']
assert c['continuous_frames_verified']>=1024 and c['mapped_subset_frames']>=128
cert=p['fmax_certificate'];assert cert['status']=='CERTIFIED' and cert['hold_pass']
assert cert['mapped_sha256']==p['mapped_sha256']
if info.get('implementation'):
 assert info['implementation']['mapped_sha256']==p['imported_sha256']==sel['mapped_sha256']
 for n,h in info['implementation']['producer']['custom_files_sha256'].items():
  assert sha(sub/'flow'/n)==h==sha(sub/'implementation/recipes'/n)
A=p['area_um2'];ii=c['verified_frame_ii_cycles'];P=cert['passing_period_ns'];L=r['latency']['maximum_first_output_latency_cycles']
clip=lambda x:max(0,min(1,x));a=clip(3500/(A+3000));t=clip(math.log(3840/(ii*P))/math.log(240));l=clip((300-L)/237)
assert abs(g['score']-(.6*a+.3*t+.1*l))<1e-12
rows=list(csv.DictReader((sub/'measurements.csv').open()))
assert any(row['id']=='arch_'+sel['candidate'] and abs(float(row['total_score'])-g['score'])<1e-12 for row in rows)
print(json.dumps(dict(status='AUDIT_PASSED',candidate=sel['candidate'],rtl_sha256=info['source_sha256'],exported_mapped_sha256=sel['mapped_sha256'],area_um2=A,minimum_frame_sqnr_db=r['quality']['minimum_frame_sqnr_db'],verified_ii=ii,certified_period_ns=P,setup_slack_10ns=p['worst_setup_slack_ns'],hold_slack_ns=p['worst_hold_slack_ns'],first_cycles=L,last_cycles=r['latency']['maximum_frame_completion_cycles'],components=dict(area=a,throughput=t,latency=l),score=g['score'],report=sel['public_report']),indent=2))
