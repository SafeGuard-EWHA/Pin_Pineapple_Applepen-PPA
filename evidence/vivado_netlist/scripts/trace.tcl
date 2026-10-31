# 10 ns 단위 단계 실행. 진행 상황(cnt, accuracy)을 즉시 기록하고, stop.flag 파일이 생기면 정상 종료하여 TB의 $display 결과를 남긴다.
set tb /top_tb_1000
set t0 [clock seconds]
for {set k 1} {$k <= 860} {incr k} {
  run 10 ns
  puts "STEP k=$k t=[current_time] cnt=[get_value -radix unsigned $tb/cnt] acc=[get_value -radix unsigned $tb/accuracy] wall=[expr {[clock seconds]-$t0}]s"
  flush stdout
  if {[file exists stop.flag]} break
}
puts "TRACE_END"
quit
