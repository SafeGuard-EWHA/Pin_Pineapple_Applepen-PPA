//------------------------------------------------------------------------
//  score_margin_calc.v  -  AdaPath-NPU Region 2
//
//  Score Margin = Top-1 score - Top-2 score.
//  top1 >= top2 가 보장되므로 결과는 항상 0 이상 -> unsigned 12-bit.
//  하드웨어 비용: Subtractor 1개. (Entropy 방식의 log LUT 를 대체하는
//  본 과제 핵심 아이디어의 회로 구현부)
//------------------------------------------------------------------------
module score_margin_calc #(
    parameter SCORE_W = 12
) (
    input                        clk,
    input                        rst_n,
    input                        valid_in,
    input  signed [SCORE_W-1:0]  top1,
    input  signed [SCORE_W-1:0]  top2,
    output reg [SCORE_W-1:0]     margin,      // 0 ~ 2^SCORE_W - 2
    output reg                   valid_out
);

    wire signed [SCORE_W:0] diff = top1 - top2;   // 1비트 확장 감산

    always @(posedge clk) begin
        if (~rst_n) begin
            margin    <= {SCORE_W{1'b0}};
            valid_out <= 1'b0;
        end else begin
            valid_out <= valid_in;
            if (valid_in)
                margin <= diff[SCORE_W-1:0];      // top1>=top2 이므로 부호비트 0
        end
    end

endmodule
