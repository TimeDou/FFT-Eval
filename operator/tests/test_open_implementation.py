"""Agent optimization artifacts, trusted remeasurement and cache identity."""
from pathlib import Path
import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'fft64_benchmark/tools'))
from common import COMB,SEQ,DesignInvalidError,read,save,sha
import implementation as artifacts
from evaluate import assemble
from build_implementation import initialize
import test_commercial_metrics as fixtures
from local_asic import unique_timing_aliases

RTL='module fft64_top(input clk); endmodule\n'
NET='module fft64_top(input clk, input d, output q); DFFHQNx1_ASAP7_75t_R r(.CLK(clk),.D(d),.QN(q)); endmodule\n'


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.sub=self.root/'submission';(self.sub/'rtl').mkdir(parents=True)
        (self.sub/'rtl/top.sv').write_text(RTL)
        self.rtl_sha=hashlib.sha256(RTL.encode()).hexdigest()

    def tearDown(self):self.tmp.cleanup()

    def artifact(self,mapped=NET):
        out=self.sub/'implementation';out.mkdir(exist_ok=True)
        (out/'mapped.v').write_text(mapped)
        save(out/'manifest.json',dict(rtl_sha256=self.rtl_sha,mapped_sha256=sha(out/'mapped.v'),
            libraries_sha256={p.name:sha(p)for p in [COMB,SEQ]},producer=dict(custom_files_sha256={})))
        return out

    def test_structural_artifact_binds_rtl_netlist_and_technology(self):
        out=self.artifact();loaded=artifacts.load(self.sub,self.rtl_sha)
        self.assertEqual(loaded['mapped_sha256'],sha(out/'mapped.v'))
        for field in ['rtl_sha256','mapped_sha256','libraries_sha256']:
            original=read(out/'manifest.json');changed=dict(original);changed[field]='wrong'
            save(out/'manifest.json',changed)
            with self.assertRaisesRegex(DesignInvalidError,field):artifacts.load(self.sub,self.rtl_sha)
            save(out/'manifest.json',original)

    def test_behavioral_models_tasks_and_library_redefinitions_are_rejected(self):
        for suffix in ['initial $system("anything");','always @(posedge clk) q<=d;','`include "private.v"','function f; endfunction']:
            with self.subTest(suffix=suffix),self.assertRaises(DesignInvalidError):artifacts.validate_structural(NET.replace('endmodule',suffix+' endmodule'))
        with self.assertRaises(DesignInvalidError):artifacts.validate_structural(NET+'module DFFHQNx1_ASAP7_75t_R; endmodule')
        self.assertEqual(artifacts.validate_structural(NET.replace(' r(',r' \$abc$cell (')),NET.replace(' r(',r' \$abc$cell ('))

    def test_incomplete_and_escaped_paths_cannot_be_imported(self):
        out=self.sub/'implementation';out.mkdir()
        with self.assertRaises(DesignInvalidError):artifacts.load(self.sub,self.rtl_sha)
        out.rmdir();elsewhere=self.root/'external';elsewhere.mkdir();out.symlink_to(elsewhere)
        with self.assertRaises(DesignInvalidError):artifacts.load(self.sub,self.rtl_sha)

    def test_changed_recipe_requires_rebuild_but_never_executes_it(self):
        out=self.artifact();flow=self.sub/'flow';flow.mkdir()
        marker=self.root/'must_not_exist'
        script=flow/'dc_opt.tcl';script.write_text('exec touch '+str(marker))
        manifest=read(out/'manifest.json');manifest['producer']['custom_files_sha256']={'dc_opt.tcl':sha(script)};save(out/'manifest.json',manifest)
        artifacts.load(self.sub,self.rtl_sha);self.assertFalse(marker.exists())
        script.write_text('changed recipe')
        with self.assertRaisesRegex(DesignInvalidError,'recipe changed'):artifacts.load(self.sub,self.rtl_sha)

    def test_full_assembly_includes_artifact_and_quick_build_can_ignore_stale_export(self):
        out=self.artifact();source,info=assemble(self.sub)
        self.assertIn('implementation',info)
        (out/'mapped.v').write_text(NET+'// changed')
        with self.assertRaises(DesignInvalidError):assemble(self.sub)
        source,info=assemble(self.sub,include_implementation=False)
        self.assertEqual(source,RTL);self.assertNotIn('implementation',info)

    def test_custom_recipe_is_not_silently_ignored_without_export(self):
        initialize(self.sub)
        with self.assertRaisesRegex(DesignInvalidError,'exported implementation'):assemble(self.sub)
        self.assertEqual(assemble(self.sub,include_implementation=False)[0],RTL)

    def test_initialization_preserves_user_files_and_export_preserves_old_artifact(self):
        initialize(self.sub);recipe=self.sub/'flow/dc_opt.tcl';recipe.write_text('user recipe')
        initialize(self.sub);self.assertEqual(recipe.read_text(),'user recipe')
        old=self.artifact();previous=(old/'mapped.v').read_bytes()
        replacement=self.root/'built';replacement.mkdir();(replacement/'mapped.v').write_text(NET+'// new')
        save(replacement/'manifest.json',dict(mapped_sha256=sha(replacement/'mapped.v')))
        artifacts.export_artifacts(replacement,self.sub,self.root/'backup')
        self.assertEqual((self.root/'backup/mapped.v').read_bytes(),previous)
        self.assertEqual((old/'mapped.v').read_text(),NET+'// new')


