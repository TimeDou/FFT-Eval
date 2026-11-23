# Retiming only inside the W64 multiplier (W8 rotators are hand-pipelined), area recovery.
set_fix_hold [get_clocks clk]
set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
set_optimize_registers true -designs [get_designs {w64mul}]
set_dp_smartgen_options -booth_encoding true -booth_radix8 true
compile_ultra -no_autoungroup
optimize_netlist -area
compile -incremental_mapping -only_hold_time
