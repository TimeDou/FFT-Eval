"""Actual invalid-throughput claim; source and passing runs are never modified."""
from pathlib import Path
import json,sys,time,copy
ROOT=Path('/mnt/mydata/FFT-Bench-profiles')
sys.path.insert(0,str(ROOT/'fft64_benchmark/tools'))
from common import read,save
from evaluate import assemble,used_cell_models
from throughput import qualify
from model import make_frames
from scoring import score_result
out=Path('/mnt/mydata/score_profile_v04/negative_ii_319')
out.mkdir(parents=True,exist_ok=True)
base=Path('/mnt/mydata/eval/scoring_profiles_v04_area_r1/candidates/fft64_solution')
limit=time.monotonic()+1800
while True:
    latest=base/'latest.json'
    if latest.exists():
        run=Path(read(latest)['directory']);r=read(run/'result.json')
        if r.get('status')=='COMPLETE' and 'seconds'in r:break
    if time.monotonic()>limit:raise TimeoutError('Passing reference not yet available')
    time.sleep(5)
source,info=assemble(run/'submission')
mapped=(run/'asic/mapped.v').read_text()
mapped_source=used_cell_models(mapped)+'\n'+mapped
frames,_=make_frames(20261121,3)
bad=qualify(source,mapped_source,frames,out,319,'vcs',20261121+31,
            rtl_compiled=run/'rtl_sim',gate_compiled=run/'mapped_sim')
if bad['status']!='FAIL':raise AssertionError('Invalid II=319 unexpectedly qualified; revise the diagnosis, never force an expected failure')
probe=copy.deepcopy(r);probe.update(profile='architecture',status='THROUGHPUT_FAILED',throughput_check=bad)
grade=score_result(probe)
assert not grade['resolved'] and grade['score']==0 and grade['score_valid']
save(out/'negative_test.json',dict(status='EXPECTED_SPEC_FAILURE_CONFIRMED',invalid_declared_ii=319,
     passing_parent_directory=str(run),parent_mapped_sha256=r['ppa']['mapped_sha256'],qualification=bad,grade=grade,
     scope='actual continuous RTL simulation using full input set and the unchanged mapped parent; failure occurs before gate comparison'))
print(json.dumps(dict(status='EXPECTED_SPEC_FAILURE_CONFIRMED',reason=bad.get('reason'),grade=grade)),flush=True)
