from pathlib import Path
import math, argparse
p=argparse.ArgumentParser();p.add_argument('--lanes',type=int,choices=[1,2],default=2);p.add_argument('--width',type=int,default=21);p.add_argument('--drop',type=int,default=1);p.add_argument('--tf',type=int,default=11);p.add_argument('--out',default='submission');a=p.parse_args()
W,DROP,TF=a.width,a.drop,a.tf
lanes=a.lanes; banks=lanes*2; bits=6-(banks.bit_length()-1); depth=1<<bits
lines=[]
def emit(s):lines.append(s)
emit('''// Generated complete radix-2 DIF. Parity banking allows conflict-free butterflies.
module fft64_top (
 input wire clk,rst,in_valid,frame_start,
 input wire signed [15:0] in_re,in_im,
 output reg out_valid,out_start,
 output reg signed [23:0] out_re,out_im
);''')
emit(f'localparam W={W}, DROP={DROP}, TF={TF};')
emit(f'localparam IDLE=0,LOAD=1,CALC=2,SEND=3; reg[1:0] state; reg[5:0] icnt,ocnt; reg[{bits-1}:0] bc; reg[2:0] stage;')
if banks==2:
 emit('function bank; input[5:0] x; begin bank=^x; end endfunction')
else:
 emit('function [1:0] bank; input[5:0] x; begin bank={x[5]^x[3]^x[1], x[4]^x[2]^x[0]}; end endfunction')
for b in range(banks):emit(f'reg signed[W-1:0] re{b}[0:{depth-1}],im{b}[0:{depth-1}];')
emit('reg[5:0] a0; always @* begin case(stage)')
for st in range(6):
 t=(5 if st%2==0 else 4) if banks==4 else None
 positions=[i for i in range(6) if i!=st and i!=t]
 val=["1'b0" if i==st or i==t else f'bc[{positions.index(i)}]' for i in range(5,-1,-1)]
 emit(f"3'd{st}: a0={{{','.join(val)}}};")
emit('default:a0=0; endcase end')
emit('wire[5:0] b0=a0^(6\'d1<<stage);')
if lanes==2:emit("wire[5:0] a1=a0^(stage[0]?6'd16:6'd32), b1=a1^(6'd1<<stage);")
nodes=[v+str(l) for l in range(lanes) for v in ['a','b']]
for n in nodes:emit(f'wire[{banks.bit_length()-2}:0] bank_{n}=bank({n});')
for b in range(banks):
 emit(f'wire[{bits-1}:0] ra{b}='+''.join(f'bank_{n}=={b}?{n}[{bits-1}:0]:' for n in nodes[:-1])+f'{nodes[-1]}[{bits-1}:0];')
for n in nodes:
 for z in ['re','im']:
  emit(f'wire signed[W-1:0] {z}_{n}='+''.join(f'bank_{n}=={b}?{z}{b}[ra{b}]:' for b in range(banks-1))+f'{z}{banks-1}[ra{banks-1}];')
emit("wire[4:0] exponent=a0[4:0]<<(5-stage); reg signed[TF+1:0] wr,wi;")
emit('always @* begin wr=0;wi=0; case(exponent)')
def lit(v):return ('-' if v<0 else '')+f"{TF+2}'sd{abs(v)}"
for k in range(32):
 r=round(math.cos(2*math.pi*k/64)*(1<<TF)); i=round(-math.sin(2*math.pi*k/64)*(1<<TF))
 emit(f"5'd{k}:begin wr={lit(r)};wi={lit(i)};end")
emit('endcase end')
for l in range(lanes):
 emit(f'''wire signed[W-1:0] sr{l}=re_a{l}+re_b{l},si{l}=im_a{l}+im_b{l},dr{l}=re_a{l}-re_b{l},di{l}=im_a{l}-im_b{l};
wire signed[W+TF+1:0] rr{l}=dr{l}*wr,ii{l}=di{l}*wi,ri{l}=dr{l}*wi,ir{l}=di{l}*wr;
wire signed[W+TF+2:0] tr{l}=$signed(rr{l})-$signed(ii{l})+(1<<(TF-1)), ti{l}=$signed(ri{l})+$signed(ir{l})+(1<<(TF-1));
wire signed[W-1:0] xr{l}=exponent==0?dr{l}:exponent==16?di{l}:(tr{l}>>>TF),xi{l}=exponent==0?di{l}:exponent==16?-dr{l}:(ti{l}>>>TF);''')
 if l==1:emit("wire signed[W-1:0] rot_re1=stage==5?xi1:xr1,rot_im1=stage==5?-xr1:xi1;")
