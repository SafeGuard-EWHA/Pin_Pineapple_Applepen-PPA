`timescale 1ns/1ps
// 레퍼런스 chip 게이트레벨 시뮬레이션 + VCD (주최측 top_tb 와 동일한 리셋/스트리밍 방식)
`ifndef START_IMG
`define START_IMG 0
`endif
`ifndef N_IMG
`define N_IMG 1
`endif
`ifndef VCDFILE
`define VCDFILE "gl_ref.vcd"
`endif
module tb_gl_ref;
    integer start_img;
    reg [8*64-1:0] vcdname;
    reg clk = 0, rst_n = 0;
    always #5 clk = ~clk;
    reg [7:0] pixels [0:1000*784-1];
    reg [7:0] data_in;
    wire [3:0] decision; wire valid_out_6;
    reg signed [7:0] weight_11 [0:24]; reg signed [7:0] weight_12 [0:24]; reg signed [7:0] weight_13 [0:24];
    reg signed [7:0] bias_1 [0:2]; reg signed [7:0] bias_2 [0:2];
    reg signed [7:0] weight_211 [0:24]; reg signed [7:0] weight_212 [0:24]; reg signed [7:0] weight_213 [0:24];
    reg signed [7:0] weight_221 [0:24]; reg signed [7:0] weight_222 [0:24]; reg signed [7:0] weight_223 [0:24];
    reg signed [7:0] weight_231 [0:24]; reg signed [7:0] weight_232 [0:24]; reg signed [7:0] weight_233 [0:24];
    reg signed [7:0] weight_fc [0:479]; reg signed [7:0] bias_fc [0:9];
    wire [0:199] w_11, w_12, w_13, w_211, w_212, w_213, w_221, w_222, w_223, w_231, w_232, w_233;
    wire [0:23] b_1, b_2; wire [0:3839] w_fc; wire [0:79] b_fc;
    genvar g;
    generate
        for (g = 0; g <= 24; g = g + 1) begin : W25
            assign w_11[(8*g)+:8] = weight_11[g];  assign w_12[(8*g)+:8] = weight_12[g];  assign w_13[(8*g)+:8] = weight_13[g];
            assign w_211[(8*g)+:8] = weight_211[g]; assign w_212[(8*g)+:8] = weight_212[g]; assign w_213[(8*g)+:8] = weight_213[g];
            assign w_221[(8*g)+:8] = weight_221[g]; assign w_222[(8*g)+:8] = weight_222[g]; assign w_223[(8*g)+:8] = weight_223[g];
            assign w_231[(8*g)+:8] = weight_231[g]; assign w_232[(8*g)+:8] = weight_232[g]; assign w_233[(8*g)+:8] = weight_233[g];
        end
        for (g = 0; g <= 2; g = g + 1) begin : B3
            assign b_1[(8*g)+:8] = bias_1[g]; assign b_2[(8*g)+:8] = bias_2[g];
        end
        for (g = 0; g <= 479; g = g + 1) begin : WFC assign w_fc[(8*g)+:8] = weight_fc[g]; end
        for (g = 0; g <= 9; g = g + 1)   begin : BFC assign b_fc[(8*g)+:8] = bias_fc[g]; end
    endgenerate
    chip dut (clk, rst_n, data_in, decision, valid_out_6,
              w_11, w_12, w_13, b_1, b_2, w_211, w_212, w_213, w_221, w_222, w_223, w_231, w_232, w_233, w_fc, b_fc);

    integer i, cyc, acc, idx;
    reg [9:0] img_idx;
    initial begin
        $readmemh("ref_data/conv1_weight_1.txt", weight_11); $readmemh("ref_data/conv1_weight_2.txt", weight_12);
        $readmemh("ref_data/conv1_weight_3.txt", weight_13); $readmemh("ref_data/conv1_bias.txt", bias_1);
        $readmemh("ref_data/conv2_bias.txt", bias_2);
        $readmemh("ref_data/conv2_weight_11.txt", weight_211); $readmemh("ref_data/conv2_weight_12.txt", weight_212);
        $readmemh("ref_data/conv2_weight_13.txt", weight_213); $readmemh("ref_data/conv2_weight_21.txt", weight_221);
        $readmemh("ref_data/conv2_weight_22.txt", weight_222); $readmemh("ref_data/conv2_weight_23.txt", weight_223);
        $readmemh("ref_data/conv2_weight_31.txt", weight_231); $readmemh("ref_data/conv2_weight_32.txt", weight_232);
        $readmemh("ref_data/conv2_weight_33.txt", weight_233);
        $readmemh("ref_data/fc_weight.txt", weight_fc); $readmemh("ref_data/fc_bias.txt", bias_fc);
        $readmemh("ref_data/input_1000.txt", pixels);
        if (!$value$plusargs("START=%d", start_img)) start_img = 0;
        if (!$value$plusargs("VCD=%s", vcdname)) vcdname = "gl.vcd";
        
        
        acc = 0; data_in = 0;
        for (i = 0; i < `N_IMG; i = i + 1) begin
            idx = start_img + i;
            rst_n = 0; repeat (12) @(posedge clk); #1; rst_n = 1;
            cyc = 0;
            while (valid_out_6 !== 1'b1 && cyc < 4000) begin
                data_in = (cyc < 784) ? pixels[idx*784 + cyc] : 8'd0;
                @(posedge clk); #1; cyc = cyc + 1;
            end
            if (valid_out_6 === 1'b1 && decision === (idx % 10)) acc = acc + 1;
            if (0) $display("img %0d : decision=%0d (label %0d) cycles=%0d", idx, decision, idx % 10, cyc);
        end
        $display("==== gate-level ref: %0d / %0d correct, VCD -> %0s ====", acc, `N_IMG, vcdname);
        $finish;
    end
endmodule
