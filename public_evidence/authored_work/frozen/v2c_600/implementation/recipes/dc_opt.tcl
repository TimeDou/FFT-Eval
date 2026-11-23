# FFT64-Quant agent DC recipe (sourced by the public build after elaborate/link
# and the benchmark's 10 ns constraints).  It only steers optimization; final
# area/timing are re-measured independently on the exported netlist.
#
# Strategy:
#  * timing-driven compile_ultra against a tighter internal clock target, so the
#    exported netlist certifies a short clock period in the benchmark's scan;
#  * register retiming confined to the twiddle multiplier and the two W8
#    rotators (their extra pipeline registers are spread through the arithmetic);
#    all delay-line / control registers keep their RTL placement;
#  * hierarchy kept during compile (the wrapper flattens before export);
#  * hold repair, because imported netlists are measured without any repair.
set FFT_TARGET_PS 600

create_clock -name clk -period $FFT_TARGET_PS [get_ports clk]
set_clock_uncertainty -setup 100 [get_clocks clk]
set_clock_transition 20 [get_clocks clk]
set_input_delay 0 -clock clk [get_ports {rst in_valid frame_start in_re* in_im*}]
set_input_transition 20 [get_ports {rst in_valid frame_start in_re* in_im*}]
set_output_delay 0 -clock clk [all_outputs]
set_load 1 [all_outputs]
set_false_path -from [get_ports rst]

set_fix_hold [get_clocks clk]
set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
set_optimize_registers true -designs [get_designs {w64mul w8rot3 w8rot6}]
compile_ultra -no_autoungroup
compile -incremental_mapping -only_hold_time