for b in range(banks):
 for z in ['re','im']:
  vals=[]
  for n in nodes:
   l=int(n[1]);is_a=n[0]=='a'
   v=('sr' if z=='re' else 'si')+str(l) if is_a else (('rot_'+z+str(l)) if l==1 else ('xr' if z=='re' else 'xi')+str(l))
   vals.append(v)
  emit(f'wire signed[W-1:0] wd_{z}{b}='+''.join(f'bank_{n}=={b}?{v}:' for n,v in zip(nodes[:-1],vals[:-1]))+vals[-1]+';')
emit("wire[5:0] ip=state==IDLE?6'd0:icnt,op={ocnt[0],ocnt[1],ocnt[2],ocnt[3],ocnt[4],ocnt[5]};")
emit(f'wire[{banks.bit_length()-2}:0] ibank=bank(ip),ob=bank(op);')
for z in ['re','im']:
 emit(f'wire signed[W-1:0] out_{z}='+''.join(f'ob=={b}?{z}{b}[op[{bits-1}:0]]:' for b in range(banks-1))+f'{z}{banks-1}[op[{bits-1}:0]];')
emit(f"wire signed[16:0] input_re=$signed(in_re)+17'sd{(1<<(DROP-1)) if DROP else 0},input_im=$signed(in_im)+17'sd{(1<<(DROP-1)) if DROP else 0};")
emit('always @(posedge clk) begin if(!rst) begin')
for b in range(banks):
 emit(f'''if(((state==IDLE&&in_valid&&frame_start)||(state==LOAD&&in_valid))&&ibank=={b}) begin
 re{b}[ip[{bits-1}:0]]<=input_re>>>DROP;im{b}[ip[{bits-1}:0]]<=input_im>>>DROP;
end else if(state==CALC) begin re{b}[ra{b}]<=wd_re{b};im{b}[ra{b}]<=wd_im{b};end''')
emit('end end')
emit(f'''always @(posedge clk) begin
 if(rst) begin state<=IDLE;icnt<=0;ocnt<=0;bc<=0;stage<=5;out_valid<=0;out_start<=0;end
 else begin out_valid<=0;out_start<=0;
 case(state)
 IDLE:if(in_valid&&frame_start)begin state<=LOAD;icnt<=1;end
 LOAD:if(in_valid)begin icnt<=icnt+1'b1;if(icnt==63)begin state<=CALC;stage<=5;bc<=0;end end
 CALC:begin bc<=bc+1'b1;if(bc=={depth-1})begin stage<=stage-1'b1;if(stage==0)begin state<=SEND;ocnt<=0;end end end
 SEND:begin out_valid<=1;out_start<=ocnt==0;out_re<=$signed(out_re)*0;out_re<=$signed(out_re); 
 out_re<=$signed(out_re);out_re<=$signed(out_re); // replaced below
 ocnt<=ocnt+1'b1;if(ocnt==63)state<=IDLE;end
 endcase end end
endmodule''')
s='\n'.join(lines).replace('out_re','out_re')
# Distinct names for combinational memory read and registered top-level output.
s=s.replace('wire signed[W-1:0] out_re=', 'wire signed[W-1:0] memory_re=').replace('wire signed[W-1:0] out_im=', 'wire signed[W-1:0] memory_im=')
s=s.replace('out_re<=$signed(out_re)*0;out_re<=$signed(out_re); \n out_re<=$signed(out_re);out_re<=$signed(out_re); // replaced below', 'out_re<=$signed(memory_re)*(1<<DROP);out_im<=$signed(memory_im)*(1<<DROP);')
out=Path(a.out);(out/'rtl').mkdir(parents=True,exist_ok=True);(out/'rtl/fft64_top.sv').write_text(s+'\n');(out/'design_config.json').write_text('{"rtl":["rtl/fft64_top.sv"],"frame_ii_cycles":'+str(128+192//lanes)+'}\n')
