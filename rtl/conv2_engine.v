//------------------------------------------------------------------------
//  conv2_engine.v  -  Region 3 가변 채널 Conv2 (5x5, C1 -> C2 ch)
//
//  레퍼런스 conv2_buf(라인버퍼)를 입력 채널마다 1개씩 재사용하고,
//  출력 채널마다 mac_tree(N = C1*25) 를 둔다.
//  ch_en[o] = 0 인 출력 채널은 operand isolation 으로 MAC 입력이 0 에 고정되어
//  스위칭이 일어나지 않는다 (Medium 모드: ch0~3 만 활성).
//------------------------------------------------------------------------
module conv2_engine #(
    parameter C1    = 3,
    parameter C2    = 8,
    parameter SHIFT = 8
) (
    input                     clk,
    input                     rst_n,
    input                     valid_in,               // fmap replay 스트림
    input  [C1*12-1:0]        data_in_flat,
    input  [C2-1:0]           ch_en,
    input  [C2*C1*25*8-1:0]   w_flat,                 // [o][c][tap]
    input  [C2*16-1:0]        b_flat,
    output [C2*12-1:0]        out_flat,
    output reg                valid_out
);

    // ---- 입력 채널별 라인버퍼 ----
    wire [11:0] win [0:C1-1][0:24];
    wire        v_buf [0:C1-1];
    genvar c, t, o;
    generate
        for (c = 0; c < C1; c = c + 1) begin : LB
            conv2_buf #(.WIDTH(12), .HEIGHT(12), .DATA_BITS(12)) u_buf (
                .clk(clk), .rst_n(rst_n), .valid_in(valid_in),
                .data_in(data_in_flat[c*12 +: 12]),
                .data_out_0(win[c][0]),   .data_out_1(win[c][1]),   .data_out_2(win[c][2]),   .data_out_3(win[c][3]),   .data_out_4(win[c][4]),
                .data_out_5(win[c][5]),   .data_out_6(win[c][6]),   .data_out_7(win[c][7]),   .data_out_8(win[c][8]),   .data_out_9(win[c][9]),
                .data_out_10(win[c][10]), .data_out_11(win[c][11]), .data_out_12(win[c][12]), .data_out_13(win[c][13]), .data_out_14(win[c][14]),
                .data_out_15(win[c][15]), .data_out_16(win[c][16]), .data_out_17(win[c][17]), .data_out_18(win[c][18]), .data_out_19(win[c][19]),
                .data_out_20(win[c][20]), .data_out_21(win[c][21]), .data_out_22(win[c][22]), .data_out_23(win[c][23]), .data_out_24(win[c][24]),
                .valid_out_buf(v_buf[c]));
        end
    endgenerate

    // 윈도우 평탄화: index = c*25 + tap  (Python w2[o,c,dy,dx].ravel 순서)
    wire [C1*25*12-1:0] win_flat;
    generate
        for (c = 0; c < C1; c = c + 1) begin : PK_C
            for (t = 0; t < 25; t = t + 1) begin : PK_T
                assign win_flat[(c*25+t)*12 +: 12] = win[c][t];
            end
        end
    endgenerate

    // 라인버퍼는 valid_in 이 들어온 사이클의 윈도우를 다음 사이클에 레지스터 출력한다.
    // 따라서 윈도우 유효 = (직전 사이클 valid_in) & valid_out_buf
    reg v_in_d;
    always @(posedge clk) begin
        if (~rst_n) v_in_d <= 1'b0;
        else        v_in_d <= valid_in;
    end
    wire v_win = v_in_d & v_buf[0];

    generate
        for (o = 0; o < C2; o = o + 1) begin : OC
            wire v_o;
            mac_tree #(.N(C1*25), .DATA_W(12), .SHIFT(SHIFT)) u_mac (
                .clk(clk), .rst_n(rst_n), .en(ch_en[o]), .valid_in(v_win),
                .data_flat(win_flat),
                .w_flat(w_flat[o*C1*25*8 +: C1*25*8]),
                .bias(b_flat[o*16 +: 16]),
                .out(out_flat[o*12 +: 12]),
                .valid_out(v_o));
        end
    endgenerate

    always @(posedge clk) begin
        if (~rst_n) valid_out <= 1'b0;
        else        valid_out <= v_win;
    end

endmodule
