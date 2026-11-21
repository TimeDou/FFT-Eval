"""Create the small, separate DSBench evaluation attachment."""
from pathlib import Path
import argparse
import hashlib
import json
import secrets
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ['common.py','model.py','simulate.py','evaluate.py','scoring.py','local_asic.py','commercial.py','toolchain.py','frequency.py','throughput.py','local_frequency.py']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--calibration')
    parser.add_argument('--profile',choices=['area','architecture'],default='architecture')
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    reference = None
    expected_settings=None
    if args.calibration:
        reference = Path(args.calibration).resolve()
        reference_data=json.loads(reference.read_text())
        if reference_data.get('backend') != 'commercial' or reference_data.get('profile')!=args.profile:
            raise SystemExit('DSBench grading needs a commercial calibration; local references are for local experiments.')
        policy_sha=hashlib.sha256((ROOT/'profiles/policy.json').read_bytes()).hexdigest()
        if reference_data.get('policy_sha256')!=policy_sha:
            raise SystemExit('Calibration uses another scoring policy; recalibrate before packaging.')
        protocol=reference_data.get('evaluation_protocol')
        if protocol is None:
            runs=reference_data.get('baseline_results',{}).values()
            pairs={(r.get('seed'),r.get('scale'))for r in runs}
            if len(pairs)==1:
                seed,scale=next(iter(pairs));protocol=dict(seed=seed,scale=scale)
        if not protocol or type(protocol.get('seed'))is not int or type(protocol.get('scale'))is not int or protocol['scale']<1:
            raise SystemExit('Calibration needs its original input seed/scale; generate it with the current operator or calibrate.py.')
        expected_settings=dict(seed=protocol['seed'],scale=protocol['scale'],profile=args.profile)
        shutil.copy2(reference, out/'area_reference.json')
    settings = out/'settings.json'
    if not settings.exists():
        settings.write_text(json.dumps(expected_settings or dict(seed=secrets.randbits(48),scale=3,profile=args.profile))+'\n')
    if json.loads(settings.read_text()).get('profile','area')!=args.profile:
        raise SystemExit('Existing settings belong to another profile; use a new output directory.')
    if expected_settings and json.loads(settings.read_text())!=expected_settings:
        raise SystemExit('Existing grader inputs differ from the calibrated protocol; use a new output directory.')
    attachment = out/'fft64_grader.zip'
    with zipfile.ZipFile(attachment, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in TOOLS:
            archive.write(ROOT/'tools'/name, 'fft64_grader/tools/'+name)
        for path in (ROOT/'flow').glob('*'):
            if path.is_file():
                archive.write(path, 'fft64_grader/flow/'+path.name)
        archive.write(ROOT/'SPEC.json','fft64_grader/SPEC.json')
        for name in ['policy.json','PRE_REGISTERED.json']:
            archive.write(ROOT/'profiles'/name,'fft64_grader/profiles/'+name)
        archive.write(settings,'fft64_grader/settings.json')
    shutil.copy2(ROOT/'grading/test_by_code.py',out/'test_by_code.py')
    total = attachment.stat().st_size+(reference.stat().st_size if reference else 0)
    if total >= 1_000_000:
        raise SystemExit('Evaluation attachment exceeds 1 MB')
    print(json.dumps(dict(attachment=str(attachment),attachment_bytes=total,
                         commercial_calibration_included=bool(reference)),indent=2))

if __name__=='__main__':
    main()
