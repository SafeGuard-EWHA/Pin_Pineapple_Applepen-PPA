run all
foreach name {outputs unscored_outputs unknown_decisions rand1000 invalid_reads unknown_reads} {
 puts "CHECK $name=[get_value -radix unsigned /official_observer/$name]"
}
puts "CHECK accuracy=[get_value -radix unsigned /top_tb_1000/accuracy]"
puts "CHECK cnt=[get_value -radix unsigned /top_tb_1000/cnt]"
quit
