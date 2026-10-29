# sta_prelayout.tcl - 합성 넷리스트(1_synth.v)에 대한 pre-layout STA + 전력 추정
# 사용:  openroad -exit sta_prelayout.tcl   (환경변수 PLATFORM_DIR NETLIST SDC TOP REPORT)
set platform_dir $::env(PLATFORM_DIR)
set netlist      $::env(NETLIST)
set sdc          $::env(SDC)
set top          $::env(TOP)
set report       $::env(REPORT)

# OpenROAD 는 read_verilog 전에 기술(LEF)이 필요하다
foreach lef [glob -nocomplain $platform_dir/lef/*tech*.lef] { read_lef $lef }
foreach lef [glob -nocomplain $platform_dir/lef/asap7sc7p5t*.lef] { read_lef $lef }
foreach lib [glob -nocomplain $platform_dir/lib/NLDM/*RVT_TT*.lib.gz $platform_dir/lib/NLDM/*RVT_TT*.lib] {
    read_liberty $lib
}
read_verilog $netlist
link_design $top
read_sdc $sdc

# 전력 활동률 가정 (벡터 없는 상대 비교용):
#   가중치/bias 포트 = 0 (추론 중 고정)  /  픽셀 입력 = 0.25  /  제어 = 0.05
set_power_activity -input -activity 0.0
catch { set_power_activity -input_ports [get_ports pixel_in*] -activity 0.25 }
catch { set_power_activity -input_ports [get_ports data_in*] -activity 0.25 }
catch { set_power_activity -input_ports [get_ports scores_flat*] -activity 0.25 }
catch { set_power_activity -input_ports [get_ports {start front_done back_done valid_in}] -activity 0.05 }

set fp [open $report w]
puts $fp "=== $top ==="
puts $fp "--- report_checks (setup, worst) ---"
puts $fp [report_checks -path_delay max -format full_clock_expanded -digits 1 -group_count 1]
puts $fp "--- WNS / TNS ---"
puts $fp "wns [sta::worst_slack -max]   tns [sta::total_negative_slack -max]"
puts $fp "--- report_power ---"
puts $fp [report_power -digits 6]
close $fp
puts "written $report"
