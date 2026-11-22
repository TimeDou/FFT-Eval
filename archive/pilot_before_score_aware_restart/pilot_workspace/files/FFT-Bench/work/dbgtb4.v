`timescale 1ns/1ps
module dbgtb4;
 reg clk=0,rst=1,in_valid=0,frame_start=0;
 reg signed[15:0] in_re=0,in_im=0;
 wire out_valid,out_start;wire signed[23:0] out_re,out_im;
 fft64_top dut(.clk(clk),.rst(rst),.in_valid(in_valid),.frame_start(frame_start),
               .in_re(in_re),.in_im(in_im),.out_valid(out_valid),.out_start(out_start),
               .out_re(out_re),.out_im(out_im));
 integer i,k;
 task dumpmem; begin
   for(k=0;k<64;k=k+1) if(dut.mem_re[k]!==0) $display("   mem[%0d]=%0d",k,dut.mem_re[k]);
 end endtask
 initial begin
   for(i=0;i<4;i=i+1) begin clk=0;rst=1;in_valid=0;frame_start=0; #5; clk=1; #5; end
   rst=0;
   for(i=0;i<64;i=i+1) begin
     clk=0; in_valid=1; frame_start=(i==0); in_re=(i==0)?16384:0; in_im=0; #5; clk=1; #5;
   end
   clk=0; in_valid=0; frame_start=0; #5;
   for(i=0;i<400;i=i+1) begin
     clk=0; #1;
     if (dut.st==2'd2 && dut.slot==3'd3)
       $display("bc=%0d slot3: x0=%0d x1=%0d x2=%0d x3=%0d p1=%0d p2=%0d p3=%0d ny0=%0d ny1=%0d ny2=%0d ny3=%0d",
          dut.bc,dut.x0_re,dut.x1_re,dut.x2_re,dut.x3_re,dut.p1r_reg,dut.p2r_reg,dut.p3r_reg,
          dut.ny0_re,dut.ny1_re,dut.ny2_re,dut.ny3_re);
     if (dut.st==2'd2 && dut.bc==6'd16 && dut.slot==3'd0) begin $display("== after stage0 =="); dumpmem; end
     if (dut.st==2'd2 && dut.bc==6'd32 && dut.slot==3'd0) begin $display("== after stage1 =="); dumpmem; end
     #4; clk=1; #5;
   end
   $finish;
 end
endmodule
