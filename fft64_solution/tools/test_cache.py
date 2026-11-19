"""Checkpoint policy fixtures; these tests do not claim numerical measurements."""
from pathlib import Path
import copy
import errno
import shutil
import tempfile
import unittest
from unittest.mock import patch
import solve
from common import read,save,sha


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.original=solve.SOLUTION
        self.context=dict(tools={name:dict(path='/fixture/'+name,sha256=f'{i:064x}')for i,name in
                          enumerate(['yosys','abc','sta','iverilog','vvp','verilator','g++','make'])},
                          libraries={'ASAP7_RVT_TT_nldm_NO_FAHA.lib':'a'*64,
                                     'ASAP7_SEQ_RVT_TT_nldm_220123.lib':'b'*64,'cells_sim.v':'c'*64},
                          python='fixture',numpy='fixture')
        self.temporary=tempfile.TemporaryDirectory(prefix='fft64_cache_test_')
        self.root=Path(self.temporary.name)
        (self.root/'tools').mkdir()
        for name in ['generate.py']:
            shutil.copy2(self.original/'tools'/name,self.root/'tools'/name)
        (self.root/'results/runs').mkdir(parents=True)
        self.source=self.root/'candidate.sv';self.source.write_text('module fixture; endmodule\n')
        self.previous=self.root/'results/runs/previous'
        with patch.object(solve,'SOLUTION',self.root),patch.object(solve,'execution_context',return_value=self.context):
            metadata=read(solve.run_root()/'run_info.json')
        save(self.previous/'run_info.json',metadata)
        save(self.previous/'toolchain.json',self.context)
        case=self.previous/'development/quantized_banked'
        save(case/'result.json',dict(status='COMPLETE',seed=20261118,scale=2,
                                     source=dict(source_sha256=sha(self.source))))
        signature={key:self.context['tools'][key]['sha256']for key in ['abc','sta','yosys']}
        signature.update(comb='a'*64,seq='b'*64)
        save(case/'asic/signature.json',signature)

    def tearDown(self):self.temporary.cleanup()

    def attempt(self,context,seed=20261118):
        with patch.object(solve,'SOLUTION',self.root),patch.object(solve,'execution_context',return_value=context):
            directory=solve.run_root()/'development/quantized_banked'
            return solve.reuse(Path('development/quantized_banked'),directory,self.source,seed,2)

    def test_matching_measurement_can_resume(self):
        self.assertEqual(self.attempt(self.context)['status'],'COMPLETE')

    def test_different_tool_binary_cannot_reuse_prior_measurement(self):
        context=copy.deepcopy(self.context);context['tools']['yosys']['sha256']='f'*64
        self.assertIsNone(self.attempt(context))

    def test_different_input_protocol_cannot_reuse_prior_measurement(self):
        self.assertIsNone(self.attempt(self.context,seed=999999))

    def test_different_evaluator_cannot_reuse_prior_measurement(self):
        metadata=read(self.previous/'run_info.json');metadata['tools/common.py']='0'*64
        save(self.previous/'run_info.json',metadata)
        self.assertIsNone(self.attempt(self.context))

    def test_cache_transfer_falls_back_when_hardlinks_are_unavailable(self):
        source=self.root/'transfer_source';source.mkdir();(source/'payload').write_text('fixture\n')
        target=self.root/'transfer_target'
        with patch.object(solve.os,'link',side_effect=OSError(errno.EXDEV,'cross-device link')):
            solve.transfer(source,target)
        self.assertEqual((target/'payload').read_text(),'fixture\n')


if __name__=='__main__':unittest.main()
