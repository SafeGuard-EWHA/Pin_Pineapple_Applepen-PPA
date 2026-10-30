# OpenROAD / OpenSTA pre-layout VCD power audit.
# Required environment: PLATFORM_DIR ODB SDC VCD SCOPE
# Optional: GATE_PIN (exact mapped gate output, inspected after synthesis)
foreach family {AO INVBUF OA SEQ SIMPLE} {
  set libs [glob $::env(PLATFORM_DIR)/lib/NLDM/asap7sc7p5t_${family}_RVT_TT_nldm_*.lib*]
  if {[llength $libs] != 1} {error "Expected exactly one TT library for $family"}
  set lib [lindex $libs 0]
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
if {[info exists ::env(PROPAGATE_CLOCKS)] && $::env(PROPAGATE_CLOCKS) eq "1"} {
  set_propagated_clock [all_clocks]
  puts "AUDIT_PROPAGATED_CLOCKS 1"
} else {
  puts "AUDIT_PROPAGATED_CLOCKS 0"
}
report_units
check_setup -verbose
report_checks -path_delay max -format full_clock_expanded -group_path_count 5 -digits 6
report_checks -path_delay min -format full_clock_expanded -group_path_count 5 -digits 6
if {[info exists ::env(GATE_PIN)] && $::env(GATE_PIN) ne ""} {
  regsub {/GCLK$} $::env(GATE_PIN) /ENA ena_path
  puts "AUDIT_ICG_ENABLE_TIMING $ena_path"
  report_checks -to [get_pins $ena_path] -path_delay min_max -format full_clock_expanded -digits 6
}
report_clock_properties
report_check_types -clock_gating_setup -clock_gating_hold -verbose -digits 6
report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 6
puts "AUDIT_WNS [sta::worst_slack -max]"
puts "AUDIT_MIN_SLACK [sta::worst_slack -min]"
if {[info exists ::env(SKIP_POWER)] && $::env(SKIP_POWER) eq "1"} {exit}
read_vcd -scope $::env(SCOPE) $::env(VCD)
report_activity_annotation
report_power -digits 9
if {[info exists ::env(POWER_JSON)]} {
  report_power -format json -digits 9 > $::env(POWER_JSON)
}
# Aggregate JSON and text reports above are supported by this pinned OpenSTA.
# Per-instance ranking is omitted: this build does not support that option.
exit
