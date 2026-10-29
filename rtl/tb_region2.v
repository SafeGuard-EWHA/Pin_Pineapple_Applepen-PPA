//------------------------------------------------------------------------
//  tb_region2.v  -  Region 2 (top2_finder + score_margin_calc +
//                   difficulty_decoder + mode_control_fsm) 통합 검증
//
//  N_CLASS 개 class score 를 다루는 범용판. MNIST 검증에서는 N_CLASS=10.
//
//  Part 1: 실제 테스트 이미지에서 뽑은 Early Classifier score 벡터
//          (region2_vectors.txt)를 흘려 넣고, margin / mode 가
//          Python golden reference 와 전부 일치하는지 확인한다.
//  Part 2: FSM 을 Easy / Medium / Hard 시나리오로 구동해 enable /
//          clock-gating 신호가 명세대로 나오는지 확인한다. (파형 4컷 근거)
//
//  실행:  iverilog -g2012 -I. -o tb.vvp *.v && vvp tb.vvp
//------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_region2;

    localparam N_CLASS = 10;
    localparam SCORE_W = 12;
    localparam N_VEC   = 200;
    localparam WORDS_PER_VEC = N_CLASS + 2;         // scores + margin + mode
    `include "thresholds.vh"

    reg clk = 0, rst_n = 0;
    always #5 clk = ~clk;

    // ---- DUT 연결 ----
    reg                        valid_in = 0;
    reg  [N_CLASS*SCORE_W-1:0] scores_flat;
    wire signed [SCORE_W-1:0]  top1, top2;
    wire [$clog2(N_CLASS)-1:0] top1_idx;
    wire                       v_top2;
    wire [SCORE_W-1:0]         margin;
    wire                       v_margin;
    wire [1:0]                 mode;
    wire                       v_mode;

    top2_finder #(.SCORE_W(SCORE_W), .N(N_CLASS)) u_top2 (
        .clk(clk), .rst_n(rst_n), .valid_in(valid_in),
        .scores_flat(scores_flat),
        .top1(top1), .top2(top2), .top1_idx(top1_idx), .valid_out(v_top2));

    score_margin_calc #(.SCORE_W(SCORE_W)) u_margin (
        .clk(clk), .rst_n(rst_n), .valid_in(v_top2),
        .top1(top1), .top2(top2), .margin(margin), .valid_out(v_margin));

    difficulty_decoder #(.SCORE_W(SCORE_W)) u_dec (
        .clk(clk), .rst_n(rst_n), .valid_in(v_margin),
        .margin(margin), .th_low_i(12'd0), .th_high_i(12'd0),
        .mode(mode), .valid_out(v_mode));

    // ---- FSM ----
    reg  start = 0, front_done = 0, back_done = 0;
    wire front_en, conv2_en, fc_light_en, fc_full_en, done;
    wire [7:0] ch_en;
    wire [1:0] result_sel;

    mode_control_fsm u_fsm (
        .clk(clk), .rst_n(rst_n), .start(start),
        .front_done(front_done), .mode_valid(v_mode), .mode(mode),
        .back_done(back_done),
        .front_en(front_en), .conv2_en(conv2_en), .ch_en(ch_en),
        .fc_light_en(fc_light_en), .fc_full_en(fc_full_en),
        .result_sel(result_sel), .done(done));

    // ---- 벡터 메모리 ----
    reg [15:0] vec [0:N_VEC*WORDS_PER_VEC-1];
    integer i, j, pass, fail;
    reg [SCORE_W-1:0] exp_margin;
    reg [1:0]         exp_mode;

    initial begin
        $dumpfile("tb_region2.vcd");
        $dumpvars(0, tb_region2);
        $readmemh("region2_vectors.txt", vec);

        rst_n = 0; repeat (3) @(posedge clk); rst_n = 1; @(posedge clk);

        // ================= Part 1: golden 대조 =================
        pass = 0; fail = 0;
        for (i = 0; i < N_VEC; i = i + 1) begin
            for (j = 0; j < N_CLASS; j = j + 1)
                scores_flat[j*SCORE_W +: SCORE_W] = vec[i*WORDS_PER_VEC + j][SCORE_W-1:0];
            exp_margin = vec[i*WORDS_PER_VEC + N_CLASS][SCORE_W-1:0];
            exp_mode   = vec[i*WORDS_PER_VEC + N_CLASS + 1][1:0];

            valid_in = 1;  @(posedge clk); #1;      // #1: 엣지 직후 해제 (레이스 방지)
            valid_in = 0;  repeat (3) @(posedge clk);   // 3단 파이프 대기
            #1;
            if (margin === exp_margin && mode === exp_mode) pass = pass + 1;
            else begin
                fail = fail + 1;
                $display("FAIL vec %0d: margin %0d (exp %0d)  mode %0d (exp %0d)",
                         i, margin, exp_margin, mode, exp_mode);
            end
        end
        $display("[Part1] golden 대조: %0d PASS / %0d FAIL (of %0d, N_CLASS=%0d)",
                 pass, fail, N_VEC, N_CLASS);

        // ================= Part 2: FSM 게이팅 시나리오 =================
        // thresholds.vh 의 T_LOW/T_HIGH 기준으로 세 모드에 해당하는 margin 을 만든다
        run_fsm_scenario(T_HIGH + 12'sd100,        12'sd0, "Easy  ");   // margin > T_HIGH
        run_fsm_scenario((T_LOW + T_HIGH) >>> 1,   12'sd0, "Medium");   // T_LOW <= m < T_HIGH
        run_fsm_scenario(T_LOW >>> 1,              12'sd0, "Hard  ");   // margin < T_LOW

        if (fail == 0) $display("== ALL PASS ==");
        else           $display("== %0d FAILURES ==", fail);
        $finish;
    end

    // FSM 시나리오: score 2개(a,b)만 실제값, 나머지는 0으로 채워 mode 를 유도
    task run_fsm_scenario(input signed [SCORE_W-1:0] a, input signed [SCORE_W-1:0] b,
                          input [47:0] name);
        integer k;
        begin
            @(posedge clk); #1; start = 1; @(posedge clk); #1; start = 0;
            repeat (2) @(posedge clk);
            scores_flat = {N_CLASS*SCORE_W{1'b0}};
            scores_flat[0*SCORE_W +: SCORE_W] = a;
            scores_flat[1*SCORE_W +: SCORE_W] = b;
            valid_in = 1; front_done = 1; @(posedge clk); #1;
            valid_in = 0; front_done = 0;
            repeat (3) @(posedge clk); #1;
            $display("[Part2 %s] mode=%0d conv2_en=%b ch_en=%02h light=%b full=%b sel=%0d done=%b",
                     name, mode, conv2_en, ch_en, fc_light_en, fc_full_en,
                     result_sel, done);
            if (!done) begin
                back_done = 1; @(posedge clk); #1; back_done = 0;
                $display("[Part2 %s] after back_done: done=%b result_sel=%0d",
                         name, done, result_sel);
            end
            @(posedge clk);
        end
    endtask

endmodule
