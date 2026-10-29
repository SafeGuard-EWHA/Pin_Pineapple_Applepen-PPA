`timescale 1ps/1ps
module audit_top;
control_monitor #(.C2(3),.C2_MED(1),.TL(63),.TH(63)) mon(
.start(top_tb_1000.chip1.u_core.start),
.mode_v(top_tb_1000.chip1.u_core.mode_v),
.conv2_en(top_tb_1000.chip1.u_core.conv2_en),
.fc_light_en(top_tb_1000.chip1.u_core.fc_light_en),
.fc_full_en(top_tb_1000.chip1.u_core.fc_full_en),
.fsm_done(top_tb_1000.chip1.u_core.fsm_done),
.mode(top_tb_1000.chip1.u_core.mode),
.result_sel(top_tb_1000.chip1.u_core.result_sel),
.margin(top_tb_1000.chip1.u_core.margin),
.ch_en(top_tb_1000.chip1.u_core.ch_en),
.clk(top_tb_1000.clk),
.rst_n(top_tb_1000.rst_n),
.valid_out(top_tb_1000.valid_out_6),
.state(top_tb_1000.chip1.u_core.u_fsm.state),
.decision(top_tb_1000.decision),
.data_in(top_tb_1000.data_in));
endmodule
