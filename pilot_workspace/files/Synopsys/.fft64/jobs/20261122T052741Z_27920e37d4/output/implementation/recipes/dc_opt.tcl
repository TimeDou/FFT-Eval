# Candidate: steer mapping with a 2 ns clock. Independent evaluation still
# uses the fixed 10 ns setup/hold constraints and scans this exported netlist.
create_clock -name clk -period 2000 [get_ports clk]
ungroup -all -flatten
set_fix_hold [get_clocks clk]
set_max_area 0
set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
compile_ultra -area_high_effort_script
compile -incremental_mapping -only_hold_time
