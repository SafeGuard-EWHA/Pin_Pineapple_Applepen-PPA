//------------------------------------------------------------------------
//  tb_wm.v  -  자유주제(WM-811K 4-class) RTL 검증용 테스트벤치
//
//  주최 측 chip 인터페이스(chip_adapath.v, CHIP_N_CLASS = 4)를 그대로 사용하고,
//  주최 측 top_tb 와 같은 방식(이미지마다 리셋 후 1 px/cycle 스트리밍)으로 954장을 순서대로 처리한다.
//  wm_expect.txt 의 정수 Golden(판정·모드·Score Margin)과 비트 단위로 대조하고 라벨 기준 정확도를 출력한다.
//------------------------------------------------------------------------
`timescale 1ns/1ps
module tb_wm;
    localparam N_IMG = 954, N_CLASS = 4;

    reg clk = 0, rst_n = 0;
    always #5 clk = ~clk;

    reg  [7:0] pixels [0:N_IMG*784-1];
    reg  [7:0] data_in = 8'd0;
    wire [3:0] decision;
    wire       valid_out_6;

    chip dut (
        .clk(clk), .rst_n(rst_n), .data_in(data_in), .decision(decision), .valid_out_6(valid_out_6),
        .w_11(200'd0), .w_12(200'd0), .w_13(200'd0), .b_1(24'd0), .b_2(24'd0),
        .w_211(200'd0), .w_212(200'd0), .w_213(200'd0), .w_221(200'd0), .w_222(200'd0),
        .w_223(200'd0), .w_231(200'd0), .w_232(200'd0), .w_233(200'd0),
        .w_fc(3840'd0), .b_fc(80'd0));

    integer   base;
    reg [9:0] img_idx;
    always @(posedge clk) begin
        if (~rst_n) img_idx <= 10'd0;
        else begin
            if (img_idx < 10'd784) img_idx <= img_idx + 1'b1;
            data_in <= pixels[base + img_idx];
        end
    end

    integer fd, i, k, cyc, rc;
    integer e_label, e_dec, e_mode, e_margin;
    integer acc, dec_match, all_match, n_mode0, n_mode1, n_mode2;
    integer cls_n [0:N_CLASS-1];
    integer cls_ok [0:N_CLASS-1];

    initial begin
        $readmemh("wm_input_954.txt", pixels);
        fd = $fopen("wm_expect.txt", "r");
        acc = 0; dec_match = 0; all_match = 0; n_mode0 = 0; n_mode1 = 0; n_mode2 = 0;
        for (k = 0; k < N_CLASS; k = k + 1) begin cls_n[k] = 0; cls_ok[k] = 0; end
        for (i = 0; i < N_IMG; i = i + 1) begin
            rc = $fscanf(fd, "%d %d %d %d\n", e_label, e_dec, e_mode, e_margin);
            base = i * 784;
            rst_n = 0; repeat (4) @(posedge clk); #1;
            rst_n = 1;
            cyc = 0;
            while (valid_out_6 !== 1'b1 && cyc < 4000) begin @(posedge clk); #1; cyc = cyc + 1; end
            cls_n[e_label] = cls_n[e_label] + 1;
            if (decision == e_label) begin acc = acc + 1; cls_ok[e_label] = cls_ok[e_label] + 1; end
            if (decision == e_dec) dec_match = dec_match + 1;
            if (decision == e_dec && dut.u_core.mode_out == e_mode && dut.u_core.margin_out == e_margin)
                all_match = all_match + 1;
            else if (all_match + 10 > i)
                $display("MISMATCH img %0d: dec %0d/%0d mode %0d/%0d margin %0d/%0d", i, decision, e_dec,
                         dut.u_core.mode_out, e_mode, dut.u_core.margin_out, e_margin);
            case (dut.u_core.mode_out) 2'd0: n_mode0 = n_mode0 + 1; 2'd1: n_mode1 = n_mode1 + 1;
                                       default: n_mode2 = n_mode2 + 1; endcase
        end
        $fclose(fd);
        $display("------ Final Accuracy for %0d WM-811K Test Images ------", N_IMG);
        $display("Accuracy : %0d / %0d = %0d.%02d %%", acc, N_IMG, acc * 100 / N_IMG, (acc * 10000 / N_IMG) % 100);
        $display("Golden match (decision)              : %0d / %0d", dec_match, N_IMG);
        $display("Golden match (decision, mode, margin): %0d / %0d", all_match, N_IMG);
        $display("Mode Easy / Medium / Hard            : %0d / %0d / %0d", n_mode0, n_mode1, n_mode2);
        for (k = 0; k < N_CLASS; k = k + 1)
            $display("Class %0d recall : %0d / %0d", k, cls_ok[k], cls_n[k]);
        $finish;
    end
endmodule
