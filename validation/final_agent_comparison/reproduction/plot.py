"""Plot only measured current designs; future models stay out of the figures."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(Path('/tmp/fft_final_agent_review_path.txt').read_text().strip())


def main():
    rows=json.loads((ROOT/'analysis/summary.json').read_text())['completed_designs']
    labels=['Claude\nDS-Flash','Codex 6.1\nSol-Max','Codex 6.2\nSol-Max']
    x=np.arange(len(rows));colors=['#4c78a8','#f58518','#54a24b']
    plt.rcParams.update({'font.size':11,'pdf.fonttype':42,'ps.fonttype':42})
    figure,axes=plt.subplots(2,2,figsize=(11.5,8))
    a=axes[0,0]
    seq=[r['sequential_cell_area_um2']for r in rows];comb=[r['combinational_cell_area_um2']for r in rows]
    a.bar(x,seq,label='Sequential cells',color='#9ecae9')
    a.bar(x,comb,bottom=seq,label='Combinational cells',color='#3182bd')
    a.set_ylabel('Full mapped area (μm²)');a.legend(fontsize=9)
    a=axes[0,1]
    a.bar(x,[r['throughput_ffts_per_second']/1e6 for r in rows],color=colors)
    a.set_ylabel('Certified capability (million FFT/s)')
    a=axes[1,0]
    a.bar(x,[r['first_output_cycles']for r in rows],color=colors)
    a.set_ylabel('Worst first output (cycles at 10 ns)')
    a=axes[1,1];bottom=np.zeros(3)
    for key,weight,color,label in [('area_component',.6,'#4c78a8','Area ×0.60'),
                                 ('throughput_component',.3,'#f58518','Throughput ×0.30'),
                                 ('latency_component',.1,'#54a24b','Latency ×0.10')]:
        values=np.array([r[key]*weight for r in rows]);a.bar(x,values,bottom=bottom,color=color,label=label);bottom+=values
    for i,r in enumerate(rows):a.text(i,r['score']+.015,f"{r['score']:.4f}",ha='center')
    a.set_ylabel('Verified combined hardware score');a.set_ylim(0,1);a.legend(fontsize=9)
    for axis in axes.flat:
        axis.set_xticks(x,labels);axis.grid(axis='y',alpha=.2);axis.set_axisbelow(True)
    figure.suptitle('Current FFT64 submissions: hardware and fixed-score contributions',fontsize=15)
    figure.text(.5,.018,'N=64, external P=1 | SQNR≥50 dB | ASAP7 RVT/TT | common hidden protocol | pre-layout / ideal-interconnect STA',ha='center',fontsize=9)
    figure.tight_layout(rect=[0,.045,1,.95])
    out=ROOT/'analysis/figures';out.mkdir(exist_ok=True)
    figure.savefig(out/'hardware_and_score.png',dpi=220)
    figure.savefig(out/'hardware_and_score.pdf',metadata={'CreationDate':None,'ModDate':None})
    figure,axis=plt.subplots(figsize=(7,5))
    for row,color,label in zip(rows,colors,labels):
        axis.scatter(row['area_um2'],row['throughput_ffts_per_second']/1e6,s=110,color=color,label=label.replace('\n',' '))
        rightmost=row['area_um2']==max(r['area_um2']for r in rows)
        axis.annotate(f"II={row['verified_frame_ii']}, {row['minimum_hidden_sqnr_db']:.2f} dB",(row['area_um2'],row['throughput_ffts_per_second']/1e6),xytext=(-8 if rightmost else 8,-17),textcoords='offset points',ha='right'if rightmost else'left',fontsize=9)
    axis.set(xlabel='Full mapped cell area (μm²)',ylabel='Certified capability (million FFT/s)',title='Three measured design trade-offs')
    axis.legend();axis.grid(alpha=.2);axis.margins(x=.2,y=.18)
    figure.text(.5,.02,'FFT64, P=1 | identical QoR and technology | pre-layout | no claim of global Pareto optimality',ha='center',fontsize=8)
    figure.tight_layout(rect=[0,.05,1,1])
    figure.savefig(out/'area_throughput.png',dpi=220)
    figure.savefig(out/'area_throughput.pdf',metadata={'CreationDate':None,'ModDate':None})


if __name__=='__main__':main()
