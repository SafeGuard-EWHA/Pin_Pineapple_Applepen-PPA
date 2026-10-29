set W C:/Users/yhe44/idec_vivado/adapath
create_project PPA_AdaPath_NPU $W/proj -part xc7a35tcpg236-1 -force
add_files [glob $W/src/*.v]
add_files [glob $W/src/*.vh]
set_property file_type {Verilog Header} [get_files *.vh]
set_property include_dirs $W/src [current_fileset]
add_files -fileset sim_1 $W/sim/top_tb.v
add_files -fileset sim_1 [glob $W/data/*.txt]
set_property include_dirs $W/src [get_filesets sim_1]
set_property top chip [current_fileset]
set_property top top_tb_1000 [get_filesets sim_1]
set_property -name {xsim.simulate.runtime} -value {all} -objects [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
launch_simulation
close_sim
close_project
