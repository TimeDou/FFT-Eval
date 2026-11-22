# Target a faster mapping. The benchmark separately re-applies its own
# clock, I/O constraints and setup/hold checks to the exported cells.
ungroup -all -flatten
create_clock -name clk -period 580 [get_ports clk]
set_clock_uncertainty -setup 100 [get_clocks clk]
set_clock_transition 20 [get_clocks clk]
set_input_delay 0 -clock clk [get_ports {rst in_valid frame_start in_re* in_im*}]
set_output_delay 0 -clock clk [all_outputs]
set_fix_hold [get_clocks clk]
set_max_area 0
set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
compile_ultra -retime
optimize_netlist -area
compile -incremental_mapping -only_hold_time

