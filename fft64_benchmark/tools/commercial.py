"""Exported commercial backend. Execution status is separate from local evidence."""
from pathlib import Path
import math,os,re,time,subprocess,shutil,hashlib,json
from common import ROOT,TECH,COMB,SEQ,run,read,save,sha,lock,flow_identity
from toolchain import activate,find_tool

def preflight(require_db=True):
 tools=activate()
 cmds=['vcs','dc_shell','pt_shell']
 return dict(commands={x:tools[x]for x in cmds},libraries={str(x):x.exists()for x in [COMB,SEQ]},compiled_db={str(x):x.exists()for x in [TECH/'db/comb_rvt_tt.db',TECH/'db/seq_rvt_tt.db']},ready=all(tools[x]for x in cmds)and all(x.exists()for x in [COMB,SEQ])and(not require_db or all(x.exists()for x in [TECH/'db/comb_rvt_tt.db',TECH/'db/seq_rvt_tt.db'])))

def check_log(path):
 # A Synopsys batch process can exit zero after reporting script errors.
 errors=re.findall(r'^\s*(?:Error:|Fatal:|TASK_FATAL)[^\n]*',path.read_text(),re.M)
 if errors:raise RuntimeError(str(path)+'\n'+'\n'.join(errors[:8]))

def checked_metrics(path,kind):
 try:metrics=read(path)
 except (OSError,ValueError) as exc:raise RuntimeError('Missing or malformed '+kind+' metrics: '+str(path))from exc
 fields=['area_um2','register_area_um2']if kind=='DC'else['worst_setup_slack_ns','worst_hold_slack_ns','clock_period_ns']
 if not isinstance(metrics,dict):raise RuntimeError('Invalid '+kind+' metrics object: '+str(path))
 for field in fields:
  value=metrics.get(field)
  if type(value)not in (int,float)or not math.isfinite(value):
   raise RuntimeError('Invalid '+kind+' metric '+field+': '+str(path))
 if kind=='DC':
  if(metrics['area_um2']<=0 or not 0<=metrics['register_area_um2']<=metrics['area_um2']
     or type(metrics.get('cells'))is not int or metrics['cells']<=0):
   raise RuntimeError('Invalid DC mapped area/count: '+str(path))
 elif metrics['clock_period_ns']<=0:
  raise RuntimeError('Invalid PT required period: '+str(path))
 return metrics

def mapping_identity():
 files=['flow/synth_dc.tcl','flow/constraints.sdc','flow/timing_pt.tcl','flow/paths.tcl']
 libraries=[COMB,SEQ,TECH/'db/comb_rvt_tt.db',TECH/'db/seq_rvt_tt.db']
 tools={name:find_tool(name)for name in ['dc_shell','pt_shell']}
 if not all(tools.values()):raise EnvironmentError('DC/PT mapping environment is unavailable')
 data=dict(files={f:sha(ROOT/f)for f in files},libraries={p.name:sha(p)for p in libraries},
           tools={name:dict(path=p,sha256=sha(p))for name,p in tools.items()},clock_period_ns=10.0,hold_repair=True)
 return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()

def measure(source,outdir,formal=False):
 destination=Path(outdir).resolve()
 physical=mapping_identity()
 cache=os.environ.get('FFT_PHYSICAL_CACHE_DIR')
 if not cache:return _measure(source,destination,formal,physical)
 key=hashlib.sha256(json.dumps(dict(source=hashlib.sha256(source.encode()).hexdigest(),physical=physical,formal=formal),sort_keys=True).encode()).hexdigest()[:24]
 canonical=Path(cache).resolve()/key
 result=_measure(source,canonical,formal,physical)
 if destination!=canonical:
  destination.mkdir(parents=True,exist_ok=True)
  with lock(destination/'publish.lock'):
   shutil.copytree(canonical,destination,dirs_exist_ok=True,
                   ignore=shutil.ignore_patterns('lock','publish.lock','dc_work','frequency_certificates'))
   save(destination/'physical_cache.json',dict(directory=str(canonical),key=key,physical_flow_id=physical))
 return result

