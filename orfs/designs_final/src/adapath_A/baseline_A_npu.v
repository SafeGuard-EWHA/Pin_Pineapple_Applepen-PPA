//  baseline_npu.v  -  adapath_top VARIANT=0 고정 wrapper (ORFS 합성용, 자동 생성)
module baseline_A_npu #(
    parameter C1 = 3, parameter C2 = 3, parameter C2_MED = 1, parameter N_CLASS = 10
) (
    input                         clk,
    input                         rst_n,
    input                         start,
    input  [7:0]                  pixel_in,
    input  [C1*25*8-1:0]          w_conv1,
    input  [C1*16-1:0]            b_conv1,
    input  [C2*C1*25*8-1:0]       w_conv2,
    input  [C2*16-1:0]            b_conv2,
    input  [N_CLASS*C1*16*8-1:0]  w_fce,
    input  [N_CLASS*16-1:0]       b_fce,
    input  [N_CLASS*C2_MED*16*8-1:0] w_fcl,
    input  [N_CLASS*16-1:0]       b_fcl,
    input  [N_CLASS*C2*16*8-1:0]  w_fcf,
    input  [N_CLASS*16-1:0]       b_fcf,
    output [$clog2(N_CLASS)-1:0]  decision,
    output                        valid_out,
    output [1:0]                  mode_out,
    output [11:0]                 margin_out
);
    `include "shifts.vh"
    adapath_top #(.VARIANT(0), .C1(C1), .C2(C2), .C2_MED(C2_MED), .N_CLASS(N_CLASS),
                  .SH_CONV1(SHIFT_CONV1), .SH_CONV2(SHIFT_CONV2),
                  .SH_FCE(SHIFT_FC_EARLY), .SH_FCL(SHIFT_FC_LIGHT), .SH_FCF(SHIFT_FC_FULL)) u (
        .clk(clk), .rst_n(rst_n), .start(start), .pixel_in(pixel_in),
        .w_conv1(w_conv1), .b_conv1(b_conv1), .w_conv2(w_conv2), .b_conv2(b_conv2),
        .w_fce(w_fce), .b_fce(b_fce), .w_fcl(w_fcl), .b_fcl(b_fcl), .w_fcf(w_fcf), .b_fcf(b_fcf),
        .decision(decision), .valid_out(valid_out), .mode_out(mode_out), .margin_out(margin_out));
endmodule
