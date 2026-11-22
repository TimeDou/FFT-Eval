# Explicit timing-target experiment. Independent scoring retains the fixed SDC.
ungroup -all -flatten
create_clock -name clk -period 700 [get_ports clk]
set_fix_hold [get_clocks clk]
set_max_area 0
set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
compile_ultra -timing_high_effort_script
compile -incremental_mapping -only_hold_time
