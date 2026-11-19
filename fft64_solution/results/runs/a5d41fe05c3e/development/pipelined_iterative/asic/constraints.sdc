create_clock -name clk -period 10000 [get_ports clk]
set_clock_uncertainty -setup 100 [get_clocks clk]
set_clock_transition 20 [get_clocks clk]
set_input_delay 0 -clock clk [get_ports {rst in_valid frame_start in_re* in_im*}]
set_input_transition 20 [get_ports {rst in_valid frame_start in_re* in_im*}]
set_output_delay 0 -clock clk [all_outputs]
set_load 1 [all_outputs]
# Reset is exercised functionally; frequency rating is for normal operation.
set_false_path -from [get_ports rst]
