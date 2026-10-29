`timescale 1ns/1ps
module medium_observer;
integer medium_outputs=0, medium_back_cycles=0, violations=0;
always @(negedge tb_adapath.clk) begin
 if(tb_adapath.rst_n && tb_adapath.dut.mode == 1 && tb_adapath.dut.u_fsm.state == 3) begin
  medium_back_cycles=medium_back_cycles+1;
  if(tb_adapath.dut.u_fsm.ch_en !== 8'h0f || tb_adapath.dut.u_fsm.fc_light_en !== 1'b1 || tb_adapath.dut.u_fsm.fc_full_en !== 1'b0) violations=violations+1;
 end

end
always @(posedge tb_adapath.valid_out) if(tb_adapath.mode_out == 1) medium_outputs=medium_outputs+1;
final $display("MEDIUM_OBSERVER outputs=%0d back_cycles=%0d violations=%0d",medium_outputs,medium_back_cycles,violations);
endmodule
