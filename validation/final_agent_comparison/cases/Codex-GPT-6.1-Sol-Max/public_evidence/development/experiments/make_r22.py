from pathlib import Path
p=Path('experiments/R001/rtl/fft64_top.sv');s=p.read_text()
s=s.replace('single-path delay-feedback FFT','radix-2-squared single-path delay-feedback FFT')
s=s.replace('LG=5, IW=15, TF=9','LG=5, IW=15, TF=9, FIRST=0')
s=s.replace('reg[4:0] exponent;\nwire[4:0] exp_now=op[LG]?((op[4:0] & (D-1))<<(5-LG)):5\'d0;', '''reg[5:0] exponent;
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
end endgenerate''')
s=s.replace('wire q=exponent[4];','wire[1:0] q=exponent[5:4];')
old='''reg signed[W-1:0] out_r,out_i;reg out_v,out_s;
always @(posedge clk)begin
 if(rst)begin out_v<=0;out_s<=0;end
 else begin out_v<=bf_v;out_s<=bf_s;end
 out_r<=q?xi:xr;out_i<=q?-xr:xi;
end
assign ov=out_v;assign ofs=out_s;assign ore=out_r;assign oim=out_i;'''
new='''wire signed[W-1:0] rot_re=q==0?xr:q==1?xi:q==2?-xr:-xi;
wire signed[W-1:0] rot_im=q==0?xi:q==1?-xr:q==2?-xi:xr;
generate if(FIRST || LG==0)begin
 assign ov=bf_v;assign ofs=bf_s;assign ore=rot_re;assign oim=rot_im;
end else begin
 reg signed[W-1:0] out_r,out_i;reg out_v,out_s;
 always @(posedge clk)begin
 if(rst)begin out_v<=0;out_s<=0;end
 else begin out_v<=bf_v;out_s<=bf_s;end
 out_r<=rot_re;out_i<=rot_im;
 end
 assign ov=out_v;assign ofs=out_s;assign ore=out_r;assign oim=out_i;
end endgenerate'''
assert old in s;s=s.replace(old,new)
for st in range(6):s=s.replace(f'.IW({15+st}),.TF(9)) stage{st}', f'.IW({15+st}),.TF(9),.FIRST({1 if st%2==0 else 0})) stage{st}')
p.write_text(s)
