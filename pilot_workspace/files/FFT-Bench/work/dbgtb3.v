`timescale 1ns/1ps
module dbgtb3;
 reg clk=0,rst=1,in_valid=0,frame_start=0;
 reg signed[15:0] in_re=0,in_im=0;
 wire out_valid,out_start;wire signed[23:0] out_re,out_im;
 fft64_top dut(.clk(clk),.rst(rst),.in_valid(in_valid),.frame_start(frame_start),
               .in_re(in_re),.in_im(in_im),.out_valid(out_valid),.out_start(out_start),
               .out_re(out_re),.out_im(out_im));
 integer i,k;
 initial begin
   for(i=0;i<4;i=i+1) begin clk=0;rst=1;in_valid=0;frame_start=0; #5; clk=1; #5; end
   rst=0;
   for(i=0;i<64;i=i+1) begin
     clk=0; in_valid=1; frame_start=(i==0); in_re=(i==0)?16384:0; in_im=0; #5; clk=1; #5;
   end
   clk=0; in_valid=0; frame_start=0; #5;
   for(i=0;i<30;i=i+1) begin
     clk=0; #1;
     if (dut.st==2'd2)
       $display("cyc st=COMP bc=%0d slot=%0d base=%0d m=%0d ra0=%0d ra1=%0d rd0=%0d rd1=%0d we0=%b we1=%b wa0=%0d wa1=%0d wd0=%0d wd1=%0d pbase=%0d pstep=%0d",
         dut.bc,dut.slot,dut.cur_base,dut.cur_m,dut.ra0,dut.ra1,dut.rd0_re,dut.rd1_re,dut.we0,dut.we1,dut.wa0,dut.wa1,dut.wd0_re,dut.wd1_re,dut.pbase,dut.pstep);
     #4; clk=1; #5;
   end
   $finish;
 end
endmodule
