# Optional additional complete sequential equivalence proof.
# Mandatory mapped-netlist simulation is run even when this proof succeeds.
source [file join [file dirname [info script]] paths.tcl]
set_svf [file join $WORK design.svf]
foreach db $DBLIST {read_db -r $db;read_db -i $db}
read_sverilog -r [file join $WORK staged.sv]
set_top r:/WORK/fft64_top
read_verilog -i [file join $WORK mapped.v]
set_top i:/WORK/fft64_top
match
set passed [verify]
report_failing_points > [file join $WORK fm_failing.rpt]
set f [open [file join $WORK fm_status.txt] w]
if {$passed} {puts $f PASS} else {puts $f FAILED}
close $f
if {!$passed} {exit 2}
exit
