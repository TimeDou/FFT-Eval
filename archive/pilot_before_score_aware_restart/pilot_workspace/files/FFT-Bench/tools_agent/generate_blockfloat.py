#!/usr/bin/env python3
"""Generate an adaptive block-floating variant from the folded FFT template."""
from pathlib import Path
import argparse, subprocess, sys, re
p=argparse.ArgumentParser();p.add_argument('--width',type=int,default=16);p.add_argument('--twfrac',type=int,default=9);p.add_argument('--mul',type=int,choices=[3,4],default=3);p.add_argument('--out',default='experiments/block16/rtl/fft64_top.sv');a=p.parse_args()
W=a.width; input_shift=max(0,16-W);first_shift=max(0,17-W-input_shift)
assert 15<=W<=18
out=Path(a.out)
subprocess.run([sys.executable,str(Path(__file__).with_name('generate_fft.py')),'--width',str(W),'--frac',str(15-input_shift),'--twfrac',str(a.twfrac),'--scale-from','2','--rne','--fused','--mul',str(a.mul),'--compact-coeff','--out',str(out)],check=True)
s=out.read_text().replace('folded radix-2 DIT, parity-banked standard-cell storage.','folded radix-2 DIT, adaptive shared block exponent, parity banks.')
s=s.replace('wire signed [W-1:0] tr =','wire signed [W:0] tr =').replace('wire signed [W-1:0] ti =','wire signed [W:0] ti =')
for tag,src,rot,op in [('sr','ar','tr','+'),('si','ai','ti','+'),('dr','ar','tr','-'),('di','ai','ti','-')]:
 s=s.replace(f'wire signed [W:0] full_{tag}={{{src}[W-1],{src}}}{op}{{{rot}[W-1],{rot}}};', f'wire signed [W+1:0] full_{tag}={{{{2{{{src}[W-1]}}}},{src}}}{op}{{{rot}[W],{rot}}};')
for dst,src in [('sum_r','sr'),('sum_i','si'),('dif_r','dr'),('dif_i','di')]:
 s=re.sub(r'wire signed \[W-1:0\] '+dst+r' = [^;]+;',f'wire signed [W-1:0] {dst} = quantize(full_{src},current_shift);',s)
extra='''
    // A shared exponent changes only between complete butterfly stages.
    // The magnitude flags conservatively bound the next butterfly by 3*M.
    reg [1:0] current_shift;
    reg [3:0] exponent;
    reg peak_hi,peak_lo;
    function automatic signed [W-1:0] quantize;
        input signed [W+1:0] v;
        input [1:0] sh;
        reg signed [W+1:0] q;
        begin
            case (sh)
                0: q=v;
                1: q=(v >>> 1)+(v[0]&v[1]);
                default: q=(v >>> 2)+(v[1]&(v[0]|v[2]));
            endcase
            quantize=q[W-1:0];
        end
    endfunction
    wire flag_hi=(sum_r[W-1]^sum_r[W-2]) | (sum_i[W-1]^sum_i[W-2]) |
                 (dif_r[W-1]^dif_r[W-2]) | (dif_i[W-1]^dif_i[W-2]);
    wire flag_lo=(sum_r[W-1]^sum_r[W-3]) | (sum_i[W-1]^sum_i[W-3]) |
                 (dif_r[W-1]^dif_r[W-3]) | (dif_i[W-1]^dif_i[W-3]);
    wire hi=peak_hi|flag_hi, lo=peak_lo|flag_lo;
    wire [1:0] next_shift=(stage==0) ? (hi ? 2'd1 : 2'd0) :
                            (hi ? 2'd2 : (lo ? 2'd1 : 2'd0));
    always @(posedge clk) begin
        if (rst) begin current_shift<=FIRST_SHIFT; exponent<=INITIAL_EXP; peak_hi<=0; peak_lo<=0; end
        else if (state==IDLE && in_valid && frame_start) begin
            current_shift<=FIRST_SHIFT; exponent<=INITIAL_EXP; peak_hi<=0; peak_lo<=0;
        end else if ((state==LOAD && sample[5] && in_valid) || state==CALC) begin
            if ((state==LOAD && sample==63) || (state==CALC && butterfly==31)) begin
                peak_hi<=0; peak_lo<=0;
                if (stage<5) begin current_shift<=next_shift; exponent<=exponent+next_shift; end
            end else begin peak_hi<=hi; peak_lo<=lo; end
        end
    end
    wire signed [W-1:0] output_r=(^sample)?r1:r0, output_i=(^sample)?i1:i0;
'''.replace('FIRST_SHIFT',str(first_shift)).replace('INITIAL_EXP',str(first_shift+input_shift))
s=s.replace('    reg [2:0] stage;', '    reg [2:0] stage;\n    reg [1:0] current_shift;\n    reg [3:0] exponent;\n    reg peak_hi,peak_lo;')
extra=extra.replace('    reg [1:0] current_shift;\n    reg [3:0] exponent;\n    reg peak_hi,peak_lo;\n','')
s=s.replace('    reg we0,we1;',extra+'\n    reg we0,we1;')
s=re.sub(r'out_re<=\$signed\(sum_r\) \* \d+;', 'out_re<=$signed({{(24-W){sum_r[W-1]}},sum_r}) <<< exponent;',s)
s=re.sub(r'out_im<=\$signed\(sum_i\) \* \d+;', 'out_im<=$signed({{(24-W){sum_i[W-1]}},sum_i}) <<< exponent;',s)
s=re.sub(r'out_re <= \$signed\(\(\^sample\)\?r1:r0\) \* \d+;', 'out_re <= $signed({{(24-W){output_r[W-1]}},output_r}) <<< exponent;',s)
s=re.sub(r'out_im <= \$signed\(\(\^sample\)\?i1:i0\) \* \d+;', 'out_im <= $signed({{(24-W){output_i[W-1]}},output_i}) <<< exponent;',s)
out.write_text(s)
