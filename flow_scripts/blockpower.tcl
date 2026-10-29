# 블록별 전력 (VCD 기반): 이름이 남아 있는 셀(FF)은 블록별, 이름 없는 셀(ABC 조합 논리)은 _comb 로 합산
set platform_dir $::env(PLATFORM_DIR)
foreach lib [glob -nocomplain $platform_dir/lib/NLDM/*RVT_TT*.lib.gz $platform_dir/lib/NLDM/*RVT_TT*.lib] { read_liberty $lib }
read_db $::env(ODB)
read_sdc $::env(SDC)
read_vcd -scope $::env(SCOPE) $::env(VCD)
report_power -digits 6
namespace eval sta {
  set scene [cmd_scene]
  array set P {}
  array set N {}
  foreach inst [network_leaf_instances] {
    set n [get_full_name $inst]
    lassign [instance_power $inst $scene] pi ps pl pt
    if {[string index $n 0] == "_"} {
      set g "_comb"
    } else {
      regsub {^u\.} $n "" m
      regsub {^G_[A-Za-z0-9]+\.} $m "" m
      set g [lindex [split $m ".\[\$"] 0]
    }
    if {![info exists P($g)]} { set P($g) {0 0 0 0}; set N($g) 0 }
    lassign $P($g) a b c d
    set P($g) [list [expr {$a+$pi}] [expr {$b+$ps}] [expr {$c+$pl}] [expr {$d+$pt}]]
    incr N($g)
  }
  set fp [open $::env(OUTF) w]
  foreach g [lsort [array names P]] { puts $fp "$g $N($g) [join $P($g) { }]" }
  close $fp
}
puts "BLOCKPOWER_DONE"
