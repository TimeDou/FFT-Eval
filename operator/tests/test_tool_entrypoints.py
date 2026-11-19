"""Symlink-dispatch fixtures reproduce argv[0] behavior, not licensed EDA work."""
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'fft64_benchmark/tools'))
import common
import toolchain


class EntrypointTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='fft64_entrypoint_')
        self.root=Path(self.temporary.name);self.bin=self.root/'bin';self.bin.mkdir()
        dispatcher=self.bin/'snps_shell'
        dispatcher.write_text('#!'+sys.executable+'\n'+'''
import os,sys
from pathlib import Path
mode=Path(sys.argv[0]).name
if mode not in {'lc_shell','dc_shell','pt_shell','vcs'}:
    print('Error: The script is not supported.')
    sys.exit(23)
print('MODE='+mode)
if mode=='lc_shell' and os.environ.get('FFT_FIXTURE_NO_DB')!='1':
    target=Path(os.environ['FFT_TECH_DIR'])/'db'
    target.mkdir(parents=True,exist_ok=True)
    for name in ['comb_rvt_tt.db','seq_rvt_tt.db']:
        (target/name).write_text('TEST FIXTURE ONLY; NOT A SYNOPSYS DB')
''')
        dispatcher.chmod(0o755)
        for name in ['lc_shell','dc_shell','pt_shell','vcs']:(self.bin/name).symlink_to('snps_shell')
        self.tech=self.root/'tech';self.tech.mkdir()
        (self.tech/'cells_sim.v').write_text('// fixture only\n')
        self.env={entry[0]:''for entry in toolchain.TOOLS.values()}
        self.env.update(PATH=str(self.bin)+os.pathsep+os.environ.get('PATH',''),
                        FFT_EDA_PROFILE_LOADED='1',FFT_TECH_DIR=str(self.tech),
                        FFT_TOOLS_PREFIX=str(self.root/'tools'),LC_HOME=str(self.root),DC_HOME=str(self.root))

    def tearDown(self):self.temporary.cleanup()

    def test_path_discovery_preserves_both_product_names(self):
        with patch.dict(os.environ,self.env):
            for name in ['lc_shell','dc_shell']:
                selected=toolchain.find_tool(name)
                self.assertEqual(selected,str(self.bin/name))
                self.assertNotEqual(selected,str((self.bin/name).resolve()))

    def test_explicit_override_preserves_product_name(self):
        with patch.dict(os.environ,self.env|{'FFT_LC_BIN':str(self.bin/'lc_shell')}):
            self.assertEqual(toolchain.find_tool('lc_shell'),str(self.bin/'lc_shell'))

    def test_home_discovery_preserves_product_name(self):
        with patch.dict(os.environ,self.env|{'PATH':'/usr/bin:/bin'}):
            self.assertEqual(toolchain.find_tool('lc_shell'),str(self.bin/'lc_shell'))

    def test_common_executable_helper_preserves_entrypoint(self):
        with patch.dict(os.environ,self.env):
            self.assertEqual(common.executable('FFT_DC',['dc_shell']),self.bin/'dc_shell')
        with patch.dict(os.environ,self.env|{'FFT_DC':str(self.bin/'dc_shell')}):
            self.assertEqual(common.executable('FFT_DC',['dc_shell']),self.bin/'dc_shell')

    def test_real_dispatch_failure_and_success_via_alias(self):
        with patch.dict(os.environ,self.env):
            with self.assertRaisesRegex(RuntimeError,'The script is not supported'):
                common.run([self.bin/'snps_shell','-f','fixture.tcl'],self.root/'generic.log')
            for name in ['lc_shell','dc_shell']:
                log=self.root/(name+'.log')
                common.run([name,'-f','fixture.tcl'],log)
                self.assertIn('MODE='+name,log.read_text())
                receipt=json.loads(Path(str(log)+'.json').read_text())
                self.assertEqual(receipt['argv'][0],str(self.bin/name))

    def test_prepare_uses_lc_alias_and_checks_both_artifacts(self):
        with patch.dict(os.environ,self.env),patch.object(toolchain,'TECH',self.tech):
            result=toolchain.prepare('commercial',allow_build=False)
        self.assertTrue(result['ready'],result)
        self.assertEqual(result['tools']['lc_shell'],str(self.bin/'lc_shell'))
        self.assertTrue(toolchain.probe()['numpy_available'])
        self.assertIn('MODE=lc_shell',(self.tech/'library_compile.log').read_text())
        for name in ['comb_rvt_tt.db','seq_rvt_tt.db']:
            self.assertGreater((self.tech/'db'/name).stat().st_size,0)

    def test_success_exit_without_database_files_is_not_ready(self):
        with patch.dict(os.environ,self.env|{'FFT_FIXTURE_NO_DB':'1'}),patch.object(toolchain,'TECH',self.tech):
            result=toolchain.prepare('commercial',allow_build=False)
        self.assertFalse(result['ready'])
        self.assertTrue(any('both nonempty' in item for item in result['failures']))
        self.assertFalse(any('Compiled the supplied' in item for item in result['actions']))


if __name__=='__main__':unittest.main()
