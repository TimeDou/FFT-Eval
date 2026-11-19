"""Checkpoint reuse requires matching tools, source and input protocol."""
from pathlib import Path
import copy
import shutil
import tempfile
import unittest
from unittest.mock import patch
import solve
from common import read


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.original=solve.SOLUTION
        status=read(self.original/'results/status.json')
        self.previous=self.original/status['run_relative']
        self.context=read(self.previous/'toolchain.json')
        self.temporary=tempfile.TemporaryDirectory(prefix='fft64_cache_test_')
        self.root=Path(self.temporary.name)
        (self.root/'tools').mkdir()
        for name in ['generate.py']:
            shutil.copy2(self.original/'tools'/name,self.root/'tools'/name)
        (self.root/'results/runs').mkdir(parents=True)
        (self.root/'results/runs/previous').symlink_to(self.previous,target_is_directory=True)

    def tearDown(self):self.temporary.cleanup()

    def attempt(self,context,seed=20261118):
        with patch.object(solve,'SOLUTION',self.root),patch.object(solve,'execution_context',return_value=context):
            directory=solve.run_root()/'development/quantized_banked'
            return solve.reuse(Path('development/quantized_banked'),directory,
                               self.original/'candidates/quantized_banked/rtl/fft64_top.sv',seed,2)

    def test_matching_measurement_can_resume(self):
        self.assertEqual(self.attempt(self.context)['status'],'COMPLETE')

    def test_different_tool_binary_cannot_reuse_prior_measurement(self):
        context=copy.deepcopy(self.context);context['tools']['yosys']['sha256']='0'*64
        self.assertIsNone(self.attempt(context))

    def test_different_input_protocol_cannot_reuse_prior_measurement(self):
        self.assertIsNone(self.attempt(self.context,seed=999999))


if __name__=='__main__':unittest.main()
