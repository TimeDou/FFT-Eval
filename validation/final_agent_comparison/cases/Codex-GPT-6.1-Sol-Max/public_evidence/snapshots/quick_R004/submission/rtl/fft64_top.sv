// Radix-2 DIF radix-2-squared single-path delay-feedback FFT, with pipelined rotations.
module fft64_sdf_stage #(parameter LG=5, IW=15, TF=9, FIRST=0)(
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
reg[5:0] exponent;
wire[5:0] exp_now;
generate if(FIRST)begin
 assign exp_now=(&op[LG:LG-1])?6'd16:6'd0;
end else begin
 reg[5:0] angle;
 always @*begin
 case(op[LG+1:LG])
 2'd0:angle=0;
 2'd1:angle=((op[4:0]&(D-1))*2)<<(4-LG);
 2'd2:angle=(op[4:0]&(D-1))<<(4-LG);
 2'd3:angle=((op[4:0]&(D-1))*3)<<(4-LG);
 endcase end
 assign exp_now=angle;
end endgenerate
always @(posedge clk)begin
 if(rst)begin bf_v<=0;bf_s<=0;exponent<=0;end
 else begin bf_v<=vdelay[D-1];bf_s<=sdelay[D-1];exponent<=exp_now;end
 bf_reg_re<=bf_re;bf_reg_im<=bf_im;
end
// Quadrant reduction specializes trivial rotations and halves coefficient ROM.
wire[1:0] q=exponent[5:4];
wire[3:0] j=exponent[3:0];
reg signed[TF:0] cr_now,ci_now;
reg signed[TF:0] cr,ci;
always @(posedge clk)begin cr<=cr_now;ci<=ci_now;end
always @*begin cr_now=0;ci_now=0;
 case(exp_now[3:0])

4'd1:begin cr_now=10'sd510;ci_now=-10'sd50;end
4'd2:begin cr_now=10'sd502;ci_now=-10'sd100;end
4'd3:begin cr_now=10'sd490;ci_now=-10'sd149;end
4'd4:begin cr_now=10'sd473;ci_now=-10'sd196;end
4'd5:begin cr_now=10'sd452;ci_now=-10'sd241;end
4'd6:begin cr_now=10'sd426;ci_now=-10'sd284;end
4'd7:begin cr_now=10'sd396;ci_now=-10'sd325;end
4'd8:begin cr_now=10'sd362;ci_now=-10'sd362;end
4'd9:begin cr_now=10'sd325;ci_now=-10'sd396;end
4'd10:begin cr_now=10'sd284;ci_now=-10'sd426;end
4'd11:begin cr_now=10'sd241;ci_now=-10'sd452;end
4'd12:begin cr_now=10'sd196;ci_now=-10'sd473;end
4'd13:begin cr_now=10'sd149;ci_now=-10'sd490;end
4'd14:begin cr_now=10'sd100;ci_now=-10'sd502;end
4'd15:begin cr_now=10'sd50;ci_now=-10'sd510;end
endcase end
// Only two rotations need products. Decode is registered alongside data.
generate if(FIRST || LG==0)begin
 assign ov=bf_v;assign ofs=bf_s;
 assign ore=q==0?bf_reg_re:bf_reg_im;
 assign oim=q==0?bf_reg_im:-bf_reg_re;
end else begin
 wire signed[W:0] add_data=$signed(bf_reg_re)+$signed(bf_reg_im);
 wire signed[TF+1:0] add_coeff=$signed(cr)+$signed(ci);
 reg signed[W+TF:0] prod_rr,prod_ii;
 reg signed[W+TF+2:0] prod_combined;
 reg signed[W-1:0] pass_re,pass_im;
 reg[1:0] prod_q;
 reg trivial,mul_v,mul_s;
 always @(posedge clk)begin
  prod_rr<=bf_reg_re*cr;prod_ii<=bf_reg_im*ci;prod_combined<=add_data*add_coeff;
  pass_re<=bf_reg_re;pass_im<=bf_reg_im;prod_q<=q;trivial<=j==0;
  if(rst)begin mul_v<=0;mul_s<=0;end else begin mul_v<=bf_v;mul_s<=bf_s;end
 end
 wire signed[W+TF+3:0] pr=$signed(prod_rr)-$signed(prod_ii)+(1<<(TF-1));
 wire signed[W+TF+3:0] pi=$signed(prod_combined)-$signed(prod_rr)-$signed(prod_ii)+(1<<(TF-1));
 wire signed[W-1:0] xr=trivial?pass_re:(pr>>>TF),xi=trivial?pass_im:(pi>>>TF);
 wire signed[W-1:0] rot_re=prod_q==0?xr:prod_q==1?xi:prod_q==2?-xr:-xi;
 wire signed[W-1:0] rot_im=prod_q==0?xi:prod_q==1?-xr:prod_q==2?-xi:xr;
 reg signed[W-1:0] out_r,out_i;reg out_v,out_s;
 always @(posedge clk)begin
 if(rst)begin out_v<=0;out_s<=0;end
 else begin out_v<=mul_v;out_s<=mul_s;end
 out_r<=rot_re;out_i<=rot_im;
 end
 assign ov=out_v;assign ofs=out_s;assign ore=out_r;assign oim=out_i;
