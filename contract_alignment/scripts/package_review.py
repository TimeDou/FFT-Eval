"""Package exact source checkouts and separate private native audit evidence."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import io
import json
import subprocess
import zipfile

BASE = Path(__file__).resolve().parents[2]


def source_archive(repo, destination):
    assert not subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip()
    commit = subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    payload = subprocess.check_output(['git','-C',str(repo),'archive','--format=zip',
                                       '--prefix='+repo.name+'/', 'HEAD'])
    entries = {}
    for record in subprocess.check_output(['git','-C',str(repo),'ls-tree','-r','-z','HEAD']).split(b'\0'):
        if not record:
            continue
        meta,name = record.split(b'\t',1)
        mode,kind,oid = meta.split()
        assert kind == b'blob'
        entries[repo.name+'/'+name.decode()] = oid.decode()
    fmt = subprocess.check_output(['git','-C',str(repo),'rev-parse','--show-object-format'],text=True).strip()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert archive.testzip() is None
        assert {item.filename for item in archive.infolist() if not item.is_dir()} == set(entries)
        for name,oid in entries.items():
            data = archive.read(name)
            assert hashlib.new(fmt,b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() == oid
    destination.write_bytes(payload)
    return dict(commit=commit, tracked_source_files=len(entries), verified_git_blobs=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence',required=True,type=Path)
    args = parser.parse_args()
    evidence = args.evidence.resolve()
    manifest = json.loads((evidence/'FILE_MANIFEST.json').read_text())
    for name in ['fft64_grader.zip','test_by_code.py','area_reference.json','settings.json']:
        assert 'native/grader/'+name in manifest['files'], 'Missing deployment artifact: '+name
    private = BASE/'DSBench/FFT-Eval/fft64_benchmark'
    assert (evidence/'native/grader/test_by_code.py').read_bytes() == (private/'grading/test_by_code.py').read_bytes()
    with zipfile.ZipFile(evidence/'native/grader/fft64_grader.zip') as archive:
        for name in archive.namelist():
            rel = name.removeprefix('fft64_grader/')
            if rel == 'settings.json':
                continue
            assert archive.read(name) == (private/rel).read_bytes(), 'Stale grader runtime source: '+rel
    directory = BASE/'DSBench/review_packages'/('FFT-contract-review-'+datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S'))
    directory.mkdir(parents=True,exist_ok=False)
    records = {}
    for name in ['FFT-Bench','FFT-Eval']:
        destination = directory/(name+'.zip')
        record = source_archive(BASE/'DSBench'/name,destination)
        if name == 'FFT-Eval':
            with zipfile.ZipFile(destination,'a',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
                for rel,item in manifest['files'].items():
                    path = evidence/rel
                    assert path.stat().st_size == item['bytes']
                    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']
                    archive.write(path,'FFT-Eval-evidence/contract_alignment/'+rel)
                archive.write(evidence/'FILE_MANIFEST.json','FFT-Eval-evidence/contract_alignment/FILE_MANIFEST.json')
            record['private_native_evidence_included'] = True
            record['evidence_files'] = len(manifest['files'])+1
        with zipfile.ZipFile(destination) as archive:
            assert archive.testzip() is None
        record.update(bytes=destination.stat().st_size,sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
        records[name] = record
    (directory/'CONTENTS.json').write_text(json.dumps(records,indent=2)+'\n')
    (directory/'SHA256SUMS').write_text(''.join(value['sha256']+'  '+name+'.zip\n'for name,value in records.items()))
    (directory/'README.txt').write_text(
        'FFT-Bench.zip: exact public main source, no Git history, hidden inputs or local run artifacts.\n'
        'FFT-Eval.zip: exact private main source plus separate FFT-Eval-evidence/contract_alignment native validation. '
        'Private audit material: not an Agent task distribution.\n'
        'CONTENTS.json identifies source commits and file verification; SHA256SUMS verifies both ZIPs.\n'
        'The supplied review folder contained only four files; the fourteen revised/FFT-Bench bodies referenced by SYNC_MAP were absent. '
        'The available Chinese startup prompt was incorporated, translated and aligned with the current contract.\n')
    print(json.dumps(dict(directory=str(directory),archives=records),indent=2))


if __name__ == '__main__':
    main()
