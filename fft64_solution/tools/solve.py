"""Migrate and remeasure a compact author attempt against the new benchmark."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import lru_cache
import argparse
import hashlib
import json
import os
import shutil
import sys
import time

SOLUTION = Path(__file__).resolve().parents[1]
BENCHMARK = SOLUTION.with_name('fft64_benchmark')
sys.path.insert(0, str(BENCHMARK/'tools'))
from common import read, save, sha, flow_identity,lock
from evaluate import evaluate, score_result
from generate import emit
from tool_context import current as current_tool_context

CASES = {
    'accurate_sdf': dict(architecture='sdf'),
    'accurate_iterative': dict(architecture='folded'),
    'exact_banked': dict(architecture='folded', banked=True),
    'quantized_banked': dict(architecture='folded', banked=True, drop=1, twiddle=9),
    'pipelined_iterative': dict(architecture='folded', pipeline=True),
    'aggressive_quantization': dict(architecture='folded', banked=True, drop=2, twiddle=9),
}


@lru_cache(maxsize=1)
def execution_context():
    return current_tool_context()


def run_root():
    identity = {str(p.relative_to(BENCHMARK)): sha(p) for p in [
        BENCHMARK/'SPEC.json', *[BENCHMARK/'tools'/n for n in
        ['common.py','evaluate.py','simulate.py','model.py','local_asic.py']]]}
    identity['generate.py'] = sha(SOLUTION/'tools/generate.py')
    identity['solve.py'] = sha(__file__)
    identity['execution_tools'] = hashlib.sha256(json.dumps(execution_context(),sort_keys=True).encode()).hexdigest()
    tag = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:12]
    directory = SOLUTION/'results/runs'/tag
    directory.mkdir(parents=True, exist_ok=True)
    save(directory/'run_info.json', identity)
    save(directory/'toolchain.json',execution_context())
    return directory


def transfer(source,destination):
    """Publish a complete cache copy; /tmp and data disks may be different filesystems."""
    def link_or_copy(src,dst):
        try:os.link(src,dst)
        except OSError:shutil.copy2(src,dst)
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging=destination.with_name(destination.name+'.copy.'+str(time.time_ns()))
    shutil.copytree(source,staging,copy_function=link_or_copy)
    if destination.exists():
        history=destination.parent/'attempts';history.mkdir(exist_ok=True)
        destination.rename(history/(destination.name+'.'+str(time.time_ns())))
    staging.rename(destination)


def reuse(relative, directory, source, seed, scale):
    previous = directory/'result.json'
    if previous.exists():
        result = read(previous)
        if (result['status'] in {'COMPLETE','QUALITY_FAILED'} and result.get('seed')==seed
                and result.get('scale')==scale and result.get('source',{}).get('source_sha256')==sha(source)):
            return result
    # A generator fix to one design need not rerun unrelated measured designs.
    # Reuse only the same source, test driver, metric and hardware setup.
    current=read(run_root()/'run_info.json')
    for earlier in sorted((SOLUTION/'results/runs').iterdir(),key=lambda p:p.stat().st_mtime,reverse=True):
        if earlier==run_root() or not(earlier/'run_info.json').exists():continue
        prior=read(earlier/'run_info.json')
        if any(prior.get(key)!=value for key,value in current.items() if key not in {'generate.py','solve.py','execution_tools'}):continue
        if not(earlier/'toolchain.json').exists()or read(earlier/'toolchain.json')!=execution_context():continue
        stored=earlier/relative
        if not(stored/'result.json').exists():continue
        result=read(stored/'result.json')
        if result['status']not in {'COMPLETE','QUALITY_FAILED'}:continue
        if result.get('seed')!=seed or result.get('scale')!=scale:continue
        if result['source']['source_sha256']!=sha(source):continue
        if result['status']=='COMPLETE':
            signature=read(stored/'asic/signature.json')
            context=execution_context()
            expected={key:context['tools'][key]['sha256']for key in ['abc','sta','yosys']}
            expected.update(comb=context['libraries']['ASAP7_RVT_TT_nldm_NO_FAHA.lib'],
                            seq=context['libraries']['ASAP7_SEQ_RVT_TT_nldm_220123.lib'])
            if any(signature.get(key)!=value for key,value in expected.items()):continue
        transfer(stored,directory)
        save(directory/'reuse.json',dict(from_directory=str(stored.relative_to(SOLUTION)),reason='Same source, protocol, evaluator, tool binaries, libraries, Python and NumPy.'))
        return result
    return None


def case(name):
    directory = run_root()/'development'/name
    result=reuse(Path('development')/name,directory,SOLUTION/'candidates'/name/'rtl/fft64_top.sv',20261118,2)
    if result is not None:return name,result
    result = evaluate(SOLUTION/'candidates'/name, directory, 'local', seed=20261118, scale=2)
    return name, result


def run_search():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--holdout', action='store_true')
    args = parser.parse_args()
    run = run_root()
    for name, configuration in CASES.items():
        directory = SOLUTION/'candidates'/name
        emit(configuration, directory)
        (directory/'DESIGN_PLAN.md').write_text(f'# Candidate: {name}\n\nConfiguration: `{json.dumps(configuration)}`.\n\nMeasured with the common FFT64 evaluator; results are collected by tools/report.py.\n')
        (directory/'measurements.csv').write_text('id,status\n'+name+',PENDING\n')
    save(SOLUTION/'results/status.json', dict(status='RUNNING', run=str(run),run_relative=str(run.relative_to(SOLUTION)), total=len(CASES), completed=0))
    results = {}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(case, name) for name in CASES]):
            name, result = future.result()
            results[name] = result
            save(run/'development.json', results)
            save(SOLUTION/'results/status.json', dict(status='RUNNING', run=str(run),run_relative=str(run.relative_to(SOLUTION)), total=len(CASES), completed=len(results)))
            print(name, result['status'], result.get('quality',{}).get('minimum_frame_sqnr_db'), result.get('ppa',{}).get('area_um2'), flush=True)
    accurate = [results[name] for name in ['accurate_sdf','accurate_iterative']]
    if not all(r['status']=='COMPLETE' and r['ppa']['timing_pass'] for r in accurate):
        save(SOLUTION/'results/status.json',dict(status='NEEDS_BASELINE_FIX',run=str(run),run_relative=str(run.relative_to(SOLUTION)),completed=len(results),total=len(CASES)))
        raise RuntimeError('An accurate baseline needs attention; completed results are retained')
    calibration = dict(benchmark_id='fft64_quant_arch_v0.2', backend='local', flow_id=flow_identity('local'),
                       reference_area_um2=min(r['ppa']['area_um2'] for r in accurate),
                       pass_area_ratio=.8, score='fractional_area_saving')
    save(SOLUTION/'results/local_area_reference.json', calibration)
    for name, result in results.items():
        result['grade'] = score_result(result, calibration)
        save(run/'development'/name/'result.json', result)
    save(run/'development.json', results)
    feasible = {name:r for name,r in results.items() if r['status']=='COMPLETE' and r['ppa']['timing_pass']}
    chosen = min(feasible, key=lambda name: feasible[name]['ppa']['area_um2'])
    emit(CASES[chosen], SOLUTION)
    freeze = dict(selected=chosen, config=CASES[chosen], source_sha256=sha(SOLUTION/'rtl/fft64_top.sv'),
                  validation_seeds=[2026111911,2026111912], scale=3)
    frozen_path = SOLUTION/'results/selected.json'
    if frozen_path.exists():
        assert read(frozen_path)==freeze, 'Retain the previous selection and use a new solution version for a changed candidate'
    else:
        save(frozen_path, freeze)
    validation = []
    if args.holdout:
        for seed in freeze['validation_seeds']:
            directory = run/'validation'/str(seed)
            result=reuse(Path('validation')/str(seed),directory,SOLUTION/'rtl/fft64_top.sv',seed,3)
            if result is not None:
                result['grade']=score_result(result,calibration)
                save(directory/'result.json',result)
                validation.append(result);save(run/'validation.json',validation)
                print('VALIDATION',seed,result['status'],'reused matching measurement',flush=True)
                assert result['grade']['resolved']
                continue
            if not(directory/'asic').exists():
                directory.mkdir(parents=True,exist_ok=True)
                transfer(run/'development'/chosen/'asic',directory/'asic')
            if (directory/'result.json').exists() and read(directory/'result.json')['status']=='COMPLETE':
                result=read(directory/'result.json')
            else:
                result=evaluate(SOLUTION,directory,'local',seed=seed,scale=3,calibration=calibration)
            validation.append(result)
            save(run/'validation.json', validation)
            print('VALIDATION',seed,result['status'],result.get('quality'),flush=True)
            assert result['grade']['resolved'], 'Validation did not pass; retain and diagnose the failure'
    save(SOLUTION/'results/status.json',dict(status='COMPLETE_LOCAL' if args.holdout else 'DEVELOPMENT_COMPLETE',
         run=str(run),run_relative=str(run.relative_to(SOLUTION)),selected=chosen,development_cases=len(results),validation_groups=len(validation),
         commercial='NOT_RUN',pnr='NOT_RUN'))


def main():
    with lock(SOLUTION/'results/search.lock'):run_search()


if __name__=='__main__':main()
