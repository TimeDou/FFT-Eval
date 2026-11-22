# Run once in the commercial container: lc_shell -f compile_libraries.tcl.
# This script is exported but cannot be executed in the local open-source host.
set TASK_ROOT [file normalize [file join [file dirname [info script]] ..]]
set TECH_DIR [file join $TASK_ROOT tech]
if {[info exists ::env(FFT_TECH_DIR)]} {set TECH_DIR [file normalize $::env(FFT_TECH_DIR)]}
file mkdir [file join $TECH_DIR db]
foreach pair {{ASAP7_RVT_TT_nldm_NO_FAHA.lib comb_rvt_tt.db} {ASAP7_SEQ_RVT_TT_nldm_220123.lib seq_rvt_tt.db}} {
    set src [file join $TECH_DIR [lindex $pair 0]]
    set f [open $src r];set text [read $f];close $f
    if {![regexp {library\s*\(\s*([^\s\)]+)\s*\)} $text unused libname]} {error "No Liberty library name: $src"}
    read_lib $src
    write_lib $libname -format db -output [file join $TECH_DIR db [lindex $pair 1]]
}
exit
