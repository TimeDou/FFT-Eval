import argparse
import json
import shutil
from common import COMB, SEQ

parser = argparse.ArgumentParser()
parser.add_argument('--backend', choices=['commercial', 'local'], default='commercial')
args = parser.parse_args()
if args.backend == 'commercial':
    from commercial import preflight
    result = preflight()
else:
    from local_asic import ABC, STA
    paths = {name: shutil.which(name) for name in ['yosys', 'iverilog', 'vvp', 'verilator']}
    paths.update(ABC=str(ABC), OpenSTA=str(STA))
    result = dict(commands=paths, ready=all(paths.values()) and ABC.is_file() and STA.is_file()
                  and COMB.is_file() and SEQ.is_file())
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['ready'] else 2)
