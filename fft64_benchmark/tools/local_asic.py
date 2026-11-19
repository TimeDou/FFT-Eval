"""Counted-register ASAP7 mapping/STA; no historical area denominators."""
from pathlib import Path
import re,shutil,os,time
from common import ROOT,COMB,SEQ,run,save,read,sha,lock,executable

ABC=executable('FFT_ABC', ['yosys-abc','abc','berkeley-abc'])
STA=executable('FFT_STA', ['sta','opensta'])

def setup_sdc():
 return '''create_clock -name clk -period 10000 [get_ports clk]
set_clock_uncertainty -setup 100 [get_clocks clk]
set_clock_transition 20 [get_clocks clk]
set_input_delay 0 -clock clk [get_ports {rst in_valid frame_start in_re* in_im*}]
set_input_transition 20 [get_ports {rst in_valid frame_start in_re* in_im*}]
set_output_delay 0 -clock clk [all_outputs]
set_load 1 [all_outputs]
# Reset is exercised functionally; frequency rating is for normal operation.
set_false_path -from [get_ports rst]
'''

def measure(source,outdir):
 d=Path(outdir).resolve();d.mkdir(parents=True,exist_ok=True)
 if not ABC.is_file() or not STA.is_file() or not shutil.which('yosys'):raise EnvironmentError('Install Yosys and set FFT_ABC/FFT_STA to ABC/OpenSTA executables')
 sig=dict(source=__import__('hashlib').sha256(source.encode()).hexdigest(),comb=sha(COMB),seq=sha(SEQ),abc=sha(ABC),sta=sha(STA),yosys=sha(shutil.which('yosys')),flow_sha256=sha(__file__),flow='yosys-flatten-dfflibmap-abc-scalarSTA-v4',constraints=setup_sdc())
 with lock(d/'lock'):
  if(d/'signature.json').exists():assert read(d/'signature.json')==sig,'New ASIC inputs require a new directory'
  else:save(d/'signature.json',sig)
  if(d/'metrics.json').exists():return read(d/'metrics.json')
  start=time.monotonic();(d/'source.sv').write_text(source)
  (d/'abc.constr').write_text('set_driving_cell BUFx2_ASAP7_75t_R\nset_load 1\n')
  ys=f'read_liberty -lib {COMB}\nread_liberty -lib {SEQ}\nread_verilog -sv {d}/source.sv\nsynth -top fft64_top -flatten -noabc\nwrite_verilog -noattr {d}/premap.v\ndfflibmap -liberty {SEQ}\nabc -exe {ABC} -liberty {COMB} -constr {d}/abc.constr -D 10000\nclean\nwrite_verilog -noattr -noexpr {d}/mapped.v\nwrite_json {d}/mapped.json\nstat\n'
  (d/'map.ys').write_text(ys);run(['yosys','-Q','-T','-s',d/'map.ys'],d/'mapping.log',1200)
  jj=read(d/'mapped.json')['modules'];top=jj['fft64_top'];cells=top['cells']
  aa={};ss=set()
  for lib in [COMB,SEQ]:
   txt=lib.read_text();entries=dict((n,float(a))for n,a in re.findall(r'cell\s*\(([^)]+)\)\s*\{\s*area\s*:\s*([\d.]+)',txt))
   aa.update(entries)
   if lib==SEQ:ss.update(entries)
  bad=sorted(set(c['type']for c in cells.values())-set(aa));assert not bad,('Unmapped/blackbox cells',bad)
  for c in cells.values():
   if c['type']in ss:
    assert c['type'].startswith('DFF'),'Latches/clock-gating cells are outside this task'
    assert c['connections'].get('CLK')==top['ports']['clk']['bits'],'Derived/inverted/secondary clock rejected'
  area=sum(aa[c['type']]for c in cells.values());storage=sum(aa[c['type']]for c in cells.values()if c['type']in ss)
  assert storage>0,'Sequential FFT needs counted storage'
  # Old OpenSTA cannot parse concatenated assignment LHS emitted for aliases.
  # Split the SAME mapped JSON connectivity into scalar nets for STA only.
  # Cell types/counts are unchanged; functional simulation uses mapped.v.
  scalar=f'read_json {d}/mapped.json\nsplitnets -ports\nwrite_verilog -noattr -noexpr {d}/timing_netlist.v\n'
  (d/'scalar.ys').write_text(scalar);run(['yosys','-Q','-T','-s',d/'scalar.ys'],d/'scalar.log',120)
  (d/'constraints.sdc').write_text(setup_sdc())
  timing=f'read_liberty {COMB}\nread_liberty {SEQ}\nread_verilog {d}/timing_netlist.v\nlink_design fft64_top\nsource {d}/constraints.sdc\ncheck_setup -verbose\nreport_checks -path_delay max -format full_clock_expanded -digits 4\nreport_worst_slack -digits 4\nexit\n'
  (d/'timing.tcl').write_text(timing);run([STA,'-exit',d/'timing.tcl'],d/'timing.log',300)
  log=(d/'timing.log').read_text();assert not re.search(r'^Error',log,re.M),log[-2000:]
  assert not re.search(r'missing set_input_delay|missing set_output_delay|unconstrained endpoints',log,re.I),'Incomplete timing constraints'
  slack=float(re.search(r'worst slack\s+([\d.+-]+)',log)[1]);period=(10000-slack)/1000
  out=dict(area_um2=area,register_area_um2=storage,arithmetic_control_mux_other_area_um2=area-storage,cells=len(cells),register_cells=sum(c['type']in ss for c in cells.values()),clock_period_ns=10,setup_uncertainty_ns=.1,worst_setup_slack_ns=slack/1000,effective_required_period_ns=period,timing_pass=slack>=0,prelayout_fmax_estimate_MHz=1000/period,flow='Yosys/ABC;ASAP7RVT/TT comb+sequential;countedFF storage;OpenSTA ideal-interconnect;not DC/PrimeTime or postroute',source_sha256=sig['source'],mapped_sha256=sha(d/'mapped.v'),comb_sha256=sig['comb'],seq_sha256=sig['seq'],mapping_wall_seconds=time.monotonic()-start)
  save(d/'metrics.json',out);return out

def try_equivalence(source,outdir):
 """Same-candidate sequential equivalence, never approximate-vs-accurate."""
 d=Path(outdir).resolve();models=ROOT/'tech/cells_sim.v'
 ys=f'read_verilog -sv {d}/source.sv\nhierarchy -top fft64_top\nproc\nmemory\nflatten\nopt\nrename fft64_top gold\ndesign -stash gold\nread_verilog {models}\nread_verilog {d}/mapped.v\nhierarchy -top fft64_top\nproc\nflatten\nopt\nrename fft64_top gate\ndesign -stash gate\ndesign -copy-from gold -as gold gold\ndesign -copy-from gate -as gate gate\nequiv_make gold gate equiv\nhierarchy -top equiv\nequiv_simple -seq 1\nequiv_induct -seq 4\nequiv_status -assert\n'
 (d/'equivalence.ys').write_text(ys)
 try:
  run(['yosys','-Q','-T','-s',d/'equivalence.ys'],d/'equivalence.log',180)
  result=dict(status='PASS',method='Yosys equiv_simple + equiv_induct; same candidate RTL to mapped netlist',caveat='Temporal induction paired with mandatory reset/protocol mapped simulation; not a worst-case numerical error proof.')
 except Exception as exc:result=dict(status='INCONCLUSIVE',reason=str(exc)[:800],method='Yosys sequential equivalence; mapped simulation remains separately mandatory')
 save(d/'equivalence.json',result);return result
