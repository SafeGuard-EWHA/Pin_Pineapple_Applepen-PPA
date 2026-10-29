//------------------------------------------------------------------------
//  fc_engine.v  -  범용 Fully-Connected 엔진 (Early / Light / Full FC 공용)
//
//  입력 캡처: valid_in 스트로브마다 C_IN 채널 x 12-bit 가 들어온다 (N_POS 회).
//             그중 앞 C_USE 채널만 사용 (Light FC 는 Conv2 ch0~3 만 사용).
//             buf[c*N_POS + pos] 배치 -> Python ravel() 순서와 동일.
//  연산     : go 이후 OUT_N 개 class score 를 1 사이클에 하나씩 순차 산출
//             (레퍼런스 fully_connected 와 같은 시간분할 구조, 면적 절약)
//  출력     : scores_flat [OUT_N x 12], done 펄스
//------------------------------------------------------------------------
module fc_engine #(
    parameter C_IN  = 3,
    parameter C_USE = 3,
    parameter N_POS = 16,
    parameter OUT_N = 10,
    parameter SHIFT = 9
) (
    input                         clk,
    input                         rst_n,
    input                         clear,                // 새 이미지 시작
    input                         valid_in,
    input  [C_IN*12-1:0]          data_in_flat,
    input                         go,                   // 연산 시작 허가 (FSM)
    input  [OUT_N*C_USE*N_POS*8-1:0] w_flat,            // [out][in]
    input  [OUT_N*16-1:0]         b_flat,
    output reg [OUT_N*12-1:0]     scores_flat,
    output reg                    captured,             // N_POS 개 캡처 완료
    output reg                    done                  // scores 유효 (1펄스)
);

    localparam IN_N = C_USE * N_POS;
    localparam PW   = (N_POS > 1) ? $clog2(N_POS) : 1;
    localparam OW   = (OUT_N > 1) ? $clog2(OUT_N) : 1;

    reg [IN_N*12-1:0] buf_flat;
    reg [PW-1:0]      pos;
    reg               busy;
    reg [OW-1:0]      j;            // 현재 산출 중인 출력 인덱스
    reg               j_valid;

    // ---- 입력 캡처 ----
    integer c;
    always @(posedge clk) begin
        if (~rst_n || clear) begin
            pos      <= {PW{1'b0}};
            captured <= 1'b0;
        end else if (valid_in && !captured) begin
            for (c = 0; c < C_USE; c = c + 1)
                buf_flat[(c*N_POS + pos)*12 +: 12] <= data_in_flat[c*12 +: 12];
            if (pos == N_POS - 1) captured <= 1'b1;
            else                  pos <= pos + 1'b1;
        end
    end

    // ---- 순차 dot-product ----
    wire signed [11:0] mac_out;
    wire               mac_v;
    mac_tree #(.N(IN_N), .DATA_W(12), .SHIFT(SHIFT)) u_mac (
        .clk(clk), .rst_n(rst_n), .en(1'b1), .valid_in(j_valid),
        .data_flat(buf_flat),
        .w_flat(w_flat[j*IN_N*8 +: IN_N*8]),
        .bias(b_flat[j*16 +: 16]),
        .out(mac_out), .valid_out(mac_v));

    reg [OW-1:0] j_d;               // mac 파이프 1단 지연된 인덱스
    reg          fired;             // 이미지당 1회만 연산 (재계산 방지)
    always @(posedge clk) begin
        if (~rst_n || clear) begin
            busy <= 1'b0; j <= {OW{1'b0}}; j_valid <= 1'b0; j_d <= {OW{1'b0}};
            done <= 1'b0; fired <= 1'b0;
        end else begin
            done <= 1'b0;
            j_d  <= j;
            if (!busy && captured && go && !fired) begin
                busy <= 1'b1; fired <= 1'b1; j <= {OW{1'b0}}; j_valid <= 1'b1;
            end else if (busy) begin
                if (j == OUT_N - 1) begin
                    j_valid <= 1'b0;
                    busy    <= 1'b0;
                end else
                    j <= j + 1'b1;
            end
            if (mac_v) begin
                scores_flat[j_d*12 +: 12] <= mac_out;
                if (j_d == OUT_N - 1) done <= 1'b1;
            end
        end
    end

endmodule
