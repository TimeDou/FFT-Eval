"""Last-resort, per-component source builds in a user-owned prefix.

Existing commands are reused. No sudo, tool removal or global package changes.
"""
from pathlib import Path
import os
import shutil
import subprocess
from common import run, lock, save
from toolchain import find_tool, prefix

RECIPES = {
    'yosys': ('https://github.com/YosysHQ/yosys.git', 'yosys-0.9'),
    'abc': ('https://github.com/YosysHQ/yosys.git', 'yosys-0.9'),
    'iverilog': ('https://github.com/steveicarus/iverilog.git', 'v11_0'),
    'verilator': ('https://github.com/verilator/verilator.git', 'v4.036'),
    'sta': ('https://github.com/The-OpenROAD-Project/OpenSTA.git', 'v2.2.0'),
}


def build_missing(missing):
    root = prefix()
    jobs = str(min(4, max(1, int(os.environ.get('FFT_BUILD_JOBS', '2')))))
    wanted = []
    for name in missing:
        if find_tool(name):
            continue
        component = 'iverilog' if name == 'vvp' else name
        if component not in wanted:
            wanted.append(component)
    built = []
    with lock(root/'build.lock'):
        (root/'bin').mkdir(parents=True, exist_ok=True)
        for component in wanted:
            # Another setup process may have completed while this one waited.
            required = ['iverilog', 'vvp'] if component == 'iverilog' else ['yosys', 'abc'] if component == 'yosys' else [component]
            if all(find_tool(name) for name in required):
                continue
            prerequisites = ['git', 'make', 'gcc', 'g++']
            if component != 'abc':prerequisites += ['bison','flex']
            prerequisites += ['cmake', 'swig'] if component == 'sta' else ['autoconf', 'gperf'] if component == 'iverilog' else ['autoconf', 'perl'] if component == 'verilator' else []
            absent = [name for name in prerequisites if not shutil.which(name)]
            if absent:
                raise EnvironmentError('Cannot build '+component+': missing build prerequisites '+', '.join(absent)+'. Existing EDA tools have not been replaced.')
            url, tag = RECIPES[component]
            source = root/'src'/component
            log = root/'logs'/component
            if not (source/'.git').exists():
                source.parent.mkdir(parents=True, exist_ok=True)
                run(['git', 'clone', '--depth', '1', '--branch', tag, url, source], str(log)+'_clone.log', 600)
            commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
            save(root/'sources'/f'{component}.json', dict(url=url, tag=tag, commit=commit))
            if component == 'abc':
                run(['make','config-gcc'],str(log)+'_configure.log',120,source)
                # Build only Yosys 0.9's pinned ABC (3709744), not another Yosys.
                run(['make','-j'+jobs,'yosys-abc'],str(log)+'_build.log',3600,source)
                shutil.copy2(source/'yosys-abc',root/'bin/yosys-abc')
            elif component == 'yosys':
                run(['make', 'config-gcc'], str(log)+'_configure.log', 120, source)
                options = ['PREFIX='+str(root), 'ENABLE_READLINE=0', 'ENABLE_TCL=0']
                if find_tool('abc'):
                    options += ['ABCEXTERNAL='+find_tool('abc')]
                run(['make', '-j'+jobs, *options], str(log)+'_build.log', 3600, source)
                run(['make', 'install', *options], str(log)+'_install.log', 300, source)
            elif component in {'iverilog', 'verilator'}:
                run(['sh', 'autoconf.sh'] if component == 'iverilog' else ['autoconf'], str(log)+'_autoconf.log', 180, source)
                run([source/'configure', '--prefix='+str(root)], str(log)+'_configure.log', 180, source)
                run(['make', '-j'+jobs], str(log)+'_build.log', 3600, source)
                run(['make', 'install'], str(log)+'_install.log', 300, source)
            else:
                directory = source/'build'
                directory.mkdir(exist_ok=True)
                run(['cmake', '..', '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_INSTALL_PREFIX='+str(root)], str(log)+'_configure.log', 180, directory)
                run(['make', '-j'+jobs], str(log)+'_build.log', 3600, directory)
                executable = next((p for p in [source/'app/sta', directory/'sta'] if p.is_file()), None)
                if executable is None:
                    raise EnvironmentError('OpenSTA build did not produce sta; see '+str(log)+'_build.log')
                shutil.copy2(executable, root/'bin/sta')
            built.append(component)
    return built
