# OpenROAD / OpenSTA pre-layout VCD power audit.
# Required environment: PLATFORM_DIR ODB SDC VCD SCOPE
# Optional: GATE_PIN (exact mapped gate output, inspected after synthesis)
foreach lib [lsort [glob $::env(PLATFORM_DIR)/lib/NLDM/*RVT_TT*.lib*]] {
  puts "AUDIT_LIB $lib"
  read_liberty $lib
}
read_db $::env(ODB)
read_sdc $::env(SDC)
if {[info exists ::env(GATE_PIN)] && $::env(GATE_PIN) ne ""} {
  set gate_pin [get_pins $::env(GATE_PIN)]
  if {[llength $gate_pin] != 1} {error "Expected exactly one mapped clock-gate output"}
  create_generated_clock -name clk_backend -source [get_ports clk] -divide_by 1 $gate_pin
  puts "AUDIT_GATE_PIN $::env(GATE_PIN)"
}
report_units
check_setup -verbose
report_checks -path_delay max -format full_clock_expanded -group_path_count 5 -digits 6
report_clock_properties
report_check_types -clock_gating_setup -clock_gating_hold -verbose -digits 6
report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 6
puts "AUDIT_WNS [sta::worst_slack -max]"
read_vcd -scope $::env(SCOPE) $::env(VCD)
report_activity_annotation
report_power -digits 9
if {[info exists ::env(POWER_JSON)]} {
  report_power -format json -digits 9 > $::env(POWER_JSON)
}
report_power -highest_power_instances 20 -digits 9
exit
