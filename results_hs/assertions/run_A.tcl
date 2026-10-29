open_project C:/Temp/ppa_observer_20261030/PPA_AdaPath_NPU_A/PPA_AdaPath_NPU_A.xpr
add_files -fileset sim_1 {C:/Temp/ppa_observer_20261030/control_monitor.v C:/Temp/ppa_observer_20261030/audit_A.v}
set_property top top_tb_1000 [get_filesets sim_1]
set_property xsim.elaborate.xelab.more_options {xil_defaultlib.audit_top} [get_filesets sim_1]
set_property xsim.simulate.runtime 0ns [get_filesets sim_1]
launch_simulation -mode behavioral -step compile
cd C:/Temp/ppa_observer_20261030/PPA_AdaPath_NPU_A/PPA_AdaPath_NPU_A.sim/sim_1/behav/xsim
puts [exec C:/Xilinx/Vivado/2024.1/bin/unwrapped/win64.o/xvlog.exe --work xil_defaultlib C:/Temp/ppa_observer_20261030/control_monitor.v C:/Temp/ppa_observer_20261030/audit_A.v]
launch_simulation -mode behavioral -step elaborate
launch_simulation -mode behavioral -step simulate
run all
puts "SCORED_ACCURACY=[get_value -radix unsigned /top_tb_1000/accuracy]"
puts "AUDIT starts=[get_value -radix unsigned /audit_top/mon/starts]"
puts "AUDIT completed=[get_value -radix unsigned /audit_top/mon/completed]"
puts "AUDIT aborted=[get_value -radix unsigned /audit_top/mon/aborted]"
puts "AUDIT active=[get_value -radix unsigned /audit_top/mon/active]"
puts "AUDIT max_cycles=[get_value -radix unsigned /audit_top/mon/max_cycles]"
puts "AUDIT easy=[get_value -radix unsigned /audit_top/mon/easy]"
puts "AUDIT n_medium=[get_value -radix unsigned /audit_top/mon/n_medium]"
puts "AUDIT hard=[get_value -radix unsigned /audit_top/mon/hard]"
puts "AUDIT unknown_mode=[get_value -radix unsigned /audit_top/mon/unknown_mode]"
puts "AUDIT margin_low=[get_value -radix unsigned /audit_top/mon/margin_low]"
puts "AUDIT margin_mid=[get_value -radix unsigned /audit_top/mon/margin_mid]"
puts "AUDIT margin_high=[get_value -radix unsigned /audit_top/mon/margin_high]"
puts "AUDIT margin_unknown=[get_value -radix unsigned /audit_top/mon/margin_unknown]"
puts "AUDIT easy_checks=[get_value -radix unsigned /audit_top/mon/easy_checks]"
puts "AUDIT medium_checks=[get_value -radix unsigned /audit_top/mon/medium_checks]"
puts "AUDIT mux_checks=[get_value -radix unsigned /audit_top/mon/mux_checks]"
puts "AUDIT deadline_checks=[get_value -radix unsigned /audit_top/mon/deadline_checks]"
puts "AUDIT easy_errors=[get_value -radix unsigned /audit_top/mon/easy_errors]"
puts "AUDIT medium_errors=[get_value -radix unsigned /audit_top/mon/medium_errors]"
puts "AUDIT mux_errors=[get_value -radix unsigned /audit_top/mon/mux_errors]"
puts "AUDIT deadline_errors=[get_value -radix unsigned /audit_top/mon/deadline_errors]"
puts "AUDIT unknown_controls=[get_value -radix unsigned /audit_top/mon/unknown_controls]"
puts "AUDIT unknown_input_cycles=[get_value -radix unsigned /audit_top/mon/unknown_input_cycles]"
puts "AUDIT unknown_decisions=[get_value -radix unsigned /audit_top/mon/unknown_decisions]"
close_sim
close_project
exit
