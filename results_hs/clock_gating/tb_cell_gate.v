`timescale 1ns/1ps
// Zero-delay cell-model sanity check; not a setup/hold or PVT test.
module tb_cell_gate;
  reg clk=0, en=0, d=0;
  wire held, gated, sampled, icg_out;
  reg held_ref, sampled_ref;
  integer checks=0;
  DLLx1_ASAP7_75t_R latch_cell(.CLK(clk), .D(en), .Q(held));
  assign gated=clk & held;
  ICGx1_ASAP7_75t_R icg_cell(.CLK(clk), .ENA(en), .SE(1'b0), .GCLK(icg_out));
  DFFHQNx1_ASAP7_75t_R ff_cell(.CLK(gated), .D(d), .QN(sampled));
  always #5 clk=~clk;
  always @(*) if (!clk) held_ref <= en;
  wire gated_ref=clk & held_ref;
  // QN is the inverted output of this particular library cell.
  always @(posedge gated_ref) sampled_ref <= ~d;
  always @(negedge clk) begin
    #1;
    if (held !== held_ref || gated !== gated_ref || sampled !== sampled_ref || icg_out !== gated_ref)
      $fatal(1,"CELL_MODEL mismatch at %0t", $time);
    checks=checks+1;
  end
  initial begin
    #1 en=1;
    #6 en=0; d=1;
    #7 en=1;
    #8 en=0; d=0;
    #11 en=1;
    #9 d=1;
    #14 en=0;
    #30;
    $display("CELL_MODEL PASS checks=%0d",checks);
    $finish;
  end
endmodule
