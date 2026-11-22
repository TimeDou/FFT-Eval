# Default optimization recipe. Copy to submission/flow/dc_opt.tcl and replace
# this body to explore DC commands, app variables and compile strategies.
# The design is elaborated and the default synthesis constraints are loaded.
# Examples to investigate on the installed DC (check `help` for support):
#   compile_ultra -timing_high_effort_script
#   compile_ultra -retime
#   compile -map_effort high -area_effort high
#   compile_ultra -incremental
# You may change the synthesis target to steer optimization. Final timing is
# independently measured with the benchmark's fixed constraints.
# Keep the external clk/reset/transaction behavior; do not insert clock gating.
ungroup -all -flatten
set_fix_hold [get_clocks clk]
set_max_area 0
set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
compile_ultra -area_high_effort_script
compile -incremental_mapping -only_hold_time
