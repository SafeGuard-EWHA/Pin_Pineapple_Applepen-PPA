module probe(input clk,en,d,output q);
wire gc;
ICGx1_ASAP7_75t_R gate(.CLK(clk),.ENA(en),.SE(1'b0),.GCLK(gc));
DFFHQNx1_ASAP7_75t_R ff(.CLK(gc),.D(d),.QN(q));
endmodule
