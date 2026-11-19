"""Measure operator-supplied accurate implementations and write an area reference."""
from pathlib import Path
import argparse
import json
import sys
from common import save
from evaluate import evaluate

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', action='append', required=True)
    parser.add_argument('--backend', choices=['auto', 'local', 'commercial'], default='auto')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    directory = Path(args.out).resolve()
    results = [evaluate(path, directory/f'baseline_{i}', args.backend, seed=20261118)
               for i, path in enumerate(args.baseline)]
    valid = all(r['status'] == 'COMPLETE' and r['ppa']['timing_pass'] for r in results)
    valid = valid and len({r.get('backend') for r in results}) == 1 and len({r.get('flow_id') for r in results}) == 1
    save(directory/'calibration_runs.json', results)
    if not valid:
        print('Calibration incomplete. See '+str(directory/'calibration_runs.json'))
        return 2
    best = min(results, key=lambda r: r['ppa']['area_um2'])
    reference = dict(benchmark_id='fft64_quant_arch_v0.2', backend=best['backend'],
                     flow_id=best['flow_id'], reference_area_um2=best['ppa']['area_um2'],
                     pass_area_ratio=.8, score='fractional_area_saving',
                     baselines=[dict(path=str(Path(p).resolve()), source=r['source'],
                                     area_um2=r['ppa']['area_um2']) for p, r in zip(args.baseline, results)])
    save(directory/'area_reference.json', reference)
    print(json.dumps(reference, indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())
