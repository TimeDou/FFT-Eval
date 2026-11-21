# ASAP7 library native time unit is 1ps, capacitance is 1fF.
create_clock -name clk -period 10000 [get_ports clk]
set_clock_uncertainty -setup 100 [get_clocks clk]
set_clock_transition 20 [get_clocks clk]
set_input_delay 0 -clock clk [get_ports {rst in_valid frame_start in_re* in_im*}]
set_input_transition 20 [get_ports {rst in_valid frame_start in_re* in_im*}]
set_output_delay 0 -clock clk [all_outputs]
set_load 1 [all_outputs]
# Reset must work in simulation. Performance rating excludes reset switching;
# reset is released at least two full cycles before the first input packet.
set_false_path -from [get_ports rst]
