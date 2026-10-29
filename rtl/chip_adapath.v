//------------------------------------------------------------------------
//  chip_adapath.v  -  주최측 레퍼런스(chip.v) 와 동일한 최상위 인터페이스 래퍼
//
//  - 포트 목록/폭은 레퍼런스 chip 과 동일 -> 주최측 top_tb 를 수정 없이 사용 가능
//  - 레퍼런스 가중치 포트(w_11 ... b_fc)는 받기만 하고 사용하지 않는다.
//    AdaPath 는 conv2 8ch / Early·Light·Full FC 3종으로 포트 폭이 달라
//    학습 가중치를 adapath_weights.vh 의 상수로 내부 고정한다 (보고서 명시 사항).
//  - 레퍼런스는 rst_n 해제 직후부터 픽셀을 받으므로, rst_n 상승 에지에서
//    코어의 start 펄스를 만든다.
//------------------------------------------------------------------------
module chip (
    input         clk,
    input         rst_n,
    input  [7:0]  data_in,
    output [3:0]  decision,
    output        valid_out_6,
    input [0:199] w_11,
    input [0:199] w_12,
    input [0:199] w_13,
    input [0:23]  b_1,
    input [0:23]  b_2,
    input [0:199] w_211,
    input [0:199] w_212,
    input [0:199] w_213,
    input [0:199] w_221,
    input [0:199] w_222,
    input [0:199] w_223,
    input [0:199] w_231,
    input [0:199] w_232,
    input [0:199] w_233,
    input [0:3839] w_fc,
    input [0:79]  b_fc
);

    `include "shifts.vh"
    `include "adapath_weights.vh"

    reg rst_n_d;
    always @(posedge clk) rst_n_d <= rst_n;
    wire start = rst_n & ~rst_n_d;
    wire [$clog2(CHIP_N_CLASS)-1:0] dec_core;

    adapath_top #(.VARIANT(2), .C1(3), .C2(CHIP_C2), .C2_MED(CHIP_C2_MED), .N_CLASS(CHIP_N_CLASS),
                  .SH_CONV1(SHIFT_CONV1), .SH_CONV2(SHIFT_CONV2),
                  .SH_FCE(SHIFT_FC_EARLY), .SH_FCL(SHIFT_FC_LIGHT), .SH_FCF(SHIFT_FC_FULL)) u_core (
        .clk(clk), .rst_n(rst_n), .start(start), .pixel_in(data_in),
        .w_conv1(W_CONV1), .b_conv1(B_CONV1), .w_conv2(W_CONV2), .b_conv2(B_CONV2),
        .w_fce(W_FCE), .b_fce(B_FCE), .w_fcl(W_FCL), .b_fcl(B_FCL),
        .w_fcf(W_FCF), .b_fcf(B_FCF),
        .decision(dec_core), .valid_out(valid_out_6), .mode_out(), .margin_out());

    assign decision = dec_core;           // 클래스 수 < 16 이면 상위 비트 0

endmodule
