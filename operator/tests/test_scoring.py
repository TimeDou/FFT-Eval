"""Frozen profile math and feasibility, with synthetic measurements only."""
from pathlib import Path
import copy
import json
import math
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'fft64_benchmark/tools'))
from scoring import hardware_feasible,make_calibration,performance,score_result,POLICY_SHA256,public_parameters,component_scores


def result(area=4000.,period=5.,interval=384,first=256,profile='area'):
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

    def test_public_area_ideal_half_and_continuous_large_area(self):
        for area,expected in [(500,1),(4000,.5),(11000,.25),(1,1),(30000,3500/33000)]:
            grade=score_result(result(area),self.reference)
            self.assertTrue(grade['resolved']);self.assertTrue(grade['score_valid'])
            self.assertAlmostEqual(grade['score'],expected)

    def test_no_score_or_area_cutoff_changes_feasibility(self):
        for area in [10,79,80,81,99,100,101,10000]:
            grade=score_result(result(area),self.reference)
            self.assertTrue(grade['resolved']);self.assertTrue(0<=grade['score']<=1)

    def test_area_profile_does_not_reward_frequency_or_quality(self):
        a=result(4000);b=result(4000,period=2)
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
        expected_step=math.log(2)/math.log(240)
        self.assertAlmostEqual(grade['components']['throughput']-score_result(a,cal)['components']['throughput'],expected_step)
        self.assertAlmostEqual(grade['score']-score_result(a,cal)['score'],.3*expected_step)
        self.assertEqual(grade['performance']['first_output_latency_ns'],2560)
        self.assertEqual(grade['performance']['certified_setup_fmax_MHz'],400)

    def test_public_anchors_are_explicit_and_not_fitted_to_control_designs(self):
        a=result(50,9,384,256,'architecture');b=result(100,2,64,133,'architecture')
        cal=make_calibration({'small_slow':a,'large_fast':b},profile='architecture')
        self.assertEqual(cal['reference_design'],'public_physical_anchors')
        self.assertEqual(cal['references']['area_um2'],4000)
        self.assertEqual(cal['accurate_reference_area_um2'],50)
        self.assertEqual(cal['targets']['area_um2'],500)
        self.assertEqual(cal['references']['first_output_latency_ns'],3000)
        self.assertEqual(cal['targets']['first_output_latency_ns'],630)
        self.assertAlmostEqual(cal['targets']['throughput_ffts_per_second'],62500000)
        other=make_calibration({'another_control':result(7000,3,200,200,'architecture')},profile='architecture')
        for field in ['references','targets','normalization_parameters']:
            self.assertEqual(cal[field],other[field])

    def test_feasible_very_low_combined_score_still_passes(self):
        accurate=result(profile='architecture')
        cal=make_calibration({'accurate':accurate},profile='architecture')
        design=result(area=1e9,period=10,interval=384,first=300,profile='architecture')
        g=score_result(design,cal)
        self.assertTrue(g['resolved']);self.assertTrue(g['score_valid']);self.assertGreater(g['score'],0)
        self.assertLess(g['score'],1e-4)

    def test_public_preview_scores_without_exposing_private_calibration(self):
        design=result(profile='architecture');design['audience']='public'
        preview=score_result(design)
        self.assertTrue(preview['resolved']);self.assertTrue(preview['score_valid'])
        self.assertEqual(preview['scoring_scope'],'public_preview');self.assertFalse(preview['official_score'])
        self.assertEqual(preview['normalization_parameters'],public_parameters())
        design['audience']='hidden'
        cal=make_calibration({'accurate':design},'architecture')
        hidden=score_result(design,cal)
        self.assertAlmostEqual(hidden['score'],preview['score'])
        self.assertEqual(hidden['components'],preview['components']);self.assertTrue(hidden['official_score'])
        self.assertFalse(score_result(design)['score_valid'])

    def test_area_has_no_reference_zero_plateau_and_high_throughput_keeps_credit(self):
        scores=[component_scores(dict(area_um2=a),'area')['area']for a in [2000,4000,8000,16000,32000]]
        self.assertTrue(all(x>y>0 for x,y in zip(scores,scores[1:])))
        values=[component_scores(dict(area_um2=2000,first_output_cycles=150,
                    effective_throughput_ffts_per_second=t),'architecture')['throughput']
                for t in [1e6,2.5e6,5e6,13e6,30e6,62500000]]
        self.assertTrue(all(x<y for x,y in zip(values,values[1:])))
        self.assertEqual(values[-1],1)

    def test_ideal_componentwise_point_is_one(self):
        scores=component_scores(dict(area_um2=500,first_output_cycles=63,
                  effective_throughput_ffts_per_second=62500000),'architecture')
        self.assertEqual(scores,dict(area=1,throughput=1,latency=1))

    def test_tampered_public_scales_cannot_change_official_objective(self):
        ref=copy.deepcopy(self.reference);ref['normalization_parameters']['area_ideal_um2']=1000
        self.assertFalse(score_result(result(),ref)['score_valid'])

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

    def test_changed_specification_invalidates_hidden_calibration_without_changing_feasibility(self):
        from common import sha
        from scoring import measurement_context
        design=result(profile='architecture')
        design.update(seed=1157,scale=1,audience='hidden')
        design['measurement_context']=measurement_context(design)
        calibration=make_calibration({'accurate':design},profile='architecture')
        self.assertTrue(score_result(design,calibration)['score_valid'])
        specification=ROOT/'fft64_benchmark/SPEC.json'
        replacement='0'*64 if sha(specification)!='0'*64 else '1'*64
        with patch('common.sha',side_effect=lambda p:replacement if Path(p)==specification else sha(p)):
            changed=copy.deepcopy(design)
            changed['measurement_context']=measurement_context(changed)
        self.assertEqual(design['measurement_context']['measurement_platform_fingerprint'],
                         changed['measurement_context']['measurement_platform_fingerprint'])
        self.assertNotEqual(design['measurement_context']['protocol_fingerprint'],
                            changed['measurement_context']['protocol_fingerprint'])
        grade=score_result(changed,calibration)
        self.assertTrue(grade['resolved']);self.assertFalse(grade['score_valid'])
        self.assertIn('Calibration protocol',grade['reason'])

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
