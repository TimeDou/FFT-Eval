// Original FFT64 implementation; no ALS.
module frot(input signed[22:0] dr,di,input signed[17:0] wr,wi,input[4:0] index,output signed[21:0] vr,vi);
function automatic signed [22:0] preq;input signed [22:0] x;reg signed [22:0] e;begin e=x;preq=e<<<0;end endfunction
function automatic signed [21:0] postq;input signed [41:0] x;reg signed [42:0] b;begin b=x>>>16;postq=b+((x[15:0]>16'd32768) || ((x[15:0]==16'd32768) && b[0]));end endfunction
wire signed[22:0] ar=preq(dr),ai=preq(di);wire signed[40:0] p0=ar*wr,p1=ai*wi,p2=ar*wi,p3=ai*wr;
wire signed[41:0] rr=$signed({p0[40],p0})-$signed({p1[40],p1}),ii=$signed({p2[40],p2})+$signed({p3[40],p3});
assign vr=index==0?dr:index==16?di:postq(rr);assign vi=index==0?di:index==16?-dr:postq(ii);endmodule
module fft64_top(input wire clk,input wire rst,input wire in_valid,input wire frame_start,input wire signed [15:0] in_re,in_im,output reg out_valid,output reg out_start,output reg signed [23:0] out_re,out_im);
localparam W=22;reg signed[W-1:0] mr[0:63],mi[0:63];reg[2:0] state,stage;reg[5:0] ic,oc;reg[4:0] bidx;reg[5:0] a,b;reg[4:0] tidx;integer n;
function automatic signed [21:0] iq;input signed [15:0] x;reg signed [21:0] e;begin e=x;iq=e<<<0;end endfunction
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
always @* begin a=0;b=0;tidx=0;case(stage)
3'd0:begin a=((bidx>>5)<<6) | (bidx & 5'd31);b=a+6'd32;tidx=(bidx & 5'd31)<<0;end
3'd1:begin a=((bidx>>4)<<5) | (bidx & 5'd15);b=a+6'd16;tidx=(bidx & 5'd15)<<1;end
3'd2:begin a=((bidx>>3)<<4) | (bidx & 5'd7);b=a+6'd8;tidx=(bidx & 5'd7)<<2;end
3'd3:begin a=((bidx>>2)<<3) | (bidx & 5'd3);b=a+6'd4;tidx=(bidx & 5'd3)<<3;end
3'd4:begin a=((bidx>>1)<<2) | (bidx & 5'd1);b=a+6'd2;tidx=(bidx & 5'd1)<<4;end
3'd5:begin a=((bidx>>0)<<1) | (bidx & 5'd0);b=a+6'd1;tidx=(bidx & 5'd0)<<5;end
default:begin a=0;b=0;tidx=0;end endcase end
wire signed[22:0] dr=$signed(mr[a])-$signed(mr[b]),di=$signed(mi[a])-$signed(mi[b]);wire signed[W-1:0] sr=mr[a]+mr[b],si=mi[a]+mi[b];wire signed[W-1:0] vr,vi;wire[5:0] oaddr={oc[0],oc[1],oc[2],oc[3],oc[4],oc[5]};
reg pending;reg[5:0] pa,pb;reg[4:0] pi;reg signed[W-1:0] psr,psi;reg signed[22:0] pdr,pdi;reg signed[17:0] pwr,pwi;frot rot(pdr,pdi,pwr,pwi,pi,vr,vi);
always @(posedge clk)begin if(rst)begin state<=0;stage<=0;ic<=0;oc<=0;bidx<=0;out_valid<=0;out_start<=0;out_re<=0;out_im<=0;for(n=0;n<64;n=n+1)begin mr[n]<=0;mi[n]<=0;end
pending<=0;pa<=0;pb<=0;pi<=0;psr<=0;psi<=0;pdr<=0;pdi<=0;pwr<=0;pwi<=0;
end else begin out_valid<=0;out_start<=0;
pending<=0;if(pending)begin mr[pa]<=psr;mi[pa]<=psi;mr[pb]<=vr;mi[pb]<=vi;end
case(state)
0:if(in_valid && frame_start)begin mr[0]<=iq(in_re);mi[0]<=iq(in_im);ic<=1;state<=1;end
1:if(in_valid)begin mr[ic]<=iq(in_re);mi[ic]<=iq(in_im);if(ic==63)begin state<=2;stage<=0;bidx<=0;end else ic<=ic+1;end
2:begin
pending<=1;pa<=a;pb<=b;pi<=tidx;psr<=sr;psi<=si;pdr<=dr;pdi<=di;pwr<=cr(tidx);pwi<=ci(tidx);if(bidx==31)begin bidx<=0;state<=4;end else bidx<=bidx+1;
end
4:begin if(stage==5)begin state<=3;oc<=0;end else begin stage<=stage+1;state<=2;end end
3:begin out_valid<=1;out_start<=oc==0;out_re<=$signed({{2{mr[oaddr][21]}},mr[oaddr]})<<<0;out_im<=$signed({{2{mi[oaddr][21]}},mi[oaddr]})<<<0;if(oc==63)state<=0;else oc<=oc+1;end
default:state<=0;endcase end end endmodule
