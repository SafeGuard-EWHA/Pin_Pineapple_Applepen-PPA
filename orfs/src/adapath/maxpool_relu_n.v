//------------------------------------------------------------------------
//  maxpool_relu_n.v  -  C채널 2x2 MaxPool + ReLU (스트리밍)
//
//  레퍼런스 maxpool_relu.v 의 제어 로직을 채널 수 C 로 일반화한 것.
//  입력: raster 순서로 valid_in 스트로브와 함께 1 픽셀(C채널)씩
//        한 행의 유효 픽셀 수 = 2*HALF_WIDTH
//  출력: 2x2 블록이 완성될 때마다 valid_out 1사이클 + C채널 결과
//  max 후 ReLU (ReLU 는 단조증가라 순서 무관, golden 과 동치)
//------------------------------------------------------------------------
module maxpool_relu_n #(
    parameter C          = 3,
    parameter DATA_W     = 12,
    parameter HALF_WIDTH = 12
) (
    input                       clk,
    input                       rst_n,
    input                       valid_in,
    input  [C*DATA_W-1:0]       data_in_flat,
    output reg [C*DATA_W-1:0]   data_out_flat,
    output reg                  valid_out
);

    localparam PW = (HALF_WIDTH > 1) ? $clog2(HALF_WIDTH) : 1;

    reg signed [DATA_W-1:0] buffer [0:C-1][0:HALF_WIDTH-1];
    reg [PW-1:0] pcount;
    reg          state;      // 0: 첫째 행, 1: 둘째 행
    reg          flag;       // 0: 쌍의 첫 픽셀, 1: 둘째 픽셀

    integer c;
    reg signed [DATA_W-1:0] din, mx;

    always @(posedge clk) begin
        if (~rst_n) begin
            valid_out <= 1'b0;
            pcount    <= {PW{1'b0}};
            state     <= 1'b0;
            flag      <= 1'b0;
            data_out_flat <= {C*DATA_W{1'b0}};
        end else begin
            valid_out <= 1'b0;
            if (valid_in) begin
                flag <= ~flag;
                if (flag) begin
                    if (pcount == HALF_WIDTH - 1) begin
                        pcount <= {PW{1'b0}};
                        state  <= ~state;
                    end else
                        pcount <= pcount + 1'b1;
                end

                for (c = 0; c < C; c = c + 1) begin
                    din = data_in_flat[c*DATA_W +: DATA_W];
                    if (!state && !flag) begin
                        buffer[c][pcount] <= din;                       // 1번째
                    end else if (!state && flag) begin
                        if (buffer[c][pcount] < din) buffer[c][pcount] <= din;   // 2번째
                    end else if (state && !flag) begin
                        if (buffer[c][pcount] < din) buffer[c][pcount] <= din;   // 3번째
                    end else begin                                       // 4번째 + ReLU
                        mx = (buffer[c][pcount] < din) ? din : buffer[c][pcount];
                        data_out_flat[c*DATA_W +: DATA_W] <= (mx > 0) ? mx : {DATA_W{1'b0}};
                    end
                end
                if (state && flag) valid_out <= 1'b1;
            end
        end
    end

endmodule
