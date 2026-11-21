"""Host-side snapshot/SSH tests. No container, credentials or EDA work needed."""
from pathlib import Path
import contextlib
import hashlib
import io
import json
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'operator'))
import docker_runner
import bootstrap_docker_runtime as bootstrap


class DockerRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='fft64_docker_test_')
        self.root = Path(self.temporary.name)
        self.repo = self.root/'repo'; self.repo.mkdir()
        for directory in ['fft64_benchmark/tools', 'fft64_benchmark/flow', 'fft64_benchmark/tech', 'operator']:
            (self.repo/directory).mkdir(parents=True)
        for name in docker_runner.LIBRARIES:
            (self.repo/'fft64_benchmark/tech'/name).write_text('FIXTURE '+name)
        (self.repo/'fft64_benchmark/tools/fixture.py').write_text('# source snapshot fixture\n')
        (self.repo/'operator/docker_env.sh').write_text('# profile fixture\n')
        (self.repo/'run_synopsys.sh').write_text('# flow fixture\n')
        self.design = self.root/'agent'; (self.design/'rtl').mkdir(parents=True)
        (self.design/'rtl/top.sv').write_text('module fft64_top; endmodule\n')
        (self.design/'results/runs/old').mkdir(parents=True)
        (self.design/'results/runs/old/cache').write_text('do not copy runtime build cache')
        self.shared = self.root/'shared'

    def tearDown(self):
        self.temporary.cleanup()

    def execute(self, extra=None):
        with (patch.object(docker_runner, 'ROOT', self.repo),
              patch.object(docker_runner, 'prepare') as prepare,
              patch.object(docker_runner.subprocess, 'run', return_value=types.SimpleNamespace(returncode=0)) as run,
              contextlib.redirect_stdout(io.StringIO())):
            code = docker_runner.main([str(self.design), '--shared-dir', str(self.shared),
                                       '--container-share', '/mnt/mydata', '--origin', 'reference']+(extra or []))
        return code, prepare, run

    def test_snapshot_contains_rtl_and_code_but_not_build_caches(self):
        code, prepare, run = self.execute()
        self.assertEqual(code, 0); prepare.assert_called_once()
        snapshot = next((self.shared/'jobs').iterdir())
        self.assertEqual((snapshot/'submission/rtl/top.sv').read_bytes(), (self.design/'rtl/top.sv').read_bytes())
        self.assertFalse((snapshot/'submission/results/runs').exists())
        receipt = json.loads((snapshot/'snapshot.json').read_text())
        self.assertIn('fft64_benchmark/tools/fixture.py', receipt['source_hashes'])
        command = run.call_args.args[0][-1]
        self.assertIn('set -e;', command)
        self.assertIn('if bash run_synopsys.sh submission', command)
        self.assertIn('chown -R ', command)
        self.assertIn('--state-dir /mnt/mydata/eval_state', command)
        self.assertIn('--origin reference', command)

    def test_repeated_runs_keep_separate_snapshots_and_shared_library_cache(self):
        self.execute(); self.execute()
        self.assertEqual(len(list((self.shared/'jobs').iterdir())), 2)
        self.assertEqual(len(list((self.shared/'runtime/tech').iterdir())), 1)

    def test_ssh_host_port_and_native_output_are_preserved(self):
        _, _, run = self.execute(['--ssh-host', 'test@localhost', '--ssh-port', '1235',
                                  '--out', '/mnt/mydata/eval/test'])
        argv = run.call_args.args[0]
        self.assertIn('test@localhost', argv); self.assertIn('1235', argv)
        self.assertIn('--out /mnt/mydata/eval/test', argv[-1])

    def test_unknown_submission_is_rejected_before_any_ssh(self):
        with (patch.object(docker_runner, 'prepare'),
              patch.object(docker_runner.subprocess, 'run') as run,
              contextlib.redirect_stderr(io.StringIO())):
            with self.assertRaises(SystemExit): docker_runner.main([])
        run.assert_not_called()

    def test_numpy_preparation_is_delegated_without_a_bundled_wheel(self):
        _, _, run = self.execute()
        command = run.call_args.args[0][-1]
        self.assertNotIn('vendor/wheels', command)
        self.assertNotIn('pip install', command)
        self.assertIn('run_synopsys.sh submission', command)

    def test_external_wheelhouse_uses_container_uri_and_is_not_snapshotted(self):
        wheelhouse = self.shared/'offline wheels'
        wheelhouse.mkdir(parents=True)
        (wheelhouse/'cache.whl').write_text('TEST FIXTURE ONLY')
        _, _, run = self.execute(['--wheelhouse',str(wheelhouse)])
        command = run.call_args.args[0][-1]
        self.assertIn('PIP_NO_INDEX=1', command)
        self.assertIn('PIP_FIND_LINKS=file:///mnt/mydata/offline%20wheels', command)
        snapshot = next((self.shared/'jobs').iterdir())
        self.assertFalse(list(snapshot.rglob('*.whl')))

    def test_external_wheelhouse_outside_shared_mount_is_rejected(self):
        wheelhouse = self.root/'unmounted';wheelhouse.mkdir()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                self.execute(['--wheelhouse',str(wheelhouse)])

    def test_runtime_archive_checksum_failure_does_not_extract_or_execute(self):
        runtime = self.root/'runtime'; runtime.mkdir()
        (runtime/bootstrap.ARCHIVE).write_bytes(b'wrong bytes')
        with patch.object(bootstrap.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'checksum'): bootstrap.prepare(runtime)
        run.assert_not_called()

    def test_verified_existing_runtime_is_reused_with_provenance(self):
        runtime = self.root/'runtime'; (runtime/'python/bin').mkdir(parents=True)
        (runtime/'python/bin/python3').write_text('fixture executable')
        payload = b'fixture archive'; (runtime/bootstrap.ARCHIVE).write_bytes(payload)
        with (patch.object(bootstrap, 'SHA256', hashlib.sha256(payload).hexdigest()),
              patch.object(bootstrap.subprocess, 'run') as run):
            self.assertEqual(bootstrap.prepare(runtime), runtime/'python/bin/python3')
        run.assert_not_called()
        self.assertEqual(json.loads((runtime/'python_source.json').read_text())['archive_bytes'], len(payload))


if __name__ == '__main__':
    unittest.main()
