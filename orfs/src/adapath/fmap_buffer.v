//------------------------------------------------------------------------
//  fmap_buffer.v  -  Region 1 Feature Map Buffer
//
//  Conv1 -> MaxPool/ReLU 출력(12x12 x C1, raster 순서 스트로브)을 저장한다.
//  난이도 판정(Region 2)이 끝난 뒤 FSM 이 replay 를 올리면, 저장된 특징맵을
//  1 px/cycle 로 Conv2 라인버퍼에 다시 흘려보낸다.
//  => Easy 모드에서는 replay 가 일어나지 않으므로 Conv2 가 실제로 구동되지 않는다.
//
//  replay 길이 = N_PIX + FLUSH : 라인버퍼가 마지막 윈도우들을 밀어내도록
//  FLUSH 사이클 동안 valid 를 유지(데이터 0)한다.
//------------------------------------------------------------------------
module fmap_buffer #(
    parameter C      = 3,
    parameter N_PIX  = 144,          // 12 x 12
    parameter FLUSH  = 64
) (
    input                   clk,
    input                   rst_n,
    input                   clear,
    input                   valid_in,
    input  [C*12-1:0]       data_in_flat,
    output reg              full,            // N_PIX 개 저장 완료 (= front_done 원천)
    input                   replay,          // 1 사이클 펄스
    output reg              out_valid,
    output reg [C*12-1:0]   out_flat,
    output reg              replay_done
);

    localparam AW = $clog2(N_PIX + FLUSH + 1);

    reg [C*12-1:0] mem [0:N_PIX-1];
    reg [AW-1:0]   wptr, rptr;
    reg            playing;

    always @(posedge clk) begin
        if (~rst_n || clear) begin
            wptr <= {AW{1'b0}}; full <= 1'b0;
            rptr <= {AW{1'b0}}; playing <= 1'b0;
            out_valid <= 1'b0; replay_done <= 1'b0;
            out_flat <= {C*12{1'b0}};
        end else begin
            replay_done <= 1'b0;
            // ---- 쓰기 ----
            if (valid_in && !full) begin
                mem[wptr] <= data_in_flat;
                if (wptr == N_PIX - 1) full <= 1'b1;
                else                   wptr <= wptr + 1'b1;
            end
            // ---- 재생 ----
            if (replay && full && !playing) begin
                playing <= 1'b1; rptr <= {AW{1'b0}};
            end
            if (playing) begin
                out_valid <= 1'b1;
                out_flat  <= (rptr < N_PIX) ? mem[rptr] : {C*12{1'b0}};
                if (rptr == N_PIX + FLUSH - 1) begin
                    playing <= 1'b0; replay_done <= 1'b1;
                end else
                    rptr <= rptr + 1'b1;
            end else
                out_valid <= 1'b0;
        end
    end

endmodule
