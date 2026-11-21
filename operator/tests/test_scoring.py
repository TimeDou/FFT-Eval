"""Frozen profile math and feasibility, with synthetic measurements only."""
from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'fft64_benchmark/tools'))
from scoring import hardware_feasible,make_calibration,performance,score_result,POLICY_SHA256


def result(area=100.,period=5.,interval=384,first=256,profile='area'):
    return dict(status='COMPLETE',backend='commercial',flow_id='FIXTURE_NOT_MEASURED',profile=profile,
        quality=dict(feasible=True),protocol_pass=True,mapped_simulation_pass=True,
        ppa=dict(area_um2=area,timing_pass=True,clock_period_ns=10.,mapped_sha256='FIXTURE',
                 fmax_certificate=dict(status='CERTIFIED',hold_pass=True,mapped_sha256='FIXTURE',
                    passing_period_ns=period,failing_period_ns=period-.005,capped_at_minimum_period=False)),
        latency=dict(offered_frame_II=384,first_output_latency_cycles=[first]),
        throughput_check=dict(status='PASS',mapped_pass=True,verified_frame_ii_cycles=interval,
                              first_output_latency_cycles=[first]))


class ScoringTests(unittest.TestCase):
    def setUp(self):self.reference=make_calibration({'accurate':result()})

    def test_area_reference_zero_target_one_midpoint_half(self):
        for area,expected in [(100,0),(75,.5),(50,1),(1,1),(200,0)]:
            grade=score_result(result(area),self.reference)
            self.assertTrue(grade['resolved']);self.assertTrue(grade['score_valid'])
            self.assertAlmostEqual(grade['score'],expected)

    def test_no_score_or_area_cutoff_changes_feasibility(self):
        for area in [10,79,80,81,99,100,101,10000]:
            grade=score_result(result(area),self.reference)
            self.assertTrue(grade['resolved']);self.assertTrue(0<=grade['score']<=1)

    def test_area_profile_does_not_reward_frequency_or_quality(self):
        a=result(75);b=result(75,period=2)
        b['quality']['minimum_frame_sqnr_db']=100
        self.assertEqual(score_result(a,self.reference)['score'],score_result(b,self.reference)['score'])
        del b['ppa']['fmax_certificate']
        self.assertEqual(score_result(b,self.reference)['score'],.5)

    def test_architecture_weights_frequency_only_enters_through_throughput(self):
        a=result(profile='architecture')
        cal=make_calibration({'accurate':a},profile='architecture')
        b=result(period=2.5,profile='architecture')
        grade=score_result(b,cal)
        self.assertEqual(grade['components']['latency'],score_result(a,cal)['components']['latency'])
        self.assertAlmostEqual(grade['components']['throughput'],1)
        self.assertAlmostEqual(grade['score']-score_result(a,cal)['score'],.2)
        self.assertEqual(grade['performance']['first_output_latency_ns'],2560)
        self.assertEqual(grade['performance']['certified_setup_fmax_MHz'],400)

    def test_architecture_envelope_is_explicit_and_accurate_only(self):
        a=result(50,9,384,256,'architecture');b=result(100,2,64,133,'architecture')
        cal=make_calibration({'small_slow':a,'large_fast':b},profile='architecture')
        self.assertEqual(cal['reference_design'],'paper_contract_and_accurate_calibration')
        self.assertEqual(cal['references']['area_um2'],50)
        self.assertEqual(cal['targets']['area_um2'],25)
        self.assertEqual(cal['references']['first_output_latency_ns'],3000)
        self.assertEqual(cal['targets']['first_output_latency_ns'],665)
        self.assertAlmostEqual(cal['targets']['throughput_ffts_per_second'],2e9/(2*64))

    def test_feasible_zero_combined_score_still_passes(self):
        accurate=result(profile='architecture')
        cal=make_calibration({'accurate':accurate},profile='architecture')
        design=result(area=10000,period=10,interval=384,first=300,profile='architecture')
        g=score_result(design,cal)
        self.assertTrue(g['resolved']);self.assertTrue(g['score_valid']);self.assertEqual(g['score'],0)

    def test_fixed_clock_slack_cannot_substitute_a_frequency_certificate(self):
        a=result(profile='architecture');del a['ppa']['fmax_certificate']
        a['ppa']['effective_required_period_ns']=2
        self.assertFalse(hardware_feasible(a))
        self.assertFalse(score_result(a)['resolved'])

    def test_bad_scan_bracket_hold_or_netlist_cannot_score(self):
        for field,value in [('mapped_sha256','wrong'),('hold_pass',False),('failing_period_ns',4.9),('status','RUNNING')]:
            a=result(profile='architecture');a['ppa']['fmax_certificate'][field]=value
            self.assertFalse(hardware_feasible(a),field)

    def test_unverified_ii_cannot_be_inferred_from_output_latency(self):
        a=result(profile='architecture');a['throughput_check']['mapped_pass']=False
        self.assertFalse(hardware_feasible(a))

    def test_required_checks_and_formal_failure_gate_success(self):
        for key,value in [('status','FAILED'),('protocol_pass',False),('mapped_simulation_pass',False),('quality',dict(feasible=False))]:
            a=result();a[key]=value
            self.assertFalse(score_result(a,self.reference)['resolved'])
        a=result();a['ppa']['timing_pass']=False
        self.assertFalse(hardware_feasible(a))
        a=result();a['ppa']['formal_status']='FAILED'
        self.assertFalse(hardware_feasible(a))

    def test_missing_calibration_reports_feasibility_separately(self):
        grade=score_result(result());self.assertTrue(grade['resolved']);self.assertFalse(grade['score_valid'])

    def test_other_profile_policy_or_backend_cannot_reuse_scale(self):
        for key,value in [('profile','architecture'),('policy_sha256','other'),('backend','local'),('weights',{'area':.5})]:
            cal=copy.deepcopy(self.reference);cal[key]=value
            grade=score_result(result(),cal)
            self.assertTrue(grade['resolved']);self.assertFalse(grade['score_valid'])
        self.assertEqual(self.reference['policy_sha256'],POLICY_SHA256)

    def test_invalid_area_cannot_pass(self):
        for value in [0,-1,True,float('nan'),float('inf')]:
            self.assertFalse(hardware_feasible(result(value)))

    def test_mixed_flow_or_failed_calibration_rejected(self):
        a=result();a['status']='FAILED'
        with self.assertRaises(ValueError):make_calibration({'failed':a})
        a=result();a['flow_id']='other'
        with self.assertRaises(ValueError):make_calibration({'a':a,'b':result()})

    def test_grader_includes_frozen_policy_and_all_runtime_dependencies(self):
        sys.path.insert(0,str(ROOT/'fft64_benchmark/grading'))
        import make_grader
        with tempfile.TemporaryDirectory()as d:
            with patch.object(sys,'argv',['make_grader.py','--out',d]):make_grader.main()
            with zipfile.ZipFile(Path(d)/'fft64_grader.zip')as z:
                for p in ['tools/scoring.py','tools/frequency.py','tools/throughput.py','profiles/policy.json','flow/fmax_pt.tcl']:
                    self.assertIn('fft64_grader/'+p,z.namelist())

    def test_grader_uses_calibrated_input_protocol(self):
        sys.path.insert(0,str(ROOT/'fft64_benchmark/grading'))
        import make_grader
        with tempfile.TemporaryDirectory()as d:
            root=Path(d);ref=dict(self.reference,baseline_results={'accurate':dict(seed=12345,scale=2)})
            from scoring import measurement_context
            ref['measurement_context']=measurement_context(dict(backend='commercial',seed=12345,scale=2,audience='hidden'))
            path=root/'calibration.json';path.write_text(json.dumps(ref))
            out=root/'grader'
            with patch.object(sys,'argv',['make_grader.py','--out',str(out),'--calibration',str(path),'--profile','area']):make_grader.main()
            self.assertEqual(json.loads((out/'settings.json').read_text()),dict(seed=12345,scale=2,profile='area'))
            (out/'settings.json').write_text(json.dumps(dict(seed=7,scale=2,profile='area')))
            with patch.object(sys,'argv',['make_grader.py','--out',str(out),'--calibration',str(path),'--profile','area']):
                with self.assertRaisesRegex(SystemExit,'calibrated protocol'):make_grader.main()

    def test_grader_rejects_public_or_changed_hidden_calibration_protocol(self):
        sys.path.insert(0,str(ROOT/'fft64_benchmark/grading'))
        import make_grader
        from scoring import measurement_context
        with tempfile.TemporaryDirectory()as d:
            root=Path(d)
            for audience,seed in [('public',12345),('hidden',7)]:
                ref=dict(self.reference,baseline_results={'accurate':dict(seed=12345,scale=2)},
                         measurement_context=measurement_context(dict(backend='commercial',seed=seed,scale=2,audience=audience)))
                path=root/'calibration.json';path.write_text(json.dumps(ref))
                with patch.object(sys,'argv',['make_grader.py','--out',str(root/audience),'--calibration',str(path),'--profile','area']):
                    with self.assertRaisesRegex(SystemExit,'matching hidden-data calibration'):make_grader.main()

if __name__=='__main__':unittest.main()
