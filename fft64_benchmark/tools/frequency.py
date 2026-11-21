"""Clock-scan certification on one fixed mapped ASIC netlist."""
from pathlib import Path
import csv
import hashlib
import json
import math
import os
import shutil
from common import ROOT,run,save,read,sha,lock
from scoring import profile_policy,POLICY_SHA256
from toolchain import find_tool


def validate_trials(endpoint,trials,settings):
    if endpoint.get('status')!='CERTIFIED' or not endpoint.get('hold_pass'):
        raise EnvironmentError('No passing setup/hold frequency endpoint')
    passing=endpoint['passing_period_ns'];failing=endpoint.get('failing_period_ns')
    for row in trials:
        for key in ['period_ns','actual_clock_period_ns','setup_slack_ns','hold_slack_ns']:
            if not math.isfinite(row[key]):raise EnvironmentError('Nonfinite STA scan measurement')
        if abs(row['period_ns']-row['actual_clock_period_ns'])>1e-6:
            raise EnvironmentError('STA scan did not apply the requested clock')
    point=[r for r in trials if abs(r['period_ns']-passing)<1e-8 and r['pass']]
    if not point or min(point[-1]['setup_slack_ns'],point[-1]['hold_slack_ns'])<0:
        raise EnvironmentError('Passing clock was not measured successfully')
    if endpoint.get('capped_at_minimum_period'):
        if failing is not None or abs(passing-settings['minimum_period_ns'])>1e-8:
            raise EnvironmentError('Invalid scan-cap endpoint')
    else:
        if(failing is None or failing>=passing
           or passing-failing>settings['resolution_ns']+1e-9):
            raise EnvironmentError('Invalid passing/failing frequency bracket')
        bad=[r for r in trials if abs(r['period_ns']-failing)<1e-8 and r['setup_slack_ns']<0]
        if not bad:raise EnvironmentError('Failing endpoint has no measured setup violation')
    if len(trials)!=endpoint.get('trials'):raise EnvironmentError('Incomplete frequency scan trace')


def certify(asic,backend='commercial'):
    if backend=='local':
        from local_frequency import certify_local
        return certify_local(asic)
    from commercial import check_log
    asic=Path(asic).resolve()
    settings=profile_policy('architecture')['fmax_scan']
    pt=find_tool('pt_shell')
    if not pt:raise EnvironmentError('PrimeTime is required for official frequency certification')
    identity=dict(mapped_sha256=sha(asic/'mapped.v'),script_sha256=sha(ROOT/'flow/fmax_pt.tcl'),
                  pt_path=pt,pt_sha256=sha(pt),scan=settings,policy_sha256=POLICY_SHA256,
                  mapping_signature=read(asic/'signature.json'))
    key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:24]
    work=asic/'frequency_certificates'/key
    with lock(work/'lock'):
        if(work/'certificate.json').exists():return read(work/'certificate.json'),work
        shutil.copy2(asic/'mapped.v',work/'mapped.v')
        save(work/'identity.json',identity)
        keys=['FFT_WORK','FFT_TASK_ROOT','FFT_FMAX_MIN_PS','FFT_FMAX_MAX_PS','FFT_FMAX_TOL_PS','FFT_FMAX_ITERATIONS']
        previous={k:os.environ.get(k)for k in keys}
        os.environ.update(FFT_WORK=str(work),FFT_TASK_ROOT=str(ROOT),
                          FFT_FMAX_MIN_PS=str(settings['minimum_period_ns']*1000),
                          FFT_FMAX_MAX_PS=str(settings['maximum_period_ns']*1000),
                          FFT_FMAX_TOL_PS=str(settings['resolution_ns']*1000),
                          FFT_FMAX_ITERATIONS=str(settings['maximum_iterations']))
        try:
            run(['pt_shell','-f',ROOT/'flow/fmax_pt.tcl'],work/'fmax.log',600,cwd=work)
            check_log(work/'fmax.log')
            endpoint=read(work/'fmax_scan/endpoint.json')
            with(work/'fmax_scan/trials.csv').open(newline='')as stream:
                trials=[dict(trial=int(r['trial']),period_ns=float(r['period_ns']),
                             actual_clock_period_ns=float(r['actual_clock_period_ns']),
                             setup_slack_ns=float(r['setup_slack_ns']),hold_slack_ns=float(r['hold_slack_ns']),
                             **{'pass':r['pass']=='1'})for r in csv.DictReader(stream)]
            validate_trials(endpoint,trials,settings)
            check=(work/'fmax_scan/check_at_passing.rpt').read_text()
            if __import__('re').search(r'(?im)^\s*Warning:.*(?:unconstrained|no[_ ]clock|no[_ ]input[_ ]delay|no[_ ]output[_ ]delay)',check):
                raise EnvironmentError('Frequency scan has unconstrained paths')
            certificate=dict(endpoint,**identity,trial_trace_sha256=sha(work/'fmax_scan/trials.csv'),
                             certified_frequency_MHz=1000/endpoint['passing_period_ns'],
                             measurement='PrimeTime setup/hold passing endpoint on a fixed mapped netlist; pre-layout',
                             certificate_directory=str(work))
            save(work/'certificate.json',certificate)
            return certificate,work
        finally:
            for k,v in previous.items():
                if v is None:os.environ.pop(k,None)
                else:os.environ[k]=v
