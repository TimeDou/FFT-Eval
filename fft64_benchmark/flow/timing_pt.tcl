source [file join [file dirname [info script]] paths.tcl]
set_app_var search_path [concat [get_app_var search_path] [list $WORK [file join $TECH_DIR db]]]
set_app_var link_path [concat [list *] $DBLIST]
read_verilog [file join $WORK mapped.v]
link_design fft64_top
source [file join $TASK_ROOT flow constraints.sdc]
update_timing
redirect [file join $WORK pt_units.rpt] {report_units}
redirect [file join $WORK pt_check.rpt] {check_timing -verbose}
redirect [file join $WORK pt_timing.rpt] {report_timing -delay_type max -max_paths 10 -significant_digits 6}
set paths [get_timing_paths -delay_type max -max_paths 1]
if {[sizeof_collection $paths] != 1} {error "No fully constrained setup path"}
set slack [get_attribute $paths slack]
set f [open [file join $WORK pt_metrics.json] w]
puts $f [format {{"worst_setup_slack_ns":%.9f,"effective_required_period_ns":%.9f,"clock_period_ns":10.0,"setup_uncertainty_ns":0.1,"flow":"PrimeTime ideal-interconnect pre-layout; native ps converted to ns"}} [expr {$slack/1000.0}] [expr {(10000.0-$slack)/1000.0}]]
close $f
exit
