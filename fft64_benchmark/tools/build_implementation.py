"""Public optimization worker: editable native recipes, structural artifact export."""
from pathlib import Path
import argparse
import json
import os
import shutil
import sys
import time
from common import ROOT,TECH,COMB,SEQ,run,save,sha,read,lock,CacheIdentityError
from toolchain import activate,find_tool,prepare
from implementation import validate_structural,export_artifacts


def initialize(submission):
    directory=Path(submission)/'flow';directory.mkdir(parents=True,exist_ok=True)
    for name in ['dc_opt.tcl','yosys_opt.ys','abc_opt.script','pnr_opt.tcl']:
        target=directory/name
        if not target.exists():shutil.copy2(ROOT/'flow/templates'/name,target)
    return directory


def q(path):
    return '"'+str(path).replace('\\','\\\\').replace('"','\\"')+'"'


def build(submission,outdir,backend='commercial',abc_delay_ps=10000,timeout=1800):
    from evaluate import assemble
    activate();submission=Path(submission).resolve();out=Path(outdir).resolve();out.mkdir(parents=True,exist_ok=True)
    source,info=assemble(submission,include_implementation=False)
    names=['dc_opt.tcl']if backend=='commercial'else['yosys_opt.ys','abc_opt.script']
    tools=['dc_shell']if backend=='commercial'else['yosys','abc']
    selected={name:find_tool(name)for name in tools}
    if not all(selected.values()):raise EnvironmentError('Required build tools missing: '+str(selected))
    recipes={name:(submission/'flow'/name if (submission/'flow'/name).is_file()else ROOT/'flow/templates'/name)for name in names}
    custom={str(p.relative_to(submission/'flow')):sha(p)for p in sorted((submission/'flow').rglob('*'))if p.is_file()}if(submission/'flow').is_dir()else{}
    identity=dict(rtl_sha256=info['source_sha256'],backend=backend,abc_delay_ps=abc_delay_ps,
        recipes={name:sha(path)for name,path in recipes.items()},custom_files=custom,
        libraries={p.name:sha(p)for p in [COMB,SEQ]},
        tools={name:dict(path=path,sha256=sha(path))for name,path in selected.items()},
        worker_sha256=sha(__file__),dc_driver_sha256=sha(ROOT/'flow/build_dc.tcl'))
    with lock(out/'build.lock'):
        signature=out/'build_identity.json'
        if signature.exists()and read(signature)!=identity:raise CacheIdentityError('Build inputs changed; choose a new build output directory')
        save(signature,identity)
        artifact=out/'implementation';manifest=artifact/'manifest.json'
        if manifest.exists()and(artifact/'mapped.v').exists():
            cached=read(manifest)
            if cached.get('mapped_sha256')==sha(artifact/'mapped.v'):
                return dict(status='BUILT',reused=True,implementation=str(artifact),manifest=cached)
        started=time.monotonic();work=out/'build';work.mkdir(exist_ok=True)
        (work/'source.sv').write_text(source)
        recipe_dir=work/'flow'
        if(submission/'flow').is_dir():shutil.copytree(submission/'flow',recipe_dir,dirs_exist_ok=True)
        recipe_dir.mkdir(exist_ok=True)
        for name,path in recipes.items():shutil.copy2(path,recipe_dir/name)
        old={key:os.environ.get(key)for key in ['FFT_WORK','FFT_TASK_ROOT','FFT_TECH_DIR','FFT_AGENT_DC_RECIPE','FFT_MAPPED_OUTPUT']}
        os.environ.update(FFT_WORK=str(work),FFT_TASK_ROOT=str(ROOT),FFT_TECH_DIR=str(TECH),
            FFT_AGENT_DC_RECIPE=str(recipe_dir/'dc_opt.tcl'),FFT_MAPPED_OUTPUT=str(work/'mapped.v'))
        try:
            if backend=='commercial':
                run(['dc_shell','-f',ROOT/'flow/build_dc.tcl'],work/'dc_build.log',timeout,cwd=work)
                from commercial import check_log
                check_log(work/'dc_build.log')
            else:
                abc_text='\n'.join(line for line in (recipe_dir/'abc_opt.script').read_text().splitlines()if not line.lstrip().startswith('#'))+'\n'
                abc_text=abc_text.replace('{D}','-D '+format(abc_delay_ps,'g'))
                (work/'abc_opt.script').write_text(abc_text)
                (work/'abc.constr').write_text('set_driving_cell BUFx2_ASAP7_75t_R\nset_load 1\n')
                ys=f'read_liberty -lib {q(COMB)}\nread_liberty -lib {q(SEQ)}\nread_verilog -sv {q(work/"source.sv")}\n'
                ys+=(recipe_dir/'yosys_opt.ys').read_text()+'\n'
                ys+=f'dfflibmap -liberty {q(SEQ)}\nabc -exe {q(selected["abc"])} -liberty {q(COMB)} -constr abc.constr -D {abc_delay_ps} -script abc_opt.script\n'
                ys+=f'flatten\nclean\ncheck\nwrite_verilog -noattr -noexpr {q(work/"mapped.v")}\nstat\n'
                (work/'build.ys').write_text(ys)
                run(['yosys','-Q','-T','-s',work/'build.ys'],work/'yosys_build.log',timeout,cwd=work)
            mapped=validate_structural((work/'mapped.v').read_text())
            artifact.mkdir(exist_ok=True);(artifact/'mapped.v').write_text(mapped)
            provenance=dict(rtl_sha256=info['source_sha256'],mapped_sha256=sha(artifact/'mapped.v'),
                libraries_sha256={p.name:sha(p)for p in [COMB,SEQ]},
                producer=dict(backend=backend,tools=identity['tools'],recipe_sha256=identity['recipes'],
                              custom_files_sha256=custom,abc_delay_ps=abc_delay_ps),
                build_seconds=time.monotonic()-started,
                evaluation='Area/timing are measured independently; producer reports are not scores')
            shutil.copytree(recipe_dir,artifact/'recipes',dirs_exist_ok=True)
            save(manifest,provenance)
            result=dict(status='BUILT',reused=False,implementation=str(artifact),manifest=provenance)
            save(out/'build_result.json',result);return result
        finally:
            for key,value in old.items():
                if value is None:os.environ.pop(key,None)
                else:os.environ[key]=value


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('submission');parser.add_argument('--out')
    parser.add_argument('--backend',choices=['local','commercial'],default='local')
    parser.add_argument('--init-flow',action='store_true');parser.add_argument('--export',action='store_true')
    parser.add_argument('--abc-delay-ps',type=float,default=10000)
    parser.add_argument('--timeout',type=int,default=1800)
    args=parser.parse_args(argv)
    if args.abc_delay_ps<=0 or args.timeout<=0:parser.error('Delay target and timeout must be positive')
    if args.init_flow:
        print(initialize(args.submission));return 0
    if not args.out:parser.error('--out is required')
    if args.backend=='commercial':
        environment=prepare('commercial',allow_build=False)
        if not environment['ready']:raise EnvironmentError('Commercial build environment is not ready: '+str(environment))
    result=build(args.submission,args.out,args.backend,args.abc_delay_ps,args.timeout)
    if args.export:result['exported_to']=str(export_artifacts(result['implementation'],args.submission,Path(args.out)/'export_backup'))
    print(json.dumps(result,indent=2));return 0


if __name__=='__main__':sys.exit(main())
