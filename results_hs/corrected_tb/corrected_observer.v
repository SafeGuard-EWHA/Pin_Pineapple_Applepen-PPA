`timescale 1ps/1ps
module corrected_observer;
integer outputs=0, x_outputs=0, invalid_reads=0, unknown_reads=0, reads=0;
always @(posedge top_tb_1000_corrected.clk) begin
 if(top_tb_1000_corrected.rst_n) begin
  if(top_tb_1000_corrected.valid_out_6 === 1'b1) begin
   outputs=outputs+1;
   if((^top_tb_1000_corrected.decision)===1'bx) x_outputs=x_outputs+1;
  end
  if(top_tb_1000_corrected.state===0 && top_tb_1000_corrected.img_idx<784 && top_tb_1000_corrected.valid_out_6!==1'b1) begin
   reads=reads+1;
   if(top_tb_1000_corrected.rand_num>999 || top_tb_1000_corrected.rand_num*784+top_tb_1000_corrected.img_idx>783999) invalid_reads=invalid_reads+1;
   if((^top_tb_1000_corrected.pixels[top_tb_1000_corrected.rand_num*784+top_tb_1000_corrected.img_idx])===1'bx) unknown_reads=unknown_reads+1;
  end
 end
end
final begin
 $display("OBSERVER outputs=%0d x_outputs=%0d invalid_reads=%0d unknown_reads=%0d reads=%0d",outputs,x_outputs,invalid_reads,unknown_reads,reads);
end
endmodule
