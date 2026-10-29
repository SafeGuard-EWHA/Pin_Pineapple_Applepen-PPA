# VCD 기반 전력 (환경변수 PLATFORM_DIR ODB SDC VCD SCOPE)
set platform_dir $::env(PLATFORM_DIR)
foreach lib [glob -nocomplain $platform_dir/lib/NLDM/*RVT_TT*.lib.gz $platform_dir/lib/NLDM/*RVT_TT*.lib] { read_liberty $lib }
read_db $::env(ODB)
read_sdc $::env(SDC)
read_vcd -scope $::env(SCOPE) $::env(VCD)
report_power -digits 6
