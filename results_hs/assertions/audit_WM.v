`timescale 1ps/1ps
module audit_top;
control_monitor #(.C2(8),.C2_MED(4),.TL(13),.TH(41)) mon(
.start(tb_wm.dut.u_core.start),
.mode_v(tb_wm.dut.u_core.mode_v),
.conv2_en(tb_wm.dut.u_core.conv2_en),
.fc_light_en(tb_wm.dut.u_core.fc_light_en),
.fc_full_en(tb_wm.dut.u_core.fc_full_en),
.fsm_done(tb_wm.dut.u_core.fsm_done),
.mode(tb_wm.dut.u_core.mode),
.result_sel(tb_wm.dut.u_core.result_sel),
.margin(tb_wm.dut.u_core.margin),
.ch_en(tb_wm.dut.u_core.ch_en),
.clk(tb_wm.clk),
.rst_n(tb_wm.rst_n),
.valid_out(tb_wm.valid_out_6),
.state(tb_wm.dut.u_core.u_fsm.state),
.decision(tb_wm.decision),
.data_in(tb_wm.data_in));
endmodule
