puts "SUBMIT_CHECK_BEGIN model=WM"
puts "VIVADO_VERSION=[version -short]"
if {[catch {open_project C:/Temp/ppa_final_verify_20261030/PPA_AdaPath_NPU_WM/PPA_AdaPath_NPU_WM.xpr} detail]} {
 puts "SUBMIT_CHECK_OPEN_FAILED: $detail"
 puts $::errorInfo
 return
}
if {[catch {launch_simulation -mode behavioral} detail]} {
 puts "SUBMIT_CHECK_SIM_FAILED: $detail"
 puts $::errorInfo
 return
}
puts "SUBMIT_CHECK_END model=WM"
