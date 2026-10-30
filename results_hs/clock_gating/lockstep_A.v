`timescale 1ps/1ps
module clockgate_audit;
wire [3:0] cg_decision; wire cg_valid;
chip_cg cg(.clk(top_tb_1000.clk),
.rst_n(top_tb_1000.rst_n),
.data_in(top_tb_1000.data_in),
.decision(cg_decision),
.valid_out_6(cg_valid),
.w_11(200'd0),
.w_12(200'd0),
.w_13(200'd0),
.b_1(24'd0),
.b_2(24'd0),
.w_211(200'd0),
.w_212(200'd0),
.w_213(200'd0),
.w_221(200'd0),
.w_222(200'd0),
.w_223(200'd0),
.w_231(200'd0),
.w_232(200'd0),
.w_233(200'd0),
.w_fc(3840'd0),
.b_fc(80'd0));
integer checked=0, valid_mismatches=0, output_mismatches=0;
integer easy=0,med=0,hard=0, parent_edges=0,gated_edges=0,glitches=0;
always @(posedge cg.u_core.clk_backend) begin
 gated_edges=gated_edges+1;
 if (top_tb_1000.clk !== 1'b1) glitches=glitches+1;
end
always @(posedge top_tb_1000.clk) begin
 parent_edges=parent_edges+1;
 #1;
 if(top_tb_1000.rst_n === 1'b1) begin
   if(cg_valid !== top_tb_1000.valid_out_6) begin
     valid_mismatches=valid_mismatches+1;
     if(valid_mismatches<10) $display("VALID_MISMATCH time=%0t ref=%b gated=%b",$time,top_tb_1000.valid_out_6,cg_valid);
   end
   if(top_tb_1000.valid_out_6 === 1'b1) begin
     checked=checked+1;
     if(cg_decision !== top_tb_1000.decision || cg.u_core.mode_out !== top_tb_1000.chip1.u_core.mode_out || cg.u_core.margin_out !== top_tb_1000.chip1.u_core.margin_out) begin
       output_mismatches=output_mismatches+1;
       if(output_mismatches<10) $display("OUTPUT_MISMATCH time=%0t ref=%d gated=%d",$time,top_tb_1000.decision,cg_decision);
     end
     case(top_tb_1000.chip1.u_core.mode_out) 0:easy=easy+1;1:med=med+1;2:hard=hard+1;endcase
   end
 end
end
endmodule
