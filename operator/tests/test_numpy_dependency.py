"""NumPy is reused or installed through pip, without a repository wheel."""
from pathlib import Path
import copy
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'fft64_benchmark/tools'))
import toolchain


def report(available):
    return dict(quick=True,numpy_available=available,python=sys.executable,
                tools={name:'/fixture/'+name for name in toolchain.TOOLS},
                commercial=dict(tools_present=True,ready=available,missing=[]if available else['numpy']),
                local=dict(tools_present=True,ready=available,missing=[]if available else['numpy']))


class NumpyDependencyTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.root=Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def prepare(self,initial,final=None,check_only=False,failed=False):
        with (patch.object(toolchain,'activate'),
              patch.object(toolchain,'probe',side_effect=[report(initial),report(initial if final is None else final)]),
              patch.object(toolchain,'prefix',return_value=self.root),
              patch.object(toolchain,'run',side_effect=RuntimeError('fixture pip unavailable')if failed else None)as run):
            result=toolchain.prepare('commercial',quick=True,check_only=check_only,allow_build=False)
        return result,run

    def test_existing_numpy_is_never_reinstalled(self):
        result,run=self.prepare(True)
        self.assertTrue(result['ready']);run.assert_not_called()

    def test_missing_numpy_uses_pinned_binary_requirement_on_supported_pythons(self):
        for version in [(3,10,0),(3,12,0)]:
            with self.subTest(version=version),patch.object(sys,'version_info',version):
                result,run=self.prepare(False,True)
            self.assertTrue(result['ready'])
            argv=run.call_args.args[0]
            self.assertEqual(argv[:4],[sys.executable,'-m','pip','install'])
            self.assertIn('--only-binary=:all:',argv)
            self.assertEqual(argv[-2:],['-r',ROOT/'fft64_benchmark/requirements.txt'])
            self.assertNotIn('--no-index',argv);self.assertNotIn('--find-links',argv)
        self.assertIn('numpy==2.2.6',(ROOT/'fft64_benchmark/requirements.txt').read_text())

    def test_check_only_never_installs(self):
        result,run=self.prepare(False,check_only=True)
        self.assertFalse(result['ready']);run.assert_not_called()

    def test_unavailable_index_or_cache_remains_a_setup_error(self):
        result,run=self.prepare(False,failed=True)
        self.assertFalse(result['ready']);self.assertTrue(result['failures'])
        self.assertIn('fixture pip unavailable',result['failures'][0])

if __name__=='__main__':unittest.main()
