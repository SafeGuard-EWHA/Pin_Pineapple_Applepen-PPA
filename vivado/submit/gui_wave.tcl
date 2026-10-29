set C C:/Users/yhe44/idec_vivado/capture
open_project $C/PPA_AdaPath_NPU_A/PPA_AdaPath_NPU_A.xpr
set_property -name {xsim.simulate.runtime} -value {415ns} -objects [get_filesets sim_1]
set_property -name {xsim.simulate.log_all_signals} -value {true} -objects [get_filesets sim_1]
launch_simulation
catch {remove_wave [get_waves *]}
set T /top_tb_1000
set U /top_tb_1000/chip1/u_core
proc aw {path name radix} {
  set w [add_wave -radix $radix $path]
  catch {set_property DISPLAY_NAME $name $w}
}
add_wave_divider "Organizer top_tb : input"
aw $T/clk          "clk"                      bin
aw $T/rst_n        "rst_n"                    bin
aw $T/data_in      "data_in (pixel)"          hex
add_wave_divider "Region 2 : difficulty decision"
aw $U/margin       "Score Margin"             unsigned
aw $U/mode         "mode (0=Easy, 2=Hard)"    unsigned
add_wave_divider "Region 3 : back-end enables"
aw $U/conv2_en     "conv2_en"                 bin
aw $U/fc_full_en   "fc_full_en"               bin
add_wave_divider "Output"
aw $T/valid_out_6  "valid_out_6"              bin
aw $T/decision     "decision"                 unsigned
aw $T/rand_num     "label index (rand_num)"   unsigned
aw $T/accuracy     "accuracy (correct count)"             unsigned
set f $C/demo.wcfg
save_wave_config $f
set fp [open $f r]; set x [read $fp]; close $fp
set n1 [regsub {<ZoomStartTime time="[^"]*"} $x {<ZoomStartTime time="382000ps"} x]
set n2 [regsub {<ZoomEndTime time="[^"]*"} $x {<ZoomEndTime time="412000ps"} x]
set fp [open $f w]; puts -nonewline $fp $x; close $fp
close_wave_config -force [current_wave_config]
open_wave_config $f
set fp [open $C/ready1.txt w]; puts $fp "zoom_subst=$n1/$n2"; close $fp
