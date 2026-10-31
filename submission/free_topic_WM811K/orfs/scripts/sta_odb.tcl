# sta_odb.tcl - ORFS 1_synth.odb 기반 pre-layout STA + 정적 전력 (환경변수 PLATFORM_DIR ODB SDC REPORT)
set platform_dir $::env(PLATFORM_DIR)
foreach lib [glob -nocomplain $platform_dir/lib/NLDM/*RVT_TT*.lib.gz $platform_dir/lib/NLDM/*RVT_TT*.lib] { read_liberty $lib }
read_db $::env(ODB)
read_sdc $::env(SDC)
set_power_activity -input -activity 0.0
catch { set_power_activity -input_ports [get_ports pixel_in*] -activity 0.25 }
catch { set_power_activity -input_ports [get_ports data_in*] -activity 0.25 }
catch { set_power_activity -input_ports [get_ports scores_flat*] -activity 0.25 }
catch { set_power_activity -input_ports [get_ports {start front_done back_done valid_in}] -activity 0.05 }
report_checks -path_delay max -format full_clock_expanded -digits 1 -group_count 1
puts "wns [sta::worst_slack -max]   tns [sta::total_negative_slack -max]"
report_power -digits 6
set fp [open $::env(REPORT) w]
puts $fp "wns [sta::worst_slack -max]   tns [sta::total_negative_slack -max]"
close $fp
