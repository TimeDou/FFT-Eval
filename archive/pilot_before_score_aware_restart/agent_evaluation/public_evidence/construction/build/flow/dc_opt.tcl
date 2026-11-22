# Optimize for a 1.2 ns synthesis target. Public import and STA use the
# benchmark constraints and independently re-certify the mapped netlist.
create_clock -name clk -period 1200 [get_ports clk]
set_clock_uncertainty -setup 100 [get_clocks clk]
set_clock_transition 20 [get_clocks clk]
set_input_delay 0 -clock clk [get_ports {rst in_valid frame_start in_re* in_im*}]
set_output_delay 0 -clock clk [all_outputs]

ungroup -all -flatten
set_fix_hold [get_clocks clk]
set_max_area 0
set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
compile_ultra
optimize_netlist -area
compile -incremental_mapping -only_hold_time
