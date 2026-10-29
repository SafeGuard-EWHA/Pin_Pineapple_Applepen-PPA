`timescale 1ns/1ps
module tb_icg;
 reg clk=0,enable=0,test_enable=0;
 wire gclk;
 icg_latch dut(clk,enable,test_enable,gclk);
 always #5 clk=~clk;
 time last_rise,last_fall;
 integer errors=0,rises=0,falls=0;
 always @(posedge clk) last_rise=$time;
 always @(negedge clk) last_fall=$time;
 always @(posedge gclk) begin
   #0;
   rises=rises+1;
   if(clk !== 1'b1 || $time!=last_rise) errors=errors+1;
 end
 always @(negedge gclk) begin
   #0;
   if($time>0) begin
     falls=falls+1;
     if(clk !== 1'b0 || $time!=last_fall) errors=errors+1;
   end
 end
 initial begin
   // Includes enable changes during high phase, which must not truncate pulses.
   #7 enable=1; #7 enable=0; #8 enable=1; #5 enable=0;
   #9 test_enable=1; #2 test_enable=0; #7 test_enable=1;
   #18 test_enable=0; #11 enable=1; #13 enable=0;
   #33;
   if(errors || rises==0 || rises!=falls) $fatal(1,"ICG_TEST failed errors=%0d rises=%0d falls=%0d",errors,rises,falls);
   $display("ICG_TEST PASS phase_errors=%0d rises=%0d falls=%0d",errors,rises,falls);
   $finish;
 end
endmodule
