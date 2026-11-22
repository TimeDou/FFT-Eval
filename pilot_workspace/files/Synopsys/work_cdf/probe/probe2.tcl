set TECH "/mnt/mydata/.fft64/tech/99619e6e51b75f151556"
set_app_var target_library [list $TECH/db/comb_rvt_tt.db $TECH/db/seq_rvt_tt.db]
set_app_var link_library [concat [list *] $target_library]
define_design_lib WORK -path /mnt/mydata/work_cdf/probe/work2
set mods {rf64x44_1r1w rf32x44_1r1w rf32x44_2r2w rf64x44_1r1w_banked rf64x88_1r1w rf64x44_2r2w_indep bfly}
foreach m $mods {
  analyze -format verilog /mnt/mydata/work_cdf/probe/probe2.v
  elaborate $m
  current_design $m
  link
  create_clock -name clk -period 10000 [get_ports clk]
  set_max_area 0
  compile_ultra -area_high_effort_script
  set ar 0.0
  foreach_in_collection c [get_cells -hierarchical *] {
    if {[get_attribute $c is_hierarchical]} {continue}
    set ref [get_attribute $c ref_name]
    set lc [get_lib_cells -quiet */$ref]
    if {[sizeof_collection $lc]==1} { set ar [expr {$ar+[get_attribute $lc area]}] }
  }
  set tp [get_timing_paths -delay_type max -max_paths 1]
  set sl [get_attribute $tp arrival]
  puts "PROBE2_AREA $m $ar delay=$sl"
  remove_design -all
}
exit
