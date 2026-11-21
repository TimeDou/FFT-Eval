#!/usr/bin/env python3
"""Check output integer codes; RTL, protocol and PPA use run_preview.sh."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from model import quality
from numeric_io import input_frames, samples

def check(inputs, outputs):
    names, frames = input_frames(inputs)
    entries = outputs.get('frames')
    if not isinstance(entries, list) or len(entries) != len(names):
        raise ValueError('Output frames are missing or extra')
    table = {}
    for item in entries:
        if item['id'] in table:
            raise ValueError('Duplicate output frame ID')
        table[item['id']] = samples(item.get('outputs_iq'), -(1 << 23), (1 << 23)-1)
    if set(table) != set(names):
        raise ValueError('Output frame IDs differ from the input IDs')
    result = quality(frames, np.asarray([table[name] for name in names]))
    result['failed_ids'] = [names[i] for i in result['failed_frames']]
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--outputs', required=True)
    args = parser.parse_args()
    try:
        result = check(json.loads(Path(args.inputs).read_text()), json.loads(Path(args.outputs).read_text()))
    except (ValueError, KeyError, TypeError) as exc:
        print(json.dumps(dict(feasible=False, failure=str(exc))))
        return 1
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result['feasible'] else 1

if __name__ == '__main__':
    sys.exit(main())
