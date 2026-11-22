"""Collect compact measurement evidence without removing original experiment data."""
from pathlib import Path
import gzip,hashlib,json,shutil,sys

ROOT=Path(__file__).resolve().parent


def copy(source,destination):
    source=Path(source);destination=Path(destination)
    if not source.is_file():return
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,destination)


def main():
    target=Path(sys.argv[1]);target.mkdir(parents=True,exist_ok=True)
    campaign=json.loads((ROOT/'campaign.json').read_text())
    if json.loads((ROOT/'status.json').read_text())['status']!='COMPLETE':raise RuntimeError('Wait for completed campaign')
    for name in ['campaign.json','supplementary_cases.json','calibration.json','summary.json','status.json','environment.json',
                 'execution_source_manifest.json','frequency_prefetch.json','exact_family_comparison.json','resource_monitor.json']:
        copy(ROOT/name,target/name)
    for name in ['driver.py','worker.py','supplementary_worker.py','generate.py','analyze.py','collect_numeric.py','prefetch_frequency.py','publish_results.py']:
        copy(ROOT/name,target/'scripts'/name)
    for p in (ROOT/'analysis').glob('*'):
        if p.is_file():copy(p,target/'analysis'/p.name)
    for p in (ROOT/'numeric_evidence').glob('*'):
        if p.is_file():copy(p,target/'numeric_evidence'/p.name)
    cases=[dict(c,measurement=ROOT/'measurements'/c['id'],submission=ROOT/'submissions'/c['id'])for c in campaign['cases']]
    extra=json.loads((ROOT/'supplementary_cases.json').read_text())
    cases.extend(dict(c,measurement=ROOT/'supplementary'/c['id']/'measurement',submission=ROOT/'supplementary'/c['id']/'submission')for c in extra['cases'])
    for c in cases:
        case_target=target/'cases'/c['id'];measurement=c['measurement']
        result=json.loads((measurement/'result.json').read_text())
        grade=json.loads((ROOT/'analysis'/(c['id']+'_grade.json')).read_text())
        if not grade['score_valid']:raise RuntimeError('Do not publish infrastructure error as scored result: '+c['id'])
        copy(measurement/'result.json',case_target/'measurement/result.json')
        (case_target/'code_result.json').parent.mkdir(parents=True,exist_ok=True)
        (case_target/'code_result.json').write_text(json.dumps({k:grade[k]for k in ['resolved','score','reason']},indent=2)+'\n')
        for p in c['submission'].rglob('*'):
            if p.is_file()and '__pycache__'not in p.parts:copy(p,case_target/'submission'/p.relative_to(c['submission']))
        for name in ['source.json','dataset.json','per_frame_quality.json','environment.json','submission_completeness.json','worker_resources.json']:
            copy(measurement/name,case_target/'measurement'/name)
        for directory in ['asic','rtl_sim','mandatory_service','mapped_reference_rtl','mapped_sim']:
            source=measurement/directory
            if not source.exists():continue
            for p in source.rglob('*'):
                if not p.is_file():continue
                if any(x in p.parts for x in ['dc_work','csrc','simv.daidir','obj']):continue
                if p.name in ['mapped.ddc','simv','vectors.txt','output.txt','staged.sv','source.sv','tb.sv','lock','publish.lock']:continue
                if p.suffix in ['.json','.rpt','.log','.csv','.sdc','.tcl']or p.name in ['mapped.v','input_mapped.v']:
                    # One mapped netlist per ASIC is enough; the frequency
                    # certificate binds its unchanged hash.
                    if p.name=='mapped.v'and 'frequency_certificates'in p.parts:continue
                    copy(p,case_target/'measurement'/p.relative_to(measurement))
        throughput=measurement/'throughput'
        if throughput.exists():
            for p in throughput.iterdir():
                if p.is_file()and p.suffix=='.json':copy(p,case_target/'measurement/throughput'/p.name)
            subset=throughput/'mapped_subset'
            if subset.exists():
                for p in subset.rglob('*'):
                    if p.is_file()and p.suffix in ['.json','.log']and not any(x in p.parts for x in ['csrc','simv.daidir']):
                        copy(p,case_target/'measurement/throughput/mapped_subset'/p.relative_to(subset))
    for source in (ROOT/'rtl_capacity_cache').iterdir():
        if not source.is_dir():continue
        directory=target/'capacity'/source.name
        for p in source.rglob('*'):
            if not p.is_file()or any(x in p.parts for x in ['csrc','simv.daidir']):continue
            if p.name in ['source.sv','tb.sv','vectors.txt','output.txt','simv','lock']:continue
            if p.suffix in ['.json','.log','.csv','.npz']:copy(p,directory/p.relative_to(source))
    for name in ['abc_default','abc_resyn2']:
        build=ROOT/'supplementary'/name/'build'
        for p in build.rglob('*'):
            if p.is_file()and p.name in ['build_identity.json','build_result.json','yosys_build.log','yosys_build.log.json','build.ys','abc_opt.script','abc.constr']:
                copy(p,target/'construction'/name/p.relative_to(build))
    build=ROOT/'builds/timing2ns_folded'
    for p in build.rglob('*'):
        if p.is_file()and p.name in ['build_identity.json','build_result.json','dc_build.log','dc_build.log.json','build_area.rpt','build_timing.rpt']:
            copy(p,target/'construction/timing2ns_folded'/p.relative_to(build))
    cleanup=Path(Path('/tmp/fft_cleanup_path.txt').read_text().strip())
    for name in ['README.md','status.json','preservation_check.json']:
        copy(cleanup/name,target/'cleanup'/name)
    for name in ['plan.json','receipts.jsonl']:
        destination=target/'cleanup'/(name+'.gz');destination.parent.mkdir(exist_ok=True)
        with(cleanup/name).open('rb')as source,gzip.open(destination,'wb',compresslevel=6)as output:shutil.copyfileobj(source,output)
    files={str(p.relative_to(target)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in target.rglob('*')if p.is_file()and p.name!='FILE_MANIFEST.json'}
    (target/'FILE_MANIFEST.json').write_text(json.dumps(dict(source_commit=campaign['source_commit'],policy_sha256=campaign['policy_sha256'],
        raw_experiment_directory=str(ROOT),scope='Compact actual measurements, numeric outputs, mapped netlists, tool reports and full capacity summaries; raw clock-by-clock text remains in the original experiment directory',files=files),indent=2)+'\n')
    print('Evidence:',target,'files',len(files),'bytes',sum(v['bytes']for v in files.values()))


if __name__=='__main__':main()
