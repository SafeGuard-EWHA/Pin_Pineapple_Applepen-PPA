# 사용: vivado -mode batch -source make_submit.tcl -tclargs <프로젝트 폴더> <프로젝트 이름>
set R [file normalize [lindex $argv 0]]
set N [lindex $argv 1]
create_project $N $R -part xc7a35tcpg236-1 -force
add_files -norecurse [glob $R/src/*.v]
add_files -norecurse [glob $R/src/*.vh]
set_property file_type {Verilog Header} [get_files *.vh]
set_property include_dirs [list $R/src] [get_filesets sources_1]
set_property include_dirs [list $R/src] [get_filesets sim_1]
add_files -fileset sim_1 -norecurse $R/sim/top_tb.v
add_files -fileset sim_1 -norecurse [glob $R/data/*.txt]
set_property top chip [get_filesets sources_1]
set_property top top_tb_1000 [get_filesets sim_1]
set_property -name {xsim.simulate.runtime} -value {all} -objects [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
close_project
