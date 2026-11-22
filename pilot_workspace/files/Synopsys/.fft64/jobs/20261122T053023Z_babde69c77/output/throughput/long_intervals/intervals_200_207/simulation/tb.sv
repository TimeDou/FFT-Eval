`timescale 1ns/1ps
module tb;
 reg clk=0,rst=1,in_valid=0,frame_start=0;
 reg signed[15:0] in_re=0,in_im=0;
 wire out_valid,out_start;wire signed[23:0] out_re,out_im;
 fft64_top dut(.clk(clk),.rst(rst),.in_valid(in_valid),.frame_start(frame_start),.in_re(in_re),.in_im(in_im),.out_valid(out_valid),.out_start(out_start),.out_re(out_re),.out_im(out_im));
 integer fi,fo,rc,c,rs,iv,ifs,ir,ii;reg[2047:0] vp,op;
 initial begin
 if(!$value$plusargs("VECTORS=%s",vp))$fatal(1,"no vector path");
 if(!$value$plusargs("OUTPUT=%s",op))$fatal(1,"no output path");
 fi=$fopen(vp,"r");fo=$fopen(op,"w");if(fi==0||fo==0)$fatal(1,"file open");c=0;
 while(!$feof(fi))begin
 rc=$fscanf(fi,"%d %d %d %d %d\n",rs,iv,ifs,ir,ii);
 if(rc==5)begin clk=0;rst=rs;in_valid=iv;frame_start=ifs;in_re=ir;in_im=ii;
 #5;clk=1;#1;
 if(out_valid===1'b1)
 $fdisplay(fo,"%0d %0d %0d %0d %0d",c,1,(out_start===1'b0?0:out_start===1'b1?1:2),
 ((^out_re===1'bx)?32'sd1073741824:$signed(out_re)),((^out_im===1'bx)?32'sd1073741824:$signed(out_im)));
 else $fdisplay(fo,"%0d %0d %0d 0 0",c,(out_valid===1'b0?0:2),(out_start===1'b0?0:out_start===1'b1?1:2));
 #4;clk=0;c=c+1;
 end end
 $fclose(fi);$fclose(fo);$finish;end
endmodule
