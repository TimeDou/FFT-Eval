"""Reset exactly three archived pilot workspaces to a published public task."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys

STATE=Path(__file__).resolve().parent
BASE=Path('/home/sj/FFT').resolve()
RESEARCH=Path('/mnt/DATA1/sj/ALS/DP2.0/DSBench')
AGENTS=['Claude-DS-Flash','Codex-GPT-6.1-Sol-Max','Codex-GPT-6.2-Sol-Max']
ORIGIN='git@github.com:TimeDou/FFT-Bench.git'
ARCHIVE='cpython-3.12.10+20250529-x86_64-unknown-linux-gnu-install_only.tar.gz'
ARCHIVE_SHA='3b7de567f4a8a1c3e5be2d51af3023dd3c1075cfacb6cd8efb511e0ef4b31fa8'


def run(args,**kw):
    return subprocess.run(list(map(str,args)),check=True,**kw)


def output(args,**kw):
    return subprocess.check_output(list(map(str,args)),text=True,**kw).strip()


def save(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--public-commit',required=True)
    p.add_argument('--execute',action='store_true')
    args=p.parse_args()
    remote=output(['git','ls-remote',ORIGIN,'refs/heads/main']).split()[0]
    if remote!=args.public_commit:raise RuntimeError('The public main changed; review the expected commit before resetting')
    manifest=json.loads((BASE/'environments.json').read_text())
    containers={r['agent']:r for r in manifest['agents']}
    local_archive=RESEARCH/'Synopsys/runtime'/ARCHIVE
    if not local_archive.exists():
        local_archive=BASE/'Claude-Fable-5.2/Synopsys/.fft64/runtime'/ARCHIVE
    assert hashlib.sha256(local_archive.read_bytes()).hexdigest()==ARCHIVE_SHA
    statuspath=STATE/'workspace_reset_status.json'
    status=json.loads(statuspath.read_text())if statuspath.exists()else dict(public_commit=args.public_commit,agents={})
    assert status['public_commit']==args.public_commit
    plan=[]
    for name in AGENTS:
        if status['agents'].get(name,{}).get('status')=='COMPLETE':continue
        case=BASE/name;assert case.is_dir()and case.parent==BASE
        archive=RESEARCH/('FFT-Eval-agent-'+name)/'pilot_workspace/capture_manifest.json'
        evidence=json.loads(archive.read_text())
        branch=RESEARCH/('FFT-Eval-agent-'+name)
        local=output(['git','rev-parse','HEAD'],cwd=branch)
        published=output(['git','ls-remote','origin','refs/heads/agents/'+name],cwd=branch).split()[0]
        if local!=published:raise RuntimeError('Pilot preservation branch is not fully pushed: '+name)
        if not status['agents'].get(name,{}).get('removal_started'):
            assert output(['git','rev-parse','HEAD'],cwd=case/'FFT-Bench')==evidence['public_commit']
            for record in evidence['records']:
                if record['action']!='retained':continue
                original=case/record['path']
                if not original.is_file()or hashlib.sha256(original.read_bytes()).hexdigest()!=record['sha256']:
                    raise RuntimeError('A pilot file changed after archival: '+str(original))
        row=containers[name]
        inspected=subprocess.run(['docker','container','inspect',row['container']],capture_output=True,text=True)
        if inspected.returncode==0:
            current=json.loads(inspected.stdout)[0]
            assert current['Config']['Labels']['fft.agent']==name
            mounts=[m for m in current['Mounts']if m['Destination']=='/mnt/mydata']
            assert len(mounts)==1 and Path(mounts[0]['Source']).resolve()==(case/'Synopsys').resolve()
            image_id=current['Image']
        elif status['agents'].get(name,{}).get('removal_started'):
            image_id=status['agents'][name]['image_id']
        else:raise RuntimeError('Expected pilot container is absent: '+name)
        plan.append(dict(agent=name,container=row['container'],ssh_port=row['ssh_port'],
             image_id=image_id,archive_commit=local,root=str(case),container_exists=inspected.returncode==0,
             reset='Replace public clone, clear all shared experiment files, recreate only this container; reinstall verified public dependencies'))
    save(STATE/'workspace_reset_plan.json',dict(public_commit=args.public_commit,targets=plan))
    if not args.execute:
        print(json.dumps(plan,indent=2));return
    sys.path.insert(0,str(RESEARCH/'FFT-Bench/fft64_benchmark/tools'))
    from prepare_remote_python import prepare
    source_tech=RESEARCH/'Synopsys/.fft64/tech/99619e6e51b75f151556'
    for item in plan:
        name=item['agent'];case=BASE/name;row=status['agents'].setdefault(name,{})
        row.update(status='RESETTING',removal_started=True,archive_commit=item['archive_commit'],image_id=item['image_id']);save(statuspath,status)
        # A new container removes per-Agent /root and /tmp histories as well.
        uidgid=str(case.stat().st_uid)+':'+str(case.stat().st_gid)
        if item['container_exists']:
            run(['docker','exec','--user','0',item['container'],'chown','-R',uidgid,'/mnt/mydata'])
            run(['docker','container','rm','--force',item['container']])
        elif (case/'Synopsys').exists():
            run(['docker','run','--rm','--user','0','--entrypoint','/bin/chown',
                 '--mount','type=bind,source='+str(case/'Synopsys')+',target=/mnt/mydata',
                 item['image_id'],'-R',uidgid,'/mnt/mydata'])
        for part in ['FFT-Bench','Synopsys']:
            target=case/part
            if target.exists():shutil.rmtree(target)
        (case/'Synopsys/.fft64').mkdir(parents=True)
        run(['git','clone','--depth','1','--single-branch','--branch','main',ORIGIN,case/'FFT-Bench'])
        assert output(['git','rev-parse','HEAD'],cwd=case/'FFT-Bench')==args.public_commit
        prepare(case/'Synopsys/.fft64/runtime',local_archive)
        tech=case/'Synopsys/.fft64/tech/99619e6e51b75f151556'
        for rel in ['ASAP7_RVT_TT_nldm_NO_FAHA.lib','ASAP7_SEQ_RVT_TT_nldm_220123.lib','cells_sim.v',
                    'db/comb_rvt_tt.db','db/seq_rvt_tt.db']:
            dest=tech/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source_tech/rel,dest)
        run(['bash',BASE/'create_synopsys_envs.sh','--agent',name])
        assert (case/'port.txt').read_text().strip()==str(item['ssh_port'])
        row.update(status='COMPLETE',public_commit=args.public_commit,port=item['ssh_port'],fresh_container=True)
        save(statuspath,status);print('RESET_COMPLETE',name,flush=True)
    status['status']='COMPLETE';save(statuspath,status)


if __name__=='__main__':main()
