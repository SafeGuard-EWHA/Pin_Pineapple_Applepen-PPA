# sta_vcd_power.tcl — 게이트레벨 시뮬 VCD 를 읽어 실제 스위칭 기반 전력 산출
#
# 정적(vectorless) 추정과 달리 모드 게이팅(Easy 82 %에서 후단 정지) 효과가 반영된다.
#
# 사용:
#   PLATFORM_DIR=... NETLIST=... SDC=... TOP=... VCD=... VCD_SCOPE=... REPORT=... \
#     openroad -exit sta_vcd_power.tcl
set platform_dir $::env(PLATFORM_DIR)
set netlist      $::env(NETLIST)
set sdc          $::env(SDC)
set top          $::env(TOP)
set vcd          $::env(VCD)
set scope        $::env(VCD_SCOPE)
set report       $::env(REPORT)

foreach lef [glob -nocomplain $platform_dir/lef/*tech*.lef] { read_lef $lef }
foreach lef [glob -nocomplain $platform_dir/lef/asap7sc7p5t*.lef] { read_lef $lef }
foreach lib [glob -nocomplain $platform_dir/lib/NLDM/*RVT_TT*.lib.gz \
                              $platform_dir/lib/NLDM/*RVT_TT*.lib] {
    read_liberty $lib
}
read_verilog $netlist
link_design $top
read_sdc $sdc

# 스위칭 파형 적용 (VCD 의 DUT 스코프)
read_vcd -scope $scope $vcd

set fp [open $report w]
puts $fp "=== $top : VCD-based power ==="
puts $fp "vcd   : $vcd"
puts $fp "scope : $scope"
puts $fp "--- report_power (VCD annotated) ---"
puts $fp [report_power -digits 6]
close $fp
puts "written $report"
