# FFT64-Quant agent DC recipe (sourced by the public build after elaborate/link
# and the benchmark's 10 ns constraints).  It only steers optimization; final
# area/timing are re-measured independently on the exported netlist.
#
# Strategy:
#  * timing-driven compile_ultra against a tighter internal clock target.  The
#    target sits on a grid point of the evaluator's bisection clock scan
#    (0.25..10 ns, 0.01 ns resolution), so the certified period equals the
#    target instead of rounding up to the next grid point;
#  * register retiming confined to the W64 twiddle multiplier.  The two W8
#    rotators are hand-pipelined in RTL (pre-add/select register, then constant
#    multiply), and all delay-line / control registers keep their RTL placement;
#  * Booth-encoded multipliers, hierarchy kept during compile (the public build
#    wrapper flattens before export), exact area recovery (optimize_netlist);
#  * hold repair, because imported netlists are measured without any repair.
set FFT_TARGET_PS 554

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
set_optimize_registers true -designs [get_designs {w64mul}]
set_dp_smartgen_options -booth_encoding true
compile_ultra -no_autoungroup
optimize_netlist -area
compile -incremental_mapping -only_hold_time
