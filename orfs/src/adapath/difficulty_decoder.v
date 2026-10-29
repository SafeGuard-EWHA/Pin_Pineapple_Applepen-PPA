//------------------------------------------------------------------------
//  difficulty_decoder.v  -  AdaPath-NPU Region 2
//
//  Score Margin 을 두 임계값과 비교해 3단계 동작 모드를 결정한다.
//    margin >= T_HIGH          -> MODE_EASY   (후단 전면 비활성)
//    T_LOW <= margin < T_HIGH  -> MODE_MEDIUM (Conv2 부분 채널 + Light FC)
//    margin <  T_LOW           -> MODE_HARD   (전체 경로)
//
//  임계값은 Python 검증 단계(analyze_margin.py -> export_int8.py)에서
//  도출되어 thresholds.vh 로 주입된다. USE_REG_TH=1 로 두면 런타임에
//  레지스터로 갱신 가능한 구조(Operating Point 가변)가 된다.
//------------------------------------------------------------------------
module difficulty_decoder #(
    parameter SCORE_W    = 12,
    parameter USE_REG_TH = 0            // 1: th_* 입력 포트 사용
) (
    input                   clk,
    input                   rst_n,
    input                   valid_in,
    input  [SCORE_W-1:0]    margin,
    input  [SCORE_W-1:0]    th_low_i,   // USE_REG_TH=1 일 때만 사용
    input  [SCORE_W-1:0]    th_high_i,
    output reg [1:0]        mode,       // 00 Easy / 01 Medium / 10 Hard
    output reg              valid_out
);

    localparam [1:0] MODE_EASY = 2'd0, MODE_MEDIUM = 2'd1, MODE_HARD = 2'd2;

    `include "thresholds.vh"            // T_LOW, T_HIGH (signed 12'sd)

    wire [SCORE_W-1:0] th_low  = USE_REG_TH ? th_low_i  : T_LOW[SCORE_W-1:0];
    wire [SCORE_W-1:0] th_high = USE_REG_TH ? th_high_i : T_HIGH[SCORE_W-1:0];

    // if/else: margin 이 미정(X)이면 Hard 로 판정 (정확도 우선 기본값)
    reg [1:0] n_mode;
    always @(*) begin
        if (margin >= th_high)     n_mode = MODE_EASY;
        else if (margin >= th_low) n_mode = MODE_MEDIUM;
        else                       n_mode = MODE_HARD;
    end

    always @(posedge clk) begin
        if (~rst_n) begin
            mode      <= MODE_HARD;     // 리셋 기본값: 정확도 우선
            valid_out <= 1'b0;
        end else begin
            valid_out <= valid_in;
            if (valid_in)
                mode <= n_mode;
        end
    end

endmodule
