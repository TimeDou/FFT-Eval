"""Measure operator-supplied accurate implementations and write an area reference."""
from pathlib import Path
import argparse
import json
import sys
from common import save
from evaluate import evaluate
from scoring import make_calibration

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', action='append', required=True)
    parser.add_argument('--backend', choices=['auto', 'local', 'commercial'], default='auto')
    parser.add_argument('--out', required=True)
    parser.add_argument('--profile',choices=['area','architecture'],default='area')
    args = parser.parse_args()
    directory = Path(args.out).resolve()
    results = [evaluate(path, directory/f'baseline_{i}', args.backend, seed=20261118,profile=args.profile,auto_ii=args.profile=='architecture')
               for i, path in enumerate(args.baseline)]
    valid = all(r['status'] == 'COMPLETE' and r['ppa']['timing_pass'] for r in results)
    valid = valid and len({r.get('backend') for r in results}) == 1 and len({r.get('flow_id') for r in results}) == 1
    save(directory/'calibration_runs.json', results)
    if not valid:
        print('Calibration incomplete. See '+str(directory/'calibration_runs.json'))
        return 2
    reference = make_calibration({str(i):r for i,r in enumerate(results)},profile=args.profile,
                     benchmark_id='fft64_quant_arch_v0.4',
                     baselines=[dict(path=str(Path(p).resolve()), source=r['source'],
                                     area_um2=r['ppa']['area_um2']) for p, r in zip(args.baseline, results)])
    save(directory/'area_reference.json', reference)
    print(json.dumps(reference, indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())
