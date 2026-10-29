//------------------------------------------------------------------------
//  mode_control_fsm.v  -  AdaPath-NPU Region 2
//
//  전체 추론 시퀀스를 제어하고 모드별 enable / clock-gating 신호를 만든다.
//
//    IDLE -> FRONT(Conv1+EarlyCls) -> DECIDE -> RUN_BACK -> DONE
//                                        |Easy---------------^
//
//  모드별 게이팅:
//    Easy   : conv2_en=0, ch_en=8'h00, FC 전부 0, result_sel=EARLY
//    Medium : conv2_en=1, ch_en=8'h0F (ch0~3),  fc_light_en=1, result_sel=LIGHT
//    Hard   : conv2_en=1, ch_en=8'hFF (전체),   fc_full_en=1,  result_sel=FULL
//------------------------------------------------------------------------
module mode_control_fsm (
    input            clk,
    input            rst_n,
    input            start,          // 새 이미지 입력 시작
    input            front_done,     // Conv1 + Early Classifier 완료
    input            mode_valid,     // difficulty_decoder 출력 유효
    input      [1:0] mode,           // 00 Easy / 01 Medium / 10 Hard
    input            back_done,      // Conv2 + FC 완료 (Medium/Hard)
    output reg       front_en,
    output reg       conv2_en,
    output reg [7:0] ch_en,          // Conv2 채널별 clock-gating mask
    output reg       fc_light_en,
    output reg       fc_full_en,
    output reg [1:0] result_sel,     // 00 EARLY / 01 LIGHT / 10 FULL
    output reg       done
);

    localparam [2:0] S_IDLE   = 3'd0,
                     S_FRONT  = 3'd1,
                     S_DECIDE = 3'd2,
                     S_BACK   = 3'd3,
                     S_DONE   = 3'd4;

    localparam [1:0] MODE_EASY = 2'd0, MODE_MEDIUM = 2'd1;
    localparam [1:0] SEL_EARLY = 2'd0, SEL_LIGHT = 2'd1, SEL_FULL = 2'd2;

    reg [2:0] state, n_state;
    reg [1:0] mode_r;

    // ---- 상태 천이 ----
    always @(*) begin
        n_state = state;
        case (state)
            S_IDLE:   if (start)      n_state = S_FRONT;
            S_FRONT:  if (front_done) n_state = S_DECIDE;
            // if/else: 판정이 미정(X)이면 Hard 경로로 진행 (정확도 우선 기본값)
            S_DECIDE: if (mode_valid) begin
                          if (mode == MODE_EASY) n_state = S_DONE;
                          else                   n_state = S_BACK;
                      end
            S_BACK:   if (back_done)  n_state = S_DONE;
            S_DONE:                   n_state = S_IDLE;
            default:                  n_state = S_IDLE;
        endcase
    end

    always @(posedge clk) begin
        if (~rst_n) begin
            state  <= S_IDLE;
            mode_r <= 2'd2;                       // 기본 Hard (정확도 우선)
        end else begin
            state <= n_state;
            if (state == S_DECIDE && mode_valid)
                mode_r <= mode;
        end
    end

    // ---- 출력 (모드별 게이팅) ----
    always @(*) begin
        front_en    = (state == S_FRONT);
        conv2_en    = 1'b0;
        ch_en       = 8'h00;
        fc_light_en = 1'b0;
        fc_full_en  = 1'b0;
        done        = (state == S_DONE);
        result_sel  = SEL_EARLY;

        if (state == S_BACK) begin
            conv2_en = 1'b1;
            if (mode_r == MODE_MEDIUM) begin
                ch_en       = 8'h0F;              // ch0~ch3 만 활성
                fc_light_en = 1'b1;
            end else begin                        // Hard
                ch_en       = 8'hFF;
                fc_full_en  = 1'b1;
            end
        end

        case (mode_r)
            MODE_EASY:   result_sel = SEL_EARLY;
            MODE_MEDIUM: result_sel = SEL_LIGHT;
            default:     result_sel = SEL_FULL;
        endcase
        if (state == S_FRONT || state == S_IDLE)
            result_sel = SEL_EARLY;               // 결정 전 기본값
    end

endmodule
