from pathlib import Path
import re
import numpy as np
from common import ROOT,run,save,sha,lock,read

TB=r'''`timescale 1ns/1ps
module tb;
 reg clk=0,rst=1,in_valid=0,frame_start=0;
 reg signed[15:0] in_re=0,in_im=0;
 wire out_valid,out_start;wire signed[23:0] out_re,out_im;
 fft64_top dut(.clk(clk),.rst(rst),.in_valid(in_valid),.frame_start(frame_start),.in_re(in_re),.in_im(in_im),.out_valid(out_valid),.out_start(out_start),.out_re(out_re),.out_im(out_im));
 integer fi,fo,rc,c,rs,iv,ifs,ir,ii;reg[2047:0] vp,op;
 initial begin
 if(!$value$plusargs("VECTORS=%s",vp))$fatal(1,"no vector path");
 if(!$value$plusargs("OUTPUT=%s",op))$fatal(1,"no output path");
 fi=$fopen(vp,"r");fo=$fopen(op,"w");if(fi==0||fo==0)$fatal(1,"file open");c=0;
 while(!$feof(fi))begin
 rc=$fscanf(fi,"%d %d %d %d %d\n",rs,iv,ifs,ir,ii);
 if(rc==5)begin clk=0;rst=rs;in_valid=iv;frame_start=ifs;in_re=ir;in_im=ii;
 #5;clk=1;#1;
 if((out_valid!==1'b0 && out_valid!==1'b1)||(out_start!==1'b0 && out_start!==1'b1))$fatal(1,"X control cycle%0d",c);
 if(out_valid && ((^out_re===1'bx)||(^out_im===1'bx)))$fatal(1,"X data cycle%0d",c);
 // Data are don't-care outside out_valid. Do not reject legal uninitialized
 // or deliberately unspecified invalid payload by trying to parse an X.
 if(out_valid)$fdisplay(fo,"%0d %0d %0d %0d %0d",c,out_valid,out_start,out_re,out_im);
 else $fdisplay(fo,"%0d %0d %0d 0 0",c,out_valid,out_start);
 #4;clk=0;c=c+1;
 end end
 $fclose(fi);$fclose(fo);$finish;end
endmodule
'''

CPP=r'''#include "Vfft64_top.h"
#include "verilated.h"
#include <fstream>
#include <cstdint>
int main(int argc,char**argv){std::ifstream in(argv[1]);std::ofstream out(argv[2]);Vfft64_top d;long long rs,iv,fs,r,i;long long c=0;
 while(in>>rs>>iv>>fs>>r>>i){d.clk=0;d.rst=rs;d.in_valid=iv;d.frame_start=fs;d.in_re=(uint32_t)r;d.in_im=(uint32_t)i;d.eval();d.clk=1;d.eval();
 int64_t rr=(int64_t)(((uint64_t)d.out_re^8388608ULL)-8388608ULL),ii=(int64_t)(((uint64_t)d.out_im^8388608ULL)-8388608ULL);
 out<<c<<" "<<(int)d.out_valid<<" "<<(int)d.out_start<<" "<<rr<<" "<<ii<<"\n";d.clk=0;d.eval();++c;}d.final();}
'''

def testbench(probe=False):
 if not probe:return TB
 start=TB.index(' if((out_valid!==')
 end=TB.index(' #4;clk=0',start)
 # Qualification probes retain unknowns as out-of-domain sentinels instead
 # of aborting the whole batch at the first expected failing interval.
 capture=''' if(out_valid===1'b1)
 $fdisplay(fo,"%0d %0d %0d %0d %0d",c,1,(out_start===1'b0?0:out_start===1'b1?1:2),
 ((^out_re===1'bx)?32'sd1073741824:$signed(out_re)),((^out_im===1'bx)?32'sd1073741824:$signed(out_im)));
 else $fdisplay(fo,"%0d %0d %0d 0 0",c,(out_valid===1'b0?0:2),(out_start===1'b0?0:out_start===1'b1?1:2));
'''
 return TB[:start]+capture+TB[end:]

