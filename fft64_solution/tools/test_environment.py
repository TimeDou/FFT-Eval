"""Tool-availability policy tests; mocked Synopsys paths are not PPA evidence."""
from pathlib import Path
import copy
import contextlib
import io
import json
import os
import shlex
import subprocess
import sys
import tempfile
from unittest.mock import patch

SOLUTION=Path(__file__).resolve().parents[1]
BENCHMARK=SOLUTION.with_name('fft64_benchmark')
sys.path.insert(0,str(BENCHMARK/'tools'))
import toolchain
from common import save


def report(commercial=False,local=False,yosys=False,quick=False):
    tools={name:None for name in toolchain.TOOLS}
    if commercial:
        for name in toolchain.COMMERCIAL:tools[name]='/installed/'+name
    if local:
        for name in toolchain.LOCAL:tools[name]='/installed/'+name
    if yosys:tools['yosys']='/installed/yosys'
    return dict(tools=tools,python=sys.executable,numpy_available=True,quick=quick,
                commercial=dict(tools_present=commercial,ready=commercial,missing=[] if commercial else toolchain.COMMERCIAL),
                local=dict(tools_present=local,ready=local,missing=[] if local else [n for n in toolchain.LOCAL if not tools[n]]))


def main():
    tests=[]
    with tempfile.TemporaryDirectory(prefix='fft64_environment_test_')as temporary:
        root=Path(temporary);tech=root/'tech';(tech/'db').mkdir(parents=True)
        for name in ['comb_rvt_tt.db','seq_rvt_tt.db']:(tech/'db'/name).write_text('availability test fixture only')
        for label,available,requested,calibration,expected in [
            ('prefer_synopsys_over_existing_oss',report(True,True),'auto',None,'commercial'),
            ('reuse_existing_oss',report(False,True),'auto',None,'local'),
            ('explicit_local_override',report(True,True),'local',None,'local'),
            ('calibrated_backend_stays_fixed',report(False,True),'auto',{'backend':'commercial'},'commercial')]:
            with patch.object(toolchain,'activate'),patch.object(toolchain,'probe',return_value=available),patch.object(toolchain,'TECH',tech),patch.object(toolchain,'run')as command,patch('bootstrap_oss.build_missing')as build:
                result=toolchain.prepare(requested,calibration=calibration)
                assert result['selected_backend']==expected
                assert not result['actions']
                command.assert_not_called();build.assert_not_called()
            tests.append(dict(name=label,passed=True))
        initial=report(False,False,yosys=True)
        initial['tools']={name:'/installed/'+name for name in toolchain.LOCAL if name!='sta'}|{name:None for name in toolchain.COMMERCIAL}|{'sta':None,'lc_shell':None}
        with patch.object(toolchain,'activate'),patch.object(toolchain,'probe',side_effect=[initial,initial,report(False,True)]),patch.object(toolchain,'find_tool',side_effect=lambda n:initial['tools'].get(n)),patch('bootstrap_oss.build_missing',return_value=['sta'])as build:
            result=toolchain.prepare()
            build.assert_called_once_with(['sta'])
            assert result['ready']
        tests.append(dict(name='existing_yosys_only_missing_opensta_is_built',passed=True))
        initial=report()
        with patch.object(toolchain,'activate'),patch.object(toolchain,'probe',side_effect=[initial,initial,report(False,True)]),patch.object(toolchain,'find_tool',return_value=None),patch('bootstrap_oss.build_missing',return_value=['yosys','abc','iverilog','verilator','sta'])as build:
            result=toolchain.prepare()
            build.assert_called_once_with(toolchain.LOCAL)
            assert result['ready']
        tests.append(dict(name='source_build_is_last_fallback',passed=True))
        for label,keywords in [('check_only_has_no_install',dict(check_only=True)),('no_build_respected',dict(allow_build=False))]:
            with patch.object(toolchain,'activate'),patch.object(toolchain,'probe',return_value=initial),patch.object(toolchain,'run')as command,patch('bootstrap_oss.build_missing')as build:
                result=toolchain.prepare(**keywords)
                assert not result['ready'];command.assert_not_called();build.assert_not_called()
            tests.append(dict(name=label,passed=True))
        for path in (tech/'db').glob('*.db'):path.unlink()
        available=report(True,False);available['commercial'].update(ready=False,missing=['ASAP7 DB'])
        with patch.object(toolchain,'activate'),patch.object(toolchain,'probe',return_value=available),patch.object(toolchain,'TECH',tech),patch.object(toolchain,'find_tool',return_value=None),patch('bootstrap_oss.build_missing')as build:
            result=toolchain.prepare()
            assert result['selected_backend']=='commercial'and not result['ready']
            build.assert_not_called()
            assert any('DBs are missing' in failure for failure in result['failures'])
        tests.append(dict(name='missing_db_does_not_trigger_yosys_install',passed=True))
        available=report(True,True);available['commercial'].update(ready=False,missing=['ASAP7 DB'])
        with patch.object(toolchain,'activate'),patch.object(toolchain,'probe',return_value=available),patch.object(toolchain,'TECH',tech),patch.object(toolchain,'find_tool',return_value=None),patch('bootstrap_oss.build_missing')as build:
            result=toolchain.prepare()
            assert result['selected_backend']=='local'and result['ready']
            assert result['notices']and not result['failures']
            build.assert_not_called()
        tests.append(dict(name='missing_db_can_reuse_an_already_ready_oss_chain',passed=True))
        # Exercise shell profile loading and HOME/bin discovery in a real child
        # process, without executing any dummy EDA tool or reporting its PPA.
        profile=root/'eda-env.sh';lines=[]
        for home,command in [('VCS_HOME','vcs'),('DC_HOME','dc_shell'),('PT_HOME','pt_shell')]:
            directory=root/home/'bin';directory.mkdir(parents=True)
            executable=directory/command;executable.write_text('#!/bin/sh\nexit 0\n');executable.chmod(0o755)
            lines.append('export '+home+'='+shlex.quote(str(directory.parent)))
        profile.write_text('\n'.join(lines)+'\n')
        env=dict(os.environ,FFT_EDA_PROFILE=str(profile),FFT_PYTHON=sys.executable,FFT_TECH_DIR=str(tech),PYTHONDONTWRITEBYTECODE='1')
        for key in toolchain.TOOLS.values():env.pop(key[0],None)
        process=subprocess.run(['bash',str(BENCHMARK/'setup.sh'),'--check-only','--quick'],capture_output=True,text=True,env=env)
        result=json.loads(process.stdout)
        assert process.returncode==0 and result['selected_backend']=='commercial'and result['ready']and not result['actions'],process.stdout+process.stderr
        assert result['tools']['vcs']==str(root/'VCS_HOME/bin/vcs')
        tests.append(dict(name='platform_profile_home_paths_and_vcs_only_quick_mode',passed=True))
        env.pop('FFT_EDA_PROFILE_LOADED',None)
        process=subprocess.run([sys.executable,str(BENCHMARK/'tools/environment.py'),'--check-only','--quick'],capture_output=True,text=True,env=env)
        result=json.loads(process.stdout)
        assert process.returncode==0 and result['selected_backend']=='commercial'and result['ready'],process.stdout+process.stderr
        tests.append(dict(name='nonlogin_python_entry_loads_eda_profile',passed=True))
        import calibrate
        measured=[dict(status='COMPLETE',backend='local',flow_id='fixture-flow',source={},ppa=dict(area_um2=a,timing_pass=True))for a in [100.,90.]]
        with patch.object(sys,'argv',['calibrate.py','--baseline','a','--baseline','b','--out',str(root/'calibration')]),patch.object(calibrate,'evaluate',side_effect=measured),contextlib.redirect_stdout(io.StringIO()):
            assert calibrate.main()==0
        reference=json.loads((root/'calibration/area_reference.json').read_text())
        assert reference['backend']=='local'and reference['reference_area_um2']==90.
        tests.append(dict(name='auto_calibration_records_actual_backend',passed=True))
    receipt=dict(passed=True,tests=tests,scope='Policy tests with mocked availability plus a shell-profile fixture. No commercial simulation/synthesis/STA or source compilation is claimed.')
    save(SOLUTION/'results/environment_update/policy_tests.json',receipt)
    print(json.dumps(dict(passed=True,tests=len(tests))))


if __name__=='__main__':main()
