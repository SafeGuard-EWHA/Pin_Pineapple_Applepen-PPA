//------------------------------------------------------------------------
//  top2_finder.v  -  AdaPath-NPU Region 2  (N-class 범용판, 토너먼트 트리)
//
//  Early Classifier 의 N개 class score 에서 Top-1 / Top-2 / Top-1 index 를 추출한다.
//
//  구조: 이진 토너먼트 트리 (조합 논리, 출력 레지스터 1단 - 지연 cycle 불변)
//    각 노드가 (1위 값, 1위 index, 2위 값) 을 올려 보내고,
//    두 자식 A(낮은 index), B 의 병합 규칙은 다음과 같다.
//        A.v1 >= B.v1 : 1위 = A,  2위 = max(A.v2, B.v1)
//        A.v1 <  B.v1 : 1위 = B,  2위 = max(A.v1, B.v2)
//    동점이면 낮은 index 가 1위가 되므로 기존 순차 비교(strict '>') 와 결과가 동일하다.
//
//  논리 깊이: 기존 2-pass 비교기 체인 2(N-1)단 -> 트리 ceil(log2 N) 단.
//  (이전 판은 임계 경로가 이 모듈의 비교기 체인이어서 Fmax 를 제한했다.)
//------------------------------------------------------------------------
module top2_finder #(
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

    localparam IW = $clog2(N);
    localparam NP = (1 << IW);                       // 2의 거듭제곱으로 패딩
    localparam signed [SCORE_W-1:0] MINVAL = {1'b1, {SCORE_W-1{1'b0}}};

    // 힙 인덱스 트리: 노드 k 의 자식은 2k, 2k+1 / 잎은 NP .. 2NP-1
    reg signed [SCORE_W-1:0] v1 [1:2*NP-1];
    reg signed [SCORE_W-1:0] v2 [1:2*NP-1];
    reg        [IW-1:0]      id [1:2*NP-1];

    integer k;
    always @(*) begin
        for (k = 0; k < NP; k = k + 1) begin
            v1[NP+k] = (k < N) ? scores_flat[k*SCORE_W +: SCORE_W] : MINVAL;
            v2[NP+k] = MINVAL;
            id[NP+k] = k[IW-1:0];
        end
        for (k = NP-1; k >= 1; k = k - 1) begin
            if (v1[2*k] >= v1[2*k+1]) begin
                v1[k] = v1[2*k];
                id[k] = id[2*k];
                v2[k] = (v2[2*k] >= v1[2*k+1]) ? v2[2*k] : v1[2*k+1];
            end else begin
                v1[k] = v1[2*k+1];
                id[k] = id[2*k+1];
                v2[k] = (v1[2*k] >= v2[2*k+1]) ? v1[2*k] : v2[2*k+1];
            end
        end
    end

    always @(posedge clk) begin
        if (~rst_n) begin
            top1      <= {SCORE_W{1'b0}};
            top2      <= {SCORE_W{1'b0}};
            top1_idx  <= {IW{1'b0}};
            valid_out <= 1'b0;
        end else begin
            valid_out <= valid_in;
            if (valid_in) begin
                top1     <= v1[1];
                top2     <= v2[1];
                top1_idx <= id[1];
            end
        end
    end

endmodule
