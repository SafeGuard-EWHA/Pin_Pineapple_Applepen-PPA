//------------------------------------------------------------------------
//  mac_tree.v  -  범용 N-tap INT8 MAC + 재양자화
//
//  out = sat12( round_shift( sum_i data[i]*w[i] + bias , SHIFT ) )
//
//  * data : N x DATA_W signed   (conv1 은 픽셀 0~255 를 9-bit 로 zero-extend)
//  * w    : N x 8-bit signed
//  * bias : 16-bit signed, 누산기 도메인 (export_int8.py 규약)
//  * 재양자화 : (acc + 2^(SHIFT-1)) >> SHIFT, 12-bit 포화
//  Python golden(export_int8.py IntNet) 과 bit-accurate.
//------------------------------------------------------------------------
module mac_tree #(
    parameter N      = 25,
    parameter DATA_W = 12,
    parameter SHIFT  = 8,
    parameter ACC_W  = 32
) (
    input                         clk,
    input                         rst_n,
    input                         en,          // 1 이면 연산 (operand isolation)
    input                         valid_in,
    input  [N*DATA_W-1:0]         data_flat,
    input  [N*8-1:0]              w_flat,
    input  signed [15:0]          bias,
    output reg signed [11:0]      out,
    output reg                    valid_out
);

    integer i;
    reg signed [ACC_W-1:0] acc;
    reg signed [DATA_W-1:0] d;
    reg signed [7:0]        w;

    // operand isolation: en=0 이면 곱셈기 입력을 0 으로 고정해 스위칭 전력 차단
    always @(*) begin
        acc = {{(ACC_W-16){bias[15]}}, bias};
        for (i = 0; i < N; i = i + 1) begin
            d = en ? data_flat[i*DATA_W +: DATA_W] : {DATA_W{1'b0}};
            w = w_flat[i*8 +: 8];
            acc = acc + d * w;
        end
    end

    // 반올림 시프트 + 12-bit 포화
    wire signed [ACC_W-1:0] rnd = (SHIFT > 0) ? (acc + (1 <<< (SHIFT-1))) >>> SHIFT
                                              : acc;
    wire signed [11:0] sat = (rnd >  32'sd2047) ? 12'sd2047 :
                             (rnd < -32'sd2048) ? -12'sd2048 : rnd[11:0];

    always @(posedge clk) begin
        if (~rst_n) begin
            out       <= 12'sd0;
            valid_out <= 1'b0;
        end else begin
            valid_out <= valid_in & en;
            if (valid_in & en)
                out <= sat;
        end
    end

endmodule
