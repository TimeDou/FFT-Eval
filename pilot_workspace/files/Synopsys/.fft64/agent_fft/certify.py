from pathlib import Path
import json,sys,os
work=Path(sys.argv[1]);sys.path.insert(0,str(work.parent.parent/'fft64_benchmark/tools'))
pre=json.loads((work/'preflight.json').read_text())
os.environ['FFT_TECH_DIR']=str(Path(next(iter(pre['libraries']))).parent)
from frequency import certify
c,d=certify(work,'commercial')
(work.parent/'agent_frequency_certificate.json').write_text(json.dumps(c,indent=2))
print(json.dumps({k:c[k] for k in ['status','passing_period_ns','failing_period_ns','certified_frequency_MHz','passing_setup_slack_ns','passing_hold_slack_ns']},indent=2))
