"""Container-side public environment check and FFT preview; no hidden evaluation."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import time
import traceback
from common import ROOT, TECH, save, sha
from toolchain import prepare

SMOKE_RTL = '''module fft64_top(
 input wire clk,rst,in_valid,frame_start,
 input wire signed [15:0] in_re,in_im,
 output reg out_valid,out_start,
 output reg signed [23:0] out_re,out_im);
 always @(posedge clk) begin
  if(rst) begin out_valid<=0;out_start<=0;out_re<=0;out_im<=0;end
  else begin
   out_valid<=in_valid;out_start<=in_valid && frame_start;
   out_re<={{8{in_re[15]}},in_re};out_im<={{8{in_im[15]}},in_im};
  end
 end
endmodule
'''


def smoke(directory):
    import numpy as np
    from simulate import simulate
    from commercial import measure
    from evaluate import used_cell_models
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    events=np.asarray([[1,0,0,0,0],[1,0,0,0,0],[0,0,0,0,0],
        [0,1,1,-16384,16384],[0,1,0,7,-9],[0,0,0,3,4],
        [0,1,1,16383,-16383],[1,0,0,0,0],[0,1,1,-17,19],[0,0,0,0,0]],dtype=np.int64)
    expected=[]
    for cycle,(rst,valid,start,real,imag)in enumerate(events):
        active=bool(valid and not rst)
        expected.append([cycle,int(active),int(active and start),int(real)if active else 0,int(imag)if active else 0])
    expected=np.asarray(expected,dtype=np.int64)
    rtl=simulate(SMOKE_RTL,events,directory/'rtl','vcs')
    if not np.array_equal(rtl,expected):raise RuntimeError('VCS smoke RTL/reset behavior does not match expected results')
    # Availability checks must execute DC/PT, including fresh license checkout.
    # Candidate evaluations may reuse their separate physical cache.
    physical_cache=os.environ.pop('FFT_PHYSICAL_CACHE_DIR',None)
    try:
        ppa=measure(SMOKE_RTL,directory/'asic')
    finally:
        if physical_cache is not None:os.environ['FFT_PHYSICAL_CACHE_DIR']=physical_cache
    mapped=(directory/'asic/mapped.v').read_text()
    mapped_source=used_cell_models(mapped)+'\n'+mapped
    for mode in [0,1,20261121]:
        gate=simulate(mapped_source,events,directory/'mapped','vcs',initialization=mode)
        if not np.array_equal(gate,rtl):raise RuntimeError('Mapped smoke test differs from RTL, initialization '+str(mode))
    if not ppa['timing_pass']:raise RuntimeError('Small registered smoke circuit failed the fixed setup/hold check; inspect STA reports')
    return dict(status='PASS',directory=str(directory),rtl_compile_and_simulation='PASS',dc_mapping='PASS',primetime_setup_hold='PASS',
                mapped_simulation='PASS',gate_initial_state_modes=[0,1,20261121],
                area_um2=ppa['area_um2'],worst_setup_slack_ns=ppa['worst_setup_slack_ns'],
                worst_hold_slack_ns=ppa['worst_hold_slack_ns'],clock_target_ns=ppa['clock_period_ns'],
                mapped_sha256=ppa['mapped_sha256'],source_sha256=hashlib.sha256(SMOKE_RTL.encode()).hexdigest(),
                scope='small registered transfer circuit; tool/library check, not an FFT result or score')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['check','run','build'])
    parser.add_argument('--out',required=True)
    parser.add_argument('--inspect-only',action='store_true')
    parser.add_argument('--submission')
    parser.add_argument('--quick',action='store_true')
    parser.add_argument('--profile',choices=['area','architecture'],default='architecture')
    parser.add_argument('--seed',type=int,default=20261118)
    parser.add_argument('--scale',type=int,default=1)
    parser.add_argument('--formal',action='store_true')
    parser.add_argument('--backend',choices=['commercial','local'],default='commercial')
    parser.add_argument('--abc-delay-ps',type=float,default=10000)
    parser.add_argument('--tool-timeout',type=int,default=1800)
    args=parser.parse_args(argv)
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    report=dict(status='CHECKING',ready=False,mode=args.mode,measurement_backend='commercial')
    save(out/'environment.json',report)
    try:
        environment=prepare(args.backend if args.mode=='build'else'commercial',check_only=args.inspect_only,
                            quick=args.quick if args.mode=='run'else False,allow_build=False)
        report.update(environment)
        report.update(installed_ready=environment['ready'],ready=False)
        report['tools_sha256']={name:sha(path)for name,path in environment['tools'].items()if path and name in {'vcs','dc_shell','pt_shell','lc_shell'}}
        report['libraries_sha256']={str(p):sha(p)for p in [TECH/'ASAP7_RVT_TT_nldm_NO_FAHA.lib',TECH/'ASAP7_SEQ_RVT_TT_nldm_220123.lib',TECH/'db/comb_rvt_tt.db',TECH/'db/seq_rvt_tt.db']if p.is_file()}
        save(out/'environment.json',report)
        if not environment['ready']:
            raise RuntimeError('Required container tools, Python packages or libraries are unavailable: '+', '.join(environment['missing']))
        if args.mode=='build':
            from build_implementation import build
            built=build(args.submission,out,args.backend,args.abc_delay_ps,args.tool_timeout)
            report.update(status='READY',ready=True,build_status='BUILT')
            save(out/'environment.json',report)
            print(json.dumps(built,indent=2),flush=True);return 0
        if args.mode=='check':
            if args.inspect_only:
                report.update(status='INSTALLED',ready=True,license_and_execution_verified=False)
            else:
                report['smoke']=smoke(out/'smoke'/str(time.time_ns()))
                report.update(status='READY',ready=True,license_and_execution_verified=True)
        else:
            if not args.submission:raise ValueError('A submission is required')
            from evaluate import evaluate,compact
            result=evaluate(args.submission,out,'commercial',seed=args.seed,scale=args.scale,
                            quick=args.quick,formal=args.formal,profile=args.profile,audience='public')
            report.update(status='READY',ready=True,preview_status=result['status'])
            save(out/'environment.json',report)
            print(json.dumps(compact(result),indent=2),flush=True)
            return 0 if result['status']in{'COMPLETE','QUICK_CHECK_PASSED'}and result.get('ppa',{}).get('timing_pass',True)else 2
    except Exception as exc:
        report.update(status='NOT_READY',ready=False,failure=str(exc),traceback=traceback.format_exc())
    report['seconds']=time.monotonic()-started
    save(out/'environment.json',report)
    print(json.dumps(report,indent=2),flush=True)
    if report['ready']:
        print('Synopsys environment: '+report['status'],flush=True)
    else:
        print('Synopsys environment: NOT_READY; inspect '+str(out/'environment.json'),file=sys.stderr)
    return 0 if report['ready']else 2


if __name__=='__main__':sys.exit(main())
