# Flattened timing-driven compile; adaptive retiming allowed only on registers
# that originate in the three rotator blocks (u_m4, u_r3, u_r6).
set_fix_hold [get_clocks clk]
set_fix_multiple_port_nets -all -buffer_constants
set_dont_touch_network [get_ports clk]
ungroup -all -flatten
set seqs [get_cells -hierarchical * -filter "is_sequential==true"]
set_dont_retime $seqs true
set rot [filter_collection $seqs "full_name =~ u_m4* || full_name =~ u_r3* || full_name =~ u_r6*"]
echo "ROTATOR_REGS [sizeof_collection $rot] of [sizeof_collection $seqs]"
set_dont_retime $rot false
compile_ultra -retime
compile -incremental_mapping -only_hold_time
