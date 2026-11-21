"""Simulator execution/initial-state receipts, using explicit process fixtures."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'fft64_benchmark/tools'))
import simulate as simulation
from common import read,DesignInvalidError


class SimulationDriverTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='fft64_sim_driver_')
        self.root=Path(self.temporary.name)
        self.events=np.asarray([[1,0,0,0,0],[0,0,0,0,0]],dtype=np.int64)
        self.calls=[];self.message=''

    def tearDown(self):self.temporary.cleanup()

    def fake_run(self,argv,log,*args,**kwargs):
        argv=list(map(str,argv));self.calls.append((argv,Path(kwargs['cwd'])))
        log=Path(log);log.parent.mkdir(parents=True,exist_ok=True);log.write_text(self.message if log.name=='simulation.log' else '')
        if argv[0]=='vcs':Path(argv[argv.index('-o')+1]).write_text('simulator fixture')
        else:
            output=Path(next(x.split('=',1)[1]for x in argv if x.startswith('+OUTPUT=')))
            output.write_text('0 0 0 0 0\n1 0 0 0 0\n')

    def test_compile_cache_is_private_to_each_run_directory(self):
        with patch.object(simulation,'run',side_effect=self.fake_run):
            simulation.simulate('module fixture; endmodule',self.events,self.root/'run','vcs')
        self.assertEqual(self.calls[0][1],self.root/'run')
        self.assertEqual(self.calls[1][1],self.root/'run')
        self.assertNotIn('+vcs+initreg+random',self.calls[0][0])

    def test_three_gate_starts_share_one_compile_but_keep_separate_outputs(self):
        with patch.object(simulation,'run',side_effect=self.fake_run):
            for mode in [0,1,20261121]:
                simulation.simulate('module fixture; endmodule',self.events,self.root/'run','vcs',initialization=mode)
        compile_calls=[x for x,cwd in self.calls if x[0]=='vcs']
        self.assertEqual(len(compile_calls),1)
        self.assertIn('+vcs+initreg+random',compile_calls[0])
        for mode in [0,1,20261121]:
            run=self.root/'run'/('initial_state_'+str(mode))
            self.assertEqual(read(run/'receipt.json')['initialization'],mode)
            self.assertTrue((run/'output.txt').is_file())
            self.assertTrue(any('+vcs+initreg+'+str(mode)in argv for argv,cwd in self.calls))

    def test_zero_exit_fatal_is_reported_before_truncated_output_is_parsed(self):
        self.message='Fatal: tb: X control cycle411\n'
        with patch.object(simulation,'run',side_effect=self.fake_run):
            with self.assertRaisesRegex(DesignInvalidError,'X control cycle411'):
                simulation.simulate('module fixture; endmodule',self.events,self.root/'run','vcs')

    def test_ignored_initialization_flag_cannot_be_marked_verified(self):
        self.message='Warning: VCS initreg not enabled at compile time\n'
        with patch.object(simulation,'run',side_effect=self.fake_run):
            with self.assertRaisesRegex(RuntimeError,'initreg not enabled'):
                simulation.simulate('module fixture; endmodule',self.events,self.root/'run','vcs',initialization=0)

    def test_gate_modes_do_not_silently_change_another_backend(self):
        with self.assertRaises(ValueError):
            simulation.simulate('unused',self.events,self.root/'run','iverilog',initialization=0)


if __name__=='__main__':unittest.main()
