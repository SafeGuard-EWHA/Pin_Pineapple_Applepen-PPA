open_project C:/Temp/ppa_clockgate_20261030/PPA_AdaPath_NPU_WM/PPA_AdaPath_NPU_WM.xpr
set_property xsim.elaborate.xelab.more_options {xil_defaultlib.clockgate_audit} [get_filesets sim_1]
set_property xsim.simulate.runtime 0ns [get_filesets sim_1]
launch_simulation -mode behavioral -step compile
cd C:/Temp/ppa_clockgate_20261030/PPA_AdaPath_NPU_WM/PPA_AdaPath_NPU_WM.sim/sim_1/behav/xsim
puts [exec C:/Xilinx/Vivado/2024.1/bin/unwrapped/win64.o/xvlog.exe --work xil_defaultlib -i C:/Temp/ppa_clockgate_20261030/PPA_AdaPath_NPU_WM/src C:/Temp/ppa_clockgate_20261030/PPA_AdaPath_NPU_WM/src/icg_latch.v C:/Temp/ppa_clockgate_20261030/PPA_AdaPath_NPU_WM/src/adapath_top_cg.v C:/Temp/ppa_clockgate_20261030/PPA_AdaPath_NPU_WM/src/chip_cg.v C:/Temp/ppa_clockgate_20261030/lockstep_WM.v]
launch_simulation -mode behavioral -step elaborate
launch_simulation -mode behavioral -step simulate
run all
puts "CLOCKGATE checked=[get_value -radix unsigned /clockgate_audit/checked]"
puts "CLOCKGATE valid_mismatches=[get_value -radix unsigned /clockgate_audit/valid_mismatches]"
puts "CLOCKGATE output_mismatches=[get_value -radix unsigned /clockgate_audit/output_mismatches]"
puts "CLOCKGATE easy=[get_value -radix unsigned /clockgate_audit/easy]"
puts "CLOCKGATE med=[get_value -radix unsigned /clockgate_audit/med]"
puts "CLOCKGATE hard=[get_value -radix unsigned /clockgate_audit/hard]"
puts "CLOCKGATE parent_edges=[get_value -radix unsigned /clockgate_audit/parent_edges]"
puts "CLOCKGATE gated_edges=[get_value -radix unsigned /clockgate_audit/gated_edges]"
puts "CLOCKGATE glitches=[get_value -radix unsigned /clockgate_audit/glitches]"
close_sim
close_project
exit
