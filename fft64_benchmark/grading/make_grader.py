"""Create the small, separate DSBench evaluation attachment."""
from pathlib import Path
import argparse
import json
import secrets
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ['common.py','model.py','simulate.py','evaluate.py','local_asic.py','commercial.py']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--calibration')
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    reference = None
    if args.calibration:
        reference = Path(args.calibration).resolve()
        if json.loads(reference.read_text()).get('backend') != 'commercial':
            raise SystemExit('DSBench grading needs a commercial calibration; local references are for local experiments.')
        shutil.copy2(reference, out/'area_reference.json')
    settings = out/'settings.json'
    if not settings.exists():
        settings.write_text(json.dumps(dict(seed=secrets.randbits(48),scale=3))+'\n')
    attachment = out/'fft64_grader.zip'
    with zipfile.ZipFile(attachment, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in TOOLS:
            archive.write(ROOT/'tools'/name, 'fft64_grader/tools/'+name)
        for path in (ROOT/'flow').glob('*'):
            if path.is_file():
                archive.write(path, 'fft64_grader/flow/'+path.name)
        archive.write(ROOT/'SPEC.json','fft64_grader/SPEC.json')
        archive.write(settings,'fft64_grader/settings.json')
    shutil.copy2(ROOT/'grading/test_by_code.py',out/'test_by_code.py')
    total = attachment.stat().st_size+(reference.stat().st_size if reference else 0)
    if total >= 1_000_000:
        raise SystemExit('Evaluation attachment exceeds 1 MB')
    print(json.dumps(dict(attachment=str(attachment),attachment_bytes=total,
                         commercial_calibration_included=bool(reference)),indent=2))

if __name__=='__main__':
    main()
