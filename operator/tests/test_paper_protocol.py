"""FFT protocol: frame cardinality, worst-frame extrema, optional II."""
from pathlib import Path
import sys,tempfile,unittest,copy
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'fft64_benchmark/tools'))
from model import evaluation_frames,quality,quality_union
from simulate import decode
import throughput


class PaperProtocolTests(unittest.TestCase):
    def test_random_frame_count_does_not_change_fft_length(self):
        for count in [1024,8192]:
            x,labels=evaluation_frames(1157,count)
            self.assertEqual(x.shape[1:],(64,2));self.assertGreater(len(x),count)
            self.assertTrue(all(s.startswith('independent_random')for s in labels[:count]))
            self.assertTrue(np.all(np.sqrt(np.mean(np.sum((x[:count]/32768)**2,axis=-1),axis=-1))>=1/32))
            self.assertEqual(count*64,65536 if count==1024 else 524288)
        a,_=evaluation_frames(1);b,_=evaluation_frames(2)
        self.assertFalse(np.array_equal(a[:1024],b[:1024]))

    def test_quality_union_uses_minimum_not_mean_db(self):
        q=dict(frames=1024,minimum_frame_sqnr_db=60.,worst_frame_nmse=1e-6,zero_frame_exact=True,feasible=True)
        z=dict(q,minimum_frame_sqnr_db=49.,worst_frame_nmse=10**(-4.9),feasible=False,failed_frames=[1023])
        merged=quality_union(q,z)
        self.assertEqual(merged['minimum_frame_sqnr_db'],49);self.assertFalse(merged['feasible'])

    def test_last_frame_latency_is_included(self):
        frames=np.zeros((1024,64,2),dtype=np.int64)
        e,m,_=throughput.stream_schedule(frames,384,tail=False,reset_probes=False)
        raw=np.zeros((len(e),5),dtype=np.int64);raw[:,0]=np.arange(len(e))
        for j,start in enumerate(m['frame_starts']):
            first=start+(299 if j==1023 else 64)
            raw[first:first+64,1]=1;raw[first,2]=1
        _,lat=decode(raw,e,m)
        self.assertEqual(lat['maximum_first_output_latency_cycles'],299)
        self.assertEqual(lat['maximum_frame_completion_cycles'],362)
        self.assertEqual(len(lat['per_frame_first_output_latency_cycles']),1024)

    def test_optional_failure_and_agent_claim_do_not_override_measured_service(self):
        q=dict(frames=1024,minimum_frame_sqnr_db=60.,worst_frame_nmse=1e-6,zero_frame_exact=True,feasible=True)
        observations=[dict(frame_ii_cycles=383,tested_frames=1024,pass_rtl=False),dict(frame_ii_cycles=384,tested_frames=1024,pass_rtl=True,quality=q,maximum_first_output_cycles=256,maximum_completion_cycles=319)]
        gate=dict(status='PASS',mapped_pass=True,quality=q,latency={},first_output_latency_cycles=[256])
        with tempfile.TemporaryDirectory()as d,patch.object(throughput,'probe_intervals',return_value=observations),patch.object(throughput,'qualify',return_value=gate):
            r=throughput.verify('rtl','mapped',np.zeros((1024,64,2)),d,claimed_interval=64)
        self.assertEqual(r['status'],'PASS');self.assertEqual(r['verified_frame_ii_cycles'],384)
        self.assertEqual(r['continuous_frames_verified'],1024);self.assertEqual(r['optional_shorter_failures'],1)
        self.assertEqual(r['ignored_agent_claim'],64)

if __name__=='__main__':unittest.main()
