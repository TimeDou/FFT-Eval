"""Prepare a pinned, isolated Python runtime on the host's shared directory."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import urllib.request

ARCHIVE = 'cpython-3.12.10+20250529-x86_64-unknown-linux-gnu-install_only.tar.gz'
URL = 'https://github.com/astral-sh/python-build-standalone/releases/download/20250529/'+ARCHIVE
# Published .sha256 sidecar, verified against the downloaded archive.
SHA256 = '3b7de567f4a8a1c3e5be2d51af3023dd3c1075cfacb6cd8efb511e0ef4b31fa8'


def prepare(root):
    root = Path(root).resolve(); root.mkdir(parents=True, exist_ok=True)
    archive = root/ARCHIVE
    if not archive.exists():
        print('Downloading the pinned Python runtime; installed EDA tools are reused.', flush=True)
        request = urllib.request.Request(URL, headers={'User-Agent': 'FFT-Bench-runtime-setup'})
        temporary = archive.with_suffix('.download')
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open('wb') as output:
            shutil.copyfileobj(response, output)
        temporary.replace(archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != SHA256:
        raise ValueError('Python runtime archive checksum does not match the pinned release')
    if not (root/'python/bin/python3').is_file():
        subprocess.run(['tar', '-xzf', str(archive), '-C', str(root)], check=True)
    receipt = dict(url=URL, sha256=digest, archive_bytes=archive.stat().st_size,
                   scope='Isolated Python only; no EDA or license installation')
    (root/'python_source.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return root/'python/bin/python3'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runtime_directory')
    print(prepare(parser.parse_args().runtime_directory))
