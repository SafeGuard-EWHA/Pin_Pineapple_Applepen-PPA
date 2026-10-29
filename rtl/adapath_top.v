//------------------------------------------------------------------------
//  adapath_top.v  -  AdaPath-NPU 최상위 (3종 아키텍처 공용)
//
//  VARIANT = 0 : Baseline NPU     (항상 전체 경로, Early Classifier/Region2 없음)
//  VARIANT = 1 : Early-Exit NPU   (Easy / Hard 2단계, Medium 경로 없음)
//  VARIANT = 2 : AdaPath-NPU      (Easy / Medium / Hard 3단계)  <- 제안 구조
//
//  데이터 흐름
//    pixel_in(1px/cycle) -> conv1_engine -> maxpool_relu_n(12x12)
//        -> fmap_buffer (저장)            -> early_classifier -> Region 2 -> FSM
//        -> (Medium/Hard) fmap replay -> conv2_engine(ch_en) -> maxpool_relu_n(4x4)
//        -> fc_light / fc_full -> result mux -> argmax -> decision
//
//  가중치는 레퍼런스(chip.v)와 같이 외부 포트로 공급된다.
//------------------------------------------------------------------------
module adapath_top #(
    parameter VARIANT  = 2,
    parameter C1       = 3,
    parameter C2       = 8,
    parameter C2_MED   = 4,
    parameter N_CLASS  = 10,
    parameter SH_CONV1 = 8,
    parameter SH_CONV2 = 8,
    parameter SH_FCE   = 9,
    parameter SH_FCL   = 9,
    parameter SH_FCF   = 9,
    parameter USE_REG_TH = 0          // 1: th_low_i/th_high_i 포트로 런타임 임계값 사용
) (
    input                         clk,
    input                         rst_n,
    input                         start,            // reset 후 1펄스 (픽셀 스트림 시작)
    input  [7:0]                  pixel_in,
    // ---- weights / biases (export_int8.py 산출) ----
    input  [C1*25*8-1:0]          w_conv1,
    input  [C1*16-1:0]            b_conv1,
    input  [C2*C1*25*8-1:0]       w_conv2,
    input  [C2*16-1:0]            b_conv2,
    input  [N_CLASS*C1*16*8-1:0]  w_fce,            // early : 48 -> N
    input  [N_CLASS*16-1:0]       b_fce,
    input  [N_CLASS*C2_MED*16*8-1:0] w_fcl,         // light : 64 -> N
    input  [N_CLASS*16-1:0]       b_fcl,
    input  [N_CLASS*C2*16*8-1:0]  w_fcf,            // full  : 128 -> N
    input  [N_CLASS*16-1:0]       b_fcf,
    // ---- runtime thresholds (USE_REG_TH=1 일 때만 사용) ----
    input  [11:0]                 th_low_i,
    input  [11:0]                 th_high_i,
    // ---- outputs ----
    output [$clog2(N_CLASS)-1:0]  decision,
    output                        valid_out,
    output [1:0]                  mode_out,         // 00 Easy / 01 Medium / 10 Hard
    output [11:0]                 margin_out
);

    localparam [1:0] MODE_EASY = 2'd0, MODE_MEDIUM = 2'd1, MODE_HARD = 2'd2;

    // ================= Region 1 : 공유 전단부 =================
    wire [C1*12-1:0] c1_out;  wire c1_v;
    conv1_engine #(.C1(C1), .SHIFT(SH_CONV1)) u_conv1 (
        .clk(clk), .rst_n(rst_n), .pixel_in(pixel_in),
        .w_flat(w_conv1), .b_flat(b_conv1), .out_flat(c1_out), .valid_out(c1_v));

    wire [C1*12-1:0] p1_out;  wire p1_v;
    maxpool_relu_n #(.C(C1), .DATA_W(12), .HALF_WIDTH(12)) u_pool1 (
        .clk(clk), .rst_n(rst_n), .valid_in(c1_v),
        .data_in_flat(c1_out), .data_out_flat(p1_out), .valid_out(p1_v));

    wire              fm_full, fm_ov, fm_done;
    wire [C1*12-1:0]  fm_out;
    reg               replay_req;
    fmap_buffer #(.C(C1), .N_PIX(144), .FLUSH(64)) u_fmap (
        .clk(clk), .rst_n(rst_n), .clear(start),
        .valid_in(p1_v), .data_in_flat(p1_out), .full(fm_full),
        .replay(replay_req), .out_valid(fm_ov), .out_flat(fm_out), .replay_done(fm_done));

    // ================= Region 2 : 난이도 판단 =================
    wire [N_CLASS*12-1:0] sc_early;
    wire                  early_done;
    wire [1:0]            mode;
    wire                  mode_v;
    wire [11:0]           margin;
    wire                  base_front_done;     // VARIANT 0 전용

    generate if (VARIANT != 0) begin : G_R2
        early_classifier #(.C1(C1), .N_CLASS(N_CLASS), .SHIFT(SH_FCE)) u_early (
            .clk(clk), .rst_n(rst_n), .clear(start),
            .valid_in(p1_v), .data_in_flat(p1_out),
            .w_flat(w_fce), .b_flat(b_fce),
            .scores_flat(sc_early), .done(early_done));

        wire signed [11:0] top1, top2;  wire [$clog2(N_CLASS)-1:0] t1i;  wire v_t2, v_mg;
        top2_finder #(.SCORE_W(12), .N(N_CLASS)) u_top2 (
            .clk(clk), .rst_n(rst_n), .valid_in(early_done), .scores_flat(sc_early),
            .top1(top1), .top2(top2), .top1_idx(t1i), .valid_out(v_t2));
        score_margin_calc #(.SCORE_W(12)) u_margin (
            .clk(clk), .rst_n(rst_n), .valid_in(v_t2), .top1(top1), .top2(top2),
            .margin(margin), .valid_out(v_mg));
        wire [1:0] mode_raw;
        difficulty_decoder #(.SCORE_W(12), .USE_REG_TH(USE_REG_TH)) u_dec (
            .clk(clk), .rst_n(rst_n), .valid_in(v_mg), .margin(margin),
            .th_low_i(th_low_i), .th_high_i(th_high_i), .mode(mode_raw), .valid_out(mode_v));
        // Early-Exit(2단계) 변형: Medium 을 Hard 로 접는다
        assign mode = (VARIANT == 1 && mode_raw == MODE_MEDIUM) ? MODE_HARD : mode_raw;
        assign base_front_done = 1'b0;
    end else begin : G_NOR2
        assign sc_early   = {N_CLASS*12{1'b0}};
        assign early_done = 1'b0;
        assign margin     = 12'd0;
        // Baseline: fmap 이 차면 front_done 펄스, 1사이클 뒤 "Hard 결정" 펄스
        reg fm_full_d, fm_full_dd;
        always @(posedge clk) begin
            if (~rst_n || start) begin fm_full_d <= 1'b0; fm_full_dd <= 1'b0; end
            else begin fm_full_d <= fm_full; fm_full_dd <= fm_full_d; end
        end
        assign mode   = MODE_HARD;
        assign mode_v = fm_full_d & ~fm_full_dd;
        assign base_front_done = fm_full & ~fm_full_d;
    end endgenerate

    // ================= FSM =================
    wire front_en, conv2_en, fc_light_en, fc_full_en, fsm_done;
    wire [7:0] ch_en8;  wire [1:0] result_sel;
    wire back_done;
    // Baseline 은 front_done = fmap full 에지, 그 외는 early classifier 완료
    wire front_done = (VARIANT == 0) ? base_front_done : early_done;

    mode_control_fsm u_fsm (
        .clk(clk), .rst_n(rst_n), .start(start),
        .front_done(front_done), .mode_valid(mode_v), .mode(mode),
        .back_done(back_done),
        .front_en(front_en), .conv2_en(conv2_en), .ch_en(ch_en8),
        .fc_light_en(fc_light_en), .fc_full_en(fc_full_en),
        .result_sel(result_sel), .done(fsm_done));

    // conv2_en 상승 에지에서 replay 1펄스
    reg conv2_en_d;
    always @(posedge clk) begin
        if (~rst_n) begin conv2_en_d <= 1'b0; replay_req <= 1'b0; end
        else begin conv2_en_d <= conv2_en; replay_req <= conv2_en & ~conv2_en_d; end
    end

    // ================= Region 3 : 후단 데이터패스 =================
    wire [C2-1:0] ch_en = (VARIANT == 2) ? ch_en8[C2-1:0] : {C2{conv2_en}};
    wire [C2*12-1:0] c2_out;  wire c2_v;
    conv2_engine #(.C1(C1), .C2(C2), .SHIFT(SH_CONV2)) u_conv2 (
        .clk(clk), .rst_n(rst_n), .valid_in(fm_ov), .data_in_flat(fm_out),
        .ch_en(ch_en), .w_flat(w_conv2), .b_flat(b_conv2),
        .out_flat(c2_out), .valid_out(c2_v));

    wire [C2*12-1:0] p2_out;  wire p2_v;
    maxpool_relu_n #(.C(C2), .DATA_W(12), .HALF_WIDTH(4)) u_pool2 (
        .clk(clk), .rst_n(rst_n), .valid_in(c2_v),
        .data_in_flat(c2_out), .data_out_flat(p2_out), .valid_out(p2_v));

    wire [N_CLASS*12-1:0] sc_full, sc_light;
    wire fcf_done, fcl_done;
    fc_engine #(.C_IN(C2), .C_USE(C2), .N_POS(16), .OUT_N(N_CLASS), .SHIFT(SH_FCF)) u_fcf (
        .clk(clk), .rst_n(rst_n), .clear(start),
        .valid_in(p2_v), .data_in_flat(p2_out), .go(fc_full_en),
        .w_flat(w_fcf), .b_flat(b_fcf), .scores_flat(sc_full), .captured(), .done(fcf_done));

    generate if (VARIANT == 2) begin : G_LIGHT
        fc_engine #(.C_IN(C2), .C_USE(C2_MED), .N_POS(16), .OUT_N(N_CLASS), .SHIFT(SH_FCL)) u_fcl (
            .clk(clk), .rst_n(rst_n), .clear(start),
            .valid_in(p2_v), .data_in_flat(p2_out), .go(fc_light_en),
            .w_flat(w_fcl), .b_flat(b_fcl), .scores_flat(sc_light), .captured(), .done(fcl_done));
    end else begin : G_NOLIGHT
        assign sc_light = {N_CLASS*12{1'b0}};
        assign fcl_done = 1'b0;
    end endgenerate

    assign back_done = fcf_done | fcl_done;

    // ================= Result MUX + argmax =================
    wire [N_CLASS*12-1:0] sc_sel = (result_sel == 2'd0) ? sc_early :
                                   (result_sel == 2'd1) ? sc_light : sc_full;
    wire signed [11:0] f1, f2;  wire fv;
    top2_finder #(.SCORE_W(12), .N(N_CLASS)) u_argmax (
        .clk(clk), .rst_n(rst_n), .valid_in(fsm_done), .scores_flat(sc_sel),
        .top1(f1), .top2(f2), .top1_idx(decision), .valid_out(fv));

    assign valid_out  = fv;
    assign mode_out   = (VARIANT == 0) ? MODE_HARD : mode;
    assign margin_out = margin;

endmodule
