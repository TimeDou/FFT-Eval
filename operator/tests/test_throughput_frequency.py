"""Continuous-service and frequency-certification regressions; synthetic traces."""
from pathlib import Path
import copy
import sys
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'fft64_benchmark/tools'))
from throughput import stream_schedule,validate_interval
from simulate import decode,testbench
from frequency import validate_trials
from scoring import profile_policy


class ThroughputTests(unittest.TestCase):
    def setUp(self):self.frames=np.zeros((20,64,2),dtype=np.int64)

    def trace(self,interval=64):
        events,meta,frames=stream_schedule(self.frames,interval,tail=True)
        raw=np.zeros((len(events),5),dtype=np.int64);raw[:,0]=np.arange(len(events))
        for start in meta['frame_starts']:
            raw[start+64:start+128,1]=1;raw[start+64,2]=1
        return events,meta,raw,frames

    def test_actual_dense_interval_reset_and_mixed_gaps_are_generated(self):
        e,m,r,frames=self.trace(80)
        starts=m['frame_starts'];self.assertTrue(all(np.diff(starts[:20])==80))
        self.assertEqual(len(m['reset_probes']),2)
        self.assertEqual(len(frames),36)
        self.assertTrue({80,81,87,384}.issubset(set(np.diff(starts))))
        output,lat=decode(r,e,m)
        self.assertEqual(output.shape,(36,64,2))
        self.assertEqual(lat['offered_frame_II'],80)
        self.assertEqual(lat['first_output_latency_cycles'],[64])

    def test_missing_extra_and_noncontiguous_outputs_fail(self):
        for mode in ['missing','extra','hole']:
            e,m,r,_=self.trace()
            start=m['frame_starts'][0]+64
            if mode=='missing':r[start,2]=0
            if mode=='extra':r[start-2,1]=1
            if mode=='hole':r[start+2,1]=0
            with self.assertRaises(AssertionError):decode(r,e,m)

    def test_unknown_capture_sentinels_never_pass_qualification(self):
        for column,value in [(1,2),(3,1073741824)]:
            e,m,r,_=self.trace();r[m['frame_starts'][0]+64,column]=value
            with self.assertRaises(AssertionError):decode(r,e,m)
        self.assertIn('$fatal',testbench(False))
        self.assertNotIn('X control cycle',testbench(True))

    def test_declared_ii_is_an_integer_physical_interface_bound(self):
        for x in [True,63,385,64.0,None,'64']:
            with self.assertRaises(ValueError):validate_interval(x)
        self.assertEqual(validate_interval(64),64)


class FrequencyTests(unittest.TestCase):
    def setUp(self):
        self.settings=profile_policy('architecture')['fmax_scan']
        self.endpoint=dict(status='CERTIFIED',passing_period_ns=4.,failing_period_ns=3.995,
                           hold_pass=True,capped_at_minimum_period=False,trials=2)
        self.rows=[dict(period_ns=3.995,actual_clock_period_ns=3.995,setup_slack_ns=-.001,
                       hold_slack_ns=.01,**{'pass':False}),
                   dict(period_ns=4.,actual_clock_period_ns=4.,setup_slack_ns=.004,
                       hold_slack_ns=.01,**{'pass':True})]

    def test_clock_reconstraint_and_both_endpoints_required(self):
        validate_trials(self.endpoint,self.rows,self.settings)
        for key,value in [('actual_clock_period_ns',10.),('hold_slack_ns',-.0001),('setup_slack_ns',float('nan'))]:
            rows=copy.deepcopy(self.rows);rows[1][key]=value
            with self.assertRaises(EnvironmentError):validate_trials(self.endpoint,rows,self.settings)

    def test_mislabeled_failing_or_incomplete_scan_rejected(self):
        rows=copy.deepcopy(self.rows);rows[0]['setup_slack_ns']=.1
        with self.assertRaises(EnvironmentError):validate_trials(self.endpoint,rows,self.settings)
        with self.assertRaises(EnvironmentError):validate_trials(self.endpoint,self.rows[:1],self.settings)

    def test_minimum_period_cap_reports_achieved_bound(self):
        e=dict(self.endpoint,passing_period_ns=.25,failing_period_ns=None,capped_at_minimum_period=True,trials=1)
        r=dict(self.rows[1],period_ns=.25,actual_clock_period_ns=.25)
        validate_trials(e,[r],self.settings)

if __name__=='__main__':unittest.main()
