"""Portable public SSH transport, deployment layout and isolated snapshots."""
from pathlib import Path
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'fft64_benchmark/tools'))
import synopsys_remote as remote


class RemoteTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='fft remote layout ')
        self.root=Path(self.tmp.name);self.repo=self.root/'FFT-Bench';self.repo.mkdir()
        self.shared=self.root/'Synopsys';self.shared.mkdir()
        (self.root/'port.txt').write_text('23456\n')
        self.layout=remote.Layout(repo=self.repo)
        task=self.repo/'fft64_benchmark';task.mkdir()
        for name in remote.PUBLIC_FILES:(task/name).write_text('public fixture '+name)
        for name in remote.PUBLIC_DIRS:
            (task/name).mkdir();(task/name/'fixture.txt').write_text('public '+name)
        (task/'tech').mkdir()
        for name in remote.LIBRARIES:(task/'tech'/name).write_text('fixture '+name)
        # Private files in a sibling tree must never be staged by this bridge.
        (task/'grading').mkdir();(task/'grading/secret.txt').write_text('private sentinel')
        (task/'OPERATOR.md').write_text('private sentinel')
        (self.repo/'operator').mkdir();(self.repo/'operator/secret.txt').write_text('private sentinel')
        self.submission=self.root/'submission';(self.submission/'rtl').mkdir(parents=True)
        (self.submission/'rtl/top.sv').write_text('module fft64_top; endmodule')
        (self.submission/'runs').mkdir();(self.submission/'runs/large.log').write_text('not staged')
        self.connections=[]

    def tearDown(self):
        for connection in self.connections:shutil.rmtree(connection.state,ignore_errors=True)
        self.tmp.cleanup()

    def connection(self):
        c=remote.Connection(self.layout);self.connections.append(c);return c

    def test_sibling_layout_and_whitespace_port(self):
        self.assertEqual(self.layout.port,23456)
        self.assertEqual(self.layout.shared,self.shared)
        self.assertEqual(self.layout.remote(self.shared/'test path/a.v'),'/mnt/mydata/test path/a.v')
        with self.assertRaises(ValueError):self.layout.remote(self.repo/'a.v')

    def test_missing_malformed_and_out_of_range_ports_are_clear_errors(self):
        p=self.root/'port.txt'
        for value in ['', 'ssh -p 1234', '12\n34','-1','65536','0']:
            p.write_text(value)
            with self.subTest(value=value),self.assertRaises(ValueError):remote.Layout(repo=self.repo)
        p.unlink()
        with self.assertRaisesRegex(ValueError,'Cannot read'):remote.Layout(repo=self.repo)
        self.assertEqual(remote.Layout(repo=self.repo,port=22).port,22)

    def test_snapshot_is_public_and_independent_of_source_edits(self):
        job,out=remote.stage(self.layout,self.submission,dict(quick=True),self.repo/'runs/quick')
        self.assertTrue(out.is_symlink());self.assertEqual(out.resolve(),job/'output')
        self.assertFalse((job/'fft64_benchmark/grading').exists())
        self.assertFalse((job/'fft64_benchmark/OPERATOR.md').exists())
        self.assertFalse((job/'operator').exists());self.assertFalse((job/'submission/runs').exists())
        initial=(job/'submission/rtl/top.sv').read_bytes()
        (self.submission/'rtl/top.sv').write_text('changed')
        self.assertEqual((job/'submission/rtl/top.sv').read_bytes(),initial)

    def test_resume_matches_inputs_and_refuses_stale_source_or_options(self):
        job,out=remote.stage(self.layout,self.submission,dict(quick=True),self.repo/'runs/quick')
        self.assertEqual(remote.stage(self.layout,self.submission,dict(quick=True),out,True),(job,out))
        with self.assertRaisesRegex(ValueError,'already exists'):remote.stage(self.layout,self.submission,dict(quick=True),out)
        with self.assertRaisesRegex(ValueError,'inputs changed'):remote.stage(self.layout,self.submission,dict(quick=False),out,True)
        (self.submission/'rtl/top.sv').write_text('different source')
        with self.assertRaisesRegex(ValueError,'inputs changed'):remote.stage(self.layout,self.submission,dict(quick=True),out,True)

    def test_resume_rejects_modified_staged_rtl_even_when_host_is_unchanged(self):
        job,out=remote.stage(self.layout,self.submission,dict(quick=True),self.repo/'runs/quick')
        (job/'submission/rtl/top.sv').write_text('modified inside container')
        with self.assertRaisesRegex(ValueError,'Staged inputs changed'):
            remote.stage(self.layout,self.submission,dict(quick=True),out,True)

    def test_conflicting_output_and_external_resume_are_never_overwritten(self):
        out=self.repo/'runs/existing';out.mkdir(parents=True);(out/'data').write_text('keep')
        with self.assertRaises(ValueError):remote.stage(self.layout,self.submission,out=out,resume=True)
        self.assertEqual((out/'data').read_text(),'keep')
        link=self.repo/'external';link.symlink_to(self.root)
        with self.assertRaises(ValueError):remote.stage(self.layout,self.submission,out=link,resume=True)

    def test_library_cache_reuses_content_and_refuses_corruption(self):
        cache=remote.prepare_library_cache(self.layout)
        self.assertEqual(remote.prepare_library_cache(self.layout),cache)
        (cache/remote.LIBRARIES[0]).write_text('corrupt')
        with self.assertRaisesRegex(RuntimeError,'content mismatch'):remote.prepare_library_cache(self.layout)

    def test_password_authentication_needs_no_sshpass_and_stores_no_password(self):
        connection=self.connection();captured={}
        def fake_run(argv,**kwargs):
            captured.update(argv=argv,kwargs=kwargs)
            helper=Path(kwargs['env']['SSH_ASKPASS'])
            self.assertTrue(helper.is_file());self.assertNotIn('test-password',helper.read_text())
            self.assertEqual(kwargs['env']['FFT_SSH_PASSWORD'],'test-password')
            self.assertEqual(kwargs['env']['SSH_ASKPASS_REQUIRE'],'force')
            return subprocess.CompletedProcess(argv,0,'ok','')
        with patch.object(remote.subprocess,'run',side_effect=fake_run),patch.dict(os.environ,FFT_SSH_PASSWORD='test-password'):
            result=connection.run('printf ok',capture=True)
        self.assertEqual(result.returncode,0)
        self.assertNotIn('test-password',str(captured['argv']))
        self.assertFalse(Path(captured['kwargs']['env']['SSH_ASKPASS']).exists())
        self.assertLess(len(str(connection.state/'socket')),100)

    def test_handshake_requires_a_matching_bidirectional_mount(self):
        connection=self.connection()
        def fake_success(script,capture=False):
            directory=next((self.shared/'.fft64/handshakes').iterdir())
            (directory/'container.txt').write_text((directory/'host.txt').read_text())
            return subprocess.CompletedProcess([],0,'','')
        with patch.object(connection,'run',side_effect=fake_success):
            self.assertTrue(connection.handshake()['shared_write'])
        with patch.object(connection,'run',return_value=subprocess.CompletedProcess([],0,'','')):
            with self.assertRaisesRegex(RuntimeError,'expected writable shared mount'):connection.handshake()

    def test_environment_script_preserves_explicit_home_and_supports_tool_aliases(self):
        script=remote.environment_script(self.layout,need_python=False)
        result=subprocess.run(['bash','-n'],input=script,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('VCS_HOME',script);self.assertIn('command -v vcs',script)
        self.assertIn('FFT_EDA_PROFILE_LOADED=1',script)
        explicit=remote.environment_script(self.layout,python='/custom python/bin/python3')
        self.assertIn("'/custom python/bin/python3'",explicit)
        self.assertNotIn('/opt/dsbench/bin/python3',explicit)

    def test_cli_accepts_options_before_submission_and_preserves_exec_arguments(self):
        for args in [['run','submission','--quick'],['run','--quick','submission'],
                     ['exec','--','bash','-c','printf ok']]:
            with self.subTest(args=args),patch.object(remote,'Layout',side_effect=RuntimeError('parsed correctly')),contextlib.redirect_stderr(io.StringIO())as stream:
                self.assertEqual(remote.main(args),2)
                self.assertIn('parsed correctly',stream.getvalue())

    def test_command_arguments_are_quoted_without_local_shell_execution(self):
        connection=self.connection()
        with patch.object(remote.subprocess,'run',return_value=subprocess.CompletedProcess([],0))as call:
            connection.run('printf %s '+__import__('shlex').quote('$(must_not_run); text'))
        argv=call.call_args.args[0]
        self.assertEqual(argv[-2],self.layout.host)
        self.assertTrue(argv[-1].startswith('bash -lc '))
        self.assertNotIn('shell',call.call_args.kwargs)



class EnvironmentReportTests(unittest.TestCase):
    def exercise(self, failing=False):
        import synopsys_environment as checker
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)
            inventory=dict(ready=True,tools={},missing=[],actions=[])
            def probe(directory):
                current=json.loads((out/'environment.json').read_text())
                self.assertEqual(current['status'],'CHECKING')
                self.assertFalse(current['ready'])
                if failing:raise RuntimeError('fixture tool execution failure')
                return dict(status='PASS')
            with patch.object(checker,'prepare',return_value=inventory)as prepare,patch.object(checker,'smoke',side_effect=probe),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                code=checker.main(['check','--out',str(out)])
            self.assertFalse(prepare.call_args.kwargs['allow_build'])
            report=json.loads((out/'environment.json').read_text())
            return code,report

    def test_installed_tools_are_not_ready_before_actual_probe_finishes(self):
        code,report=self.exercise()
        self.assertEqual(code,0);self.assertEqual(report['status'],'READY');self.assertTrue(report['ready'])

    def test_tool_execution_failure_marks_environment_not_ready(self):
        code,report=self.exercise(failing=True)
        self.assertEqual(code,2);self.assertEqual(report['status'],'NOT_READY');self.assertFalse(report['ready'])


