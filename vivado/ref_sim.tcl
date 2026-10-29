set W C:/Users/yhe44/idec_vivado/ref
create_project ref_chip $W/proj -part xc7a35tcpg236-1 -force
add_files [list $W/src/chip.v $W/src/comparator.v $W/src/conv1.v $W/src/conv2.v $W/src/fc.v $W/src/maxpool_relu.v]
add_files -fileset sim_1 $W/src/top_tb.v
set_property top chip [current_fileset]
set_property top top_tb_1000 [get_filesets sim_1]
set_property -name {xsim.simulate.runtime} -value {all} -objects [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
run all
close_sim
close_project
