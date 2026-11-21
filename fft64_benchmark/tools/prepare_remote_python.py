"""Optional pinned binary Python runtime; no interpreter or EDA compilation."""
from pathlib import Path
import argparse
import fcntl
import hashlib
import json
import shutil
import subprocess
import tempfile
import urllib.request

ARCHIVE='cpython-3.12.10+20250529-x86_64-unknown-linux-gnu-install_only.tar.gz'
URL='https://github.com/astral-sh/python-build-standalone/releases/download/20250529/'+ARCHIVE
SHA256='3b7de567f4a8a1c3e5be2d51af3023dd3c1075cfacb6cd8efb511e0ef4b31fa8'


def prepare(root, source_archive=None):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    with (root/'python_prepare.lock').open('a') as guard:
        fcntl.flock(guard,fcntl.LOCK_EX)
        archive=root/ARCHIVE
        if source_archive and Path(source_archive).resolve()!=archive:
            source=Path(source_archive).resolve()
            if hashlib.sha256(source.read_bytes()).hexdigest()!=SHA256:
                raise ValueError('Python runtime archive checksum does not match the pinned binary')
            temporary=root/(ARCHIVE+'.copy')
            shutil.copy2(source,temporary);temporary.replace(archive)
        if not archive.exists():
            print('Downloading an isolated binary Python runtime; installed EDA tools are reused.',flush=True)
            request=urllib.request.Request(URL,headers={'User-Agent':'FFT-Bench-runtime-setup'})
            temporary=root/(ARCHIVE+'.download')
            with urllib.request.urlopen(request,timeout=60) as response,temporary.open('wb') as output:
                shutil.copyfileobj(response,output)
            if hashlib.sha256(temporary.read_bytes()).hexdigest()!=SHA256:
                raise ValueError('Downloaded Python runtime checksum does not match the pinned binary')
            temporary.replace(archive)
        digest=hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest!=SHA256:raise ValueError('Python runtime archive checksum does not match the pinned binary')
        if not (root/'python/bin/python3').is_file():
            if (root/'python').exists():raise ValueError('Incomplete Python directory exists; choose a clean runtime directory')
            with tempfile.TemporaryDirectory(prefix='python_extract_',dir=root) as temporary:
                subprocess.run(['tar','-xzf',str(archive),'-C',temporary],check=True)
                extracted=Path(temporary)/'python'
                if not (extracted/'bin/python3').is_file():raise ValueError('Standalone archive has no Python executable')
                extracted.replace(root/'python')
        receipt=dict(url=URL,sha256=digest,archive_bytes=archive.stat().st_size,
                     scope='Isolated binary Python only; no EDA or license installation')
        (root/'python_source.json').write_text(json.dumps(receipt,indent=2)+'\n')
        return root/'python/bin/python3'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runtime_directory');parser.add_argument('--archive')
    args=parser.parse_args();print(prepare(args.runtime_directory,args.archive))
