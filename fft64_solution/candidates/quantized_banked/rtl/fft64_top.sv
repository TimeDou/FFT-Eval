// Original FFT64 implementation; no ALS.
module frot(input signed[21:0] dr,di,input signed[10:0] wr,wi,input[4:0] index,output signed[20:0] vr,vi);
function automatic signed [21:0] preq;input signed [21:0] x;reg signed [21:0] e;begin e=x;preq=e<<<0;end endfunction
function automatic signed [20:0] postq;input signed [33:0] x;reg signed [34:0] b;begin b=x>>>9;postq=b+((x[8:0]>9'd256) || ((x[8:0]==9'd256) && b[0]));end endfunction
wire signed[21:0] ar=preq(dr),ai=preq(di);wire signed[32:0] p0=ar*wr,p1=ai*wi,p2=ar*wi,p3=ai*wr;
wire signed[33:0] rr=$signed({p0[32],p0})-$signed({p1[32],p1}),ii=$signed({p2[32],p2})+$signed({p3[32],p3});
assign vr=index==0?dr:index==16?di:postq(rr);assign vi=index==0?di:index==16?-dr:postq(ii);endmodule
module parity_mem(input clk,rst,input[5:0] ra,rb,wa,wb,input ena,enb,input signed[20:0] dra,dia,drb,dib,output signed[20:0] ar,ai,br,bi);
reg signed[20:0] r0[0:31],i0[0:31],r1[0:31],i1[0:31];integer k;
wire ba=^ra,bwa=^wa,bwb=^wb;
wire[4:0] a0=ba?rb[5:1]:ra[5:1],a1=ba?ra[5:1]:rb[5:1];
wire signed[20:0] qr0=r0[a0],qi0=i0[a0],qr1=r1[a1],qi1=i1[a1];
assign ar=ba?qr1:qr0;assign ai=ba?qi1:qi0;assign br=ba?qr0:qr1;assign bi=ba?qi0:qi1;
wire e0=(ena&&!bwa)||(enb&&!bwb),e1=(ena&&bwa)||(enb&&bwb);
wire takea0=ena&&!bwa,takea1=ena&&bwa;
wire[4:0] w0=takea0?wa[5:1]:wb[5:1],w1=takea1?wa[5:1]:wb[5:1];
wire signed[20:0] wr0=takea0?dra:drb,wi0=takea0?dia:dib,wr1=takea1?dra:drb,wi1=takea1?dia:dib;
always @(posedge clk)if(rst)begin for(k=0;k<32;k=k+1)begin r0[k]<=0;i0[k]<=0;r1[k]<=0;i1[k]<=0;end end else begin
if(e0)begin r0[w0]<=wr0;i0[w0]<=wi0;end if(e1)begin r1[w1]<=wr1;i1[w1]<=wi1;end end endmodule
module fft64_top(input wire clk,input wire rst,input wire in_valid,input wire frame_start,input wire signed [15:0] in_re,in_im,output reg out_valid,output reg out_start,output reg signed [23:0] out_re,out_im);localparam W=21;reg[2:0] state,stage;reg[5:0] ic,oc;reg[4:0] bidx;reg[5:0] a,b;reg[4:0] tidx;
function automatic signed [20:0] iq;input signed [15:0] x;reg signed [21:0] b;begin b=x>>>1;iq=b+((x[0:0]>1'd1) || ((x[0:0]==1'd1) && b[0]));end endfunction
function automatic signed [10:0] cr;input [4:0] j;begin case(j)
5'd0:cr=11'sd512;
5'd1:cr=11'sd510;
5'd2:cr=11'sd502;
5'd3:cr=11'sd490;
5'd4:cr=11'sd473;
5'd5:cr=11'sd452;
5'd6:cr=11'sd426;
5'd7:cr=11'sd396;
5'd8:cr=11'sd362;
5'd9:cr=11'sd325;
5'd10:cr=11'sd284;
5'd11:cr=11'sd241;
5'd12:cr=11'sd196;
5'd13:cr=11'sd149;
5'd14:cr=11'sd100;
5'd15:cr=11'sd50;
5'd16:cr=11'sd0;
5'd17:cr=-11'sd50;
5'd18:cr=-11'sd100;
5'd19:cr=-11'sd149;
5'd20:cr=-11'sd196;
5'd21:cr=-11'sd241;
5'd22:cr=-11'sd284;
5'd23:cr=-11'sd325;
5'd24:cr=-11'sd362;
5'd25:cr=-11'sd396;
5'd26:cr=-11'sd426;
5'd27:cr=-11'sd452;
5'd28:cr=-11'sd473;
5'd29:cr=-11'sd490;
5'd30:cr=-11'sd502;
5'd31:cr=-11'sd510;
default:cr=0;endcase end endfunction
function automatic signed [10:0] ci;input [4:0] j;begin case(j)
5'd0:ci=11'sd0;
5'd1:ci=-11'sd50;
5'd2:ci=-11'sd100;
5'd3:ci=-11'sd149;
5'd4:ci=-11'sd196;
5'd5:ci=-11'sd241;
5'd6:ci=-11'sd284;
5'd7:ci=-11'sd325;
5'd8:ci=-11'sd362;
5'd9:ci=-11'sd396;
5'd10:ci=-11'sd426;
5'd11:ci=-11'sd452;
5'd12:ci=-11'sd473;
5'd13:ci=-11'sd490;
5'd14:ci=-11'sd502;
5'd15:ci=-11'sd510;
5'd16:ci=-11'sd512;
5'd17:ci=-11'sd510;
5'd18:ci=-11'sd502;
5'd19:ci=-11'sd490;
5'd20:ci=-11'sd473;
5'd21:ci=-11'sd452;
5'd22:ci=-11'sd426;
5'd23:ci=-11'sd396;
5'd24:ci=-11'sd362;
5'd25:ci=-11'sd325;
5'd26:ci=-11'sd284;
5'd27:ci=-11'sd241;
5'd28:ci=-11'sd196;
5'd29:ci=-11'sd149;
5'd30:ci=-11'sd100;
5'd31:ci=-11'sd50;
default:ci=0;endcase end endfunction
always @* begin a=0;b=0;tidx=0;case(stage)
3'd0:begin a=((bidx>>5)<<6)|(bidx&5'd31);b=a+6'd32;tidx=(bidx&5'd31)<<0;end
3'd1:begin a=((bidx>>4)<<5)|(bidx&5'd15);b=a+6'd16;tidx=(bidx&5'd15)<<1;end
3'd2:begin a=((bidx>>3)<<4)|(bidx&5'd7);b=a+6'd8;tidx=(bidx&5'd7)<<2;end
3'd3:begin a=((bidx>>2)<<3)|(bidx&5'd3);b=a+6'd4;tidx=(bidx&5'd3)<<3;end
3'd4:begin a=((bidx>>1)<<2)|(bidx&5'd1);b=a+6'd2;tidx=(bidx&5'd1)<<4;end
3'd5:begin a=((bidx>>0)<<1)|(bidx&5'd0);b=a+6'd1;tidx=(bidx&5'd0)<<5;end
default:begin a=0;b=0;tidx=0;end endcase end
wire[5:0] oaddr={oc[0],oc[1],oc[2],oc[3],oc[4],oc[5]},ra=state==3?oaddr:a;
wire signed[W-1:0] ar,ai,br,bi;
wire signed[W-1:0] sr=ar+br,si=ai+bi;
wire signed[W-1:0] vr,vi;
wire signed[21:0] dr=$signed(ar)-$signed(br),di=$signed(ai)-$signed(bi);
frot rot(dr,di,cr(tidx),ci(tidx),tidx,vr,vi);
wire load=(state==0&&in_valid&&frame_start)||(state==1&&in_valid),compute=state==2;
wire[5:0] wa=load?(state==0?6'd0:ic):a;
wire signed[W-1:0] wr=load?iq(in_re):sr,wi=load?iq(in_im):si;
parity_mem mem(clk,rst,ra,b,wa,b,load||compute,compute,wr,wi,vr,vi,ar,ai,br,bi);
always @(posedge clk)begin if(rst)begin state<=0;stage<=0;ic<=0;oc<=0;bidx<=0;out_valid<=0;out_start<=0;out_re<=0;out_im<=0;end else begin
out_valid<=0;out_start<=0;case(state)
0:if(in_valid&&frame_start)begin ic<=1;state<=1;end
1:if(in_valid)begin if(ic==63)begin state<=2;stage<=0;bidx<=0;end else ic<=ic+1;end
2:begin if(bidx==31)begin bidx<=0;if(stage==5)begin state<=3;oc<=0;end else stage<=stage+1;end else bidx<=bidx+1;end
3:begin out_valid<=1;out_start<=oc==0;
out_re<=$signed({{3{ar[20]}},ar})<<<1;out_im<=$signed({{3{ai[20]}},ai})<<<1;
if(oc==63)state<=0;else oc<=oc+1;end
default:state<=0;endcase end end endmodule
