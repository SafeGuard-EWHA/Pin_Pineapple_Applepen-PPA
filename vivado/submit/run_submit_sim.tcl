# 사용: vivado -mode batch -source run_submit_sim.tcl -tclargs <.xpr 경로>
open_project [lindex $argv 0]
launch_simulation
close_sim
close_project
