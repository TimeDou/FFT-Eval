"""Feasibility and ranking policy tests with explicit synthetic PPA fixtures."""
from pathlib import Path
import copy
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'fft64_benchmark/tools'))
from scoring import hardware_feasible, make_calibration, performance, score_result


def result(area=100., period=5., interval=384):
    return dict(status='COMPLETE', backend='commercial', flow_id='FIXTURE_NOT_MEASURED',
                quality=dict(feasible=True), protocol_pass=True, mapped_simulation_pass=True,
                ppa=dict(area_um2=area, effective_required_period_ns=period,
                         timing_pass=True, clock_period_ns=10.),
                latency=dict(offered_frame_II=interval))


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.reference = make_calibration({'accurate': result()})

    def test_exact_anchor_scores_half_and_is_feasible(self):
        grade = score_result(result(), self.reference)
        self.assertTrue(grade['resolved']); self.assertTrue(grade['score_valid'])
        self.assertEqual(grade['score'], .5)

    def test_no_score_or_area_cutoff_changes_hardware_feasibility(self):
        for area in [10., 79., 80., 81., 99., 100., 101., 10000.]:
            with self.subTest(area=area):
                grade = score_result(result(area=area), self.reference)
                self.assertTrue(grade['resolved'])
                self.assertGreater(grade['score'], 0.)
                self.assertLess(grade['score'], 1.)

    def test_smaller_area_improves_score(self):
        self.assertGreater(score_result(result(area=50), self.reference)['score'], .5)
        self.assertLess(score_result(result(area=200), self.reference)['score'], .5)

    def test_faster_sta_period_improves_score(self):
        self.assertAlmostEqual(score_result(result(period=2.5), self.reference)['score'], 2/3)

    def test_frequency_is_counted_once_through_throughput(self):
        grade = score_result(result(period=2.5), self.reference)
        self.assertEqual(grade['relative_throughput_per_area'], 2.)
        measured = grade['performance']
        self.assertEqual(measured['prelayout_fmax_estimate_MHz'], 400.)
        self.assertAlmostEqual(measured['target_clock_samples_per_second'], 64e9/(384*10))

    def test_interval_must_be_verified_and_not_inferred_from_latency(self):
        design = result(); design['latency'].pop('offered_frame_II')
        design['latency']['frame_completion_cycles'] = [100]
        grade = score_result(design, self.reference)
        self.assertFalse(grade['resolved']); self.assertFalse(grade['score_valid'])
        self.assertEqual(grade['score'], 0.)

    def test_reference_anchor_uses_one_real_design(self):
        designs = {'small_slow': result(area=50, period=9),
                   'large_fast': result(area=100, period=2)}
        reference = make_calibration(designs)
        self.assertEqual(reference['reference_design'], 'large_fast')
        self.assertEqual(reference['reference_area_um2'], 100)
        self.assertEqual(reference['reference_period_ns'], 2)

    def test_each_required_hardware_check_gates_success(self):
        mutations = [('status', 'FAILED'), ('protocol_pass', False),
                     ('mapped_simulation_pass', False), ('quality', dict(feasible=False)),
                     ('ppa', dict(area_um2=100, effective_required_period_ns=5, timing_pass=False))]
        for key, value in mutations:
            with self.subTest(key=key):
                design = result(); design[key] = value
                grade = score_result(design, self.reference)
                self.assertFalse(grade['resolved']); self.assertEqual(grade['score'], 0.)

    def test_formality_failure_cannot_be_hidden_by_simulation(self):
        design = result(); design['ppa']['formal_status'] = 'FAILED'
        self.assertFalse(hardware_feasible(design))

    def test_missing_calibration_preserves_feasibility_but_has_no_valid_score(self):
        grade = score_result(result())
        self.assertTrue(grade['resolved']); self.assertFalse(grade['score_valid'])

    def test_old_area_only_calibration_requires_recalibration(self):
        reference = dict(backend='commercial', flow_id='FIXTURE_NOT_MEASURED',
                         reference_area_um2=100, pass_area_ratio=.8)
        grade = score_result(result(), reference)
        self.assertTrue(grade['resolved']); self.assertFalse(grade['score_valid'])
        self.assertIn('recalibrate', grade['reason'])

    def test_mixed_backend_calibration_does_not_score(self):
        reference = copy.deepcopy(self.reference); reference['backend'] = 'local'
        grade = score_result(result(), reference)
        self.assertTrue(grade['resolved']); self.assertFalse(grade['score_valid'])
        self.assertIsNone(grade['area_ratio'])

    def test_nonfinite_or_boolean_measurements_do_not_score(self):
        for area in [0, -1, True, float('nan'), float('inf')]:
            with self.subTest(area=area):
                grade = score_result(result(area=area), self.reference)
                self.assertFalse(grade['resolved']); self.assertEqual(grade['score'], 0.)

    def test_calibration_rejects_failed_and_mixed_flow_measurements(self):
        failed = result(); failed['status'] = 'FAILED'
        with self.assertRaises(ValueError): make_calibration({'failed': failed})
        changed = result(); changed['flow_id'] = 'other'
        with self.assertRaises(ValueError): make_calibration({'a': result(), 'b': changed})

    def test_grading_attachment_contains_new_scoring_dependency(self):
        sys.path.insert(0, str(ROOT/'fft64_benchmark/grading'))
        import make_grader
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sys, 'argv', ['make_grader.py', '--out', directory]):
                make_grader.main()
            with zipfile.ZipFile(Path(directory)/'fft64_grader.zip') as archive:
                self.assertIn('fft64_grader/tools/scoring.py', archive.namelist())


if __name__ == '__main__':
    unittest.main()