class FreshMappingTests(unittest.TestCase):
    def test_environment_probe_does_not_use_candidate_mapping_cache(self):
        import numpy as np
        import commercial,simulate,synopsys_environment as checker
        def fake_simulation(source,events,*args,**kwargs):
            result=[]
            for cycle,(rst,valid,start,real,imag) in enumerate(events):
                active=bool(valid and not rst)
                result.append([cycle,int(active),int(active and start),int(real)if active else 0,int(imag)if active else 0])
            return np.asarray(result,dtype=np.int64)
        def mapping(*args,**kwargs):
            self.assertNotIn('FFT_PHYSICAL_CACHE_DIR',os.environ)
            raise RuntimeError('mapping reached')
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,FFT_PHYSICAL_CACHE_DIR='/candidate/cache'),patch.object(simulate,'simulate',side_effect=fake_simulation),patch.object(commercial,'measure',side_effect=mapping):
            with self.assertRaisesRegex(RuntimeError,'mapping reached'):checker.smoke(directory)
            self.assertEqual(os.environ['FFT_PHYSICAL_CACHE_DIR'],'/candidate/cache')




class RuntimePreparationTests(unittest.TestCase):
    def test_pinned_offline_runtime_is_reused_without_replacing_an_active_interpreter(self):
        import hashlib,tarfile
        import prepare_remote_python as runtime
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary);source=root/'source';(source/'python/bin').mkdir(parents=True)
            (source/'python/bin/python3').write_text('fixture binary, not an actual interpreter')
            archive=root/'fixture.tar.gz'
            with tarfile.open(archive,'w:gz')as tar:tar.add(source/'python',arcname='python')
            checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
            with patch.object(runtime,'SHA256',checksum):
                executable=runtime.prepare(root/'runtime',archive)
                self.assertTrue(executable.is_file())
                executable.write_text('active interpreter sentinel')
                self.assertEqual(runtime.prepare(root/'runtime',archive),executable)
                self.assertEqual(executable.read_text(),'active interpreter sentinel')
                self.assertEqual(json.loads((root/'runtime/python_source.json').read_text())['sha256'],checksum)

    def test_wrong_offline_checksum_cannot_replace_a_valid_archive(self):
        import prepare_remote_python as runtime
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary);cache=root/'runtime';cache.mkdir()
            original=cache/runtime.ARCHIVE;original.write_bytes(b'keep archive')
            bad=root/'wrong.tar.gz';bad.write_bytes(b'invalid')
            with self.assertRaisesRegex(ValueError,'checksum'):runtime.prepare(cache,bad)
            self.assertEqual(original.read_bytes(),b'keep archive')


if __name__=='__main__':unittest.main()
