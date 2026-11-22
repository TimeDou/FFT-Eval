# Agent synthesis recipe: steer optimization toward a short clock period.
# Final grading re-constrains this fixed netlist with the benchmark SDC.
create_clock -name clk -period 1200 [get_ports clk]
set_clock_uncertainty -setup 100 [get_clocks clk]
set_clock_transition 20 [get_clocks clk]
set_input_delay 0 -clock clk [get_ports {rst in_valid frame_start in_re* in_im*}]
set_input_transition 20 [get_ports {rst in_valid frame_start in_re* in_im*}]
set_output_delay 0 -clock clk [all_outputs]
set_load 1 [all_outputs]
set_false_path -from [get_ports rst]
ungroup -all -flatten
set_fix_hold [get_clocks clk]
set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
compile_ultra -timing_high_effort_script
compile -incremental_mapping -only_hold_time
