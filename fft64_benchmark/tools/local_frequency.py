"""Fixed-netlist OpenSTA setup/hold clock scan; separate local calibration."""
from pathlib import Path
import hashlib,json,math,shutil
from common import COMB,SEQ,ROOT,read,save,sha,run,lock
from scoring import profile_policy,POLICY_SHA256
from toolchain import find_tool


def certify_local(asic):
    from frequency import validate_trials
    import csv
    asic=Path(asic).resolve();sta=find_tool('sta')
    if not sta:raise EnvironmentError('OpenSTA unavailable; set FFT_STA to the installed executable')
    cfg=profile_policy('architecture')['fmax_scan']
    identity=dict(mapped_sha256=sha(asic/'mapped.v'),scalar_netlist_sha256=sha(asic/'timing_netlist.v'),
        libraries={p.name:sha(p)for p in [COMB,SEQ]},sta_sha256=sha(sta),script_sha256=sha(__file__),policy_sha256=POLICY_SHA256,settings=cfg)
    key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:24]
    work=asic/'frequency_certificates'/key
    with lock(work/'lock'):
        if(work/'certificate.json').exists():return read(work/'certificate.json'),work
        script=f'read_liberty {{{COMB}}}\nread_liberty {{{SEQ}}}\nread_verilog {{{asic/"timing_netlist.v"}}}\nlink_design fft64_top\n'
        script+=r'''
set trace [open TRACE w]
puts $trace "trial,period_ns,actual_clock_period_ns,setup_slack_ns,hold_slack_ns,pass"
set trials 0
proc trial {p} {
 global trace trials
 incr trials
 create_clock -name clk -period $p [get_ports clk]
 set_clock_uncertainty -setup 100 [get_clocks clk]
 set_clock_transition 20 [get_clocks clk]
 set_input_delay 0 -clock clk [get_ports {rst in_valid frame_start in_re* in_im*}]
 set_input_transition 20 [get_ports {rst in_valid frame_start in_re* in_im*}]
 set_output_delay 0 -clock clk [all_outputs]
 set_load 1 [all_outputs]
 set_false_path -from [get_ports rst]
 set setup [sta::worst_slack -max]
 set hold [sta::worst_slack -min]
 set actual [get_property [get_clocks clk] period]
 set ok [expr {$setup>=0 && $hold>=0}]
 puts $trace [format "%d,%.12f,%.12f,%.12f,%.12f,%d" $trials [expr {$p/1000.}] [expr {$actual/1000.}] [expr {$setup/1000.}] [expr {$hold/1000.}] $ok]
 flush $trace
 return [list $ok $setup $hold]
}
set hi MAXIMUM
set lo MINIMUM
if {![lindex [trial $hi] 0]} {error "Required 10ns setup/hold failed"}
set cap [lindex [trial $lo] 0]
if {$cap} {set hi $lo} else {
 for {set i 0} {$hi-$lo>TOLERANCE && $i<MAXITER} {incr i} {
  set p [expr {($hi+$lo)/2.}]
  if {[lindex [trial $p] 0]} {set hi $p} else {set lo $p}
 }
}
set last [trial $hi]
puts "FFT_FINAL $hi $lo $cap $trials [lindex $last 1] [lindex $last 2]"
check_setup -verbose
report_checks -path_delay max -digits 9 > SETUPREPORT
report_checks -path_delay min -digits 9 > HOLDREPORT
close $trace
exit
'''
        replacements={'TRACE':'{'+str(work/'trials.csv')+'}','MAXIMUM':str(cfg['maximum_period_ns']*1000),'MINIMUM':str(cfg['minimum_period_ns']*1000),'TOLERANCE':str(cfg['resolution_ns']*1000),'MAXITER':str(cfg['maximum_iterations']),'SETUPREPORT':'{'+str(work/'setup_at_passing.rpt')+'}','HOLDREPORT':'{'+str(work/'hold_at_passing.rpt')+'}'}
        for a,b in replacements.items():script=script.replace(a,b)
        (work/'scan.tcl').write_text(script);run([sta,'-exit',work/'scan.tcl'],work/'fmax.log',600,cwd=work)
        import re
        log=(work/'fmax.log').read_text()
        if re.search(r'^Error|unconstrained endpoints|missing set_input_delay|missing set_output_delay',log,re.M):raise EnvironmentError('OpenSTA scan failed: '+log[-2000:])
        row=re.search(r'FFT_FINAL (\S+) (\S+) (\S+) (\S+) (\S+) (\S+)',log)
        if not row:raise EnvironmentError('Missing OpenSTA clock-scan endpoint')
        passing,failing,cap,n,setup,hold=map(float,row.groups())
        endpoint=dict(status='CERTIFIED',passing_period_ns=passing/1000,failing_period_ns=None if cap else failing/1000,
            hold_pass=hold>=0,passing_setup_slack_ns=setup/1000,passing_hold_slack_ns=hold/1000,
            capped_at_minimum_period=bool(cap),trials=int(n))
        with(work/'trials.csv').open()as f:
            trials=[dict(period_ns=float(r['period_ns']),actual_clock_period_ns=float(r['actual_clock_period_ns']),setup_slack_ns=float(r['setup_slack_ns']),hold_slack_ns=float(r['hold_slack_ns']),**{'pass':r['pass']=='1'})for r in csv.DictReader(f)]
        validate_trials(endpoint,trials,cfg)
        result=dict(endpoint,**identity,certified_frequency_MHz=1000/endpoint['passing_period_ns'],certificate_directory=str(work),measurement='OpenSTA ideal-interconnect fixed-netlist clock scan; local backend only')
        save(work/'certificate.json',result);return result,work
