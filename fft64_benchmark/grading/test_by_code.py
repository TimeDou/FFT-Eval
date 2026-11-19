"""DSBench Code Grade entry. Attach fft64_grader.zip and area_reference.json."""
from pathlib import Path
import json
import os
import sys
import tempfile
import zipfile

def main():
    out = Path('/eval')
    out.mkdir(exist_ok=True)
    code = dict(resolved=False,score=0.0,reason='Evaluation did not finish.')
    try:
        calibration = json.loads(Path('/test_files/area_reference.json').read_text())
        if calibration.get('backend')!='commercial':
            raise ValueError('The commercial area reference is missing.')
        with tempfile.TemporaryDirectory(prefix='fft64_grader_') as temporary:
            root = Path(temporary)
            with zipfile.ZipFile('/test_files/fft64_grader.zip') as archive:
                if any(not (root/name).resolve().is_relative_to(root) for name in archive.namelist()):
                    raise ValueError('Invalid attachment path')
                archive.extractall(root)
            task = root/'fft64_grader'
            os.environ['FFT_TECH_DIR']='/workspace/benchmark/tech'
            sys.path.insert(0,str(task/'tools'))
            from evaluate import evaluate
            settings = json.loads((task/'settings.json').read_text())
            result = evaluate('/workspace/submission',out/'fft64_measurements','commercial',
                              seed=settings['seed'],scale=settings['scale'],calibration=calibration)
            grade = result['grade']
            code = {key:grade[key] for key in ['resolved','score','reason']}
            if result['status']=='ENVIRONMENT_ERROR':
                code['reason']='Environment error: '+result.get('failure','')
    except Exception as exc:
        code = dict(resolved=False,score=0.0,reason=str(exc))
    (out/'code_result.json').write_text(json.dumps(code,indent=2)+'\n')

if __name__=='__main__':
    main()
