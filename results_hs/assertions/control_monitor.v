`timescale 1ps/1ps
// Read-only observer. Sample inputs at posedge and outputs after NBA (+1 ps).
module control_monitor #(parameter C2=8, C2_MED=4, TL=13, TH=41)(
 input clk,rst_n,start,mode_v,valid_out,conv2_en,fc_light_en,fc_full_en,fsm_done,
 input [1:0] mode,result_sel, input [2:0] state,
 input [11:0] margin, input [C2-1:0] ch_en,
 input [3:0] decision, input [7:0] data_in);
 integer starts=0,completed=0,aborted=0,age=0,max_cycles=0;
 integer easy=0,n_medium=0,hard=0,unknown_mode=0;
 integer margin_low=0,margin_mid=0,margin_high=0,margin_unknown=0;
 integer easy_checks=0,medium_checks=0,mux_checks=0,deadline_checks=0;
 integer easy_errors=0,medium_errors=0,mux_errors=0,deadline_errors=0;
 integer unknown_controls=0,unknown_input_cycles=0,unknown_decisions=0;
 reg active=0,decided=0,timed_out=0;
 reg [1:0] chosen;
 reg sampled_start,sampled_reset,sampled_accept;
 integer fd;
 initial begin
   fd=$fopen("transactions.csv","w");
   $fdisplay(fd,"transaction,mode,margin,cycles,decision,time_ps");
 end
 always @(posedge clk) begin
   sampled_reset=(rst_n !== 1'b1);
   sampled_start=(start === 1'b1);
   sampled_accept=(state === 3'd2 && mode_v === 1'b1);
   if(sampled_reset) begin
     if(active) aborted=aborted+1;
     active=0; decided=0;
   end else begin
     if(sampled_start) begin
       if(active) aborted=aborted+1;
       starts=starts+1; active=1; age=0; decided=0; timed_out=0;
     end else if(active) age=age+1;
     if(sampled_accept && active) begin chosen=mode; decided=1; end
     #1;
     if(active) begin
       if(^data_in === 1'bx) unknown_input_cycles=unknown_input_cycles+1;
       if(^{conv2_en,fc_light_en,fc_full_en,ch_en,result_sel} === 1'bx)
         unknown_controls=unknown_controls+1;
       if(decided && chosen === 2'd0) begin
         easy_checks=easy_checks+1;
         if(conv2_en !== 1'b0) easy_errors=easy_errors+1;
       end
       // Mask requirement applies while the n_medium backend is active;
       // it must be zero after the backend is disabled.
       if(decided && chosen === 2'd1 && state === 3'd3) begin
         medium_checks=medium_checks+1;
         if(ch_en !== ((1 << C2_MED)-1) || conv2_en !== 1'b1 ||
            fc_light_en !== 1'b1 || fc_full_en !== 1'b0)
           medium_errors=medium_errors+1;
       end
       // result_sel is consumed at S_DONE; IDLE intentionally defaults to Early.
       if(decided && (state === 3'd3 || fsm_done === 1'b1)) begin
         mux_checks=mux_checks+1;
         if(chosen === 2'd0 || chosen === 2'd1 || chosen === 2'd2) begin
           if(result_sel !== chosen) mux_errors=mux_errors+1;
         end else if(result_sel !== 2'd2) mux_errors=mux_errors+1;
       end
       if(age >= 4000 && valid_out !== 1'b1 && !timed_out) begin
         deadline_errors=deadline_errors+1; timed_out=1;
       end
       if(valid_out === 1'b1) begin
         completed=completed+1; deadline_checks=deadline_checks+1;
         if(age > 4000 && !timed_out) deadline_errors=deadline_errors+1;
         if(age>max_cycles) max_cycles=age;
         case(chosen)
           0:easy=easy+1; 1:n_medium=n_medium+1; 2:hard=hard+1;
           default:unknown_mode=unknown_mode+1;
         endcase
         if(^margin === 1'bx) margin_unknown=margin_unknown+1;
         else if(margin<TL) margin_low=margin_low+1;
         else if(margin<TH) margin_mid=margin_mid+1;
         else margin_high=margin_high+1;
         if(^decision === 1'bx) unknown_decisions=unknown_decisions+1;
         $fdisplay(fd,"%0d,%0d,%0d,%0d,%0d,%0t",completed,chosen,margin,age,decision,$time);
         $fflush(fd);
         active=0;
       end
     end
   end
 end
endmodule
