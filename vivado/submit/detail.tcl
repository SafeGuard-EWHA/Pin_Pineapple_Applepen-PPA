log_wave -r /top_tb_1000
run 415ns
proc aw {path name radix} { set w [add_wave -radix $radix $path]; catch {set_property DISPLAY_NAME $name $w} }
set T /top_tb_1000
set U /top_tb_1000/chip1/u_core
add_wave_divider "Input (organizer top_tb)"
aw $T/clk            "clk"                                   bin
aw $T/rst_n          "rst_n"                                 bin
aw $T/data_in        "data_in (pixel stream)"                hex
add_wave_divider "Region 1 : shared front-end"
aw $U/fm_full        "fmap_buffer full (12x12x3 stored)"     bin
add_wave_divider "Region 2 : difficulty decision"
aw $U/early_done     "early classifier done"                 bin
aw $U/margin         "Score Margin (Top1 - Top2)"            unsigned
aw $U/mode_v         "decision valid"                        bin
aw $U/mode           "mode (0=Easy, 2=Hard)"                 unsigned
aw $U/u_fsm/state    "FSM (1 FRONT 2 DECIDE 3 BACK 4 DONE)"  unsigned
add_wave_divider "Region 3 : back-end (Hard only)"
aw $U/replay_req     "fmap replay start"                     bin
aw $U/fm_ov          "fmap replay data valid"                bin
aw $U/ch_en          "conv2 channel enable"                  bin
aw $U/conv2_en       "conv2_en"                              bin
aw $U/fc_full_en     "fc_full_en"                            bin
add_wave_divider "Output"
aw $T/valid_out_6    "valid_out_6"                           bin
aw $T/decision       "decision"                              unsigned
aw $T/accuracy       "accuracy (correct count)"              unsigned
