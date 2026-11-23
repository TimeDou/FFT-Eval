set_fix_hold [get_clocks clk]
set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
set_optimize_registers true -designs [get_designs {w64mul w8rot3 w8rot6}]
set_dp_smartgen_options -booth_encoding false
compile_ultra -no_autoungroup
compile -incremental_mapping -only_hold_time
