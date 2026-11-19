"""One fixed VCS/DC/PrimeTime scoring flow for submissions from any platform."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import csv
import datetime
import hashlib
import json
import re
import secrets
import shutil
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT/'fft64_benchmark'
sys.path.insert(0, str(BENCHMARK/'tools'))
from common import TECH,read, save, sha, lock, flow_identity
from toolchain import prepare


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def inputs(args):
    entries = []
    if args.manifest:
        path = Path(args.manifest).resolve()
        with path.open(newline='') as stream:
            for row in csv.DictReader(stream):
                submission = Path(row['submission'])
                entries.append(dict(id=row['id'], submission=str((path.parent/submission).resolve()),
                                    origin=row.get('origin','unspecified'), agent=row.get('agent','unspecified')))
    elif args.batch:
        for path in sorted(Path(args.batch).resolve().iterdir()):
            if path.is_dir() and ((path/'rtl').is_dir() or (path/'design_config.json').exists()):
                entries.append(dict(id=path.name, submission=str(path), origin=args.origin, agent=args.agent))
    elif args.submission:
        path = Path(args.submission).resolve()
        entries.append(dict(id=args.id or path.name, submission=str(path), origin=args.origin, agent=args.agent))
    if not entries and not args.check_only:
        raise ValueError('Provide a submission directory, --batch DIR, or --manifest CSV')
    names = set()
    for entry in entries:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}',entry['id']) or entry['id'] in names:
            raise ValueError('Submission IDs must be distinct safe names: '+entry['id'])
        if not Path(entry['submission']).is_dir():
            raise ValueError('Submission directory does not exist: '+entry['submission'])
        names.add(entry['id'])
    return entries


def protocol(args, state):
    definition = dict(benchmark_id=read(BENCHMARK/'SPEC.json')['benchmark_id'],
                      specification_sha256=sha(BENCHMARK/'SPEC.json'),
                      data_generator_sha256=sha(BENCHMARK/'tools/model.py'))
    if args.protocol:
        result = read(Path(args.protocol).resolve())
    elif args.seed is not None:
        result = dict(**definition, seed=args.seed, scale=args.scale)
    else:
        with lock(state/'protocol.lock'):
            path = state/'evaluation_protocol.json'
            if not path.exists():
                save(path,dict(**definition,seed=secrets.randbits(48),scale=args.scale))
            result = read(path)
    if any(result.get(key) != value for key,value in definition.items()):
        raise ValueError('Evaluation protocol uses another specification/data generator; choose a matching protocol or a new state directory')
    if type(result.get('seed')) is not int or type(result.get('scale')) is not int or result['scale'] < 1:
        raise ValueError('Protocol needs an integer seed and a positive integer scale')
    return result


def platform_identity(environment):
    from evaluate import assemble
    tools={name:dict(path=environment['tools'][name],sha256=sha(environment['tools'][name]))
           for name in ['vcs','dc_shell','pt_shell']}
    files={name:sha(BENCHMARK/'tools'/name)for name in
           ['evaluate.py','model.py','simulate.py','common.py','toolchain.py','commercial.py']}
    baselines={name:assemble(ROOT/'operator/baselines'/name)[1]['source_sha256']for name in ['sdf','iterative']}
    return dict(backend='commercial',flow_id=flow_identity('commercial'),tools=tools,
                evaluator_files=files,baseline_source_sha256=baselines,
                runner_sha256=sha(__file__))


def infrastructure_failure(result):
    if result.get('status') == 'ENVIRONMENT_ERROR':
        return True
    message = result.get('failure','')+'\n'+result.get('traceback','')
    return bool(re.search(r'license (?:checkout|check.?out|server|manager)|no valid license|licensing error|'
                          r'unable to (?:obtain|check out).*license|cannot (?:obtain|checkout).*license|'
                          r'FLEXnet|SNPSLMD_LICENSE_FILE|TimeoutExpired',message,re.I))


def cached_evaluate(submission, directory, settings, calibration=None, formal=False):
    from evaluate import evaluate, score_result
    path=directory/'result.json'
    if path.exists():
        result=read(path)
        if result.get('status') in {'COMPLETE','QUALITY_FAILED','FAILED'} and not infrastructure_failure(result):
            result['grade']=score_result(result,calibration)
            return result,True
    result=evaluate(submission,directory,'commercial',seed=settings['seed'],scale=settings['scale'],
                    calibration=calibration,formal=formal)
    return result,False


def calibration(args,state,identity,settings,location=None):
    fingerprint=digest(identity)
    key=digest(dict(platform=fingerprint,protocol=settings))[:24]
    directory=state/'calibration'/key
    if location:save(location,dict(directory=str(directory)))
    with lock(directory/'lock'):
        if args.calibration:
            reference=read(Path(args.calibration).resolve())
        elif (directory/'calibration.json').exists():
            reference=read(directory/'calibration.json')
        else:
            results={}
            for name in ['sdf','iterative']:
                result,reused=cached_evaluate(ROOT/'operator/baselines'/name,directory/name,settings)
                results[name]=result
                if result.get('status')!='COMPLETE' or not result.get('ppa',{}).get('timing_pass'):
                    save(directory/'status.json',dict(status='CALIBRATION_INCOMPLETE',baseline=name,result=result))
                    raise EnvironmentError('Accurate '+name+' calibration did not finish successfully; see '+str(directory/name/'result.json'))
            reference=dict(backend='commercial',flow_id=identity['flow_id'],platform_fingerprint=fingerprint,
                           protocol_fingerprint=digest(settings),reference_area_um2=min(r['ppa']['area_um2']for r in results.values()),
                           pass_area_ratio=read(BENCHMARK/'SPEC.json')['hardware']['proposed_pass_area_ratio_max'],
                           score='fractional_area_saving',baseline_results=results,created_utc=utc())
            save(directory/'calibration.json',reference)
        expected=dict(backend='commercial',flow_id=identity['flow_id'],platform_fingerprint=fingerprint,
                      protocol_fingerprint=digest(settings))
        if any(reference.get(key)!=value for key,value in expected.items()):
            raise EnvironmentError('Calibration does not match this Synopsys environment/protocol; omit --calibration to measure a matching reference')
        return reference,directory


def worker(entry,outdir,settings,reference,identity,formal):
    from evaluate import assemble
    directory=Path(outdir)/'candidates'/entry['id']
    source=None
    try:
        source,info=assemble(entry['submission'])
        source_key=info['source_sha256']
    except Exception as exc:
        source_key=digest(dict(submission=entry['submission'],error=str(exc)))
    key=digest(dict(source=source_key,protocol=settings,platform=digest(identity),formal=formal))[:24]
    run=directory/'runs'/key
    evaluated_source=entry['submission']
    if source is not None:
        snapshot=run/'submission'
        (snapshot/'rtl').mkdir(parents=True,exist_ok=True)
        (snapshot/'rtl/fft64_top.sv').write_text(source)
        save(snapshot/'design_config.json',dict(top='fft64_top',rtl=['rtl/fft64_top.sv']))
        save(run/'original_source.json',info)
        evaluated_source=snapshot
    result,reused=cached_evaluate(evaluated_source,run,settings,reference,formal)
    unavailable=infrastructure_failure(result)
    grade=result['grade']
    code=dict(resolved=False,score=0.0,reason='Environment error; no valid score: '+result.get('failure',''))if unavailable else {k:grade[k]for k in ['resolved','score','reason']}
    save(directory/'code_result.json',code)
    save(directory/'latest.json',dict(directory=str(run),reused=reused))
    quality=result.get('quality',{});ppa=result.get('ppa',{});lat=result.get('latency',{})
    first=max(lat.get('first_output_latency_cycles',[]),default=None)
    last=max(lat.get('frame_completion_cycles',[]),default=None)
    period=read(BENCHMARK/'SPEC.json')['timing_protocol']['clock_period_ns']
    row=dict(id=entry['id'],origin=entry['origin'],agent=entry['agent'],backend='commercial',
             state='UNSCORED_INFRASTRUCTURE'if unavailable else result['status'],resolved=code['resolved'],
             score=None if unavailable else code['score'],area_um2=ppa.get('area_um2'),
             area_ratio=grade.get('area_ratio'),worst_sqnr_db=quality.get('minimum_frame_sqnr_db'),
             worst_slack_ns=ppa.get('worst_setup_slack_ns'),timing_pass=ppa.get('timing_pass'),
             first_output_cycles=first,first_output_ns=first*period if first is not None else None,
             completion_cycles=last,completion_ns=last*period if last is not None else None,
             mapped_pass=result.get('mapped_simulation_pass'),
             reused=reused,result_directory=str(run),source_sha256=result.get('source',{}).get('source_sha256'))
    save(directory/'summary.json',row)
    return row,code


def feedback(out):
    archive=out.with_name(out.name+'_feedback.tar.gz')
    ignored={'obj','csrc','dc_work','simv.daidir','attempts','__pycache__'}
    with tarfile.open(archive,'w:gz')as tar:
        directories=[(out,Path(out.name))]
        if (out/'calibration_location.json').exists():
            directory=Path(read(out/'calibration_location.json')['directory'])
            if directory.is_dir():directories.append((directory,Path(out.name)/'calibration_diagnostics'))
        for directory,prefix in directories:
            for path in sorted(directory.rglob('*')):
                if path.is_file() and not any(p in ignored for p in path.parts) and path.name not in {'simv','lock','run.lock'}:
                    tar.add(path,arcname=str(prefix/path.relative_to(directory)),recursive=False)
    return archive


def execute(args):
    entries=inputs(args)
    stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
    out=Path(args.out or ROOT/'synopsys_results'/stamp).resolve();out.mkdir(parents=True,exist_ok=True)
    state=Path(args.state_dir or ROOT/'.eval_state').resolve()
    rows=[]
    with lock(out/'run.lock'):
        history=out/'history'/str(time.time_ns())
        for name in ['summary.json','scores.csv','code_result.json','protocol.json','platform_identity.json','calibration.json','calibration_location.json']:
            if (out/name).exists():
                history.mkdir(parents=True,exist_ok=True)
                shutil.move(str(out/name),str(history/name))
        save(out/'status.json',dict(status='PREPARING',started_utc=utc()))
        # This entry never selects local tools or builds an open-source EDA stack.
        environment=prepare('commercial',check_only=args.check_only,allow_build=False)
        save(out/'environment.json',environment)
        # Preparation can fail before calibration starts. Keep the actual
        # compiler output and argv receipt in the feedback archive as well.
        for name in ['library_compile.log','library_compile.log.json']:
            source=TECH/name
            if source.is_file():
                (out/'setup').mkdir(exist_ok=True)
                shutil.copy2(source,out/'setup'/name)
        if not environment['ready'] or args.check_only:
            status='ENVIRONMENT_READY'if environment['ready']else'ENVIRONMENT_NOT_READY'
            reason='Environment check only; no design was scored.'if environment['ready']else'Synopsys tools/libraries are not ready; see environment.json. No local fallback or valid score.'
            save(out/'status.json',dict(status=status,backend='commercial',reason=reason))
            save(out/'summary.json',dict(status=status,backend='commercial',submissions=[],reason=reason))
            save(out/'code_result.json',dict(resolved=False,score=0.0,reason=reason))
            print(json.dumps(dict(status=status,backend='commercial',output=str(out),feedback=str(feedback(out))),indent=2))
            return 0 if environment['ready'] else 2
        try:
            settings=protocol(args,state);save(out/'protocol.json',settings)
            identity=platform_identity(environment);save(out/'platform_identity.json',identity)
            save(out/'status.json',dict(status='CALIBRATING',backend='commercial',started_utc=utc()))
            reference,reference_dir=calibration(args,state,identity,settings,out/'calibration_location.json')
            save(out/'calibration.json',reference)
            save(out/'calibration_location.json',dict(directory=str(reference_dir)))
            tasks=[(entry,str(out),settings,reference,identity,args.formal)for entry in entries]
            if args.jobs==1:
                completed=(worker(*task)for task in tasks)
                for row,code in completed:
                    rows.append(row)
                    if len(entries)==1:save(out/'code_result.json',code)
                    save(out/'status.json',dict(status='RUNNING',completed=len(rows),total=len(entries)))
            else:
                with ProcessPoolExecutor(max_workers=args.jobs)as pool:
                    futures=[pool.submit(worker,*task)for task in tasks]
                    for future in as_completed(futures):
                        row,code=future.result();rows.append(row)
                        if len(entries)==1:save(out/'code_result.json',code)
                        save(out/'status.json',dict(status='RUNNING',completed=len(rows),total=len(entries)))
            rows.sort(key=lambda row:row['id'])
            with (out/'scores.csv').open('w',newline='')as stream:
                writer=csv.DictWriter(stream,list(rows[0]));writer.writeheader();writer.writerows(rows)
            status='PARTIAL_INFRASTRUCTURE_ERROR'if any(r['state']=='UNSCORED_INFRASTRUCTURE'for r in rows)else'COMPLETE'
            save(out/'summary.json',dict(status=status,backend='commercial',reference_area_um2=reference['reference_area_um2'],
                                        protocol=settings,submissions=rows))
            save(out/'status.json',dict(status=status,backend='commercial',completed=len(rows),total=len(entries),finished_utc=utc()))
            print(json.dumps(dict(status=status,backend='commercial',reference_area_um2=reference['reference_area_um2'],
                                  submissions=rows,feedback=str(feedback(out))),indent=2))
            return 2 if status!='COMPLETE'else 0
        except Exception as exc:
            save(out/'status.json',dict(status='INCOMPLETE',backend='commercial',failure=str(exc),finished_utc=utc()))
            save(out/'summary.json',dict(status='INCOMPLETE',backend='commercial',submissions=rows,failure=str(exc)))
            if len(entries)<=1:save(out/'code_result.json',dict(resolved=False,score=0.0,reason='Evaluation incomplete; no valid score: '+str(exc)))
            print(json.dumps(dict(status='INCOMPLETE',failure=str(exc),feedback=str(feedback(out))),indent=2))
            return 2


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('submission',nargs='?')
    parser.add_argument('--manifest',help='CSV: id,submission,origin,agent; paths relative to the CSV')
    parser.add_argument('--batch',help='Directory containing immediate submission subdirectories')
    parser.add_argument('--out')
    parser.add_argument('--state-dir',help='Shared calibration/protocol cache; default .eval_state/')
    parser.add_argument('--protocol',help='Frozen operator protocol JSON for cross-machine synchronization')
    parser.add_argument('--seed',type=int)
    parser.add_argument('--scale',type=int,default=3)
    parser.add_argument('--calibration',help='A calibration.json produced by this runner in the same environment')
    parser.add_argument('--jobs',type=int,default=1)
    parser.add_argument('--id')
    parser.add_argument('--origin',default='unspecified',help='For example open-source or synopsys')
    parser.add_argument('--agent',default='unspecified')
    parser.add_argument('--check-only',action='store_true')
    parser.add_argument('--formal',action='store_true')
    args=parser.parse_args()
    if sum(bool(x)for x in [args.submission,args.manifest,args.batch])>1:parser.error('Choose one input mode')
    if args.protocol and args.seed is not None:parser.error('Choose --protocol or --seed')
    if not 1<=args.jobs<=8 or args.scale<1:parser.error('jobs must be 1..8 and scale must be positive')
    try:return execute(args)
    except (ValueError,KeyError,FileNotFoundError)as exc:parser.error(str(exc))


if __name__=='__main__':
    sys.exit(main())
