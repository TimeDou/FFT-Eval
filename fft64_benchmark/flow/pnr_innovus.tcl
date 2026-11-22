# Optional Innovus P&R template; outside the scored synthesis/STA flow.
source [file join [file dirname [info script]] paths.tcl]
if {![info exists ::env(FFT_PNR_CONFIG)]} {error "Set FFT_PNR_CONFIG to a completed, matched ASAP7 physical configuration"}
source $::env(FFT_PNR_CONFIG)
if {!$PHYSICAL_SCALE_VERIFIED} {error "LEF/Liberty/RC scaling has not been verified; stop rather than invent physical QoR"}
if {!$PNR_UNITS_VERIFIED || $PNR_TIME_UNITS_PER_NS <= 0 || $PNR_CAP_UNITS_PER_FF <= 0} {error "Verify native Innovus time/capacitance units and fill the conversion factors"}
foreach path [concat $LEF_FILES [list $QRC_TECH_FILE $POWER_PLAN_TCL]] {
    if {[string match *REQUIRED* $path] || ![file exists $path]} {error "Missing matched physical asset: $path"}
}
if {[string match *REQUIRED* $CORE_SITE]} {error "Provide the exact LEF row site"}
if {![file exists [file join $WORK mapped.v]]} {error "Run DC mapping before P&R"}
set mmmc [open [file join $WORK mmmc.tcl] w]
# Keep physical-flow unit conversion explicit. The DC/PT SDC uses native ps;
# this separate SDC carries the SAME10ns/0.1ns/1fF specification in kit units.
set pnr_sdc [file join $WORK pnr_constraints.sdc]
set sf [open $pnr_sdc w]
puts $sf [format {create_clock -name clk -period %.12g [get_ports clk]} [expr {10.0*$PNR_TIME_UNITS_PER_NS}]]
puts $sf [format {set_clock_uncertainty -setup %.12g [get_clocks clk]} [expr {0.1*$PNR_TIME_UNITS_PER_NS}]]
puts $sf [format {set_clock_transition %.12g [get_clocks clk]} [expr {0.02*$PNR_TIME_UNITS_PER_NS}]]
puts $sf {set_input_delay 0 -clock clk [get_ports {rst in_valid frame_start in_re* in_im*}]}
puts $sf [format {set_input_transition %.12g [get_ports {rst in_valid frame_start in_re* in_im*}]} [expr {0.02*$PNR_TIME_UNITS_PER_NS}]]
puts $sf {set_output_delay 0 -clock clk [all_outputs]}
puts $sf [format {set_load %.12g [all_outputs]} $PNR_CAP_UNITS_PER_FF]
puts $sf {set_false_path -from [get_ports rst]}
close $sf
puts $mmmc [list create_library_set -name TT -timing [list [file join $TECH_DIR ASAP7_RVT_TT_nldm_NO_FAHA.lib] [file join $TECH_DIR ASAP7_SEQ_RVT_TT_nldm_220123.lib]]]
puts $mmmc [list create_rc_corner -name RC_TT -T 25 -qx_tech_file $QRC_TECH_FILE]
puts $mmmc {create_delay_corner -name DELAY_TT -library_set TT -rc_corner RC_TT}
puts $mmmc [list create_constraint_mode -name FUNC -sdc_files [list $pnr_sdc]]
puts $mmmc {create_analysis_view -name VIEW_TT -constraint_mode FUNC -delay_corner DELAY_TT}
puts $mmmc {set_analysis_view -setup {VIEW_TT} -hold {VIEW_TT}}
close $mmmc
set init_verilog [file join $WORK mapped.v]
set init_top_cell fft64_top
set init_lef_file $LEF_FILES
set init_mmmc_file [file join $WORK mmmc.tcl]
set init_pwr_net $POWER_NET
set init_gnd_net $GROUND_NET
init_design
set pnr_recipe [file join $TASK_ROOT flow templates pnr_opt.tcl]
if {[info exists ::env(FFT_PNR_OPT_FILE)]} {set pnr_recipe $::env(FFT_PNR_OPT_FILE)}
source $pnr_recipe
timeDesign -postRoute -outDir [file join $WORK postroute_setup]
timeDesign -postRoute -hold -outDir [file join $WORK postroute_hold]
saveDesign [file join $WORK fft64_postroute.enc]
saveNetlist [file join $WORK fft64_postroute.v]
defOut [file join $WORK fft64_postroute.def]
rcOut -spef [file join $WORK fft64_postroute.spef]
verifyGeometry -report [file join $WORK geometry.rpt]
verifyConnectivity -type all -report [file join $WORK connectivity.rpt]
exit
