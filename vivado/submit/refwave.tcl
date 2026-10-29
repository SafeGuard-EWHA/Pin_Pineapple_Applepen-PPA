log_wave -r /top_tb_1000
run 415ns
proc aw {path name radix} { set w [add_wave -radix $radix $path]; catch {set_property DISPLAY_NAME $name $w} }
set T /top_tb_1000
add_wave_divider "REFERENCE chip (organizer) : same top_tb, 0 - 415 ns"
aw $T/clk          "clk"                        bin
aw $T/rst_n        "rst_n"                      bin
aw $T/data_in      "data_in (pixel stream)"     hex
aw $T/valid_out_6  "valid_out_6"                bin
aw $T/decision     "decision"                   unsigned
aw $T/accuracy     "accuracy (correct count)"   unsigned
