// Technology-independent, low-level-transparent clock-gating model.
// This is not a claim that synthesis mapped it to a characterized ICG cell.
module icg_latch(input clk, input enable, input test_enable, output gclk);
    reg enable_latched;
    always @(*) begin
        if (!clk) enable_latched <= enable | test_enable;
    end
    assign gclk = clk & enable_latched;
endmodule
