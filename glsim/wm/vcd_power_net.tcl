# WM VCD 기반 전력 (OpenROAD/OpenSTA, 넷리스트 기반: ODB 없이 실행 가능)
# 환경변수: PLATFORM_DIR(ASAP7 플랫폼 폴더) NET(넷리스트 .v) TOP(adapath_wm_npu 또는 baseline_wm_npu) SDC VCD SCOPE(tb_gatelevel/dut)
set platform_dir $::env(PLATFORM_DIR)
foreach lib [glob -nocomplain $platform_dir/lib/NLDM/*RVT_TT*.lib.gz $platform_dir/lib/NLDM/*RVT_TT*.lib] { read_liberty $lib }
read_verilog $::env(NET)
link_design $::env(TOP)
read_sdc $::env(SDC)
read_vcd -scope $::env(SCOPE) $::env(VCD)
report_power -digits 6
