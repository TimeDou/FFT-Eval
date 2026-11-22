# Shared, fixed by the task author; candidates cannot supply timing commands.
set TASK_ROOT [file normalize [file join [file dirname [info script]] ..]]
if {[info exists ::env(FFT_TASK_ROOT)]} {set TASK_ROOT [file normalize $::env(FFT_TASK_ROOT)]}
set TECH_DIR [file join $TASK_ROOT tech]
if {[info exists ::env(FFT_TECH_DIR)]} {set TECH_DIR [file normalize $::env(FFT_TECH_DIR)]}
if {![info exists ::env(FFT_WORK)]} {error "FFT_WORK must name a trusted evaluation build directory"}
set WORK [file normalize $::env(FFT_WORK)]
file mkdir $WORK
set DBLIST [list [file join $TECH_DIR db comb_rvt_tt.db] [file join $TECH_DIR db seq_rvt_tt.db]]
foreach db $DBLIST {if {![file exists $db]} {error "Missing compiled ASAP7 DB: $db; run prepare_libraries first"}}
