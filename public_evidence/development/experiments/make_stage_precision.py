from pathlib import Path
p=Path('experiments/R002/rtl/fft64_top.sv');s=p.read_text()
start=s.index('wire v1,s1;');end=s.index('// Single reorder memory')
lines=[];widths=[15,16,16,17,17,18]
for st,w in enumerate(widths):
 ow=w+1;down=st in [1,3]
 lines.append(f'wire v{st+1},s{st+1};wire signed[{ow-1-(1 if down else 0)}:0] dr{st+1},di{st+1};')
 if down:lines.append(f'wire signed[{ow-1}:0] raw_re{st},raw_im{st};')
 ore=f'raw_re{st}'if down else f'dr{st+1}';oim=f'raw_im{st}'if down else f'di{st+1}'
 lines.append(f'fft64_sdf_stage #(.LG({5-st}),.IW({w}),.TF(9),.FIRST({1 if st%2==0 else 0})) stage{st}(.clk(clk),.rst(rst),.iv(v{st}),.ifs(s{st}),.ir(dr{st}),.ii(di{st}),.ov(v{st+1}),.ofs(s{st+1}),.ore({ore}),.oim({oim}));')
 if down:
  lines.append(f"wire signed[{ow}:0] round_re{st}=$signed(raw_re{st})+1,round_im{st}=$signed(raw_im{st})+1;\nassign dr{st+1}=round_re{st}>>>1;assign di{st+1}=round_im{st}>>>1;")
s=s[:start]+'\n'.join(lines)+'\n'+s[end:]
s=s.replace('reg signed[20:0] mem_re','reg signed[18:0] mem_re').replace('$signed(mem_re[ra])*2','$signed(mem_re[ra])*8').replace('$signed(mem_im[ra])*2','$signed(mem_im[ra])*8')
p.write_text(s)
