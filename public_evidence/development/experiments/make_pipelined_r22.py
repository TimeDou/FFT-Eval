from pathlib import Path
p=Path('experiments/R004/rtl/fft64_top.sv');s=p.read_text()
s=s.replace('reg signed[TF:0] cr,ci;\nalways @*begin cr=0;ci=0;', 'reg signed[TF:0] cr_now,ci_now;\nreg signed[TF:0] cr,ci;\nalways @(posedge clk)begin cr<=cr_now;ci<=ci_now;end\nalways @*begin cr_now=0;ci_now=0;')
s=s.replace('case(j)','case(exp_now[3:0])').replace(':begin cr=',':begin cr_now=').replace(';ci=', ';ci_now=')
start=s.index('wire signed[W+TF:0] rr=');end=s.index('\nendmodule',start)
s=s[:start]+'''// Only two rotations need products. Decode is registered alongside data.
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
end endgenerate'''+s[end:]
p.write_text(s)
