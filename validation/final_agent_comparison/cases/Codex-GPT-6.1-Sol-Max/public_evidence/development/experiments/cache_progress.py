from pathlib import Path
import json,hashlib
base=Path.cwd();bench=base/'fft64_benchmark';shared=base.parent/'Synopsys'
# Compute the documented physical-cache key for THIS candidate only.
env=json.loads((base/'runs/synopsys_20261122_184541_287142/environment.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
data=dict(files={f:sha(bench/f)for f in ['flow/synth_dc.tcl','flow/constraints.sdc','flow/timing_pt.tcl','flow/paths.tcl','flow/templates/dc_opt.tcl']},libraries={Path(p).name:v for p,v in env['libraries_sha256'].items()},tools={name:dict(path=env['tools'][name],sha256=env['tools_sha256'][name])for name in ['dc_shell','pt_shell']},clock_period_ns=10.0,independent_import_measurement=True)
physical=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
for name in ['area_F002','arch_F003','area_F004','arch_S001']:
 d=base/'runs'/name
 if not (d/'source.json').exists():continue
 source=json.loads((d/'source.json').read_text())['source_sha256']
 key=hashlib.sha256(json.dumps(dict(source=source,physical=physical,formal=False,imported_sha256=None),sort_keys=True).encode()).hexdigest()[:24]
 c=shared/'.fft64/physical_cache'/key
 print(name,key)
 if (d/'checkpoint.json').exists():print((d/'checkpoint.json').read_text())
 if (c/'dc.log').exists():print('\n'.join((c/'dc.log').read_text().splitlines()[-12:]))
 for f in ['dc_metrics.json','pt_metrics.json']:
  if (c/f).exists():print(f,(c/f).read_text())
