"""Inspect or prepare the installed EDA toolchain without importing NumPy."""
import argparse
import json
import os
import sys
from common import read, save
from toolchain import prepare, write_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', choices=['auto', 'commercial', 'local'], default='auto')
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--no-build', action='store_true')
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--calibration')
    parser.add_argument('--report')
    parser.add_argument('--env-file')
    args = parser.parse_args()
    calibration = read(args.calibration) if args.calibration else None
    report = prepare(args.backend, quick=args.quick, check_only=args.check_only,
                     allow_build=not args.no_build and os.environ.get('FFT_NO_BUILD')!='1', calibration=calibration)
    if args.report:
        save(args.report, report)
    if args.env_file and report['ready']:
        write_environment(args.env_file, report)
    print(json.dumps(report, indent=2))
    return 0 if report['ready'] else 2


if __name__ == '__main__':
    sys.exit(main())
