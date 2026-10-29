# Deterministic, fanout-bounded pre-layout clock buffering.
# This is a logical load model, NOT placed/routed CTS or skew closure.
# Apply the same fanout bound and buffer cell to both variants.
foreach family {AO INVBUF OA SEQ SIMPLE} {
  set libs [glob $::env(PLATFORM_DIR)/lib/NLDM/asap7sc7p5t_${family}_RVT_TT_nldm_*.lib*]
  if {[llength $libs] != 1} {error "Ambiguous TT library"}
  read_liberty [lindex $libs 0]
}
read_db $::env(ODB)
set db [ord::get_db]
set block [ord::get_db_block]
set master [$db findMaster BUFx2_ASAP7_75t_R]
if {$master eq "NULL"} {error "Missing BUFx2 master"}
set fanout 4
set total_added 0

proc buffer_domain {block master net tag fanout} {
  set named {}
  foreach pin [$net getITerms] {
    if {[$pin getIoType] eq "INPUT"} {
      # Gate precedes its own tree; do not cascade the front-end tree into it.
      if {$tag eq "root" && [[$pin getInst] getName] eq "u.u_backend_icg.u_icg" && [[$pin getMTerm] getName] eq "CLK"} {continue}
      lappend named [list "[[$pin getInst] getName]/[[$pin getMTerm] getName]" $pin]
    }
  }
  set current {}
  foreach item [lsort -index 0 $named] {lappend current [lindex $item 1]}
  set original_count [llength $current]
  set level 0
  set added 0
  while {[llength $current] > $fanout} {
    set next {}
    set group 0
    for {set i 0} {$i < [llength $current]} {incr i $fanout} {
      set name cgclk_${tag}_${level}_${group}
      set buf [odb::dbInst_create $block $master $name]
      set wire [odb::dbNet_create $block ${name}_net]
      set ip [$buf findITerm A]
      set op [$buf findITerm Y]
      $ip connect $net
      $op connect $wire
      foreach pin [lrange $current $i [expr {$i+$fanout-1}]] {
        $pin disconnect
        $pin connect $wire
      }
      lappend next $ip
      incr group
      incr added
    }
    set current $next
    incr level
  }
  puts "CLOCK_TREE domain=$tag sinks=$original_count buffers=$added levels=$level root_loads=[llength $current] fanout_bound=$fanout"
  return $added
}
if {$::env(VARIANT) eq "gated"} {
  set gate [$block findInst u.u_backend_icg.u_icg]
  if {$gate eq "NULL"} {error "Expected mapped ICG instance"}
  set backend [[$gate findITerm GCLK] getNet]
  incr total_added [buffer_domain $block $master $backend backend $fanout]
}
set root [$block findNet clk]
if {$root eq "NULL"} {error "Missing root clock net"}
incr total_added [buffer_domain $block $master $root root $fanout]
puts "CLOCK_TREE_TOTAL $total_added"
report_design_area
write_db $::env(OUT_ODB)
write_verilog -sort $::env(OUT_VERILOG)
exit
