"""Run the unchanged private batch operator against frozen final submissions."""
from pathlib import Path
import fcntl
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
os.environ.update(FFT_TECH_DIR='/mnt/mydata/.fft64/tech/99619e6e51b75f151556',
                  FFT_TOOLS_PREFIX='/mnt/mydata/.fft64/runtime')
sys.path.insert(0,str(ROOT/'engine_private/fft64_benchmark/tools'))
sys.path.insert(0,str(ROOT/'engine_private/operator'))
from common import read,save
from toolchain import prepare
import evaluate_synopsys as runner


def main():
    guard=(ROOT/'launcher.lock').open('a')
    fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
    started=time.monotonic()
    environment=prepare('commercial',allow_build=False)
    assert environment['ready']
    identity=runner.platform_identity(environment)
    reference=read(ROOT/'calibration.json')
    settings=dict(read(ROOT/'private_protocol.json'),measurement_backend='commercial')
    assert reference['platform_fingerprint']==runner.digest(identity),'Different platform: do not reuse calibration'
    assert reference['protocol_fingerprint']==runner.digest(settings),'Different protocol: do not reuse calibration'
    save(ROOT/'calibration_reuse_check.json',dict(status='PASS',platform_fingerprint=runner.digest(identity),
        protocol_fingerprint=runner.digest(settings),scope='Reuse completed accurate references only; all three new candidates undergo independent hidden evaluation'))
    command=[sys.executable,ROOT/'engine_private/operator/evaluate_synopsys.py',
             '--manifest',ROOT/'submissions.csv','--out',ROOT/'evaluation',
             '--state-dir',ROOT/'state','--protocol',ROOT/'private_protocol.json',
             '--calibration',ROOT/'calibration.json','--backend','commercial',
             '--profile','architecture','--jobs','3']
    save(ROOT/'official_command.json',list(map(str,command)))
    code=subprocess.run(list(map(str,command))).returncode
    save(ROOT/'launcher_result.json',dict(returncode=code,seconds=time.monotonic()-started,
                                          status='FINISHED'if code==0 else'CHECK_OPERATOR_RESULT'))
    return code


if __name__=='__main__':
    sys.exit(main())
