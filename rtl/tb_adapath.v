//------------------------------------------------------------------------
//  tb_adapath.v  -  AdaPath-NPU 통합 테스트벤치 (end-to-end golden 대조)
//
//  rtl_data_<prefix>/ 의 가중치·이미지·golden_reference 를 읽어,
//  tb_list.txt 에 나열된 이미지마다 reset -> 픽셀 스트리밍 -> decision 까지
//  돌리고 margin / mode / decision 을 Python 정수 golden 과 대조한다.
//
//  실행 (rtl/ 에서, DATA 매크로로 데이터 폴더 지정):
//    iverilog -g2012 -I. -I../out/rtl_data_mnist -DDATA='"../out/rtl_data_mnist/"' \
//             -DVARIANT=2 -o tb_adapath.vvp *.v ref/*.v && vvp tb_adapath.vvp
//------------------------------------------------------------------------
`timescale 1ns/1ps
`ifndef DATA
`define DATA "../out/rtl_data_mnist/"
`endif
`ifndef VARIANT
`define VARIANT 2
`endif

module tb_adapath;

    localparam C1 = 3, C2 = 8, C2_MED = 4, N = 10;
    `include "shifts.vh"

    reg clk = 0, rst_n = 0, start = 0;
    always #5 clk = ~clk;

    // ---------------- 가중치 메모리 ----------------
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

    // ---------------- DUT ----------------
    reg  [7:0] pixel_in;
    wire [$clog2(N)-1:0] decision;
    wire valid_out;  wire [1:0] mode_out;  wire [11:0] margin_out;

    adapath_top #(.VARIANT(`VARIANT), .C1(C1), .C2(C2), .C2_MED(C2_MED), .N_CLASS(N),
                  .SH_CONV1(SHIFT_CONV1), .SH_CONV2(SHIFT_CONV2),
                  .SH_FCE(SHIFT_FC_EARLY), .SH_FCL(SHIFT_FC_LIGHT), .SH_FCF(SHIFT_FC_FULL)) dut (
        .clk(clk), .rst_n(rst_n), .start(start), .pixel_in(pixel_in),
        .w_conv1(w_conv1), .b_conv1(b_conv1), .w_conv2(w_conv2), .b_conv2(b_conv2),
        .w_fce(w_fce), .b_fce(b_fce), .w_fcl(w_fcl), .b_fcl(b_fcl), .w_fcf(w_fcf), .b_fcf(b_fcf),
        .decision(decision), .valid_out(valid_out), .mode_out(mode_out), .margin_out(margin_out));

    // ---------------- 픽셀 스트림 (레퍼런스 top_tb 와 동일한 방식) ----------------
    reg [7:0]  pixels [0:783];
    reg [9:0]  img_idx;
    always @(posedge clk) begin
        if (~rst_n) img_idx <= 10'd0;
        else begin
            if (img_idx < 10'd784) img_idx <= img_idx + 1'b1;
            pixel_in <= pixels[img_idx];
        end
    end


    // ---------------- 디버그 카운터 ----------------
    integer n_c1v=0, n_p1v=0, n_fmov=0, n_c2v=0, n_p2v=0;
    reg seen_full=0, seen_early=0, seen_modev=0, seen_replay=0, seen_fcf=0, seen_fcl=0, seen_done=0;
    always @(posedge clk) begin
        if (!rst_n) begin n_c1v=0; n_p1v=0; n_fmov=0; n_c2v=0; n_p2v=0;
            seen_full=0; seen_early=0; seen_modev=0; seen_replay=0; seen_fcf=0; seen_fcl=0; seen_done=0; end
        else begin
            if (dut.c1_v) n_c1v=n_c1v+1;
            if (dut.p1_v) n_p1v=n_p1v+1;
            if (dut.fm_ov) n_fmov=n_fmov+1;
            if (dut.c2_v) n_c2v=n_c2v+1;
            if (dut.p2_v) n_p2v=n_p2v+1;
            if (dut.fm_full) seen_full=1;
            if (dut.early_done) seen_early=1;
            if (dut.mode_v) seen_modev=1;
            if (dut.replay_req) seen_replay=1;
            if (dut.fcf_done) seen_fcf=1;
            if (dut.fcl_done) seen_fcl=1;
            if (dut.fsm_done) seen_done=1;
        end
    end
    task dbg_print;
        $display("    dbg: c1_v=%0d p1_v=%0d full=%b early=%b mode_v=%b(mode=%0d) fsm=%0d replay=%b fm_ov=%0d c2_v=%0d p2_v=%0d fcf=%b fcl=%b done=%b",
            n_c1v, n_p1v, seen_full, seen_early, seen_modev, dut.mode, dut.u_fsm.state, seen_replay, n_fmov, n_c2v, n_p2v, seen_fcf, seen_fcl, seen_done);
    endtask

    // ---------------- 메인 ----------------
    integer fd, n_img, k, i, o, c, rc, cyc, pass, fail;
    reg [8*32-1:0] fname;
    integer g_idx, g_label, g_margin, g_mode, g_exp, g_full;
    reg [8*96-1:0] path;
    reg [8*128-1:0] line;

    initial begin
        // --- 가중치 로드 ---
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

        // --- 이미지 목록 ---
        $sformat(path, "%0stb_list.txt", `DATA);
        fd = $fopen(path, "r");
        if (fd == 0) begin $display("cannot open %0s", path); $finish; end
        rc = $fscanf(fd, "%d\n", n_img);
        $display("VARIANT=%0d, %0d images, T_LOW/T_HIGH from thresholds.vh", `VARIANT, n_img);

        pass = 0; fail = 0;
        for (i = 0; i < n_img; i = i + 1) begin
            rc = $fgets(line, fd);
            rc = $sscanf(line, "%s %d %d %d %d %d %d", fname, g_idx, g_label, g_margin, g_mode, g_exp, g_full);
            $sformat(path, "%0s%0s", `DATA, fname);
            $readmemh(path, pixels);

            // reset + start
            rst_n = 0; start = 0; repeat (4) @(posedge clk); #1;
            rst_n = 1; start = 1; @(posedge clk); #1; start = 0;

            cyc = 0;
            // 엣지 직후(#1)에 샘플해 1사이클 valid_out 펄스를 놓치지 않는다
            while (!valid_out && cyc < 4000) begin @(posedge clk); #1; cyc = cyc + 1; end
            if (!valid_out) begin
                fail = fail + 1;
                $display("[%0d] %0s  TIMEOUT (no valid_out)", i, fname);
                dbg_print;
            end else if (`VARIANT == 0) begin
                // Baseline: 항상 Hard 경로 -> golden 의 pred_full 과 비교
                if (decision === g_full) begin
                    pass = pass + 1;
                    $display("[%0d] %-16s PASS  decision=%0d (=pred_full, label %0d)  cycles=%0d  [baseline]",
                             i, fname, decision, g_label, cyc);
                end else begin
                    fail = fail + 1;
                    $display("[%0d] %-16s FAIL  decision=%0d (exp pred_full %0d)  cycles=%0d  [baseline]",
                             i, fname, decision, g_full, cyc);
                end
            end else if (`VARIANT == 1) begin
                // Early-Exit(2단계): Medium 은 Hard 로 접힘 -> 기대 mode/decision 재계산
                if (margin_out === g_margin &&
                    mode_out === ((g_mode == 1) ? 2 : g_mode) &&
                    decision === ((g_mode == 0) ? g_exp : g_full)) begin
                    pass = pass + 1;
                    $display("[%0d] %-16s PASS  margin=%0d mode=%0d decision=%0d (label %0d)  cycles=%0d  [early-exit]",
                             i, fname, margin_out, mode_out, decision, g_label, cyc);
                end else begin
                    fail = fail + 1;
                    $display("[%0d] %-16s FAIL  margin=%0d(exp %0d) mode=%0d decision=%0d  cycles=%0d  [early-exit]",
                             i, fname, margin_out, g_margin, mode_out, decision, cyc);
                end
            end else begin
                if (margin_out === g_margin && mode_out === g_mode && decision === g_exp) begin
                    pass = pass + 1;
                    $display("[%0d] %-16s PASS  margin=%0d mode=%0d decision=%0d (label %0d)  cycles=%0d",
                             i, fname, margin_out, mode_out, decision, g_label, cyc);
                end else begin
                    fail = fail + 1;
                    $display("[%0d] %-16s FAIL  margin=%0d(exp %0d) mode=%0d(exp %0d) decision=%0d(exp %0d) cycles=%0d",
                             i, fname, margin_out, g_margin, mode_out, g_mode, decision, g_exp, cyc);
                end
            end
        end
        $fclose(fd);
        $display("==== %0d PASS / %0d FAIL ====", pass, fail);
        $finish;
    end

    initial begin
        $dumpfile("tb_adapath.vcd");
        $dumpvars(1, tb_adapath);
        $dumpvars(1, dut);
        $dumpvars(0, dut.u_fsm);
    end

endmodule