end endgenerate
endmodule

module fft64_top(
 input wire clk,rst,in_valid,frame_start,
 input wire signed[15:0] in_re,in_im,
 output reg out_valid,out_start,
 output reg signed[23:0] out_re,out_im
);
wire signed[16:0] rounded_re=$signed(in_re)+$signed({1'b0,(in_re[0]&in_re[1])}),rounded_im=$signed(in_im)+$signed({1'b0,(in_im[0]&in_im[1])});
wire signed[14:0] dr0=rounded_re>>>1,di0=rounded_im>>>1;
wire v0=in_valid,s0=frame_start;

wire v1,s1;wire signed[15:0] dr1,di1;
fft64_sdf_stage #(.LG(5),.IW(15),.TF(9),.FIRST(1)) stage0(.clk(clk),.rst(rst),.iv(v0),.ifs(s0),.ir(dr0),.ii(di0),.ov(v1),.ofs(s1),.ore(dr1),.oim(di1));
wire v2,s2;wire signed[15:0] dr2,di2;
wire signed[16:0] raw_re1,raw_im1;
fft64_sdf_stage #(.LG(4),.IW(16),.TF(9),.FIRST(0)) stage1(.clk(clk),.rst(rst),.iv(v1),.ifs(s1),.ir(dr1),.ii(di1),.ov(v2),.ofs(s2),.ore(raw_re1),.oim(raw_im1));
wire signed[17:0] round_re1=$signed(raw_re1)+$signed({1'b0,(raw_re1[0]&raw_re1[1])}),round_im1=$signed(raw_im1)+$signed({1'b0,(raw_im1[0]&raw_im1[1])});
assign dr2=round_re1>>>1;assign di2=round_im1>>>1;
wire v3,s3;wire signed[16:0] dr3,di3;
fft64_sdf_stage #(.LG(3),.IW(16),.TF(9),.FIRST(1)) stage2(.clk(clk),.rst(rst),.iv(v2),.ifs(s2),.ir(dr2),.ii(di2),.ov(v3),.ofs(s3),.ore(dr3),.oim(di3));
wire v4,s4;wire signed[16:0] dr4,di4;
wire signed[17:0] raw_re3,raw_im3;
fft64_sdf_stage #(.LG(2),.IW(17),.TF(9),.FIRST(0)) stage3(.clk(clk),.rst(rst),.iv(v3),.ifs(s3),.ir(dr3),.ii(di3),.ov(v4),.ofs(s4),.ore(raw_re3),.oim(raw_im3));
wire signed[18:0] round_re3=$signed(raw_re3)+$signed({1'b0,(raw_re3[0]&raw_re3[1])}),round_im3=$signed(raw_im3)+$signed({1'b0,(raw_im3[0]&raw_im3[1])});
assign dr4=round_re3>>>1;assign di4=round_im3>>>1;
wire v5,s5;wire signed[17:0] dr5,di5;
fft64_sdf_stage #(.LG(1),.IW(17),.TF(9),.FIRST(1)) stage4(.clk(clk),.rst(rst),.iv(v4),.ifs(s4),.ir(dr4),.ii(di4),.ov(v5),.ofs(s5),.ore(dr5),.oim(di5));
wire v6,s6;wire signed[18:0] dr6,di6;
fft64_sdf_stage #(.LG(0),.IW(18),.TF(9),.FIRST(0)) stage5(.clk(clk),.rst(rst),.iv(v5),.ifs(s5),.ir(dr5),.ii(di5),.ov(v6),.ofs(s6),.ore(dr6),.oim(di6));
// Single reorder memory, alternating between natural and bit-reversed writes.
// A following frame overwrites locations in the preceding frame's read order.
reg signed[18:0] mem_re[0:63],mem_im[0:63];
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
 if(reading)begin out_re<=$signed(mem_re[ra])*8;out_im<=$signed(mem_im[ra])*8;rp<=rp+1'b1;if(rp==63)reading<=0;end
 if(v6)begin
 wp<=wi+1'b1;
 // max(bit_reverse(k)-k)=49: the first read at input index 50 is safe.
 if(wi==49)begin reading<=1;rp<=0;read_flip<=!write_flip;end
 if(wi==63)write_flip<=!write_flip;
 end
 end
end
endmodule
