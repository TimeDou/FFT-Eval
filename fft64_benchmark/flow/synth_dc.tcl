# Batch shells can log a Tcl error and continue to exit successfully. Stop at
# the first Tcl failure, and leave no partial metrics JSON for the evaluator.
if {[catch {
source [file join [file dirname [info script]] paths.tcl]
set_app_var target_library $DBLIST
set_host_options -max_cores 2
set_app_var link_library [concat [list *] $DBLIST]
define_design_lib WORK -path [file join $WORK dc_work]
set_svf [file join $WORK design.svf]
analyze -format sverilog [file join $WORK staged.sv]
elaborate fft64_top
current_design fft64_top
link
uniquify
ungroup -all -flatten
source [file join $TASK_ROOT flow constraints.sdc]
# The common physical flow repairs minimum-delay violations as well as setup.
# Both scoring profiles and all accurate baselines use this same setting.
set_fix_hold [get_clocks clk]
set_max_area 0
set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
# No gating/retiming setting supplied by the candidate. Extra RTL pipeline cuts
# remain permitted and are verified against the latency/protocol contract.
compile_ultra -area_high_effort_script
# compile_ultra area mode does not repair all short input-to-register paths
# on DC L-2016.03. Run the documented minimum-delay-only incremental pass.
compile -incremental_mapping -only_hold_time
change_names -rules verilog -hierarchy
set leaf_count 0
set ar 0.0
set seq_area 0.0
foreach_in_collection c [get_cells -hierarchical *] {
    if {[get_attribute $c is_hierarchical]} {continue}
    incr leaf_count
    set ref [get_attribute $c ref_name]
    if {![regexp {ASAP7_75t_R$} $ref]} {error "Unmapped/GTECH/foreign cell: $ref"}
    set libcell [get_lib_cells -quiet */$ref]
    if {[sizeof_collection $libcell] != 1} {error "Ambiguous/missing target cell: $ref"}
    set cell_area [get_attribute $libcell area]
    if {![string is double -strict $cell_area] || $cell_area <= 0.0 || $cell_area >= Inf} {
        error "Missing/invalid library area for $ref: '$cell_area'"
    }
    # Count every mapped leaf instance exactly once. A top-level design area
    # attribute is not available in all DC versions; report_area is retained
    # below for independent inspection of the same mapped design.
    set ar [expr {$ar+$cell_area}]
    if {[regexp {^DFF} $ref]} {
        set seq_area [expr {$seq_area+$cell_area}]
        set clknet [get_nets -of_objects [get_pins [get_object_name $c]/CLK]]
        if {[sizeof_collection $clknet] != 1 || [get_object_name $clknet] != "clk"} {error "TASK_DESIGN_INVALID: Only the direct top-level positive-edge clk is permitted"}
    } elseif {[regexp {^(LH|ICG)} $ref]} {error "TASK_DESIGN_INVALID: Latch/derived clock not permitted"}
}
if {$leaf_count == 0 || $ar <= 0.0 || $ar >= Inf} {error "No finite positive mapped cell area"}
redirect [file join $WORK dc_check.rpt] {check_design}
redirect [file join $WORK dc_units.rpt] {report_units}
redirect [file join $WORK dc_area.rpt] {report_area -hierarchy}
redirect [file join $WORK dc_timing.rpt] {report_timing -delay_type max -max_paths 5}
write -format verilog -hierarchy -output [file join $WORK mapped.v]
write -format ddc -hierarchy -output [file join $WORK mapped.ddc]
write_sdc [file join $WORK dc_generated.sdc]
set n $leaf_count
set metrics_tmp [file join $WORK dc_metrics.json.tmp]
set f [open $metrics_tmp w]
puts $f [format {{"area_um2":%.9f,"register_area_um2":%.9f,"cells":%d,"area_method":"sum_mapped_leaf_library_cell_area","flow":"DesignCompiler compile_ultra area_high_effort; pre-layout"}} $ar $seq_area $n]
close $f
file rename -force $metrics_tmp [file join $WORK dc_metrics.json]
set_svf -off
} task_error]} {
    puts stderr "TASK_FATAL: $task_error"
    exit 1
}
exit 0
