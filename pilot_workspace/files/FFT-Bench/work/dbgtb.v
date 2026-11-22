`timescale 1ns/1ps
module dbgtb;
 reg clk=0,rst=1,in_valid=0,frame_start=0;
 reg signed[15:0] in_re=0,in_im=0;
 wire out_valid,out_start;wire signed[23:0] out_re,out_im;
 fft64_top dut(.clk(clk),.rst(rst),.in_valid(in_valid),.frame_start(frame_start),
               .in_re(in_re),.in_im(in_im),.out_valid(out_valid),.out_start(out_start),
               .out_re(out_re),.out_im(out_im));
 integer i,k;
 initial begin
   // reset
   for(i=0;i<4;i=i+1) begin clk=0;rst=1;in_valid=0;frame_start=0; #5; clk=1; #5; end
   rst=0;
   // load 64 samples: impulse at n=0 of 16384
   for(i=0;i<64;i=i+1) begin
     clk=0; in_valid=1; frame_start=(i==0); in_re=(i==0)?16384:0; in_im=0; #5; clk=1; #5;
   end
   clk=0; in_valid=0; frame_start=0; #5;
   // wait for completion of compute: 196 cycles
   for(i=0;i<250;i=i+1) begin clk=1; #5; clk=0; #5;
     if (dut.st==2'd3 && dut.oc==6'd0) begin
       $display("OUT phase reached at loop %0d", i);
       for(k=0;k<64;k=k+1) $display("MEM %0d %0d", k, dut.mem_re[k]);
       $finish;
     end
   end
   $display("no out phase"); for(k=0;k<64;k=k+1) $display("MEM %0d %0d", k, dut.mem_re[k]);
   $finish;
 end
endmodule
