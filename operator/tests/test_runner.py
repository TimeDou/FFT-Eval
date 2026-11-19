"""Commercial workflow control tests with fabricated PPA fixtures, not measurements."""
from pathlib import Path
import argparse
import contextlib
import csv
import importlib.util
import io
import json
import sys
import tempfile
import tarfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('fft_synopsys_runner',ROOT/'operator/evaluate_synopsys.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
from common import read,save
from evaluate import assemble,score_result
import evaluate as engine


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='fft64_runner_test_')
        self.root=Path(self.temporary.name)
        self.submission=self.root/'agent_A';(self.submission/'rtl').mkdir(parents=True)
        (self.submission/'rtl/top.sv').write_text('module fft64_top; endmodule\n')
        (self.submission/'measurements.csv').write_text('area_um2\n1\n')
        self.calls=[];self.fail_license=False;self.fail_calibration=False
        self.identity=dict(backend='commercial',flow_id='FIXTURE_ONLY_NOT_MEASURED',tools={'fixture':'test'})
        self.environment=dict(ready=True,selected_backend='commercial',tools={},actions=[],failures=[])

    def tearDown(self):
        self.temporary.cleanup()

    def args(self,**overrides):
        values=dict(submission=str(self.submission),manifest=None,batch=None,out=str(self.root/'out'),
                    state_dir=str(self.root/'state'),protocol=None,seed=12345,scale=1,calibration=None,
                    jobs=1,id='agent_A',origin='open-source',agent='test_agent',check_only=False,formal=False)
        values.update(overrides)
        return argparse.Namespace(**values)

    def fake_evaluate(self,submission,outdir,backend,seed,scale,calibration=None,formal=False):
        self.calls.append(dict(submission=str(submission),backend=backend,seed=seed,scale=scale))
        info=assemble(submission)[1]
        area={'sdf':1000.,'iterative':900.}.get(Path(submission).name,500.)
        result=dict(status='COMPLETE',backend=backend,flow_id=self.identity['flow_id'],source=info,
                    protocol_pass=True,quality=dict(feasible=True,minimum_frame_sqnr_db=60.),
                    ppa=dict(area_um2=area,timing_pass=True,worst_setup_slack_ns=1.),
                    latency=dict(first_output_latency_cycles=[256],frame_completion_cycles=[319]),
                    mapped_simulation_pass=True)
        if calibration is not None and self.fail_license:
            result.update(status='FAILED',failure='No valid license available')
        if Path(submission).name=='sdf' and self.fail_calibration:
            result.update(status='FAILED',failure='fixture DC script failure')
        result['grade']=score_result(result,calibration)
        save(Path(outdir)/'result.json',result)
        return result

    def execute(self,args,environment=None):
        with (patch.object(runner,'prepare',return_value=environment or self.environment)as prepare,
             patch.object(runner,'platform_identity',return_value=self.identity),
             patch.object(engine,'evaluate',side_effect=self.fake_evaluate),
             contextlib.redirect_stdout(io.StringIO())):
            status=runner.execute(args)
        self.assertEqual(prepare.call_args.args,('commercial',))
        self.assertFalse(prepare.call_args.kwargs['allow_build'])
        return status

    def test_missing_synopsys_is_unscored_without_local_fallback(self):
        result=self.execute(self.args(),dict(ready=False,selected_backend='commercial',tools={},actions=[]))
        self.assertEqual(result,2);self.assertFalse(self.calls)
        self.assertEqual(read(self.root/'out/status.json')['status'],'ENVIRONMENT_NOT_READY')
        self.assertEqual(read(self.root/'out/summary.json')['submissions'],[])
        self.assertFalse(read(self.root/'out/code_result.json')['resolved'])
        self.assertTrue((self.root/'out_feedback.tar.gz').exists())

    def test_calibration_and_score_use_only_target_measurements(self):
        self.assertEqual(self.execute(self.args()),0)
        reference=read(self.root/'out/calibration.json')
        self.assertEqual(reference['reference_area_um2'],900.)
        row=read(self.root/'out/summary.json')['submissions'][0]
        self.assertEqual(row['area_um2'],500.)
        self.assertAlmostEqual(row['score'],1-500/900)
        self.assertTrue(row['resolved']);self.assertEqual(row['first_output_ns'],2560.)
        self.assertEqual(len(self.calls),3)
        self.assertTrue(all(call['backend']=='commercial'for call in self.calls))

    def test_resume_reuses_completed_calibration_and_submission(self):
        self.execute(self.args());self.calls.clear()
        self.assertEqual(self.execute(self.args()),0)
        self.assertFalse(self.calls)
        self.assertTrue(read(self.root/'out/summary.json')['submissions'][0]['reused'])

    def test_changed_source_gets_separate_run(self):
        self.execute(self.args());self.calls.clear()
        with(self.submission/'rtl/top.sv').open('a')as stream:stream.write('// another source revision\n')
        self.execute(self.args())
        self.assertEqual(len(self.calls),1)
        self.assertEqual(len(list((self.root/'out/candidates/agent_A/runs').iterdir())),2)

    def test_changed_flow_does_not_reuse_or_overwrite_failed_calibration(self):
        self.fail_calibration=True
        self.assertEqual(self.execute(self.args()),2)
        previous=list((self.root/'state/calibration').glob('*/sdf/result.json'))
        self.assertEqual(len(previous),1)
        original=previous[0].read_bytes()
        self.fail_calibration=False;self.calls.clear()
        self.identity['flow_id']='FIXTURE_NEW_SYNTH_SCRIPT_NOT_MEASURED'
        self.assertEqual(self.execute(self.args()),0)
        self.assertEqual(len(self.calls),3)
        self.assertEqual(previous[0].read_bytes(),original)
        self.assertEqual(len(list((self.root/'state/calibration').iterdir())),2)

    def test_license_failure_is_not_a_valid_zero_score_and_is_retried(self):
        self.fail_license=True
        self.assertEqual(self.execute(self.args()),2)
        row=read(self.root/'out/summary.json')['submissions'][0]
        self.assertEqual(row['state'],'UNSCORED_INFRASTRUCTURE');self.assertIsNone(row['score'])
        self.calls.clear();self.fail_license=False
        self.assertEqual(self.execute(self.args()),0)
        self.assertEqual(len(self.calls),1)

    def test_batch_origins_receive_same_protocol_and_reference(self):
        second=self.root/'agent_B';(second/'rtl').mkdir(parents=True)
        (second/'rtl/top.sv').write_text('module fft64_top; endmodule\n// B\n')
        manifest=self.root/'designs.csv'
        manifest.write_text('id,submission,origin,agent\noss,agent_A,open-source,A\nsyn,agent_B,synopsys,B\n')
        self.assertEqual(self.execute(self.args(submission=None,manifest=str(manifest))),0)
        rows=read(self.root/'out/summary.json')['submissions']
        self.assertEqual({row['origin']for row in rows},{'open-source','synopsys'})
        self.assertEqual(rows[0]['score'],rows[1]['score'])
        self.assertEqual({(call['seed'],call['scale'])for call in self.calls},{(12345,1)})

    def test_default_protocol_is_shared_and_can_be_exported(self):
        self.execute(self.args(seed=None));first=read(self.root/'out/protocol.json')
        self.execute(self.args(seed=None,out=str(self.root/'out2')))
        self.assertEqual(read(self.root/'out2/protocol.json'),first)
        self.execute(self.args(seed=None,protocol=str(self.root/'out/protocol.json'),
                               state_dir=str(self.root/'other_state'),out=str(self.root/'out3')))
        self.assertEqual(read(self.root/'out3/protocol.json'),first)

    def test_previous_success_is_not_left_as_current_score_after_environment_failure(self):
        self.execute(self.args())
        self.execute(self.args(),dict(ready=False,selected_backend='commercial',tools={},actions=[]))
        self.assertFalse((self.root/'out/scores.csv').exists())
        self.assertEqual(read(self.root/'out/summary.json')['status'],'ENVIRONMENT_NOT_READY')
        self.assertTrue(list((self.root/'out/history').rglob('scores.csv')))

    def test_library_setup_log_is_included_in_failed_feedback(self):
        tech=self.root/'tech';tech.mkdir()
        (tech/'library_compile.log').write_text('fixture compiler diagnostic\n')
        (tech/'library_compile.log.json').write_text('{"argv":["lc_shell"]}\n')
        with patch.object(runner,'TECH',tech):
            self.execute(self.args(),dict(ready=False,selected_backend='commercial',tools={},actions=[]))
        self.assertEqual((self.root/'out/setup/library_compile.log').read_text(),'fixture compiler diagnostic\n')
        with tarfile.open(self.root/'out_feedback.tar.gz')as archive:
            self.assertIn('out/setup/library_compile.log',archive.getnames())
            self.assertIn('out/setup/library_compile.log.json',archive.getnames())


if __name__=='__main__':unittest.main()
