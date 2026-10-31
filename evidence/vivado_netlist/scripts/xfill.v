`timescale 1ps/1ps
// 시뮬레이션 전용 모듈 (TB 파일 무수정).
// 1) TB가 X 픽셀을 내보내는 경우(첫 비채점 이미지, 인덱스 1000)에만 DUT 입력 포트를 0으로 치환하고, 그 외에는 TB의 data_in을 그대로 전달한다.
// 2) TB가 채점하는 시점과 같은 클럭 에지에서 이미지 인덱스(rand_num)와 decision을 기록한다(DUT를 구동하지 않음).
module xfill;
initial force top_tb_1000.chip1.data_in = ((^top_tb_1000.data_in) === 1'bx) ? 8'h00 : top_tb_1000.data_in;
always @(posedge top_tb_1000.clk)
  if (top_tb_1000.rst_n && top_tb_1000.valid_out_6 === 1'b1 && top_tb_1000.state !== 1'bx)
    $display("OBS n=%0d idx=%0d dec=%0d t=%0t", top_tb_1000.cnt, top_tb_1000.rand_num, top_tb_1000.decision, $time);
endmodule
