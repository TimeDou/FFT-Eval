"""Run production Tcl with command fixtures; no licensed PPA is measured here."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'fft64_benchmark/tools'))
import commercial
from common import read, save


# These stand-ins supply a tiny known mapped hierarchy. The production script
# still executes its real area accounting, validation, file writes and catch.
TCL_FIXTURE = r'''
set fixture_cells {group add0 group/add1 group/reg mux}
set fixture_refs [dict create add0 ADDx1_ASAP7_75t_R group/add1 ADDx1_ASAP7_75t_R group/reg DFFHQNx1_ASAP7_75t_R mux MUX2x1_ASAP7_75t_R]
set fixture_areas [dict create ADDx1_ASAP7_75t_R 1.25 DFFHQNx1_ASAP7_75t_R 2.5 MUX2x1_ASAP7_75t_R 0.375 LHx1_ASAP7_75t_R 2.0]
if {$::env(FFT_FIXTURE_MODE) eq "empty"} {set fixture_cells {}}
if {$::env(FFT_FIXTURE_MODE) eq "foreign"} {dict set fixture_refs add0 GTECH_ADD}
if {$::env(FFT_FIXTURE_MODE) eq "latch"} {dict set fixture_refs add0 LHx1_ASAP7_75t_R}
foreach command {set_app_var set_host_options define_design_lib set_svf analyze elaborate link uniquify ungroup set_max_area set_fix_multiple_port_nets set_dont_touch_network create_clock set_clock_uncertainty set_clock_transition set_input_delay set_input_transition set_output_delay set_load set_false_path change_names write write_sdc} {
    proc $command {args} {return 1}
}
proc compile_ultra {args} {
    if {$::env(FFT_FIXTURE_MODE) eq "compile_error"} {error "fixture compile failure"}
    return 1
}
proc current_design {args} {return fft64_top}
proc get_cells {args} {return $::fixture_cells}
proc foreach_in_collection {variable collection body} {
    uplevel 1 [list foreach $variable $collection $body]
}
proc sizeof_collection {collection} {return [llength $collection]}
proc get_attribute {object attribute} {
    if {$object eq "fft64_top" && $attribute eq "area"} {
        error "Attribute 'area' does not exist on design 'fft64_top'"
    }
    if {$attribute eq "is_hierarchical"} {return [expr {$object eq "group"}]}
    if {$attribute eq "ref_name"} {return [dict get $::fixture_refs $object]}
    if {$attribute eq "area"} {
        if {$::env(FFT_FIXTURE_MODE) eq "bad_area"} {return $::env(FFT_FIXTURE_AREA)}
        return [dict get $::fixture_areas [file tail $object]]
    }
    error "Unexpected fixture attribute: $attribute"
}
proc get_lib_cells {args} {
    set reference [file tail [lindex $args end]]
    if {$::env(FFT_FIXTURE_MODE) eq "missing_cell"} {return {}}
    if {$::env(FFT_FIXTURE_MODE) eq "ambiguous_cell"} {return {lib1/cell lib2/cell}}
    return [list fixture/$reference]
}
proc get_object_name {object} {return $object}
proc get_pins {args} {return [lindex $args end]}
proc get_nets {args} {
    if {$::env(FFT_FIXTURE_MODE) eq "derived_clock"} {return clk_div}
    return clk
}
proc get_ports {args} {return [lindex $args end]}
proc get_clocks {args} {return clk}
proc all_outputs {} {return {out_re out_im out_valid}}
proc redirect {path body} {
    set stream [open $path w]
    puts $stream "Command fixture only; not a DC report"
    close $stream
}
source [lindex $argv 0]
'''


@unittest.skipUnless(shutil.which('tclsh'), 'tclsh is required for production-Tcl regression')
class TclAreaTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='fft64 area fixture ')
        self.root = Path(self.temporary.name)
        self.tech = self.root/'tech'; (self.tech/'db').mkdir(parents=True)
        for name in ['comb_rvt_tt.db', 'seq_rvt_tt.db']:
            (self.tech/'db'/name).write_text('TEST FIXTURE ONLY; NOT A SYNOPSYS DB')
        self.fixture = self.root/'fixture.tcl'
        self.fixture.write_text(TCL_FIXTURE)

    def tearDown(self):
        self.temporary.cleanup()

    def execute(self, mode='valid', area='', case='run'):
        work = self.root/case
        env = dict(os.environ, FFT_TASK_ROOT=str(ROOT/'fft64_benchmark'),
                   FFT_TECH_DIR=str(self.tech), FFT_WORK=str(work),
                   FFT_FIXTURE_MODE=mode, FFT_FIXTURE_AREA=area)
        result = subprocess.run([shutil.which('tclsh'), str(self.fixture),
                                 str(ROOT/'fft64_benchmark/flow/synth_dc.tcl')],
                                env=env, capture_output=True, text=True, timeout=10)
        return result, work

    def test_leaf_library_areas_work_without_design_area_attribute(self):
        result, work = self.execute()
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        metrics = read(work/'dc_metrics.json')
        # Two ADD instances, one FF and one MUX; hierarchy contributes no area.
        self.assertEqual(metrics['area_um2'], 2*1.25+2.5+0.375)
        self.assertEqual(metrics['register_area_um2'], 2.5)
        self.assertEqual(metrics['cells'], 4)
        self.assertEqual(metrics['area_method'], 'sum_mapped_leaf_library_cell_area')
        self.assertFalse((work/'dc_metrics.json.tmp').exists())

    def test_missing_nonfinite_and_nonpositive_library_areas_are_rejected(self):
        for number, value in enumerate(['', 'invalid', '0', '-1', 'Inf', '-Inf', 'NaN']):
            with self.subTest(value=value):
                result, work = self.execute('bad_area', value, str(number))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('TASK_FATAL:', result.stderr)
                self.assertFalse((work/'dc_metrics.json').exists())

    def test_invalid_mapping_and_clocks_do_not_write_metrics(self):
        for mode in ['empty', 'foreign', 'latch', 'missing_cell', 'ambiguous_cell', 'derived_clock']:
            with self.subTest(mode=mode):
                result, work = self.execute(mode, case=mode)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('TASK_FATAL:', result.stderr)
                self.assertFalse((work/'dc_metrics.json').exists())

    def test_tcl_failure_stops_batch_with_nonzero_status(self):
        result, work = self.execute('compile_error')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('TASK_FATAL: fixture compile failure', result.stderr)
        self.assertFalse((work/'dc_metrics.json').exists())


class CommercialStageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='fft64_stage_fixture_')
        self.root = Path(self.temporary.name)
        self.calls = []
        self.dc_log = ''; self.dc_json = None; self.pt_json = None

    def tearDown(self):
        self.temporary.cleanup()

    def fake_run(self, argv, log, *args, **kwargs):
        self.calls.append(argv[0]); work = log.parent
        log.write_text(self.dc_log if argv[0] == 'dc_shell' else '')
        (work/('dc_units.rpt' if argv[0] == 'dc_shell' else 'pt_units.rpt')).write_text(
            'Time Unit: 1ps\nCapacitance Unit: 1ff\n')
        if argv[0] == 'dc_shell':
            (work/'mapped.v').write_text('// fixture mapped design, not measured\n')
            (work/'dc_metrics.json').write_text(self.dc_json if self.dc_json is not None else json.dumps(
                dict(area_um2=5.375, register_area_um2=2.5, cells=4)))
        else:
            (work/'pt_check.rpt').write_text('fixture only\n')
            (work/'pt_metrics.json').write_text(self.pt_json if self.pt_json is not None else json.dumps(
                dict(worst_setup_slack_ns=1.0, effective_required_period_ns=9.0)))
        return dict(returncode=0)

    def measure(self, case='run'):
        with (patch.object(commercial, 'preflight', return_value=dict(ready=True)),
              patch.object(commercial, 'flow_identity', return_value='FIXTURE_ONLY_NOT_MEASURED'),
              patch.object(commercial, 'sha', return_value='f'*64),
              patch.object(commercial, 'run', side_effect=self.fake_run)):
            return commercial.measure('module fixture; endmodule', self.root/case)

    def test_valid_area_and_timing_metrics_complete(self):
        metrics = self.measure()
        self.assertEqual(metrics['area_um2'], 5.375)
        self.assertEqual(metrics['register_area_um2'], 2.5)
        self.assertTrue(metrics['timing_pass'])
        self.assertEqual(self.calls, ['dc_shell', 'pt_shell'])

    def test_dc_logged_error_stops_before_primetime_even_after_exit_zero(self):
        self.dc_log = 'Error: expected floating-point number but got ""\n'
        with self.assertRaisesRegex(RuntimeError, 'expected floating-point'):
            self.measure()
        self.assertEqual(self.calls, ['dc_shell'])
        self.assertFalse((self.root/'run/metrics.json').exists())

    def test_empty_or_invalid_dc_metrics_stop_before_primetime(self):
        cases = ['', '[]', '{}', '{"area_um2":"","register_area_um2":0,"cells":4}',
                 '{"area_um2":NaN,"register_area_um2":0,"cells":4}',
                 '{"area_um2":1,"register_area_um2":2,"cells":4}',
                 '{"area_um2":1,"register_area_um2":0,"cells":false}']
        for number, value in enumerate(cases):
            with self.subTest(value=value):
                self.calls.clear(); self.dc_json = value
                with self.assertRaisesRegex(RuntimeError, '(DC metric|DC mapped)'):
                    self.measure(str(number))
                self.assertEqual(self.calls, ['dc_shell'])
                self.assertFalse((self.root/str(number)/'metrics.json').exists())

    def test_invalid_pt_metrics_are_not_saved_as_measurements(self):
        self.pt_json = '{"worst_setup_slack_ns":NaN,"effective_required_period_ns":9}'
        with self.assertRaisesRegex(RuntimeError, 'Invalid PT metric'):
            self.measure()
        self.assertFalse((self.root/'run/metrics.json').exists())

    def test_finite_negative_slack_is_a_timing_failure_not_a_tool_failure(self):
        self.pt_json = '{"worst_setup_slack_ns":-1,"effective_required_period_ns":11}'
        self.assertFalse(self.measure()['timing_pass'])


if __name__ == '__main__':
    unittest.main()
