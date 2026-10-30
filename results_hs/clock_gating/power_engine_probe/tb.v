`timescale 1ns/1ps
module tb;
reg clk=0,en=1,d=0;
wire q;
integer disabled;
probe dut(clk,en,d,q);
always #5 clk=~clk;
always @(negedge clk) d=~d;
initial begin
if (!$value$plusargs("DISABLED=%d",disabled)) disabled=0;
$dumpfile("probe.vcd"); $dumpvars(0,tb);
#21; if(disabled) en=0;
#979; $finish;
end
endmodule
