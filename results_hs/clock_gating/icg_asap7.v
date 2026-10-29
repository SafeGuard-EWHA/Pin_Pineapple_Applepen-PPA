// Technology-specific counterpart of rtl/icg_latch.v for ASIC synthesis only.
// The original portable model and original project RTL remain unchanged.
module icg_latch(input clk, input enable, input test_enable, output gclk);
    (* keep = 1 *) ICGx1_ASAP7_75t_R u_icg (
        .CLK(clk), .ENA(enable), .SE(test_enable), .GCLK(gclk)
    );
endmodule
