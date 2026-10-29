`timescale 1ps/1ps
module monitor_selftest;
 reg clk=0,rst_n=0,start=0,mode_v=0,valid_out=0,conv2_en=0,fc_light_en=0,fc_full_en=0,fsm_done=0;
 reg [1:0] mode=0,result_sel=0;
 reg [2:0] state=0;
 reg [11:0] margin=50;
 reg [7:0] ch_en=0,data_in=0;
 reg [3:0] decision=0;
 always #50 clk=~clk;
 control_monitor mon(.*);
 task begin_image(input [1:0] m);
 begin
   @(negedge clk); rst_n=0; start=0; mode_v=0; valid_out=0; state=0; fsm_done=0;
   conv2_en=0; fc_light_en=0;fc_full_en=0;ch_en=0;result_sel=0;
   @(negedge clk); rst_n=1;start=1;
   @(negedge clk);start=0;state=2;mode=m;mode_v=1;
   @(negedge clk);mode_v=0;state=3;result_sel=m;
   if(m==0) begin state=4;fsm_done=1;end
   else begin conv2_en=1;ch_en=(m==1)?8'h0f:8'hff;fc_light_en=(m==1);fc_full_en=(m==2);end
 end endtask
 task finish_image;
 begin @(negedge clk);state=4;fsm_done=1;conv2_en=0;ch_en=0;fc_light_en=0;fc_full_en=0;
 @(negedge clk);state=0;fsm_done=0;result_sel=0;valid_out=1;
 @(negedge clk);valid_out=0;end endtask
 initial begin
   begin_image(0);finish_image;
   begin_image(1);finish_image;
   begin_image(2);finish_image;
   if(mon.completed!=3 || mon.easy_errors+mon.medium_errors+mon.mux_errors+mon.deadline_errors!=0)
     $fatal(1,"SELFTEST clean controls failed");
   begin_image(0);conv2_en=1;@(negedge clk);conv2_en=0;finish_image;
   begin_image(1);ch_en=8'hff;@(negedge clk);ch_en=8'h0f;finish_image;
   begin_image(2);result_sel=0;@(negedge clk);result_sel=2;finish_image;
   begin_image(2);repeat(4001) @(negedge clk);finish_image;
   if(mon.easy_errors<1 || mon.medium_errors<1 || mon.mux_errors<1 || mon.deadline_errors<1)
      $fatal(1,"SELFTEST fault detection failed");
   $display("SELFTEST PASS clean=3 injected_easy=%0d injected_medium=%0d injected_mux=%0d injected_deadline=%0d",mon.easy_errors,mon.medium_errors,mon.mux_errors,mon.deadline_errors);
   $finish;
 end
endmodule
