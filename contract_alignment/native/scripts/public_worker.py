"""Fresh custom-recipe build/export followed by actual public evaluation."""
from pathlib import Path
import subprocess
import sys
import driver
from common import read, save

ROOT = Path(__file__).resolve().parent


def main():
    config = read(ROOT/'config.json')
    receipt = ROOT/'custom_build_receipt.json'
    if not receipt.exists():
        command = [sys.executable, ROOT/'engine_public/fft64_benchmark/tools/build_implementation.py',
                   ROOT/'public_submission', '--backend', 'commercial', '--export',
                   '--out', ROOT/'custom_build']
        save(ROOT/'logs/custom_build_command.json', list(map(str, command)))
        with (ROOT/'logs/custom_build.log').open('w') as stream:
            result = subprocess.run(list(map(str, command)), stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError('Custom native build/export failed; inspect logs/custom_build.log')
        save(receipt, dict(status='PASS', scope='Fresh custom DC recipe execution and implementation export'))
    command = [sys.executable, ROOT/'engine_public/fft64_benchmark/tools/evaluate.py',
               '--submission', ROOT/'public_submission', '--out', ROOT/'measurements/public_preview',
               '--backend', 'commercial', '--profile', 'architecture', '--audience', 'public',
               '--seed', str(config['public_seed']), '--auto-ii']
    save(ROOT/'logs/public_evaluate_command.json', list(map(str, command)))
    subprocess.run(list(map(str, command)), check=True)


if __name__ == '__main__':
    main()
