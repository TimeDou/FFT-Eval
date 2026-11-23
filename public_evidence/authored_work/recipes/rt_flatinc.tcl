# rt_arith, then flatten and an incremental compile_ultra across boundaries
set_fix_hold [get_clocks clk]
set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
set_optimize_registers true -designs [get_designs {w64mul w8rot3 w8rot6}]
compile_ultra -no_autoungroup
ungroup -all -flatten
compile_ultra -incremental
compile -incremental_mapping -only_hold_time
