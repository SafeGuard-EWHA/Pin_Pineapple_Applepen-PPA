//------------------------------------------------------------------------
//  conv1_engine.v  -  Region 1 공유 전단부 Conv1 (5x5, 1->C1 ch)
//
//  레퍼런스 conv1_buf(라인버퍼, 1 px/cycle 스트리밍)를 그대로 재사용하고,
//  MAC/재양자화는 mac_tree 로 교체해 Python golden 과 bit-accurate 로 맞춘다.
//  픽셀은 0~255 unsigned -> 9-bit signed 로 zero-extend.
//------------------------------------------------------------------------
module conv1_engine #(
    parameter C1    = 3,
    parameter SHIFT = 8
) (
    input               clk,
    input               rst_n,
    input  [7:0]        pixel_in,             // reset 직후부터 1 px/cycle
    input  [C1*25*8-1:0] w_flat,              // [ch][tap]
    input  [C1*16-1:0]  b_flat,
    output [C1*12-1:0]  out_flat,
    output              valid_out
);

    wire [7:0] d [0:24];
    wire       v_buf;

    conv1_buf #(.WIDTH(28), .HEIGHT(28), .DATA_BITS(8)) u_buf (
        .clk(clk), .rst_n(rst_n), .data_in(pixel_in),
        .data_out_0(d[0]),   .data_out_1(d[1]),   .data_out_2(d[2]),   .data_out_3(d[3]),   .data_out_4(d[4]),
        .data_out_5(d[5]),   .data_out_6(d[6]),   .data_out_7(d[7]),   .data_out_8(d[8]),   .data_out_9(d[9]),
        .data_out_10(d[10]), .data_out_11(d[11]), .data_out_12(d[12]), .data_out_13(d[13]), .data_out_14(d[14]),
        .data_out_15(d[15]), .data_out_16(d[16]), .data_out_17(d[17]), .data_out_18(d[18]), .data_out_19(d[19]),
        .data_out_20(d[20]), .data_out_21(d[21]), .data_out_22(d[22]), .data_out_23(d[23]), .data_out_24(d[24]),
        .valid_out_buf(v_buf));

    // 25 x 9-bit (zero-extended) 윈도우
    wire [25*9-1:0] win;
    genvar t, c;
    generate
        for (t = 0; t < 25; t = t + 1) begin : PACK
            assign win[t*9 +: 9] = {1'b0, d[t]};
        end
        for (c = 0; c < C1; c = c + 1) begin : CH
            wire v_c;
            mac_tree #(.N(25), .DATA_W(9), .SHIFT(SHIFT)) u_mac (
                .clk(clk), .rst_n(rst_n), .en(1'b1), .valid_in(v_buf),
                .data_flat(win),
                .w_flat(w_flat[c*200 +: 200]),
                .bias(b_flat[c*16 +: 16]),
                .out(out_flat[c*12 +: 12]),
                .valid_out(v_c));
            if (c == 0) begin : V
                assign valid_out = v_c;
            end
        end
    endgenerate

endmodule