def schedule(frames,seed=11,reset_test=True):
 rng=np.random.default_rng(seed);ev=[[1,0,0,0,0]]*3+[[0,0,0,0,0]]*2;starts=[];partial=None;reset_probes=[]
 # Deliberately abort a full input frame during compute and during output.
 # An aborted epoch may have a valid output prefix; it is discarded at reset.
 # After the last reset, the complete scored transaction stream is checked.
 if reset_test:
  for idle_after_load in [24,82,210]:
   probe_start=len(ev)
   ev.extend([0,1,int(k==0),int(z[0]),int(z[1])]for k,z in enumerate(frames[0]))
   ev.extend([[0,0,0,0,0]]*idle_after_load)
   reset_probes.append(dict(input_start=probe_start,reset_cycle=len(ev),idle_after_load=idle_after_load))
   ev.extend([[1,0,0,0,0]]*3+[[0,0,0,0,0]]*3)
 ignore_before=len(ev)
 for j,x in enumerate(frames):
  if reset_test and j==len(frames)//2:
   partial=len(ev)
   ev.extend([0,1,int(k==0),int(z[0]),int(z[1])]for k,z in enumerate(x[:20]))
   ev.extend([[1,0,0,0,0]]*3+[[0,0,0,0,0]]*7)
  starts.append(len(ev));ev.extend([0,1,int(k==0),int(z[0]),int(z[1])]for k,z in enumerate(x))
  gap=320+(0 if j<5 else int(rng.integers(0,18)))
  # One long legal idle catches finite-counter wrap and stale frame output.
  if len(frames)>10 and j==len(frames)//3:gap+=65568
  ev.extend([[0,0,0,0,0]]*gap)
 ev.extend([[0,0,0,0,0]]*32)
 return np.asarray(ev,dtype=np.int64),dict(frame_starts=starts,offered_min_frame_II=384,cancelled_partial_start=partial,clock_period_ns=10,ignore_before_cycle=ignore_before,reset_probes=reset_probes)

def simulate(source,events,outdir,backend='verilator',initialization=None,probe=False,reuse_compiled_from=None):
 if initialization is not None and(backend!='vcs' or type(initialization)is not int or initialization<0):
  raise ValueError('Explicit gate initialization requires VCS and a nonnegative integer mode/seed')
 if probe and backend not in {'vcs','iverilog'}:raise ValueError('Probe capture requires a four-state simulator')
 d=Path(outdir).resolve();d.mkdir(parents=True,exist_ok=True);signature=dict(source_sha256=__import__('hashlib').sha256(source.encode()).hexdigest(),backend=backend,driver_sha256=sha(__file__),initialized_gate=initialization is not None,probe_capture=probe)
 with lock(d/'lock'):
  if(d/'signature.json').exists():assert read(d/'signature.json')==signature,'Use a separate simulation directory for a new design'
  else:save(d/'signature.json',signature)
  (d/'source.sv').write_text(source);np.savetxt(d/'vectors.txt',events,fmt='%d')
  if backend=='verilator':
   (d/'driver.cpp').write_text(CPP);exe=d/'obj/Vfft64_top'
   if not exe.exists():run(['verilator','--cc','--exe','--build','-j','2','-Wno-fatal','--top-module','fft64_top','--Mdir',d/'obj',d/'source.sv',d/'driver.cpp'],d/'compile.log',600,cwd=d)
   run([exe,d/'vectors.txt',d/'output.txt'],d/'simulation.log',600)
  else:
   (d/'tb.sv').write_text(testbench(probe));exe=d/'simv'
   if reuse_compiled_from is not None:
    origin=Path(reuse_compiled_from).resolve()
    if read(origin/'signature.json')!=signature or not(origin/'simv').is_file():
     raise ValueError('Compiled simulator source/driver/options do not match')
    exe=origin/'simv'
   if not exe.exists():
    args=['iverilog','-g2012','-s','tb','-o',exe,d/'source.sv',d/'tb.sv']if backend=='iverilog'else['vcs','-sverilog','-full64',*(['+vcs+initreg+random']if initialization is not None else []),'-timescale=1ns/1ps','-top','tb',d/'source.sv',d/'tb.sv','-o',exe]
    # VCS's default csrc cache belongs to the current working directory. Keep
    # it private even for serial RTL/netlist runs: same-named modules from a
    # previous design must not be picked up by incremental compilation.
    run(args,d/'compile.log',600,cwd=d)
   args=['vvp',exe]if backend=='iverilog'else[exe]
   if initialization is not None:args+=['+vcs+initreg+'+str(initialization)]
   runtime=d if initialization is None else d/('initial_state_'+str(initialization))
   runtime.mkdir(exist_ok=True)
   run(args+['+VECTORS='+str(d/'vectors.txt'),'+OUTPUT='+str(runtime/'output.txt')],runtime/'simulation.log',600,cwd=runtime)
  if backend=='verilator':runtime=d
  log=(runtime/'simulation.log').read_text()
  if re.search(r'^\s*(?:Fatal:|Error:|Error-\[)',log,re.M)or'VCS initreg not enabled'in log:
   raise RuntimeError('Simulator reported an error: '+str(runtime/'simulation.log')+'\n'+log[-1600:])
  raw=np.loadtxt(runtime/'output.txt',dtype=np.int64,ndmin=2)
  assert len(raw)==len(events)and np.array_equal(raw[:,0],np.arange(len(events))), 'Missing/duplicated clock observations'
  save(runtime/'receipt.json',dict(signature=signature,input_sha256=sha(d/'vectors.txt'),output_sha256=sha(runtime/'output.txt'),cycles=len(events),initialization=initialization,compiled_from=str(reuse_compiled_from)if reuse_compiled_from else None))
  return raw

