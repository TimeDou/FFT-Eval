`timescale 1ns/1ps
module dbgtb2;
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
   for(i=0;i<250;i=i+1) begin clk=1; #1;
     if (dut.st==2'd2 && dut.slot==3'd0 && dut.bc<=6'd17)
        $display("b=%0d base=%0d m=%0d rd0=%0d rd1=%0d", dut.bc, dut.cur_base, dut.cur_m, dut.rd0_re, dut.rd1_re);
     if (dut.st==2'd2 && dut.slot==3'd1 && dut.bc<=6'd17)
        $display("b=%0d slot1 rd0=%0d rd1=%0d (addr %0d %0d)", dut.bc, dut.rd0_re, dut.rd1_re, dut.ra0, dut.ra1);
     if (dut.st==2'd2 && dut.slot==3'd3 && dut.bc<=6'd17)
        $display("b=%0d y=%0d %0d %0d %0d", dut.bc, dut.y0_re, dut.y1_re, dut.y2_re, dut.y3_re);
     #4; clk=0; #5;
   end
   $finish;
 end
endmodule
