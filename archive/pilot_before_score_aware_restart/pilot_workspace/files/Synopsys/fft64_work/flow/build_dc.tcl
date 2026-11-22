# Public optimization worker. Agent Tcl is executed here, outside hidden grading.
if {[catch {
source [file join [file dirname [info script]] paths.tcl]
set_app_var target_library $DBLIST
set_app_var link_library [concat [list *] $DBLIST]
set_host_options -max_cores 2
define_design_lib WORK -path [file join $WORK dc_work]
set_svf [file join $WORK build.svf]
analyze -format sverilog [file join $WORK source.sv]
elaborate fft64_top
current_design fft64_top
link
uniquify
source [file join $TASK_ROOT flow constraints.sdc]
source $::env(FFT_AGENT_DC_RECIPE)
# The exported interface is a flat structural netlist, regardless of the
# hierarchy retained during the agent's optimization.
current_design fft64_top
ungroup -all -flatten
change_names -rules verilog -hierarchy
write -format verilog -hierarchy -output [file join $WORK mapped.v]
redirect [file join $WORK build_area.rpt] {report_area -hierarchy}
redirect [file join $WORK build_timing.rpt] {report_timing -delay_type max -max_paths 5}
set_svf -off
} task_error]} {
    puts stderr "TASK_FATAL: $task_error"
    exit 1
}
exit 0