class ImportTclTests(unittest.TestCase):
    setUp=fixtures.TclAreaTests.setUp
    tearDown=fixtures.TclAreaTests.tearDown
    execute=fixtures.TclAreaTests.execute
    def test_imported_netlist_is_measured_without_running_synthesis_recipe(self):
        # An attempted compile raises in this fixture. Successful import proves
        # the independent measurement path did not run the optimizer.
        import test_commercial_metrics as fixtures
        fixture=fixtures.TCL_FIXTURE.replace('source [lindex $argv 0]', 'proc read_verilog {args} {return 1}\nsource [lindex $argv 0]')
        self.fixture.write_text(fixture)
        with patch.dict(os.environ,FFT_IMPORT_NETLIST='/fixture/agent_mapped.v'):
            result,work=self.execute('compile_error')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(read(work/'dc_metrics.json')['area_um2'],5.375)


class ImportCacheTests(unittest.TestCase):
    setUp=fixtures.CommercialStageTests.setUp
    tearDown=fixtures.CommercialStageTests.tearDown
    fake_run=fixtures.CommercialStageTests.fake_run
    def test_different_mapped_artifacts_never_share_a_physical_cache_entry(self):
        import commercial
        first=self.root/'first.v';first.write_text(NET)
        second=self.root/'second.v';second.write_text(NET+'// another artifact')
        with(patch.dict(os.environ,FFT_PHYSICAL_CACHE_DIR=str(self.root/'cache')),
             patch.object(commercial,'preflight',return_value=dict(ready=True)),
             patch.object(commercial,'mapping_identity',return_value='FIXTURE'),
             patch.object(commercial,'sha',side_effect=lambda p:sha(p)if Path(p).is_file()else'f'*64),
             patch.object(commercial,'run',side_effect=self.fake_run)):
            a=commercial.measure(RTL,self.root/'a',implementation=first)
            b=commercial.measure(RTL,self.root/'b',implementation=second)
        self.assertNotEqual(a['imported_sha256'],b['imported_sha256'])
        self.assertEqual(self.calls,['dc_shell','pt_shell','dc_shell','pt_shell'])
        self.assertNotIn('FFT_IMPORT_NETLIST',os.environ)


class ScalarStaCompatibilityTests(unittest.TestCase):
    def test_repeated_sign_extension_alias_does_not_reach_sta_linker(self):
        # A real Yosys import emitted the first alias twice; OpenSTA hung in
        # link_design. Keep the timing graph's cells and every distinct alias.
        net='''module fft64_top;
  DFFHQNx1_ASAP7_75t_R r(.CLK(clk),.D(d),.QN(q));
  assign \\out_re[16]  = \\out_re[15] ;
  assign \\out_re[16]  = \\out_re[15] ;
  assign \\out_re[17]  = \\out_re[15] ;
endmodule
'''
        expected=net.replace('  assign \\out_re[16]  = \\out_re[15] ;\n','',1)
        self.assertEqual(unique_timing_aliases(net),expected)
        self.assertEqual(unique_timing_aliases(expected),expected)


if __name__=='__main__':unittest.main()
