"""Cache replay attacks and real subprocess failures; no ASIC data are fabricated."""
from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'fft64_benchmark/tools'))
import cache
import common
import evaluate as evaluator
import throughput
from scoring import make_calibration,score_result


class ThroughputCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.frames=np.zeros((1024,64,2),dtype=np.int64);self.calls=0
        self.policy=copy.deepcopy(throughput.profile_policy('architecture'))
        # Small interval *test fixture*, keeping the production policy untouched.
        self.policy['ii_calibration'].update(pilot_all_integer_intervals=[383,384],chunk_intervals=1)
        self.settings_patch=patch.object(throughput,'profile_policy',return_value=self.policy)
        self.settings_patch.start()
        self.runtime_patch=patch.object(throughput,'runtime_identity',return_value={'fixture':'tool-and-driver-identity'})
        self.runtime_patch.start()
        self.sim_patch=patch.object(throughput,'simulate',side_effect=self.simulate)
        self.sim_patch.start()

    def tearDown(self):
        self.sim_patch.stop();self.runtime_patch.stop();self.settings_patch.stop();self.tmp.cleanup()

    def simulate(self,source,events,*args,**kwargs):
        self.calls+=1
        raw=np.zeros((len(events),5),dtype=np.int64);raw[:,0]=np.arange(len(events))
        # Zero FFT fixture; the real decoder checks every complete transaction.
        for start in np.flatnonzero((events[:,1]==1)&(events[:,2]==1)):
            if not np.all(events[start:start+64,1]) or np.any(events[start:start+128,0]):continue
            raw[start+64:start+128,1]=1;raw[start+64,2]=1
        return raw

    def probe(self,**kw):
        defaults=dict(source='RTL',frames=self.frames,outdir=self.root/'probe',backend='vcs',seed=7)
        defaults.update(kw);return throughput.probe_intervals(**defaults)

    def test_identical_probe_reuses_complete_authenticated_results(self):
        first=self.probe();self.assertEqual(self.calls,2)
        self.assertEqual(self.probe(),first);self.assertEqual(self.calls,2)
        self.assertTrue(all(r['pass_rtl']for r in first))

    def test_changed_rtl_data_seed_backend_policy_and_driver_are_rejected(self):
        self.probe();before=(self.root/'probe/probe_results.json').read_bytes()
        changed=self.frames.copy();changed[0,0,0]=1
        for override in [dict(source='different'),dict(frames=changed),dict(seed=8),dict(backend='iverilog')]:
            with self.subTest(override=list(override)),self.assertRaises(common.CacheIdentityError):self.probe(**override)
        self.policy['ii_calibration']['chunk_intervals']=2
        with self.assertRaises(common.CacheIdentityError):self.probe()
        self.policy['ii_calibration']['chunk_intervals']=1
        with patch.object(throughput,'runtime_identity',return_value={'fixture':'changed-tool-or-driver'}):
            with self.assertRaises(common.CacheIdentityError):self.probe()
        self.assertEqual(before,(self.root/'probe/probe_results.json').read_bytes());self.assertEqual(self.calls,2)

    def test_corrupt_aggregate_is_reconstructed_from_valid_chunks(self):
        expected=self.probe();(self.root/'probe/probe_results.json').write_text('{broken')
        self.assertEqual(self.probe(),expected);self.assertEqual(self.calls,2)

    def test_partial_chunk_is_reexecuted_instead_of_cached_as_pass(self):
        self.probe();(self.root/'probe/probe_results.json').unlink()
        (self.root/'probe/intervals_383_383/results.json').write_text('[]')
        rows=self.probe();self.assertEqual(self.calls,3);self.assertEqual(len(rows),2)

    def test_unbound_cache_cannot_replay_any_result(self):
        out=self.root/'probe';out.mkdir();(out/'probe_results.json').write_text('[{"pass_rtl":true}]')
        with self.assertRaises(common.CacheIdentityError):self.probe()
        self.assertEqual(self.calls,0)

    def test_qualification_binds_mapped_netlist_and_subset(self):
        frames=np.zeros((2,64,2),dtype=np.int64)
        args=('RTL','mapped',frames,self.root/'qualification',384)
        first=throughput.qualify(*args);calls=self.calls
        self.assertEqual(first['status'],'PASS');self.assertEqual(throughput.qualify(*args),first)
        self.assertEqual(self.calls,calls)
        for replacement in [('changed mapped',frames),('mapped',frames+1)]:
            with self.assertRaises(common.CacheIdentityError):
                throughput.qualify('RTL',*replacement,self.root/'qualification',384)
        for changes in [dict(source='changed RTL'),dict(seed=12),dict(backend='iverilog')]:
            options=dict(source='RTL',mapped_source='mapped',frames=frames,outdir=self.root/'qualification',interval=384)
            options.update(changes)
            with self.assertRaises(common.CacheIdentityError):throughput.qualify(**options)

    def test_corrupt_cache_receipt_is_rebuilt_without_reusing_its_pass(self):
        self.probe()
        (self.root/'probe/probe_results.json.cache.json').write_text('[]')
        # The completed authenticated chunks can reconstruct the aggregate.
        self.assertEqual(len(self.probe()),2);self.assertEqual(self.calls,2)

    def test_qualification_never_turns_unknown_runtime_error_into_design_failure(self):
        with patch.object(throughput,'simulate',side_effect=RuntimeError('tool crashed without license keywords')):
            with self.assertRaises(RuntimeError):
                throughput.qualify('RTL','mapped',self.frames[:2],self.root/'q',384)
        self.assertFalse((self.root/'q/ii_384/qualification.json').exists())


class OutcomeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()

    def execute_failure(self,message):
        return common.run([sys.executable,'-c','import sys;print('+repr(message)+');sys.exit(3)'],self.root/'tool.log')

    def test_actual_tool_failure_license_and_crash_are_unscored(self):
        for message in ['No valid license available','internal error: kernel crashed','unclassified tool exit']:
            with self.assertRaises(common.InfrastructureError)as caught:self.execute_failure(message)
            self.assertEqual(common.failure_status(caught.exception),'UNSCORED_INFRASTRUCTURE')
            self.assertEqual(common.read(self.root/'tool.log.json')['returncode'],3)

    def test_explicit_hdl_and_checker_failures_are_design_invalid(self):
        for message in ['source.sv:12: syntax error','Fatal: X control cycle411','TASK_DESIGN_INVALID: Latch not permitted']:
            with self.assertRaises(common.DesignInvalidError)as caught:self.execute_failure(message)
            self.assertEqual(common.failure_status(caught.exception),'DESIGN_INVALID')

    def test_vcs_copyright_license_agreement_is_not_a_license_failure(self):
        banner='may be used only as authorized in a license agreement\n'
        with self.assertRaises(common.DesignInvalidError):self.execute_failure(banner+'Error-[SE] Syntax error')
        with self.assertRaises(common.InfrastructureError):
            self.execute_failure(banner+'Error-[SE] Syntax error\nLicense checkout failed')

    def test_timeout_is_unscored_and_has_a_receipt(self):
        with self.assertRaises(common.InfrastructureError):
            common.run([sys.executable,'-c','import time;time.sleep(5)'],self.root/'timeout.log',timeout=.05)
        self.assertEqual(common.read(self.root/'timeout.log.json')['status'],'TIMEOUT')

    def test_unknown_failed_status_does_not_become_a_valid_zero(self):
        for status in ['FAILED','UNSCORED_INFRASTRUCTURE','ENVIRONMENT_ERROR','RUNNING']:
            grade=score_result(dict(status=status,profile='area',failure='failed'))
            self.assertFalse(grade['score_valid']);self.assertFalse(grade['resolved'])
        for status in ['DESIGN_INVALID','QUALITY_FAILED','THROUGHPUT_FAILED']:
            self.assertTrue(score_result(dict(status=status,profile='area'))['score_valid'])

    def test_real_subprocess_exception_propagates_through_evaluator(self):
        submission=self.root/'submission';(submission/'rtl').mkdir(parents=True)
        (submission/'rtl/top.sv').write_text('module fft64_top; endmodule')
        def broken_simulator(*args,**kwargs):self.execute_failure('unclassified tool exit')
        with (patch.object(evaluator,'activate'),patch.object(evaluator,'probe'),
              patch.object(evaluator,'select_backend',return_value=('local','test fixture')),
              patch.object(evaluator,'simulate',side_effect=broken_simulator)):
            result=evaluator.evaluate(submission,self.root/'result',backend='local',quick=True)
        self.assertEqual(result['status'],'UNSCORED_INFRASTRUCTURE')
        self.assertFalse(result['grade']['score_valid'])
        self.assertTrue(result['grade']['reason'].startswith('UNSCORED_INFRASTRUCTURE:'))

    def test_invalid_submission_and_completeness_are_distinct(self):
        submission=self.root/'submission';(submission/'rtl').mkdir(parents=True)
        (submission/'rtl/top.sv').write_text('module fft64_top; endmodule')
        common.save(submission/'design_config.json',dict(frame_ii_cycles='invalid'))
        _,info=evaluator.assemble(submission)
        self.assertEqual(info['frame_ii_cycles'],384);self.assertTrue(info['warnings'])
        completeness=evaluator.submission_completeness(submission)
        self.assertFalse(completeness['affects_hardware_score']);self.assertIn('DESIGN_PLAN.md',completeness['missing'])
        common.save(submission/'design_config.json',dict(rtl=12))
        with self.assertRaises(common.DesignInvalidError):evaluator.assemble(submission)

    def test_context_change_disables_scoring_with_same_backend_and_flow(self):
        from test_scoring import result
        baseline=result();baseline['measurement_context']=dict(protocol_fingerprint='seed-A',measurement_platform_fingerprint='tool-A')
        calibration=make_calibration({'accurate':baseline})
        self.assertTrue(score_result(baseline,calibration)['score_valid'])
        for field in ['protocol_fingerprint','measurement_platform_fingerprint']:
            candidate=copy.deepcopy(baseline);candidate['measurement_context'][field]='changed'
            grade=score_result(candidate,calibration)
            self.assertTrue(grade['resolved']);self.assertFalse(grade['score_valid'])

    def test_stale_low_level_output_directory_preserves_original_result(self):
        submission=self.root/'submission';(submission/'rtl').mkdir(parents=True)
        (submission/'rtl/top.sv').write_text('module fft64_top; endmodule')
        out=self.root/'out';out.mkdir();old={'status':'COMPLETE','source':'other RTL'};common.save(out/'result.json',old)
        with (patch.object(evaluator,'activate'),patch.object(evaluator,'probe'),
              patch.object(evaluator,'select_backend',return_value=('local','test fixture'))):
            result=evaluator.evaluate(submission,out,backend='local',quick=True)
        self.assertEqual(common.read(out/'result.json'),old)
        self.assertFalse(result['grade']['score_valid']);self.assertTrue(list((out/'rejected_attempts').glob('*.json')))


if __name__=='__main__':unittest.main()
