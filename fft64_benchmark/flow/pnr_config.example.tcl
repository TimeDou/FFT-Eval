# Copy to a separate file and fill every REQUIRED field with a MATCHED ASAP7
# physical kit. The DSBench environment itself does not include a PDK.
# Do not combine this Liberty with Nangate45/Sky130 LEF/RC.
set LEF_FILES [list REQUIRED_ASAP7_TECH_LEF REQUIRED_ASAP7_CELL_LEF]
set CORE_SITE REQUIRED_ASAP7_ROW_SITE
set QRC_TECH_FILE REQUIRED_MATCHED_ASAP7_RC_TECH
set POWER_PLAN_TCL REQUIRED_MATCHED_ASAP7_POWER_PLAN_TCL
set CORE_UTIL 0.55
set CORE_ASPECT 1.0
set CORE_MARGIN_UM 2.0
set POWER_NET VDD
set GROUND_NET VSS
# ASAP7 physical distributions sometimes use scaled coordinates. Confirm this
# kit's LEF/Liberty/RC scaling before using the suggested margin/utilization.
set PHYSICAL_SCALE_VERIFIED 0
# Verify Innovus's native constraint/report units AFTER reading this kit.
# Do not assume DC/PrimeTime's native ps normalization transfers to Innovus.
set PNR_UNITS_VERIFIED 0
set PNR_TIME_UNITS_PER_NS 1.0
set PNR_CAP_UNITS_PER_FF 0.001
# Above example values mean ns and pF. For native ps and fF use1000 and1.
