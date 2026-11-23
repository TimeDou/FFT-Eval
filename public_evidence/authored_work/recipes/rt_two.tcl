# Over-constrained first pass (560 ps), then relax to 592 ps and recover area.
proc fft_cons {p} {
  create_clock -name clk -period $p [get_ports clk]
  set_clock_uncertainty -setup 100 [get_clocks clk]
  set_clock_transition 20 [get_clocks clk]
  set_input_delay 0 -clock clk [get_ports {rst in_valid frame_start in_re* in_im*}]
  set_input_transition 20 [get_ports {rst in_valid frame_start in_re* in_im*}]
  set_output_delay 0 -clock clk [all_outputs]
  set_load 1 [all_outputs]
  set_false_path -from [get_ports rst]
}
fft_cons 560
set_fix_hold [get_clocks clk]
set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
set_optimize_registers true -designs [get_designs {w64mul w8rot3 w8rot6}]
compile_ultra -no_autoungroup
fft_cons 592
set_fix_hold [get_clocks clk]
set_max_area 0
compile_ultra -incremental -no_autoungroup
compile -incremental_mapping -only_hold_time
