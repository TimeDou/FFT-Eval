"""Targeted checks for the rewritten metric, submission and cycle interfaces."""
from pathlib import Path
import copy
import json
import sys
import tempfile
import numpy as np

SOLUTION=Path(__file__).resolve().parents[1]
BENCHMARK=SOLUTION.with_name('fft64_benchmark')
sys.path.insert(0,str(BENCHMARK/'tools'))
from common import read,save
from numeric_io import input_frames
from check_numeric import check
from model import reference
from simulate import schedule,decode
from evaluate import assemble,score_result
from scoring import SCORING_VERSION

def main():
    tests=[]
    document=read(BENCHMARK/'public_data/dev_inputs.json')
    names,frames=input_frames(document)
    oracle=reference(frames)
    quantized=np.stack([np.rint(oracle.real*32768),np.rint(oracle.imag*32768)],axis=-1).astype(np.int64)
    outputs=dict(frames=[dict(id=name,outputs_iq=z.tolist())for name,z in zip(names,quantized)])
    assert check(document,outputs)['feasible']
    tests.append(dict(name='public_vector_format_and_reference_output',passed=True))
    wrong=copy.deepcopy(outputs)
    for frame in wrong['frames']:frame['outputs_iq']=[[0,0]]*64
    assert not check(document,wrong)['feasible']
    tests.append(dict(name='wrong_numerical_output_rejected',passed=True))
    for label,value in [('fractional_code',1.5),('boolean_code',True),('out_of_range',16385)]:
        invalid=copy.deepcopy(document);invalid['frames'][0]['inputs_iq'][0][0]=value
        try:input_frames(invalid)
        except ValueError:pass
        else:raise AssertionError(label)
    invalid=copy.deepcopy(document);invalid['frames'][1]['id']=invalid['frames'][0]['id']
    try:input_frames(invalid)
    except ValueError:pass
    else:raise AssertionError('duplicate input IDs')
    invalid=dict(frames=[dict(id='low',inputs_iq=[[1,0]]*64)])
    try:input_frames(invalid)
    except ValueError:pass
    else:raise AssertionError('below RMS input')
    tests.append(dict(name='illegal_input_domain_and_duplicate_ids_rejected',passed=True))
    events,metadata=schedule(frames[:3],reset_test=False)
    raw=np.zeros((len(events),5),dtype=np.int64);raw[:,0]=np.arange(len(events))
    for index,(start,latency)in enumerate(zip(metadata['frame_starts'],[100,101,100])):
        first=start+latency;raw[first:first+64,1]=1;raw[first,2]=1
    decoded,latency=decode(raw,events,metadata)
    assert latency['observed_frame_II_on_384_cycle_workload']==[383,385]
    tests.append(dict(name='legal_variable_latency_service_accepted',passed=True))
    broken=raw.copy();broken[np.flatnonzero(raw[:,1])[1],1]=0
    try:decode(broken,events,metadata)
    except AssertionError:pass
    else:raise AssertionError('noncontiguous output accepted')
    tests.append(dict(name='output_packet_gap_rejected',passed=True))
    with tempfile.TemporaryDirectory()as temp:
        root=Path(temp);(root/'rtl').mkdir()
        (root/'rtl/body.svh').write_text('wire test_signal;\n')
        (root/'rtl/top.sv').write_text('module fft64_top;\n`include "body.svh"\nendmodule\n')
        text,source=assemble(root)
        assert 'wire test_signal' in text and len(source['files'])==2
    tests.append(dict(name='self_contained_rtl_include',passed=True))
    reference_area=dict(backend='local',flow_id='sample',reference_area_um2=100,
                        reference_period_ns=9,reference_frame_II_cycles=384,scoring_version=SCORING_VERSION)
    result=dict(status='FAILED',backend='local',flow_id='sample',protocol_pass=True,
                quality=dict(feasible=True),mapped_simulation_pass=True,
                ppa=dict(area_um2=10,timing_pass=True,effective_required_period_ns=9,clock_period_ns=10),
                latency=dict(offered_frame_II=384))
    assert score_result(result,reference_area)['score']==0
    result['status']='COMPLETE';assert score_result(result,reference_area)['resolved']
    result['backend']='commercial';assert score_result(result,reference_area)['area_ratio']is None
    tests.append(dict(name='late_failure_and_mixed_backend_do_not_score',passed=True))
    save(SOLUTION/'results/regression.json',dict(passed=True,tests=tests))
    print(json.dumps(dict(passed=True,tests=len(tests))))

if __name__=='__main__':main()
