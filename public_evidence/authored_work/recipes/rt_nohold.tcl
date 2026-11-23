set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
set_optimize_registers true -designs [get_designs {w64mul}]
set_dp_smartgen_options -booth_encoding true
compile_ultra -no_autoungroup
optimize_netlist -area
