#!/usr/bin/env python3
"""Pipeline the folded block-floating butterfly while preserving stage ordering."""
import argparse,re,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--depth',type=int,choices=[1,2],default=2);p.add_argument('--width',type=int,default=15);p.add_argument('--mul',type=int,choices=[3,4],default=3);p.add_argument('--out',default='experiments/block15_pipe2/rtl/fft64_top.sv');a=p.parse_args();D=a.depth
subprocess.run([sys.executable,str(Path(__file__).with_name('generate_blockfloat.py')),'--width',str(a.width),'--mul',str(a.mul),'--out',a.out],check=True)
s=Path(a.out).read_text()
declarations='''
    reg pipe_valid,pipe_last,pipe_first,pipe_abank;
    reg [2:0] pipe_stage;
    reg [4:0] pipe_wa0,pipe_wa1;
    reg signed [W-1:0] pipe_ar,pipe_ai;
    reg signed [W:0] pipe_tr,pipe_ti;
'''
if D==2:
 declarations+='''    reg read_valid,read_last,read_first,read_abank;
    reg [2:0] read_stage;
    reg [4:0] read_wa0,read_wa1;
    reg signed [W-1:0] read_ar,read_ai,read_br,read_bi;
    reg signed [C-1:0] read_wr,read_wi;
    reg [4:0] read_twiddle;
'''
s=s.replace('    reg [2:0] stage;', '    reg [2:0] stage;'+declarations)
for tag,orig,rot,op in [('sr','ar','tr','+'),('si','ai','ti','+'),('dr','ar','tr','-'),('di','ai','ti','-')]:
 old=f'wire signed [W+1:0] full_{tag}={{{{2{{{orig}[W-1]}}}},{orig}}}{op}{{{rot}[W],{rot}}};'
 new=f'wire signed [W+1:0] full_{tag}={{{{2{{pipe_{orig}[W-1]}}}},pipe_{orig}}}{op}{{pipe_{rot}[W],pipe_{rot}}};'
 assert old in s,old
 s=s.replace(old,new)
if D==2:
 start=s.index('    wire signed [W:0] bs') if a.mul==3 else s.index('    wire signed [W+C-1:0] rr')
 end=s.index('    wire signed [W+1:0] full_sr')
 part=s[start:end]
 for name in ['br','bi','wr','wi','twiddle']:
  part=re.sub(r'\b'+name+r'\b','read_'+name,part)
 s=s[:start]+part+s[end:]
fetch='''    wire fetch=((state==LOAD) && sample[5] && in_valid) || (state==CALC);
    wire fetch_last=(state==LOAD) ? (sample==63) : (butterfly==31);
    wire fetch_first=(state==CALC && stage==5 && butterfly==0);
    wire [4:0] fetch_wa0=(state==LOAD)?input_address[5:1]:(a_bank?bb[5:1]:aa[5:1]);
    wire [4:0] fetch_wa1=(state==LOAD)?input_address[5:1]:(a_bank?aa[5:1]:bb[5:1]);
'''
if D==1:
 pipeline='''    always @(posedge clk) begin
        if (rst) pipe_valid<=0;
        else begin
            pipe_valid<=fetch;
            if (fetch) begin
                pipe_last<=fetch_last; pipe_first<=fetch_first; pipe_abank<=a_bank;
                pipe_stage<=stage; pipe_wa0<=fetch_wa0; pipe_wa1<=fetch_wa1;
                pipe_ar<=ar; pipe_ai<=ai; pipe_tr<=tr; pipe_ti<=ti;
            end
        end
    end
'''
else:
 pipeline='''    always @(posedge clk) begin
        if (rst) begin pipe_valid<=0; read_valid<=0; end
        else begin
            read_valid<=fetch; pipe_valid<=read_valid;
            if (fetch) begin
                read_last<=fetch_last; read_first<=fetch_first; read_abank<=a_bank;
                read_stage<=stage; read_wa0<=fetch_wa0; read_wa1<=fetch_wa1;
                read_ar<=ar; read_ai<=ai; read_br<=br; read_bi<=bi;
                read_wr<=wr; read_wi<=wi; read_twiddle<=twiddle;
            end
            if (read_valid) begin
                pipe_last<=read_last; pipe_first<=read_first; pipe_abank<=read_abank;
                pipe_stage<=read_stage; pipe_wa0<=read_wa0; pipe_wa1<=read_wa1;
                pipe_ar<=read_ar; pipe_ai<=read_ai; pipe_tr<=tr; pipe_ti<=ti;
            end
        end
    end
'''
s=s.replace('    reg we0,we1;', fetch+pipeline+'\n    reg we0,we1;')
s=s.replace('wire [1:0] next_shift=(stage==0)', 'wire [1:0] next_shift=(pipe_stage==0)')
s=s.replace('else if ((state==LOAD && sample[5] && in_valid) || state==CALC) begin', 'else if (pipe_valid) begin')
s=s.replace('if ((state==LOAD && sample==63) || (state==CALC && butterfly==31)) begin', 'if (pipe_last) begin')
s=s.replace('if (stage<5) begin current_shift<=next_shift;', 'if (pipe_stage<5) begin current_shift<=next_shift;')
start=s.index('    always @* begin\n        we0=0;');end=s.index('    always @(posedge clk) begin\n        if (!rst)',start)
s=s[:start]+'''    always @* begin
        we0=0; we1=0; wa0=0; wa1=0;
        wd0r=0; wd0i=0; wd1r=0; wd1i=0;
        if (((state==IDLE) && in_valid && frame_start) || ((state==LOAD) && in_valid && !sample[5])) begin
            we0=!input_bank; we1=input_bank;
            wa0=input_address[5:1]; wa1=input_address[5:1];
            wd0r=input_r; wd0i=input_i; wd1r=input_r; wd1i=input_i;
        end else if (pipe_valid) begin
            we0=1; we1=1; wa0=pipe_wa0; wa1=pipe_wa1;
            wd0r=pipe_abank?dif_r:sum_r; wd0i=pipe_abank?dif_i:sum_i;
            wd1r=pipe_abank?sum_r:dif_r; wd1i=pipe_abank?sum_i:dif_i;
        end
    end
'''+s[end:]
# Transfer the lower-half output generation from fetch control to writeback.
start=s.index('                    if (stage==5) begin\n                        out_valid<=1;')
end=s.index('                    butterfly<=',start)
s=s[:start]+s[end:]
s=s.replace('            out_valid<=0; out_start<=0;\n            case (state)', '''            out_valid<=0; out_start<=0;
            if (pipe_valid && pipe_stage==5) begin
                out_valid<=1; out_start<=pipe_first;
                out_re<=$signed({{(24-W){sum_r[W-1]}},sum_r}) <<< exponent;
                out_im<=$signed({{(24-W){sum_i[W-1]}},sum_i}) <<< exponent;
            end
            case (state)''')
s=s.replace('                EMIT: begin\n                    out_valid<=1;', '                EMIT: if (!pipe_valid) begin\n                    out_valid<=1;')
s=s.replace('// Architecture:','// Butterfly pipeline registers: '+str(D)+' stages.\n// Architecture:')
Path(a.out).write_text(s)