def decode(raw,events,meta):
 assert np.all(np.isin(raw[:,1:3],[0,1])),'Unknown output control state'
 valid=raw[:,1]==1
 assert np.all((raw[valid,3:5]>=-(1<<23))&(raw[valid,3:5]<(1<<23))),'Unknown/out-of-range output payload'
 assert np.all(raw[events[:,0]==1,1:3]==0),'Output must be invalid during synchronous reset'
 assert not np.any((raw[:,2]!=0)&(raw[:,1]==0)),'out_start without out_valid'
 valid_epoch=np.arange(len(raw))>=meta.get('ignore_before_cycle',0)
 starts=np.flatnonzero((raw[:,2]!=0)&valid_epoch);assert len(starts)==len(meta['frame_starts']),('Missing/extra frames',len(starts),len(meta['frame_starts']))
 groups=[];covered=np.zeros(len(events),bool);lat=[];tail=[];completion=[]
 for o,i in zip(starts,meta['frame_starts']):
  assert i<=o and o+64<=len(raw),'Output before required frame or truncated'
  assert np.all(raw[o:o+64,1]==1)and np.count_nonzero(raw[o:o+64,2])==1,'Noncontiguous output frame'
  assert o-i<=300 and o+63-i<=364,('Latency limit',o-i)
  assert o>=i+63,'DFT output before last required input'
  groups.append(raw[o:o+64,3:5]);covered[o:o+64]=True;lat.append(int(o-i));tail.append(int(o-i-63));completion.append(int(o+63-i))
 assert np.array_equal(covered[valid_epoch],raw[valid_epoch,1].astype(bool)),'Unframed/extra valid outputs'
 interval=meta.get('offered_min_frame_II',384)
 ii=[int(starts[k+1]-starts[k])for k in range(len(starts)-1)if meta['frame_starts'][k+1]-meta['frame_starts'][k]==interval]
 # Returning every offered frame within its deadline demonstrates service.
 # Legal variable latency need not give an identical output-start interval.
 return np.asarray(groups),dict(first_output_latency_cycles=sorted(set(lat)),computational_tail_cycles=sorted(set(tail)),frame_completion_cycles=sorted(set(completion)),observed_frame_II_on_384_cycle_workload=sorted(set(ii))if interval==384 else[],observed_frame_II_at_verified_interval=sorted(set(ii)),offered_frame_II=interval,required_samples_per_second=64/(interval*10e-9),required_ffts_per_second=1/(interval*10e-9),clock_period_ns=10,reset_mid_frame_test=meta.get('cancelled_partial_start')is not None,reset_during_processing_probes=meta.get('reset_probes',[]))
