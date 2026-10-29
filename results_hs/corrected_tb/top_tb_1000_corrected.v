// Derived verification TB. Original submission TB and RTL are unchanged.
// Keep original ports, weight loading and positive-edge NBA pixel timing.
// Fix initialization, image bounds, 784-pixel read bound and output-based stop.
`timescale 1ps/1ps
module top_tb_1000_corrected();

reg clk, rst_n;
reg [7:0] pixels [0:783999];
reg [9:0] img_idx;
reg [7:0] data_in;
reg [9:0] cnt;  // num of input image (1000)
reg [9:0] input_cnt;
reg [9:0] rand_num; // 1000
reg state;

integer i_cnt;  // loop variable
reg [9:0] accuracy; // hit/miss count (1000)


wire [3:0] decision;
wire valid_out_6;

//conv1
reg signed [7:0] weight_11 [0:24];
reg signed [7:0] weight_12 [0:24];
reg signed [7:0] weight_13 [0:24];
reg signed [7:0] bias_1 [0:2];
//conv2
reg signed [7:0] bias_2 [0:2];
reg signed [7:0] weight_211 [0:24];
reg signed [7:0] weight_212 [0:24];
reg signed [7:0] weight_213 [0:24];

reg signed [7:0] weight_221 [0:24];
reg signed [7:0] weight_222 [0:24];
reg signed [7:0] weight_223 [0:24];

reg signed [7:0] weight_231 [0:24];
reg signed [7:0] weight_232 [0:24];
reg signed [7:0] weight_233 [0:24];
//fullyconnected

reg signed [7:0] weight_fc [0:479];
reg signed [7:0] bias_fc [0:9];


wire signed [0:199] w_11;
wire signed [0:199] w_12;
wire signed [0:199] w_13;
wire signed [0:23] b_1;
wire signed [0:23] b_2;
wire signed [0:199] w_211;
wire signed [0:199] w_212;
wire signed [0:199] w_213;
wire signed [0:199] w_221;
wire signed [0:199] w_222;
wire signed [0:199] w_223;
wire signed [0:199] w_231;
wire signed [0:199] w_232;
wire signed [0:199] w_233;
wire signed [0:3839] w_fc;
wire signed [0:79] b_fc;
// Clock generation
always #5 clk = ~clk;

// Read image text file

initial begin
   //conv1
   $readmemh("conv1_weight_1.txt", weight_11);
   $readmemh("conv1_weight_2.txt", weight_12);
   $readmemh("conv1_weight_3.txt", weight_13);
   $readmemh("conv1_bias.txt", bias_1);
   //conv2
   $readmemh("conv2_bias.txt", bias_2);
   	$readmemh("conv2_weight_11.txt", weight_211);
	$readmemh("conv2_weight_12.txt", weight_212);
	$readmemh("conv2_weight_13.txt", weight_213);
	$readmemh("conv2_weight_21.txt", weight_221);
	$readmemh("conv2_weight_22.txt", weight_222);
	$readmemh("conv2_weight_23.txt", weight_223);
    $readmemh("conv2_weight_31.txt", weight_231);
	$readmemh("conv2_weight_32.txt", weight_232);
	$readmemh("conv2_weight_33.txt", weight_233);
   //fullyconnected
   $readmemh("fc_weight.txt", weight_fc);
   $readmemh("fc_bias.txt", bias_fc);
 end
 

chip chip1 (
clk,rst_n,data_in,decision,valid_out_6,
 w_11 , w_12 , w_13 , b_1 ,
//conv2
 b_2 , w_211 , w_212 , w_213 , w_221 , w_222 , w_223 , w_231 , w_232 , w_233 ,
//fullyconnected
 w_fc, b_fc);

genvar i;
generate
    for(i=0;i<=24;i=i+1) begin
        assign w_11[(8*i)+:8]=weight_11[i];
        assign w_12[(8*i)+:8]=weight_12[i];
        assign w_13[(8*i)+:8]=weight_13[i];
        assign w_211[(8*i)+:8]=weight_211[i];
        assign w_212[(8*i)+:8]=weight_212[i];
        assign w_213[(8*i)+:8]=weight_213[i];
        assign w_221[(8*i)+:8]=weight_221[i];
        assign w_222[(8*i)+:8]=weight_222[i];
        assign w_223[(8*i)+:8]=weight_223[i];
        assign w_231[(8*i)+:8]=weight_231[i];
        assign w_232[(8*i)+:8]=weight_232[i];
        assign w_233[(8*i)+:8]=weight_233[i];            
    end
    for(i=0;i<=2;i=i+1) begin
        assign b_1[(8*i)+:8]=bias_1[i];
        assign b_2[(8*i)+:8]=bias_2[i];          
    end
    for(i=0;i<=479;i=i+1) begin
        assign w_fc[(8*i)+:8]=weight_fc[i];    
    end
    for(i=0;i<=9;i=i+1) begin
        assign b_fc[(8*i)+:8]=bias_fc[i];          
    end
endgenerate




integer outputs=0, correct_count=0, cycle_count=0, total_cycles=0;
integer read_count=0, all_reads=0, x_outputs=0, timeout_count=0;
integer easy_count=0, medium_count=0, hard_count=0;
integer sequential=0, seed_value=2026, seed_state, rng_init, unused_arg;
integer seen[0:999];
integer unique_images=0;

initial begin
  $readmemh("input_1000.txt", pixels);
  unused_arg=$value$plusargs("SEQUENTIAL=%d", sequential);
  unused_arg=$value$plusargs("SEED=%d", seed_value);
  seed_state=seed_value;
  rng_init=$urandom(seed_state);
  for(i_cnt=0;i_cnt<1000;i_cnt=i_cnt+1) seen[i_cnt]=0;
  cnt=0; img_idx=0; clk=0; input_cnt=0; rst_n=0;
  state=0; data_in=0; accuracy=0;
  if(sequential) rand_num=0; else rand_num=$urandom_range(999,0);
  $display("PROTOCOL sequential=%0d seed=%0d clock_ps=10 outputs_target=1000 pixels_per_image=784",sequential,seed_value);
end

always @(posedge clk) begin
  if(!rst_n) begin
    cycle_count=0;
    #3 rst_n<=1;
  end else begin
    cycle_count=cycle_count+1;
    if(cycle_count>4000) begin
      timeout_count=timeout_count+1;
      $fatal(1,"TIMEOUT output=%0d image=%0d",outputs,rand_num);
    end
    if(valid_out_6 === 1'b1) begin
      outputs=outputs+1;
      if(read_count!=784) $fatal(1,"PIXEL_COUNT count=%0d",read_count);
      if((^decision)===1'bx) x_outputs=x_outputs+1;
      if(decision===rand_num%10) correct_count=correct_count+1;
      accuracy=correct_count;
      if(seen[rand_num]==0) unique_images=unique_images+1;
      seen[rand_num]=seen[rand_num]+1;
      case(chip1.u_core.mode_out)
        0: easy_count=easy_count+1;
        1: medium_count=medium_count+1;
        2: hard_count=hard_count+1;
        default: $fatal(1,"UNKNOWN_MODE");
      endcase
      total_cycles=total_cycles+cycle_count;
      $display("RESULT,%0d,%0d,%0d,%0d,%0d,%0d",outputs,rand_num,rand_num%10,decision,chip1.u_core.mode_out,cycle_count);
      if(outputs==1000) begin
        $display("SUMMARY outputs=%0d correct=%0d easy=%0d medium=%0d hard=%0d reads=%0d x_outputs=%0d timeouts=%0d total_cycles=%0d unique_indices=%0d",outputs,correct_count,easy_count,medium_count,hard_count,all_reads,x_outputs,timeout_count,total_cycles,unique_images);
        #1;
        if(x_outputs || timeout_count || all_reads!=784000) $fatal(1,"VALIDATION_FAILED");
        $finish;
      end
      state<=0; rst_n<=0; img_idx<=0; data_in<=0;
      read_count=0; cnt<=outputs;
      if(sequential) rand_num<=rand_num+1; else rand_num<=$urandom_range(999,0);
    end else if(state==0) begin
      if(img_idx<784) begin
        if(rand_num>999) $fatal(1,"IMAGE_BOUNDS");
        if((^pixels[rand_num*784+img_idx])===1'bx) $fatal(1,"UNKNOWN_INPUT");
        data_in<=pixels[rand_num*784+img_idx];
        img_idx<=img_idx+1;
        read_count=read_count+1; all_reads=all_reads+1;
      end else begin
        // No 785th array read. The final pixel has reached the DUT on this edge.
        data_in<=0; state<=1;
      end
    end
  end
end
endmodule
