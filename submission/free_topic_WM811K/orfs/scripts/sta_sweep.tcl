# 클럭 주기 스윕: (1) 입출력 지연 20 % (원 SDC 규칙)  (2) 가중치 포트 정적(false path)
set platform_dir $::env(PLATFORM_DIR)
foreach lib [glob -nocomplain $platform_dir/lib/NLDM/*RVT_TT*.lib.gz $platform_dir/lib/NLDM/*RVT_TT*.lib] { read_liberty $lib }
read_db $::env(ODB)
set clk [get_ports clk]
set ins [lsearch -inline -all -not -exact [all_inputs] $clk]
set fp [open $::env(OUTF) w]
foreach mode {io20 static_w} {
  if {$mode == "static_w"} { set_false_path -from [get_ports {w_* b_*}] }
  foreach P $::env(PERIODS) {
    create_clock -name clk -period $P $clk
    set_input_delay  [expr {$P * 0.2}] -clock clk $ins
    set_output_delay [expr {$P * 0.2}] -clock clk [all_outputs]
    set w [sta::worst_slack -max]
    set path [lindex [find_timing_paths -path_delay max -group_path_count 1] 0]
    set sp [get_full_name [get_property $path startpoint]]
    puts $fp "$mode $P $w $sp"
    flush $fp
  }
}
close $fp
puts "SWEEP_DONE"