def _measure(source,outdir,formal,physical):
 d=Path(outdir).resolve();d.mkdir(parents=True,exist_ok=True)
 check=preflight();save(d/'preflight.json',check)
 if not check['ready']:raise EnvironmentError('COMMERCIAL_ENVIRONMENT_NOT_READY: '+str(d/'preflight.json'))
 identity=physical
 sig=dict(source=__import__('hashlib').sha256(source.encode()).hexdigest(),comb=sha(COMB),seq=sha(SEQ),db=[sha(TECH/'db/comb_rvt_tt.db'),sha(TECH/'db/seq_rvt_tt.db')],flow='DC-PT-setup-hold-v3',identity=identity,formal=formal)
 with lock(d/'lock'):
  if(d/'signature.json').exists():assert read(d/'signature.json')==sig,'Changed tool/RTL/constraints require new build directory'
  else:save(d/'signature.json',sig)
  if(d/'metrics.json').exists():return read(d/'metrics.json')
  start=time.monotonic();(d/'staged.sv').write_text(source)
  # Only trusted flow scripts are executed. The submission cannot supply Tcl.
  old={k:os.environ.get(k)for k in ['FFT_WORK','FFT_TASK_ROOT','FFT_TECH_DIR']}
  os.environ.update(FFT_WORK=str(d),FFT_TASK_ROOT=str(ROOT),FFT_TECH_DIR=str(TECH))
  try:
   run(['dc_shell','-f',ROOT/'flow/synth_dc.tcl'],d/'dc.log',1800,cwd=d)
   check_log(d/'dc.log')
   area=checked_metrics(d/'dc_metrics.json','DC')
   run(['pt_shell','-f',ROOT/'flow/timing_pt.tcl'],d/'pt.log',600,cwd=d)
   check_log(d/'pt.log')
   timing=checked_metrics(d/'pt_metrics.json','PT')
   # Never silently interpret a differently normalized DB time unit as ps.
   for unitfile in [d/'dc_units.rpt',d/'pt_units.rpt']:
    units=unitfile.read_text()
    if not re.search(r'Time[^\n]*(?:1(?:\.0+)?\s*ps|1(?:\.0+)?e-12)',units,re.I):
     raise EnvironmentError('TIME_UNIT_REVIEW_REQUIRED: expected1ps; inspect '+str(unitfile))
   for unitfile in [d/'dc_units.rpt',d/'pt_units.rpt']:
    units=unitfile.read_text()
    if not re.search(r'Capacit[^\n]*(?:1(?:\.0+)?\s*ff|1(?:\.0+)?e-15)',units,re.I):
     raise EnvironmentError('CAPACITANCE_UNIT_REVIEW_REQUIRED: expected1fF; inspect '+str(unitfile))
   check_text=(d/'pt_check.rpt').read_text()
   if re.search(r'(?im)^\s*Warning:.*(?:unconstrained|no[_ ]clock|no[_ ]input[_ ]delay|no[_ ]output[_ ]delay)',check_text):
    raise EnvironmentError('TIMING_CONSTRAINT_REVIEW_REQUIRED: inspect pt_check.rpt')
   out={**area,**timing,**dict(timing_pass=timing['worst_setup_slack_ns']>=0 and timing['worst_hold_slack_ns']>=0,
        source_sha256=sig['source'],mapped_sha256=sha(d/'mapped.v'),mapping_wall_seconds=time.monotonic()-start,
        library_hashes=sig['db'],physical_flow_id=identity)}
   if formal:
    if not shutil.which('fm_shell'):out['formal_status']='NOT_AVAILABLE'
    else:
     try:
      run(['fm_shell','-file',ROOT/'flow/formality.tcl'],d/'fm.log',1200,cwd=d)
      out['formal_status']=(d/'fm_status.txt').read_text().strip()
     except Exception as e:out['formal_status']='FAILED'if(d/'fm_status.txt').exists()and(d/'fm_status.txt').read_text().strip()=='FAILED'else'INCONCLUSIVE_TOOL';out['formal_reason']=str(e)[:600]
   else:out['formal_status']='NOT_REQUESTED; mapped simulation still mandatory'
   save(d/'metrics.json',out);return out
  finally:
   for k,v in old.items():
    if v is None:os.environ.pop(k,None)
    else:os.environ[k]=v
