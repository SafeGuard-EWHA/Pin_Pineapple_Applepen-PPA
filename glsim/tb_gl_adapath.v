//------------------------------------------------------------------------
//  tb_gatelevel.v  -  합성 넷리스트(gate-level) 시뮬레이션 + VCD 덤프
//
//  목적: 실제 스위칭 파형을 추출해 OpenSTA 로 전력을 재측정하기 위함.
//        (정적 vectorless 추정은 모드 게이팅 효과를 반영하지 못한다)
//
//  실행:
//    iverilog -g2012 -I. -DTOP_ADAPATH -o gl.vvp \
//        <netlist>.v ../verilog_ref/std_cell/*.v tb_gatelevel.v && vvp gl.vvp
//
//  N_IMG 장만 돌린다 (게이트레벨은 느리므로 전력 추정에는 소수 샘플로 충분).
//------------------------------------------------------------------------
`timescale 1ns/1ps
`ifndef DATA
`define DATA "data/"
`endif
`ifndef START_IMG
`define START_IMG 0
`endif
`ifndef N_IMG
`define N_IMG 4
`endif
`ifndef VCDFILE
`define VCDFILE "gl_adapath.vcd"
`endif

module tb_gatelevel;
    integer start_img;
    reg [8*64-1:0] vcdname;

    localparam C1 = 3, C2 = 8, C2_MED = 4, N = 10;

    reg clk = 0, rst_n = 0, start = 0;
    always #5 clk = ~clk;                    // 100 MHz (10 ns)

    // ---- 가중치 메모리 ----
    reg [15:0] m_b1 [0:C1-1];
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
    wire [3:0] decision;
    wire valid_out;  wire [1:0] mode_out;  wire [11:0] margin_out;

    // ---- DUT: 합성 넷리스트의 top (wrapper 이름 그대로) ----
`ifdef TOP_BASELINE
    baseline_npu dut (
`else
    adapath_npu dut (
`endif
        .clk(clk), .rst_n(rst_n), .start(start), .pixel_in(pixel_in),
        .w_conv1(w_conv1), .b_conv1(b_conv1), .w_conv2(w_conv2), .b_conv2(b_conv2),
        .w_fce(w_fce), .b_fce(b_fce), .w_fcl(w_fcl), .b_fcl(b_fcl),
        .w_fcf(w_fcf), .b_fcf(b_fcf),
        .decision(decision), .valid_out(valid_out),
        .mode_out(mode_out), .margin_out(margin_out));

    // ---- 픽셀 스트림 ----
    reg [7:0] pixels [0:1000*784-1];
    integer   base;
    reg [9:0] img_idx;
    always @(posedge clk) begin
        if (~rst_n) img_idx <= 10'd0;
        else begin
            if (img_idx < 10'd784) img_idx <= img_idx + 1'b1;
            pixel_in <= pixels[base + img_idx];
        end
    end

    integer i, k, o, c, cyc, acc;
    reg [8*96-1:0] path;

    initial begin
        if (!$value$plusargs("START=%d", start_img)) start_img = 0;
        if (!$value$plusargs("VCD=%s", vcdname)) vcdname = "gl.vcd";
        $dumpfile(vcdname);
        $dumpvars(0, tb_gatelevel);          // 넷리스트 내부까지 전부 덤프 (전력 계산용)

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

        // 이미지 (주최측 제공 세트: label = index % 10)
        $readmemh("ref_data/input_1000.txt", pixels);

        acc = 0;
        for (i = 0; i < `N_IMG; i = i + 1) begin
            base = (start_img + i) * 784;
            rst_n = 0; start = 0; repeat (12) @(posedge clk); #1;
            rst_n = 1; start = 1; @(posedge clk); #1; start = 0;
            cyc = 0;
            while (valid_out !== 1'b1 && cyc < 4000) begin @(posedge clk); #1; cyc = cyc + 1; end
            if (valid_out === 1'b1 && decision === ((start_img + i) % 10)) acc = acc + 1;
            $display("img %0d : decision=%0d (label %0d) mode=%0d margin=%0d cycles=%0d",
                     start_img + i, decision, (start_img + i) % 10, mode_out, margin_out, cyc);
        end
        $display("==== gate-level: %0d / %0d correct, VCD -> %0s ====", acc, `N_IMG, vcdname);
        $finish;
    end

endmodule
