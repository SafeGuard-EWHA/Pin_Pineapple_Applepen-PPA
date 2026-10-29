`timescale 1ns/1ps
// 새 top2_finder(토너먼트) 와 기존 top2_finder_old(2-pass 체인) 의 비트 단위 동일성 검증
module tb_top2_equiv;
    parameter N = 10, W = 12;
    reg clk = 0, rst_n = 0, vin = 0;
    reg [N*W-1:0] sc;
    wire signed [W-1:0] a1, a2, b1, b2;
    wire [$clog2(N)-1:0] ai, bi;
    wire av, bv;

    top2_finder     #(.SCORE_W(W), .N(N)) dn (.clk(clk), .rst_n(rst_n), .valid_in(vin), .scores_flat(sc),
                                              .top1(a1), .top2(a2), .top1_idx(ai), .valid_out(av));
    top2_finder_old #(.SCORE_W(W), .N(N)) dold(.clk(clk), .rst_n(rst_n), .valid_in(vin), .scores_flat(sc),
                                              .top1(b1), .top2(b2), .top1_idx(bi), .valid_out(bv));
    always #5 clk = ~clk;

    integer t, j, errs = 0, mode;
    reg [31:0] seed = 32'hC0FFEE;
    reg [W-1:0] pool [0:3];

    initial begin
        #22 rst_n = 1;
        for (t = 0; t < 400000; t = t + 1) begin
            mode = t % 5;
            pool[0] = $random(seed); pool[1] = $random(seed);
            pool[2] = {1'b1, {W-1{1'b0}}};          // MINVAL
            pool[3] = {1'b0, {W-1{1'b1}}};          // MAXVAL
            for (j = 0; j < N; j = j + 1) begin
                case (mode)
                    0: sc[j*W +: W] = $random(seed);                       // 완전 무작위
                    1: sc[j*W +: W] = pool[$random(seed) & 3];             // 동점 다수 + 경계값
                    2: sc[j*W +: W] = ($random(seed) & 3) - 2;             // 작은 값, 동점 매우 많음
                    3: sc[j*W +: W] = 12'sd100;                            // 전부 동일
                    default: sc[j*W +: W] = (j == (t >> 3) % N) ? 12'sd500 : ($random(seed) & 12'h0FF);
                endcase
            end
            vin = 1;
            @(posedge clk); #1;
            if (a1 !== b1 || a2 !== b2 || ai !== bi) begin
                errs = errs + 1;
                if (errs < 10)
                    $display("MISMATCH t=%0d mode=%0d new(%0d,%0d,%0d) old(%0d,%0d,%0d)", t, mode, a1, a2, ai, b1, b2, bi);
            end
        end
        if (errs == 0) $display("EQUIV PASS : 400000 vectors, new == old (top1/top2/idx)");
        else           $display("EQUIV FAIL : %0d mismatches", errs);
        $finish;
    end
endmodule
