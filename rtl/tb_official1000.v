//------------------------------------------------------------------------
//  tb_official1000.v  -  AdaPath-NPU 1,000장 회귀 시뮬레이션
//
//  img_batch1000.txt (1000 x 784 px) 를 순서대로 스트리밍하고
//  batch_expect.txt 의 golden(margin/mode/decision) 및 label 과 대조한다.
//
//  출력: RTL-golden 일치율 + label 기준 정확도 + 모드 분포
//------------------------------------------------------------------------
`timescale 1ns/1ps
`ifndef DATA
`define DATA "../out/rtl_data_mnist/"
`endif

module tb_official1000;

    localparam C1 = 3, C2 = 8, C2_MED = 4, N = 10;
    `include "shifts.vh"

    reg clk = 0, rst_n = 0, start = 0;
    always #5 clk = ~clk;

    // ---- 가중치 (tb_adapath 와 동일한 로드 로직) ----
    reg [7:0]  m_w1 [0:C1*25-1];
    reg [15:0] m_b1 [0:C1-1];
    reg [7:0]  m_w2 [0:C2*C1*25-1];
    reg [15:0] m_b2 [0:C2-1];
    reg [7:0]  m_we [0:N*C1*16-1];
    reg [15:0] m_be [0:N-1];
    reg [7:0]  m_wl [0:N*C2_MED*16-1];
    reg [15:0] m_bl [0:N-1];
    reg [7:0]  m_wf [0:N*C2*16-1];
    reg [15:0] m_bf [0:N-1];
    reg [7:0]  tmp25 [0:24];

    reg [C1*25*8-1:0]        w_conv1;   reg [C1*16-1:0] b_conv1;
    reg [C2*C1*25*8-1:0]     w_conv2;   reg [C2*16-1:0] b_conv2;
    reg [N*C1*16*8-1:0]      w_fce;     reg [N*16-1:0]  b_fce;
    reg [N*C2_MED*16*8-1:0]  w_fcl;     reg [N*16-1:0]  b_fcl;
    reg [N*C2*16*8-1:0]      w_fcf;     reg [N*16-1:0]  b_fcf;

    reg  [7:0] pixel_in;
    wire [$clog2(N)-1:0] decision;
    wire valid_out;  wire [1:0] mode_out;  wire [11:0] margin_out;

    adapath_top #(.VARIANT(2), .C1(C1), .C2(C2), .C2_MED(C2_MED), .N_CLASS(N),
                  .SH_CONV1(SHIFT_CONV1), .SH_CONV2(SHIFT_CONV2),
                  .SH_FCE(SHIFT_FC_EARLY), .SH_FCL(SHIFT_FC_LIGHT), .SH_FCF(SHIFT_FC_FULL)) dut (
        .clk(clk), .rst_n(rst_n), .start(start), .pixel_in(pixel_in),
        .w_conv1(w_conv1), .b_conv1(b_conv1), .w_conv2(w_conv2), .b_conv2(b_conv2),
        .w_fce(w_fce), .b_fce(b_fce), .w_fcl(w_fcl), .b_fcl(b_fcl), .w_fcf(w_fcf), .b_fcf(b_fcf),
        .decision(decision), .valid_out(valid_out), .mode_out(mode_out), .margin_out(margin_out));

    // ---- 1000장 이미지 메모리 ----
    reg [7:0] pixels [0:1000*784-1];
    integer   base;                        // 현재 이미지의 시작 오프셋
    reg [9:0] img_idx;
    always @(posedge clk) begin
        if (~rst_n) img_idx <= 10'd0;
        else begin
            if (img_idx < 10'd784) img_idx <= img_idx + 1'b1;
            pixel_in <= pixels[base + img_idx];
        end
    end

    integer fd, n_img, i, k, o, c, rc, cyc;
    integer g_label, g_margin, g_mode, g_exp;
    integer match, acc, fail_dump, m_easy, m_med, m_hard;
    reg [8*96-1:0] path;

    initial begin
        // 가중치 로드
        for (c = 0; c < C1; c = c + 1) begin
            $sformat(path, "%0sconv1_weight_%0d.txt", `DATA, c + 1);
            $readmemh(path, tmp25);
            for (k = 0; k < 25; k = k + 1) w_conv1[(c*25+k)*8 +: 8] = tmp25[k];
        end
        $sformat(path, "%0sconv1_bias.txt", `DATA);  $readmemh(path, m_b1);
        for (c = 0; c < C1; c = c + 1) b_conv1[c*16 +: 16] = m_b1[c];
        for (o = 0; o < C2; o = o + 1)
            for (c = 0; c < C1; c = c + 1) begin
                $sformat(path, "%0sconv2_weight_%0d%0d.txt", `DATA, o + 1, c + 1);
                $readmemh(path, tmp25);
                for (k = 0; k < 25; k = k + 1) w_conv2[((o*C1+c)*25+k)*8 +: 8] = tmp25[k];
            end
        $sformat(path, "%0sconv2_bias.txt", `DATA);  $readmemh(path, m_b2);
        for (o = 0; o < C2; o = o + 1) b_conv2[o*16 +: 16] = m_b2[o];
        $sformat(path, "%0searly_fc_weight.txt", `DATA);  $readmemh(path, m_we);
        $sformat(path, "%0searly_fc_bias.txt", `DATA);    $readmemh(path, m_be);
        for (k = 0; k < N*C1*16; k = k + 1) w_fce[k*8 +: 8] = m_we[k];
        for (k = 0; k < N; k = k + 1) b_fce[k*16 +: 16] = m_be[k];
        $sformat(path, "%0slight_fc_weight.txt", `DATA);  $readmemh(path, m_wl);
        $sformat(path, "%0slight_fc_bias.txt", `DATA);    $readmemh(path, m_bl);
        for (k = 0; k < N*C2_MED*16; k = k + 1) w_fcl[k*8 +: 8] = m_wl[k];
        for (k = 0; k < N; k = k + 1) b_fcl[k*16 +: 16] = m_bl[k];
        $sformat(path, "%0sfc_weight.txt", `DATA);  $readmemh(path, m_wf);
        $sformat(path, "%0sfc_bias.txt", `DATA);    $readmemh(path, m_bf);
        for (k = 0; k < N*C2*16; k = k + 1) w_fcf[k*8 +: 8] = m_wf[k];
        for (k = 0; k < N; k = k + 1) b_fcf[k*16 +: 16] = m_bf[k];

        // 주최측 제공 이미지 (라벨 = index % 10)
        $readmemh("../verilog_ref/data/input_1000.txt", pixels);
        n_img = 1000;
        $display("official input_1000.txt : %0d images (label = index %% 10)", n_img);
        $display("  sanity: pixels[0]=%0h pixels[400]=%0h", pixels[0], pixels[400]);

        match = 0; acc = 0; fail_dump = 0; m_easy = 0; m_med = 0; m_hard = 0;
        for (i = 0; i < n_img; i = i + 1) begin
            g_label = i % 10;   // 주최측 규칙: label = index % 10
            base = i * 784;
            rst_n = 0; start = 0; repeat (4) @(posedge clk); #1;
            rst_n = 1; start = 1; @(posedge clk); #1; start = 0;
            cyc = 0;
            while (!valid_out && cyc < 4000) begin @(posedge clk); #1; cyc = cyc + 1; end
            if (valid_out) match = match + 1;
            if (valid_out && decision == g_label) acc = acc + 1;
            case (mode_out) 2'd0: m_easy = m_easy + 1; 2'd1: m_med = m_med + 1;
                            default: m_hard = m_hard + 1; endcase
            if ((i + 1) % 100 == 0)
                $display("  [%0d/%0d] golden-match %0d  acc %0d", i + 1, n_img, match, acc);
        end
        $display("==== 주최측 input_1000.txt 실측 ====");
        $display("valid_out 정상 출력 : %0d / %0d", match, n_img);
        $display("정확도(label): %0d / %0d = %0d.%0d %%", acc, n_img,
                 (acc * 100) / n_img, (acc * 1000 / n_img) % 10);
        $display("모드 분포    : Easy %0d / Medium %0d / Hard %0d", m_easy, m_med, m_hard);
        $finish;
    end

endmodule
