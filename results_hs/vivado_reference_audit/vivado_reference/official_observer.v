`timescale 1ps/1ps
module official_observer;
integer unscored_outputs=0;
integer outputs=0, unknown_decisions=0, rand1000=0, invalid_reads=0, unknown_reads=0;
always @(posedge top_tb_1000.clk) begin
 if(top_tb_1000.rst_n && top_tb_1000.valid_out_6 === 1'b1) begin
  outputs=outputs+1;
  if(top_tb_1000.state === 1'bx) begin unscored_outputs=unscored_outputs+1; $display("UNSCORED_OUTPUT time=%0t cnt=%0d state=%b",$time,top_tb_1000.cnt,top_tb_1000.state); end
  if((^top_tb_1000.decision) === 1'bx) unknown_decisions=unknown_decisions+1;
 end
 if(top_tb_1000.rst_n && top_tb_1000.state === 1'b0 && top_tb_1000.cnt < 1000) begin
  if(top_tb_1000.img_idx == 0 && top_tb_1000.rand_num == 1000) rand1000=rand1000+1;
  if(top_tb_1000.rand_num*784+top_tb_1000.img_idx > 783999) invalid_reads=invalid_reads+1;
  if((^top_tb_1000.pixels[top_tb_1000.rand_num*784+top_tb_1000.img_idx]) === 1'bx) unknown_reads=unknown_reads+1;
 end
end
final $display("OBSERVER outputs=%0d unknown_decisions=%0d rand1000=%0d invalid_reads=%0d unknown_reads=%0d correct=%0d",outputs,unknown_decisions,rand1000,invalid_reads,unknown_reads,top_tb_1000.accuracy);
endmodule
