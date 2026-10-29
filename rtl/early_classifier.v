//------------------------------------------------------------------------
//  early_classifier.v  -  Region 1 Early Classifier
//
//  Conv1 pool 출력(12x12 x C1 스트로브)을 3x3 AvgPool(÷8 근사, sum>>3) 하여
//  4x4 x C1 = 48 특징으로 압축하고, fc_engine(48 -> N_CLASS) 으로
//  1차 class score 를 산출한다.  fc_engine 은 Full/Light FC 와 동일 모듈을
//  재사용하므로 별도 FC 회로가 추가되지 않는다.
//
//  AvgPool 은 스트리밍 누산 방식: 픽셀이 도착할 때마다 해당 3x3 bin 의
//  누산기에 더한다 (16 bin x C1 개 누산기, 12x12 버퍼 불필요).
//------------------------------------------------------------------------
module early_classifier #(
    parameter C1      = 3,
    parameter N_CLASS = 10,
    parameter SHIFT   = 9
) (
    input                       clk,
    input                       rst_n,
    input                       clear,
    input                       valid_in,            // pool 스트로브 (144회)
    input  [C1*12-1:0]          data_in_flat,
    input  [N_CLASS*C1*16*8-1:0] w_flat,
    input  [N_CLASS*16-1:0]     b_flat,
    output [N_CLASS*12-1:0]     scores_flat,
    output                      done
);

    // ---- 3x3 AvgPool 누산 ----
    reg [7:0]  pos;                             // 0..143
    wire [3:0] row = pos / 12;
    wire [3:0] col = pos % 12;
    wire [3:0] bin = (row / 3) * 4 + (col / 3); // 0..15

    reg signed [15:0] acc [0:C1-1][0:15];
    reg               acc_done;
    integer c, k;

    always @(posedge clk) begin
        if (~rst_n || clear) begin
            pos <= 8'd0; acc_done <= 1'b0;
            for (c = 0; c < C1; c = c + 1)
                for (k = 0; k < 16; k = k + 1)
                    acc[c][k] <= 16'sd0;
        end else if (valid_in && !acc_done) begin
            for (c = 0; c < C1; c = c + 1)
                acc[c][bin] <= acc[c][bin] + $signed(data_in_flat[c*12 +: 12]);
            if (pos == 8'd143) acc_done <= 1'b1;
            else               pos <= pos + 1'b1;
        end
    end

    // ---- 16 bin 을 순서대로 fc_engine 에 스트로브로 전달 ----
    reg [4:0] emit;                               // 0..16
    reg       emit_v;
    reg [C1*12-1:0] emit_data;
    integer cc;
    always @(posedge clk) begin
        if (~rst_n || clear) begin
            emit <= 5'd0; emit_v <= 1'b0; emit_data <= {C1*12{1'b0}};
        end else begin
            emit_v <= 1'b0;
            if (acc_done && emit < 5'd16) begin
                for (cc = 0; cc < C1; cc = cc + 1)
                    emit_data[cc*12 +: 12] <= sat12(acc[cc][emit] >>> 3);
                emit_v <= 1'b1;
                emit   <= emit + 1'b1;
            end
        end
    end

    function signed [11:0] sat12(input signed [15:0] v);
        sat12 = (v > 16'sd2047) ? 12'sd2047 : (v < -16'sd2048) ? -12'sd2048 : v[11:0];
    endfunction

    fc_engine #(.C_IN(C1), .C_USE(C1), .N_POS(16), .OUT_N(N_CLASS), .SHIFT(SHIFT)) u_fc (
        .clk(clk), .rst_n(rst_n), .clear(clear),
        .valid_in(emit_v), .data_in_flat(emit_data),
        .go(1'b1),                                // 캡처 즉시 연산
        .w_flat(w_flat), .b_flat(b_flat),
        .scores_flat(scores_flat), .captured(), .done(done));

endmodule
