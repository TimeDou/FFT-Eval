// Generated complete radix-2 DIF. Parity banking allows conflict-free butterflies.
module fft64_top (
 input wire clk,rst,in_valid,frame_start,
 input wire signed [15:0] in_re,in_im,
 output reg out_valid,out_start,
 output reg signed [23:0] out_re,out_im
);
localparam W=21, DROP=1, TF=11;
localparam IDLE=0,LOAD=1,CALC=2,SEND=3; reg[1:0] state; reg[5:0] icnt,ocnt; reg[3:0] bc; reg[2:0] stage;
function [1:0] bank; input[5:0] x; begin bank={x[5]^x[3]^x[1], x[4]^x[2]^x[0]}; end endfunction
reg signed[W-1:0] re0[0:15],im0[0:15];
reg signed[W-1:0] re1[0:15],im1[0:15];
reg signed[W-1:0] re2[0:15],im2[0:15];
reg signed[W-1:0] re3[0:15],im3[0:15];
reg[5:0] a0; always @* begin case(stage)
3'd0: a0={1'b0,bc[3],bc[2],bc[1],bc[0],1'b0};
3'd1: a0={bc[3],1'b0,bc[2],bc[1],1'b0,bc[0]};
3'd2: a0={1'b0,bc[3],bc[2],1'b0,bc[1],bc[0]};
3'd3: a0={bc[3],1'b0,1'b0,bc[2],bc[1],bc[0]};
3'd4: a0={1'b0,1'b0,bc[3],bc[2],bc[1],bc[0]};
3'd5: a0={1'b0,1'b0,bc[3],bc[2],bc[1],bc[0]};
default:a0=0; endcase end
wire[5:0] b0=a0^(6'd1<<stage);
wire[5:0] a1=a0^(stage[0]?6'd16:6'd32), b1=a1^(6'd1<<stage);
wire[1:0] bank_a0=bank(a0);
wire[1:0] bank_b0=bank(b0);
wire[1:0] bank_a1=bank(a1);
wire[1:0] bank_b1=bank(b1);
wire[3:0] ra0=bank_a0==0?a0[3:0]:bank_b0==0?b0[3:0]:bank_a1==0?a1[3:0]:b1[3:0];
wire[3:0] ra1=bank_a0==1?a0[3:0]:bank_b0==1?b0[3:0]:bank_a1==1?a1[3:0]:b1[3:0];
wire[3:0] ra2=bank_a0==2?a0[3:0]:bank_b0==2?b0[3:0]:bank_a1==2?a1[3:0]:b1[3:0];
wire[3:0] ra3=bank_a0==3?a0[3:0]:bank_b0==3?b0[3:0]:bank_a1==3?a1[3:0]:b1[3:0];
wire signed[W-1:0] re_a0=bank_a0==0?re0[ra0]:bank_a0==1?re1[ra1]:bank_a0==2?re2[ra2]:re3[ra3];
wire signed[W-1:0] im_a0=bank_a0==0?im0[ra0]:bank_a0==1?im1[ra1]:bank_a0==2?im2[ra2]:im3[ra3];
wire signed[W-1:0] re_b0=bank_b0==0?re0[ra0]:bank_b0==1?re1[ra1]:bank_b0==2?re2[ra2]:re3[ra3];
wire signed[W-1:0] im_b0=bank_b0==0?im0[ra0]:bank_b0==1?im1[ra1]:bank_b0==2?im2[ra2]:im3[ra3];
wire signed[W-1:0] re_a1=bank_a1==0?re0[ra0]:bank_a1==1?re1[ra1]:bank_a1==2?re2[ra2]:re3[ra3];
wire signed[W-1:0] im_a1=bank_a1==0?im0[ra0]:bank_a1==1?im1[ra1]:bank_a1==2?im2[ra2]:im3[ra3];
wire signed[W-1:0] re_b1=bank_b1==0?re0[ra0]:bank_b1==1?re1[ra1]:bank_b1==2?re2[ra2]:re3[ra3];
wire signed[W-1:0] im_b1=bank_b1==0?im0[ra0]:bank_b1==1?im1[ra1]:bank_b1==2?im2[ra2]:im3[ra3];
wire[4:0] exponent=a0[4:0]<<(5-stage); reg signed[TF+1:0] wr,wi;
always @* begin wr=0;wi=0; case(exponent)
5'd0:begin wr=13'sd2048;wi=13'sd0;end
5'd1:begin wr=13'sd2038;wi=-13'sd201;end
5'd2:begin wr=13'sd2009;wi=-13'sd400;end
5'd3:begin wr=13'sd1960;wi=-13'sd595;end
5'd4:begin wr=13'sd1892;wi=-13'sd784;end
5'd5:begin wr=13'sd1806;wi=-13'sd965;end
5'd6:begin wr=13'sd1703;wi=-13'sd1138;end
5'd7:begin wr=13'sd1583;wi=-13'sd1299;end
5'd8:begin wr=13'sd1448;wi=-13'sd1448;end
5'd9:begin wr=13'sd1299;wi=-13'sd1583;end
5'd10:begin wr=13'sd1138;wi=-13'sd1703;end
5'd11:begin wr=13'sd965;wi=-13'sd1806;end
5'd12:begin wr=13'sd784;wi=-13'sd1892;end
5'd13:begin wr=13'sd595;wi=-13'sd1960;end
5'd14:begin wr=13'sd400;wi=-13'sd2009;end
5'd15:begin wr=13'sd201;wi=-13'sd2038;end
5'd16:begin wr=13'sd0;wi=-13'sd2048;end
5'd17:begin wr=-13'sd201;wi=-13'sd2038;end
5'd18:begin wr=-13'sd400;wi=-13'sd2009;end
5'd19:begin wr=-13'sd595;wi=-13'sd1960;end
5'd20:begin wr=-13'sd784;wi=-13'sd1892;end
5'd21:begin wr=-13'sd965;wi=-13'sd1806;end
5'd22:begin wr=-13'sd1138;wi=-13'sd1703;end
5'd23:begin wr=-13'sd1299;wi=-13'sd1583;end
5'd24:begin wr=-13'sd1448;wi=-13'sd1448;end
5'd25:begin wr=-13'sd1583;wi=-13'sd1299;end
5'd26:begin wr=-13'sd1703;wi=-13'sd1138;end
5'd27:begin wr=-13'sd1806;wi=-13'sd965;end
5'd28:begin wr=-13'sd1892;wi=-13'sd784;end
5'd29:begin wr=-13'sd1960;wi=-13'sd595;end
5'd30:begin wr=-13'sd2009;wi=-13'sd400;end
5'd31:begin wr=-13'sd2038;wi=-13'sd201;end
endcase end
wire signed[W-1:0] sr0=re_a0+re_b0,si0=im_a0+im_b0,dr0=re_a0-re_b0,di0=im_a0-im_b0;
wire signed[W+TF+1:0] rr0=dr0*wr,ii0=di0*wi,ri0=dr0*wi,ir0=di0*wr;
wire signed[W+TF+2:0] tr0=$signed(rr0)-$signed(ii0)+(1<<(TF-1)), ti0=$signed(ri0)+$signed(ir0)+(1<<(TF-1));
wire signed[W-1:0] xr0=exponent==0?dr0:exponent==16?di0:(tr0>>>TF),xi0=exponent==0?di0:exponent==16?-dr0:(ti0>>>TF);
wire signed[W-1:0] sr1=re_a1+re_b1,si1=im_a1+im_b1,dr1=re_a1-re_b1,di1=im_a1-im_b1;
wire signed[W+TF+1:0] rr1=dr1*wr,ii1=di1*wi,ri1=dr1*wi,ir1=di1*wr;
wire signed[W+TF+2:0] tr1=$signed(rr1)-$signed(ii1)+(1<<(TF-1)), ti1=$signed(ri1)+$signed(ir1)+(1<<(TF-1));
wire signed[W-1:0] xr1=exponent==0?dr1:exponent==16?di1:(tr1>>>TF),xi1=exponent==0?di1:exponent==16?-dr1:(ti1>>>TF);
wire signed[W-1:0] rot_re1=stage==5?xi1:xr1,rot_im1=stage==5?-xr1:xi1;
wire signed[W-1:0] wd_re0=bank_a0==0?sr0:bank_b0==0?xr0:bank_a1==0?sr1:rot_re1;
wire signed[W-1:0] wd_im0=bank_a0==0?si0:bank_b0==0?xi0:bank_a1==0?si1:rot_im1;
wire signed[W-1:0] wd_re1=bank_a0==1?sr0:bank_b0==1?xr0:bank_a1==1?sr1:rot_re1;
wire signed[W-1:0] wd_im1=bank_a0==1?si0:bank_b0==1?xi0:bank_a1==1?si1:rot_im1;
wire signed[W-1:0] wd_re2=bank_a0==2?sr0:bank_b0==2?xr0:bank_a1==2?sr1:rot_re1;
wire signed[W-1:0] wd_im2=bank_a0==2?si0:bank_b0==2?xi0:bank_a1==2?si1:rot_im1;
wire signed[W-1:0] wd_re3=bank_a0==3?sr0:bank_b0==3?xr0:bank_a1==3?sr1:rot_re1;
wire signed[W-1:0] wd_im3=bank_a0==3?si0:bank_b0==3?xi0:bank_a1==3?si1:rot_im1;
wire[5:0] ip=state==IDLE?6'd0:icnt,op={ocnt[0],ocnt[1],ocnt[2],ocnt[3],ocnt[4],ocnt[5]};
wire[1:0] ibank=bank(ip),ob=bank(op);
wire signed[W-1:0] memory_re=ob==0?re0[op[3:0]]:ob==1?re1[op[3:0]]:ob==2?re2[op[3:0]]:re3[op[3:0]];
wire signed[W-1:0] memory_im=ob==0?im0[op[3:0]]:ob==1?im1[op[3:0]]:ob==2?im2[op[3:0]]:im3[op[3:0]];
wire signed[16:0] input_re=$signed(in_re)+17'sd1,input_im=$signed(in_im)+17'sd1;
always @(posedge clk) begin if(!rst) begin
if(((state==IDLE&&in_valid&&frame_start)||(state==LOAD&&in_valid))&&ibank==0) begin
 re0[ip[3:0]]<=input_re>>>DROP;im0[ip[3:0]]<=input_im>>>DROP;
end else if(state==CALC) begin re0[ra0]<=wd_re0;im0[ra0]<=wd_im0;end
if(((state==IDLE&&in_valid&&frame_start)||(state==LOAD&&in_valid))&&ibank==1) begin
 re1[ip[3:0]]<=input_re>>>DROP;im1[ip[3:0]]<=input_im>>>DROP;
end else if(state==CALC) begin re1[ra1]<=wd_re1;im1[ra1]<=wd_im1;end
if(((state==IDLE&&in_valid&&frame_start)||(state==LOAD&&in_valid))&&ibank==2) begin
 re2[ip[3:0]]<=input_re>>>DROP;im2[ip[3:0]]<=input_im>>>DROP;
end else if(state==CALC) begin re2[ra2]<=wd_re2;im2[ra2]<=wd_im2;end
if(((state==IDLE&&in_valid&&frame_start)||(state==LOAD&&in_valid))&&ibank==3) begin
 re3[ip[3:0]]<=input_re>>>DROP;im3[ip[3:0]]<=input_im>>>DROP;
end else if(state==CALC) begin re3[ra3]<=wd_re3;im3[ra3]<=wd_im3;end
end end
always @(posedge clk) begin
 if(rst) begin state<=IDLE;icnt<=0;ocnt<=0;bc<=0;stage<=5;out_valid<=0;out_start<=0;end
 else begin out_valid<=0;out_start<=0;
 case(state)
 IDLE:if(in_valid&&frame_start)begin state<=LOAD;icnt<=1;end
 LOAD:if(in_valid)begin icnt<=icnt+1'b1;if(icnt==63)begin state<=CALC;stage<=5;bc<=0;end end
 CALC:begin bc<=bc+1'b1;if(bc==15)begin stage<=stage-1'b1;if(stage==0)begin state<=SEND;ocnt<=0;end end end
 SEND:begin out_valid<=1;out_start<=ocnt==0;out_re<=$signed(memory_re)*(1<<DROP);out_im<=$signed(memory_im)*(1<<DROP);
 ocnt<=ocnt+1'b1;if(ocnt==63)state<=IDLE;end
 endcase end end
endmodule
