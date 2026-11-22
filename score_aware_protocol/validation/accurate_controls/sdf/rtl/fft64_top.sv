// Original FFT64 implementation; no ALS.
module rot0(input signed[16:0] dr,di,input signed[17:0] wr,wi,input[4:0] index,output signed[16:0] vr,vi);
function automatic signed [16:0] preq;input signed [16:0] x;reg signed [16:0] e;begin e=x;preq=e<<<0;end endfunction
function automatic signed [16:0] postq;input signed [35:0] x;reg signed [36:0] b;begin b=x>>>16;postq=b+((x[15:0]>16'd32768) || ((x[15:0]==16'd32768) && b[0]));end endfunction
wire signed[16:0] ar=preq(dr),ai=preq(di);wire signed[34:0] p0=ar*wr,p1=ai*wi,p2=ar*wi,p3=ai*wr;
wire signed[35:0] rr=$signed({p0[34],p0})-$signed({p1[34],p1}),ii=$signed({p2[34],p2})+$signed({p3[34],p3});
assign vr=index==0?dr:index==16?di:postq(rr);assign vi=index==0?di:index==16?-dr:postq(ii);endmodule
module stage0(input clk,rst,input[15:0] tick,input signed[15:0] ir,ii,output reg signed[16:0] yr,yi);
function automatic signed [15:0] iq;input signed [15:0] x;reg signed [15:0] e;begin e=x;iq=e<<<0;end endfunction
wire[5:0] phase=tick-16'd0;wire bf=phase[5];
wire signed[15:0] xr=iq(ir),xi=iq(ii);reg signed[16:0] br[0:31],bi[0:31];integer n;
wire signed[16:0] ar=br[0],ai=bi[0],sr=ar+xr,si=ai+xi,dr=ar-xr,di=ai-xi;wire signed[16:0] vr,vi;
function automatic signed [17:0] cr;input [4:0] j;begin case(j)
5'd0:cr=18'sd65536;
5'd1:cr=18'sd65220;
5'd2:cr=18'sd64277;
5'd3:cr=18'sd62714;
5'd4:cr=18'sd60547;
5'd5:cr=18'sd57798;
5'd6:cr=18'sd54491;
5'd7:cr=18'sd50660;
5'd8:cr=18'sd46341;
5'd9:cr=18'sd41576;
5'd10:cr=18'sd36410;
5'd11:cr=18'sd30893;
5'd12:cr=18'sd25080;
5'd13:cr=18'sd19024;
5'd14:cr=18'sd12785;
5'd15:cr=18'sd6424;
5'd16:cr=18'sd0;
5'd17:cr=-18'sd6424;
5'd18:cr=-18'sd12785;
5'd19:cr=-18'sd19024;
5'd20:cr=-18'sd25080;
5'd21:cr=-18'sd30893;
5'd22:cr=-18'sd36410;
5'd23:cr=-18'sd41576;
5'd24:cr=-18'sd46341;
5'd25:cr=-18'sd50660;
5'd26:cr=-18'sd54491;
5'd27:cr=-18'sd57798;
5'd28:cr=-18'sd60547;
5'd29:cr=-18'sd62714;
5'd30:cr=-18'sd64277;
5'd31:cr=-18'sd65220;
default:cr=0;endcase end endfunction
function automatic signed [17:0] ci;input [4:0] j;begin case(j)
5'd0:ci=18'sd0;
5'd1:ci=-18'sd6424;
5'd2:ci=-18'sd12785;
5'd3:ci=-18'sd19024;
5'd4:ci=-18'sd25080;
5'd5:ci=-18'sd30893;
5'd6:ci=-18'sd36410;
5'd7:ci=-18'sd41576;
5'd8:ci=-18'sd46341;
5'd9:ci=-18'sd50660;
5'd10:ci=-18'sd54491;
5'd11:ci=-18'sd57798;
5'd12:ci=-18'sd60547;
5'd13:ci=-18'sd62714;
5'd14:ci=-18'sd64277;
5'd15:ci=-18'sd65220;
5'd16:ci=-18'sd65536;
5'd17:ci=-18'sd65220;
5'd18:ci=-18'sd64277;
5'd19:ci=-18'sd62714;
5'd20:ci=-18'sd60547;
5'd21:ci=-18'sd57798;
5'd22:ci=-18'sd54491;
5'd23:ci=-18'sd50660;
5'd24:ci=-18'sd46341;
5'd25:ci=-18'sd41576;
5'd26:ci=-18'sd36410;
5'd27:ci=-18'sd30893;
5'd28:ci=-18'sd25080;
5'd29:ci=-18'sd19024;
5'd30:ci=-18'sd12785;
5'd31:ci=-18'sd6424;
default:ci=0;endcase end endfunction
wire[4:0] j=phase[4:0];wire[4:0] idx=j;rot0 rot(dr,di,cr(j),ci(j),idx,vr,vi);
always @(posedge clk)begin if(rst)begin yr<=0;yi<=0;for(n=0;n<32;n=n+1)begin br[n]<=0;bi[n]<=0;end end else begin
for(n=0;n<31;n=n+1)begin br[n]<=br[n+1];bi[n]<=bi[n+1];end
br[31]<=bf?vr:$signed(xr);bi[31]<=bf?vi:$signed(xi);yr<=bf?sr:br[0];yi<=bf?si:bi[0];end end endmodule
module rot1(input signed[17:0] dr,di,input signed[17:0] wr,wi,input[4:0] index,output signed[17:0] vr,vi);
function automatic signed [17:0] preq;input signed [17:0] x;reg signed [17:0] e;begin e=x;preq=e<<<0;end endfunction
function automatic signed [17:0] postq;input signed [36:0] x;reg signed [37:0] b;begin b=x>>>16;postq=b+((x[15:0]>16'd32768) || ((x[15:0]==16'd32768) && b[0]));end endfunction
wire signed[17:0] ar=preq(dr),ai=preq(di);wire signed[35:0] p0=ar*wr,p1=ai*wi,p2=ar*wi,p3=ai*wr;
wire signed[36:0] rr=$signed({p0[35],p0})-$signed({p1[35],p1}),ii=$signed({p2[35],p2})+$signed({p3[35],p3});
assign vr=index==0?dr:index==16?di:postq(rr);assign vi=index==0?di:index==16?-dr:postq(ii);endmodule
module stage1(input clk,rst,input[15:0] tick,input signed[16:0] ir,ii,output reg signed[17:0] yr,yi);
function automatic signed [16:0] iq;input signed [16:0] x;reg signed [16:0] e;begin e=x;iq=e<<<0;end endfunction
wire[4:0] phase=tick-16'd33;wire bf=phase[4];
wire signed[16:0] xr=iq(ir),xi=iq(ii);reg signed[17:0] br[0:15],bi[0:15];integer n;
wire signed[17:0] ar=br[0],ai=bi[0],sr=ar+xr,si=ai+xi,dr=ar-xr,di=ai-xi;wire signed[17:0] vr,vi;
function automatic signed [17:0] cr;input [3:0] j;begin case(j)
4'd0:cr=18'sd65536;
4'd1:cr=18'sd64277;
4'd2:cr=18'sd60547;
4'd3:cr=18'sd54491;
4'd4:cr=18'sd46341;
4'd5:cr=18'sd36410;
4'd6:cr=18'sd25080;
4'd7:cr=18'sd12785;
4'd8:cr=18'sd0;
4'd9:cr=-18'sd12785;
4'd10:cr=-18'sd25080;
4'd11:cr=-18'sd36410;
4'd12:cr=-18'sd46341;
4'd13:cr=-18'sd54491;
4'd14:cr=-18'sd60547;
4'd15:cr=-18'sd64277;
default:cr=0;endcase end endfunction
function automatic signed [17:0] ci;input [3:0] j;begin case(j)
4'd0:ci=18'sd0;
4'd1:ci=-18'sd12785;
4'd2:ci=-18'sd25080;
4'd3:ci=-18'sd36410;
4'd4:ci=-18'sd46341;
4'd5:ci=-18'sd54491;
4'd6:ci=-18'sd60547;
4'd7:ci=-18'sd64277;
4'd8:ci=-18'sd65536;
4'd9:ci=-18'sd64277;
4'd10:ci=-18'sd60547;
4'd11:ci=-18'sd54491;
4'd12:ci=-18'sd46341;
4'd13:ci=-18'sd36410;
4'd14:ci=-18'sd25080;
4'd15:ci=-18'sd12785;
default:ci=0;endcase end endfunction
wire[3:0] j=phase[3:0];wire[4:0] idx={j,1'b0};rot1 rot(dr,di,cr(j),ci(j),idx,vr,vi);
always @(posedge clk)begin if(rst)begin yr<=0;yi<=0;for(n=0;n<16;n=n+1)begin br[n]<=0;bi[n]<=0;end end else begin
for(n=0;n<15;n=n+1)begin br[n]<=br[n+1];bi[n]<=bi[n+1];end
br[15]<=bf?vr:$signed(xr);bi[15]<=bf?vi:$signed(xi);yr<=bf?sr:br[0];yi<=bf?si:bi[0];end end endmodule
module rot2(input signed[18:0] dr,di,input signed[17:0] wr,wi,input[4:0] index,output signed[18:0] vr,vi);
function automatic signed [18:0] preq;input signed [18:0] x;reg signed [18:0] e;begin e=x;preq=e<<<0;end endfunction
function automatic signed [18:0] postq;input signed [37:0] x;reg signed [38:0] b;begin b=x>>>16;postq=b+((x[15:0]>16'd32768) || ((x[15:0]==16'd32768) && b[0]));end endfunction
wire signed[18:0] ar=preq(dr),ai=preq(di);wire signed[36:0] p0=ar*wr,p1=ai*wi,p2=ar*wi,p3=ai*wr;
wire signed[37:0] rr=$signed({p0[36],p0})-$signed({p1[36],p1}),ii=$signed({p2[36],p2})+$signed({p3[36],p3});
assign vr=index==0?dr:index==16?di:postq(rr);assign vi=index==0?di:index==16?-dr:postq(ii);endmodule
module stage2(input clk,rst,input[15:0] tick,input signed[17:0] ir,ii,output reg signed[18:0] yr,yi);
function automatic signed [17:0] iq;input signed [17:0] x;reg signed [17:0] e;begin e=x;iq=e<<<0;end endfunction
wire[3:0] phase=tick-16'd50;wire bf=phase[3];
wire signed[17:0] xr=iq(ir),xi=iq(ii);reg signed[18:0] br[0:7],bi[0:7];integer n;
wire signed[18:0] ar=br[0],ai=bi[0],sr=ar+xr,si=ai+xi,dr=ar-xr,di=ai-xi;wire signed[18:0] vr,vi;
function automatic signed [17:0] cr;input [2:0] j;begin case(j)
3'd0:cr=18'sd65536;
3'd1:cr=18'sd60547;
3'd2:cr=18'sd46341;
3'd3:cr=18'sd25080;
3'd4:cr=18'sd0;
3'd5:cr=-18'sd25080;
3'd6:cr=-18'sd46341;
3'd7:cr=-18'sd60547;
default:cr=0;endcase end endfunction
function automatic signed [17:0] ci;input [2:0] j;begin case(j)
3'd0:ci=18'sd0;
3'd1:ci=-18'sd25080;
3'd2:ci=-18'sd46341;
3'd3:ci=-18'sd60547;
3'd4:ci=-18'sd65536;
3'd5:ci=-18'sd60547;
3'd6:ci=-18'sd46341;
3'd7:ci=-18'sd25080;
default:ci=0;endcase end endfunction
wire[2:0] j=phase[2:0];wire[4:0] idx={j,2'b0};rot2 rot(dr,di,cr(j),ci(j),idx,vr,vi);
always @(posedge clk)begin if(rst)begin yr<=0;yi<=0;for(n=0;n<8;n=n+1)begin br[n]<=0;bi[n]<=0;end end else begin
for(n=0;n<7;n=n+1)begin br[n]<=br[n+1];bi[n]<=bi[n+1];end
br[7]<=bf?vr:$signed(xr);bi[7]<=bf?vi:$signed(xi);yr<=bf?sr:br[0];yi<=bf?si:bi[0];end end endmodule
module rot3(input signed[19:0] dr,di,input signed[17:0] wr,wi,input[4:0] index,output signed[19:0] vr,vi);
function automatic signed [19:0] preq;input signed [19:0] x;reg signed [19:0] e;begin e=x;preq=e<<<0;end endfunction
function automatic signed [19:0] postq;input signed [38:0] x;reg signed [39:0] b;begin b=x>>>16;postq=b+((x[15:0]>16'd32768) || ((x[15:0]==16'd32768) && b[0]));end endfunction
wire signed[19:0] ar=preq(dr),ai=preq(di);wire signed[37:0] p0=ar*wr,p1=ai*wi,p2=ar*wi,p3=ai*wr;
wire signed[38:0] rr=$signed({p0[37],p0})-$signed({p1[37],p1}),ii=$signed({p2[37],p2})+$signed({p3[37],p3});
assign vr=index==0?dr:index==16?di:postq(rr);assign vi=index==0?di:index==16?-dr:postq(ii);endmodule
module stage3(input clk,rst,input[15:0] tick,input signed[18:0] ir,ii,output reg signed[19:0] yr,yi);
function automatic signed [18:0] iq;input signed [18:0] x;reg signed [18:0] e;begin e=x;iq=e<<<0;end endfunction
wire[2:0] phase=tick-16'd59;wire bf=phase[2];
wire signed[18:0] xr=iq(ir),xi=iq(ii);reg signed[19:0] br[0:3],bi[0:3];integer n;
wire signed[19:0] ar=br[0],ai=bi[0],sr=ar+xr,si=ai+xi,dr=ar-xr,di=ai-xi;wire signed[19:0] vr,vi;
function automatic signed [17:0] cr;input [1:0] j;begin case(j)
2'd0:cr=18'sd65536;
2'd1:cr=18'sd46341;
2'd2:cr=18'sd0;
2'd3:cr=-18'sd46341;
default:cr=0;endcase end endfunction
function automatic signed [17:0] ci;input [1:0] j;begin case(j)
2'd0:ci=18'sd0;
2'd1:ci=-18'sd46341;
2'd2:ci=-18'sd65536;
2'd3:ci=-18'sd46341;
default:ci=0;endcase end endfunction
wire[1:0] j=phase[1:0];wire[4:0] idx={j,3'b0};rot3 rot(dr,di,cr(j),ci(j),idx,vr,vi);
always @(posedge clk)begin if(rst)begin yr<=0;yi<=0;for(n=0;n<4;n=n+1)begin br[n]<=0;bi[n]<=0;end end else begin
for(n=0;n<3;n=n+1)begin br[n]<=br[n+1];bi[n]<=bi[n+1];end
br[3]<=bf?vr:$signed(xr);bi[3]<=bf?vi:$signed(xi);yr<=bf?sr:br[0];yi<=bf?si:bi[0];end end endmodule
module stage4(input clk,rst,input[15:0] tick,input signed[19:0] ir,ii,output reg signed[20:0] yr,yi);
function automatic signed [19:0] iq;input signed [19:0] x;reg signed [19:0] e;begin e=x;iq=e<<<0;end endfunction
wire[1:0] phase=tick-16'd64;wire bf=phase[1];
wire signed[19:0] xr=iq(ir),xi=iq(ii);reg signed[20:0] br[0:1],bi[0:1];integer n;
wire signed[20:0] ar=br[0],ai=bi[0],sr=ar+xr,si=ai+xi,dr=ar-xr,di=ai-xi;wire signed[20:0] vr,vi;
assign vr=phase[0]?di:dr;assign vi=phase[0]?-dr:di;
always @(posedge clk)begin if(rst)begin yr<=0;yi<=0;for(n=0;n<2;n=n+1)begin br[n]<=0;bi[n]<=0;end end else begin
for(n=0;n<1;n=n+1)begin br[n]<=br[n+1];bi[n]<=bi[n+1];end
br[1]<=bf?vr:$signed(xr);bi[1]<=bf?vi:$signed(xi);yr<=bf?sr:br[0];yi<=bf?si:bi[0];end end endmodule
module stage5(input clk,rst,input[15:0] tick,input signed[20:0] ir,ii,output reg signed[21:0] yr,yi);
function automatic signed [20:0] iq;input signed [20:0] x;reg signed [20:0] e;begin e=x;iq=e<<<0;end endfunction
wire[0:0] phase=tick-16'd67;wire bf=phase[0];
wire signed[20:0] xr=iq(ir),xi=iq(ii);reg signed[21:0] br[0:0],bi[0:0];integer n;
wire signed[21:0] ar=br[0],ai=bi[0],sr=ar+xr,si=ai+xi,dr=ar-xr,di=ai-xi;wire signed[21:0] vr,vi;
assign vr=dr;assign vi=di;
always @(posedge clk)begin if(rst)begin yr<=0;yi<=0;for(n=0;n<1;n=n+1)begin br[n]<=0;bi[n]<=0;end end else begin
br[0]<=bf?vr:$signed(xr);bi[0]<=bf?vi:$signed(xi);yr<=bf?sr:br[0];yi<=bf?si:bi[0];end end endmodule
module fft64_top(input wire clk,input wire rst,input wire in_valid,input wire frame_start,input wire signed [15:0] in_re,in_im,output reg out_valid,output reg out_start,output reg signed [23:0] out_re,out_im);reg[15:0] epoch;reg started;wire[15:0] tick=frame_start?16'd0:epoch;integer k;
always @(posedge clk)if(rst)begin epoch<=0;started<=0;end else if(frame_start)begin epoch<=1;started<=1;end else if(started)epoch <= (epoch < 16'd256) ? (epoch + 16'd1) : epoch;
wire signed[15:0] r0=in_valid?in_re:16'sd0,i0=in_valid?in_im:16'sd0;
wire signed[16:0] r1,i1;stage0 u0(clk,rst,tick,r0,i0,r1,i1);
wire signed[17:0] r2,i2;stage1 u1(clk,rst,tick,r1,i1,r2,i2);
wire signed[18:0] r3,i3;stage2 u2(clk,rst,tick,r2,i2,r3,i3);
wire signed[19:0] r4,i4;stage3 u3(clk,rst,tick,r3,i3,r4,i4);
wire signed[20:0] r5,i5;stage4 u4(clk,rst,tick,r4,i4,r5,i5);
wire signed[21:0] r6,i6;stage5 u5(clk,rst,tick,r5,i5,r6,i6);
reg signed[21:0] rr[0:63],ri[0:63];wire[5:0] ci=tick-16'd69,oi=tick-16'd133;wire[5:0] rev={ci[0],ci[1],ci[2],ci[3],ci[4],ci[5]};
always @(posedge clk)begin if(rst)begin out_valid<=0;out_start<=0;out_re<=0;out_im<=0;for(k=0;k<64;k=k+1)begin rr[k]<=0;ri[k]<=0;end end else begin out_valid<=0;out_start<=0;if(started && tick>=69 && tick<133)begin rr[rev]<=r6;ri[rev]<=i6;end
if(started && tick>=133 && tick<197)begin out_valid<=1;out_start<=tick==133;out_re<=$signed({{2{rr[oi][21]}},rr[oi]})<<<0;out_im<=$signed({{2{ri[oi][21]}},ri[oi]})<<<0;end end end endmodule
