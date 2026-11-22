# Optional public Innovus implementation recipe. Requires a matched physical kit.
# The driver has initialized the design, libraries and default constraints.
# Replace this body to choose floorplanning, placement, CTS and routing commands.
# Variables: CORE_SITE, CORE_ASPECT, CORE_UTIL, CORE_MARGIN_UM, POWER_NET,
# GROUND_NET, POWER_PLAN_TCL, WORK. Tool reports/exports follow this recipe.
# Current benchmark scores synthesis/ideal-interconnect STA, not this P&R flow.
floorPlan -site $CORE_SITE -r $CORE_ASPECT $CORE_UTIL $CORE_MARGIN_UM $CORE_MARGIN_UM $CORE_MARGIN_UM $CORE_MARGIN_UM
globalNetConnect $POWER_NET -type pgpin -pin $POWER_NET -inst *
globalNetConnect $GROUND_NET -type pgpin -pin $GROUND_NET -inst *
# PDK-specific PDN is deliberately explicit, never fabricated from a different node.
source $POWER_PLAN_TCL
placeDesign
optDesign -preCTS
create_ccopt_clock_tree_spec -file [file join $WORK ccopt.spec]
ccopt_design
optDesign -postCTS
routeDesign
optDesign -postRoute
