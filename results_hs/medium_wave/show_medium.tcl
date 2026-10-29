restart
create_wave_config medium_path
add_wave /tb_wm/clk /tb_wm/data_in
add_wave -radix unsigned /tb_wm/dut/u_core/margin /tb_wm/dut/u_core/mode
add_wave -radix hex /tb_wm/dut/u_core/ch_en
add_wave /tb_wm/dut/u_core/conv2_en /tb_wm/dut/u_core/fc_light_en /tb_wm/dut/u_core/fc_full_en /tb_wm/valid_out_6
add_wave -radix unsigned /tb_wm/decision /tb_wm/i
log_wave /tb_wm/clk /tb_wm/data_in /tb_wm/dut/u_core/margin /tb_wm/dut/u_core/mode /tb_wm/dut/u_core/ch_en /tb_wm/dut/u_core/conv2_en /tb_wm/dut/u_core/fc_light_en /tb_wm/dut/u_core/fc_full_en /tb_wm/valid_out_6 /tb_wm/decision /tb_wm/i
run 31000 ns
puts "MEDIUM_WAVE_CAPTURE_READY"
