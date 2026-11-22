# Re-constrain the SAME mapped netlist at every trial. No re-synthesis and no
# conversion of a single fixed-clock slack into a maximum-frequency claim.
if {[catch {
source [file join [file dirname [info script]] paths.tcl]
set_app_var search_path [concat [get_app_var search_path] [list $WORK [file join $TECH_DIR db]]]
set_app_var link_path [concat [list *] $DBLIST]
read_verilog [file join $WORK mapped.v]
link_design fft64_top
set fmax_dir [file join $WORK fmax_scan]
file mkdir $fmax_dir
set trace [open [file join $fmax_dir trials.csv] w]
puts $trace "trial,period_ns,setup_slack_ns,hold_slack_ns,pass,actual_clock_period_ns"
set trial_count 0
proc fft_frequency_trial {period_ps} {
    global trace trial_count
    incr trial_count
    create_clock -name clk -period $period_ps [get_ports clk]
    set_clock_uncertainty -setup 100 [get_clocks clk]
    set_clock_transition 20 [get_clocks clk]
    set_input_delay 0 -clock clk [get_ports {rst in_valid frame_start in_re* in_im*}]
    set_input_transition 20 [get_ports {rst in_valid frame_start in_re* in_im*}]
    set_output_delay 0 -clock clk [all_outputs]
    set_load 1 [all_outputs]
    set_false_path -from [get_ports rst]
    update_timing
    if {[sizeof_collection [get_clocks *]] != 1} {error "Frequency scan requires exactly one clock"}
    set actual [get_attribute [get_clocks clk] period]
    if {abs($actual-$period_ps) > 0.001} {error "Clock period was not updated"}
    set setup_paths [get_timing_paths -delay_type max -max_paths 1]
    set hold_paths [get_timing_paths -delay_type min -max_paths 1]
    if {[sizeof_collection $setup_paths] != 1 || [sizeof_collection $hold_paths] != 1} {error "Missing constrained setup/hold path"}
    set setup [get_attribute $setup_paths slack]
    set hold [get_attribute $hold_paths slack]
    set pass [expr {$setup >= 0.0 && $hold >= 0.0}]
    puts $trace [format "%d,%.12f,%.12f,%.12f,%d,%.12f" $trial_count [expr {$period_ps/1000.0}] [expr {$setup/1000.0}] [expr {$hold/1000.0}] $pass [expr {$actual/1000.0}]]
    flush $trace
    return [list $pass $setup $hold]
}
foreach key {FFT_FMAX_MIN_PS FFT_FMAX_MAX_PS FFT_FMAX_TOL_PS FFT_FMAX_ITERATIONS} {
    if {![info exists ::env($key)] || ![string is double -strict $::env($key)] || $::env($key) <= 0} {error "Missing/invalid trusted scan parameter: $key"}
}
set minimum $::env(FFT_FMAX_MIN_PS)
set maximum $::env(FFT_FMAX_MAX_PS)
set tolerance $::env(FFT_FMAX_TOL_PS)
if {$minimum >= $maximum} {error "Invalid frequency scan interval"}
set high $maximum
if {![lindex [fft_frequency_trial $high] 0]} {error "The required target clock does not pass both setup and hold"}
set low $minimum
set low_result [fft_frequency_trial $low]
set capped [lindex $low_result 0]
if {$capped} {
    set high $low
} else {
    for {set iteration 0} {$high-$low > $tolerance && $iteration < $::env(FFT_FMAX_ITERATIONS)} {incr iteration} {
        set middle [expr {($high+$low)/2.0}]
        set result [fft_frequency_trial $middle]
        if {[lindex $result 2] < 0.0} {error "Hold violation during frequency scan"}
        if {[lindex $result 0]} {set high $middle} else {set low $middle}
    }
    if {$high-$low > $tolerance} {error "Frequency scan did not converge to its frozen resolution"}
}
set final [fft_frequency_trial $high]
if {![lindex $final 0]} {error "Final passing point could not be reproduced"}
redirect [file join $fmax_dir setup_at_passing.rpt] {report_timing -delay_type max -max_paths 5 -significant_digits 9}
redirect [file join $fmax_dir hold_at_passing.rpt] {report_timing -delay_type min -max_paths 5 -significant_digits 9}
redirect [file join $fmax_dir check_at_passing.rpt] {check_timing -verbose}
set f [open [file join $fmax_dir endpoint.json] w]
if {$capped} {set failing_json "null"} else {set failing_json [format "%.12f" [expr {$low/1000.0}]]}
puts $f [format {{"status":"CERTIFIED","passing_period_ns":%.12f,"failing_period_ns":%s,"passing_setup_slack_ns":%.12f,"passing_hold_slack_ns":%.12f,"hold_pass":true,"capped_at_minimum_period":%s,"trials":%d}} [expr {$high/1000.0}] $failing_json [expr {[lindex $final 1]/1000.0}] [expr {[lindex $final 2]/1000.0}] [expr {$capped ? "true" : "false"}] $trial_count]
close $f
close $trace
} task_error]} {
    puts stderr "TASK_FATAL: $task_error"
    exit 1
}
exit 0
