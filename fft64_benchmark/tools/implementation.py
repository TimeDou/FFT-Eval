"""Mapped implementations produced by agent-controlled public optimization flows."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import tempfile
from common import COMB,SEQ,DesignInvalidError,sha,read,save

ARTIFACTS=('mapped.v','manifest.json')
RECIPES=('dc_opt.tcl','yosys_opt.ys','abc_opt.script','pnr_opt.tcl')


def validate_structural(text):
    """Accept one flattened structural top; library cell behavior comes from the kit."""
    code=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
    code=re.sub(r'\(\*.*?\*\)','',code,flags=re.S)
    code=re.sub(r'\\[^\s]+','escaped_identifier',code)
    modules=re.findall(r'\bmodule\s+([A-Za-z_][A-Za-z_0-9]*)',code)
    if modules!=['fft64_top'] or len(re.findall(r'\bendmodule\b',code))!=1:
        raise DesignInvalidError('implementation/mapped.v must contain one flattened fft64_top, without library model definitions')
    if re.search(r'[`$#]|\b(?:always(?:_ff|_comb|_latch)?|initial|final|function|task|generate|primitive|specify|force|release|DPI|real|shortreal|defparam)\b',code):
        raise DesignInvalidError('Mapped implementation must be structural standard cells and net aliases, without behavioral code or directives')
    return text


def load(submission,rtl_sha256):
    directory=Path(submission)/'implementation'
    if not directory.exists():return None
    if not directory.resolve().is_relative_to(Path(submission).resolve()):raise DesignInvalidError('Implementation must be inside the submission')
    if not all((directory/name).is_file()for name in ARTIFACTS):
        raise DesignInvalidError('implementation/ requires both mapped.v and manifest.json; build or remove the incomplete export')
    if any(not(directory/name).resolve().is_relative_to(Path(submission).resolve())for name in ARTIFACTS):raise DesignInvalidError('Implementation files must be inside the submission')
    try:manifest=read(directory/'manifest.json')
    except (OSError,ValueError)as exc:raise DesignInvalidError('Invalid implementation manifest: '+str(exc))from exc
    if not isinstance(manifest,dict):raise DesignInvalidError('Implementation manifest must be an object')
    expected=dict(rtl_sha256=rtl_sha256,mapped_sha256=sha(directory/'mapped.v'),
                  libraries_sha256={p.name:sha(p)for p in [COMB,SEQ]})
    for key,value in expected.items():
        if manifest.get(key)!=value:raise DesignInvalidError('Mapped implementation '+key+' does not match the submitted RTL/netlist or fixed ASAP7 library; rebuild it')
    producer=manifest.get('producer',{})
    if not isinstance(producer,dict):raise DesignInvalidError('Implementation producer must be an object')
    declared=producer.get('custom_files_sha256',{})
    if not isinstance(declared,dict):raise DesignInvalidError('Recipe provenance must be an object')
    for name,value in declared.items():
        path=Path(submission)/'flow'/name
        if not path.resolve().is_relative_to((Path(submission)/'flow').resolve()):raise DesignInvalidError('Invalid recipe provenance path')
        if not path.is_file()or sha(path)!=value:raise DesignInvalidError('Optimization recipe changed after export; rebuild the implementation')
    validate_structural((directory/'mapped.v').read_text())
    return dict(path=str((directory/'mapped.v').resolve()),mapped_sha256=expected['mapped_sha256'],
                manifest_sha256=sha(directory/'manifest.json'),producer=manifest.get('producer'),
                libraries_sha256=expected['libraries_sha256'],rtl_sha256=rtl_sha256)


def export_artifacts(source,submission,backup):
    source=Path(source);destination=Path(submission)/'implementation';backup=Path(backup)
    if not all((source/name).is_file()for name in ARTIFACTS):raise ValueError('Build did not produce a complete implementation')
    if destination.exists():
        if backup.exists():raise ValueError('Export backup already exists; choose a new build output')
        shutil.copytree(destination,backup)
    with tempfile.TemporaryDirectory(prefix='.implementation_',dir=destination.parent)as temporary:
        staged=Path(temporary)/'ready';shutil.copytree(source,staged)
        previous=Path(temporary)/'previous'
        if destination.exists():destination.rename(previous)
        try:staged.replace(destination)
        except BaseException:
            if previous.exists():previous.replace(destination)
            raise
    return destination
