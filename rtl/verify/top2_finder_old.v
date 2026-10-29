//------------------------------------------------------------------------
//  top2_finder.v  -  AdaPath-NPU Region 2  (N-class 범용판)
//
//  Early Classifier 의 N개 class score 에서 Top-1 / Top-2 를 추출한다.
//  MNIST(N=10) 등 클래스 수 변경에 대응하기 위해 N 을 파라미터화했다.
//
//  구조: 2-pass 순차 최댓값 탐색
//    Pass 1: N-1개 비교기로 top1 / top1_idx 탐색      (comparator chain)
//    Pass 2: top1_idx 위치만 최솟값으로 마스킹 후, 동일한
//            N-1개 비교기 구조로 재탐색 -> top2
//  총 비교기 2(N-1)개로, argmax 전용회로(N-1개) 대비 top2 추출에
//  N-1개만 추가되는 구조. (N=4 특화판은 N/2+1개로 더 작았으나,
//  본 범용판은 여러 N 에 재사용 가능한 명확성을 우선한 설계다.)
//------------------------------------------------------------------------
module top2_finder_old #(
    parameter SCORE_W = 12,
    parameter N       = 10
) (
    input                            clk,
    input                            rst_n,
    input                            valid_in,
    input      [N*SCORE_W-1:0]       scores_flat,   // {s_{N-1},...,s_1,s_0}
    output reg signed [SCORE_W-1:0]  top1,
    output reg signed [SCORE_W-1:0]  top2,
    output reg [$clog2(N)-1:0]       top1_idx,
    output reg                       valid_out
);

    localparam signed [SCORE_W-1:0] MINVAL = {1'b1, {SCORE_W-1{1'b0}}};  // 최솟값

    genvar gi;
    wire signed [SCORE_W-1:0] s [0:N-1];
    generate
        for (gi = 0; gi < N; gi = gi + 1) begin : SLICE
            assign s[gi] = scores_flat[gi*SCORE_W +: SCORE_W];
        end
    endgenerate

    integer i;

    // ---- Pass 1: top1 / top1_idx ----
    reg signed [SCORE_W-1:0] m1;
    reg [$clog2(N)-1:0]      idx1;
    always @(*) begin
        m1 = s[0]; idx1 = 0;
        for (i = 1; i < N; i = i + 1)
            if (s[i] > m1) begin
                m1 = s[i];
                idx1 = i[$clog2(N)-1:0];
            end
    end

    // ---- Pass 2: idx1 위치를 마스킹하고 재탐색 -> top2 ----
    reg signed [SCORE_W-1:0] m2;
    always @(*) begin
        m2 = (idx1 == 0) ? MINVAL : s[0];
        for (i = 1; i < N; i = i + 1)
            if ((i == idx1 ? MINVAL : s[i]) > m2)
                m2 = (i == idx1 ? MINVAL : s[i]);
    end

    always @(posedge clk) begin
        if (~rst_n) begin
            top1      <= {SCORE_W{1'b0}};
            top2      <= {SCORE_W{1'b0}};
            top1_idx  <= {$clog2(N){1'b0}};
            valid_out <= 1'b0;
        end else begin
            valid_out <= valid_in;
            if (valid_in) begin
                top1     <= m1;
                top2     <= m2;
                top1_idx <= idx1;
            end
        end
    end

endmodule
