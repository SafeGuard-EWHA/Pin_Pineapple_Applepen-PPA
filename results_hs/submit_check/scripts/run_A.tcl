puts "SUBMIT_CHECK_BEGIN model=A"
puts "VIVADO_VERSION=[version -short]"
if {[catch {open_project C:/Temp/ppa_final_verify_20261030/PPA_AdaPath_NPU_A/PPA_AdaPath_NPU_A.xpr} detail]} {
 puts "SUBMIT_CHECK_OPEN_FAILED: $detail"
 puts $::errorInfo
 return
}
if {[catch {launch_simulation -mode behavioral} detail]} {
 puts "SUBMIT_CHECK_SIM_FAILED: $detail"
 puts $::errorInfo
 return
}
puts "SUBMIT_CHECK_END model=A"
puts "CHECK accuracy_dec=[get_value -radix unsigned /top_tb_1000/accuracy] accuracy_hex=[get_value -radix hex /top_tb_1000/accuracy] cnt=[get_value -radix unsigned /top_tb_1000/cnt]"
