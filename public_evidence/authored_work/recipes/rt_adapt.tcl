# Timing-driven compile with adaptive retiming on the flattened design.
ungroup -all -flatten
set_fix_hold [get_clocks clk]
set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
compile_ultra -retime
compile -incremental_mapping -only_hold_time
