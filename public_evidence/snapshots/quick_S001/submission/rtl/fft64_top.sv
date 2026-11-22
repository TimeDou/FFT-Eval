// Radix-2 DIF single-path delay-feedback FFT, with pipelined rotations.
module fft64_sdf_stage #(parameter LG=5, IW=15, TF=11)(
 input wire clk,rst,iv,ifs,
 input wire signed[IW-1:0] ir,ii,
 output wire ov,ofs,
 output wire signed[IW:0] ore,oim
);
localparam D=1<<LG, W=IW+1;
reg signed[W-1:0] delay_re[0:D-1],delay_im[0:D-1];
reg[D-1:0] vdelay,sdelay;
reg[5:0] icount,ocount;
wire[5:0] ip=ifs?6'd0:icount,op=sdelay[D-1]?6'd0:ocount;
wire upper=iv&&ip[LG];
wire signed[W-1:0] current_re=ir,current_im=ii;
wire signed[W-1:0] bf_re=upper?delay_re[0]+current_re:delay_re[0];
wire signed[W-1:0] bf_im=upper?delay_im[0]+current_im:delay_im[0];
wire signed[W-1:0] feed_re=upper?delay_re[0]-current_re:iv?current_re:{W{1'b0}};
wire signed[W-1:0] feed_im=upper?delay_im[0]-current_im:iv?current_im:{W{1'b0}};
integer n;
always @(posedge clk) begin
 for(n=0;n<D-1;n=n+1) begin delay_re[n]<=delay_re[n+1];delay_im[n]<=delay_im[n+1];end
 delay_re[D-1]<=feed_re;delay_im[D-1]<=feed_im;
 if(rst)begin vdelay<=0;sdelay<=0;icount<=0;ocount<=0;end
 else begin
   vdelay<=(vdelay<<1)|iv;sdelay<=(sdelay<<1)|(iv&&ifs);
   if(iv)icount<=ip+1'b1;
   if(vdelay[D-1])ocount<=op+1'b1;
 end
end
reg signed[W-1:0] bf_reg_re,bf_reg_im;
reg bf_v,bf_s;
reg[4:0] exponent;
wire[4:0] exp_now=op[LG]?((op[4:0] & (D-1))<<(5-LG)):5'd0;
always @(posedge clk)begin
 if(rst)begin bf_v<=0;bf_s<=0;exponent<=0;end
 else begin bf_v<=vdelay[D-1];bf_s<=sdelay[D-1];exponent<=exp_now;end
 bf_reg_re<=bf_re;bf_reg_im<=bf_im;
end
// Quadrant reduction specializes trivial rotations and halves coefficient ROM.
wire q=exponent[4];
wire[3:0] j=exponent[3:0];
reg signed[TF:0] cr,ci;
always @*begin cr=0;ci=0;
 case(j)

4'd1:begin cr=12'sd2038;ci=-12'sd201;end
4'd2:begin cr=12'sd2009;ci=-12'sd400;end
4'd3:begin cr=12'sd1960;ci=-12'sd595;end
4'd4:begin cr=12'sd1892;ci=-12'sd784;end
4'd5:begin cr=12'sd1806;ci=-12'sd965;end
4'd6:begin cr=12'sd1703;ci=-12'sd1138;end
4'd7:begin cr=12'sd1583;ci=-12'sd1299;end
4'd8:begin cr=12'sd1448;ci=-12'sd1448;end
4'd9:begin cr=12'sd1299;ci=-12'sd1583;end
4'd10:begin cr=12'sd1138;ci=-12'sd1703;end
4'd11:begin cr=12'sd965;ci=-12'sd1806;end
4'd12:begin cr=12'sd784;ci=-12'sd1892;end
4'd13:begin cr=12'sd595;ci=-12'sd1960;end
4'd14:begin cr=12'sd400;ci=-12'sd2009;end
4'd15:begin cr=12'sd201;ci=-12'sd2038;end
endcase end
wire signed[W+TF:0] rr=bf_reg_re*cr, si=bf_reg_im*ci, ri=bf_reg_re*ci, sr=bf_reg_im*cr;
wire signed[W+TF+1:0] pr=$signed(rr)-$signed(si)+(1<<(TF-1)),pi=$signed(ri)+$signed(sr)+(1<<(TF-1));
wire signed[W-1:0] xr=j==0?bf_reg_re:(pr>>>TF),xi=j==0?bf_reg_im:(pi>>>TF);
reg signed[W-1:0] out_r,out_i;reg out_v,out_s;
always @(posedge clk)begin
 if(rst)begin out_v<=0;out_s<=0;end
 else begin out_v<=bf_v;out_s<=bf_s;end
 out_r<=q?xi:xr;out_i<=q?-xr:xi;
end
assign ov=out_v;assign ofs=out_s;assign ore=out_r;assign oim=out_i;
endmodule

module fft64_top(
 input wire clk,rst,in_valid,frame_start,
 input wire signed[15:0] in_re,in_im,
 output reg out_valid,out_start,
 output reg signed[23:0] out_re,out_im
);
wire signed[16:0] rounded_re=$signed(in_re)+17'sd1,rounded_im=$signed(in_im)+17'sd1;
wire signed[14:0] dr0=rounded_re>>>1,di0=rounded_im>>>1;
wire v0=in_valid,s0=frame_start;

wire v1,s1;wire signed[15:0] dr1,di1;
fft64_sdf_stage #(.LG(5),.IW(15),.TF(11)) stage0(.clk(clk),.rst(rst),.iv(v0),.ifs(s0),.ir(dr0),.ii(di0),.ov(v1),.ofs(s1),.ore(dr1),.oim(di1));
wire v2,s2;wire signed[16:0] dr2,di2;
fft64_sdf_stage #(.LG(4),.IW(16),.TF(11)) stage1(.clk(clk),.rst(rst),.iv(v1),.ifs(s1),.ir(dr1),.ii(di1),.ov(v2),.ofs(s2),.ore(dr2),.oim(di2));
wire v3,s3;wire signed[17:0] dr3,di3;
fft64_sdf_stage #(.LG(3),.IW(17),.TF(11)) stage2(.clk(clk),.rst(rst),.iv(v2),.ifs(s2),.ir(dr2),.ii(di2),.ov(v3),.ofs(s3),.ore(dr3),.oim(di3));
wire v4,s4;wire signed[18:0] dr4,di4;
fft64_sdf_stage #(.LG(2),.IW(18),.TF(11)) stage3(.clk(clk),.rst(rst),.iv(v3),.ifs(s3),.ir(dr3),.ii(di3),.ov(v4),.ofs(s4),.ore(dr4),.oim(di4));
wire v5,s5;wire signed[19:0] dr5,di5;
fft64_sdf_stage #(.LG(1),.IW(19),.TF(11)) stage4(.clk(clk),.rst(rst),.iv(v4),.ifs(s4),.ir(dr4),.ii(di4),.ov(v5),.ofs(s5),.ore(dr5),.oim(di5));
wire v6,s6;wire signed[20:0] dr6,di6;
fft64_sdf_stage #(.LG(0),.IW(20),.TF(11)) stage5(.clk(clk),.rst(rst),.iv(v5),.ifs(s5),.ir(dr5),.ii(di5),.ov(v6),.ofs(s6),.ore(dr6),.oim(di6));
// Single reorder memory, alternating between natural and bit-reversed writes.
// A following frame overwrites locations in the preceding frame's read order.
reg signed[20:0] mem_re[0:63],mem_im[0:63];
reg[5:0] wp,rp;
reg write_flip,read_flip;
reg reading;
wire[5:0] wi=s6?6'd0:wp;
wire[5:0] reversed_wi={wi[0],wi[1],wi[2],wi[3],wi[4],wi[5]};
wire[5:0] reversed_rp={rp[0],rp[1],rp[2],rp[3],rp[4],rp[5]};
wire[5:0] wa=write_flip?reversed_wi:wi;
wire[5:0] ra=read_flip?reversed_rp:rp;
always @(posedge clk)begin
 if(!rst&&v6)begin mem_re[wa]<=dr6;mem_im[wa]<=di6;end
 if(rst)begin wp<=0;rp<=0;write_flip<=0;read_flip<=0;reading<=0;out_valid<=0;out_start<=0;end
 else begin
 out_valid<=reading;out_start<=reading&&rp==0;
 if(reading)begin out_re<=$signed(mem_re[ra])*2;out_im<=$signed(mem_im[ra])*2;rp<=rp+1'b1;if(rp==63)reading<=0;end
 if(v6)begin
 wp<=wi+1'b1;
 if(wi==63)begin reading<=1;rp<=0;read_flip<=!write_flip;write_flip<=!write_flip;end
 end
 end
end
endmodule
