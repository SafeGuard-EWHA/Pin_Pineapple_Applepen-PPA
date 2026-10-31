set tb /top_tb_1000
add_wave $tb/clk $tb/rst_n $tb/data_in $tb/valid_out_6
add_wave -radix unsigned $tb/cnt $tb/accuracy $tb/rand_num
puts "=== original top_tb_1000 on gate-level netlist (1_synth.v + ASAP7 cell Verilog), first 45 ns ==="
run 45 ns
set f [open C:/Users/yhe44/idec_repo/evidence/vivado_netlist/summary.json r]; set j [read $f]; close $f
regexp {"total_outputs": (\d+)} $j - n; regexp {"total_decision_match": (\d+)} $j - d; regexp {"total_cycle_match": (\d+)} $j - c
puts "=== all netlist runs (default seed, -sv_seed 2-5) vs RTL result of the same image index ==="
puts "scored outputs = $n, decision match = $d, cycle match = $c"
