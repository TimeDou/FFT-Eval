"""Render the collected native area and architecture scores (no new measurements)."""
from pathlib import Path
import argparse
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('results');args=p.parse_args()
    root=Path(args.results)
    area=json.loads((root/'area/results.json').read_text())['measurements']
    arch=json.loads((root/'architecture/results.json').read_text())['measurements']
    order=['sdf','iterative','fft64_solution'];labels=['Accurate R2SDF\n(frame-isolated)','Accurate folded\nradix-2','Quantized banked\nradix-2']
    area={r['design']:r for r in area};arch={r['design']:r for r in arch}
    if not all(area[k]['resolved']and arch[k]['resolved']for k in order):raise ValueError('Only validated rows belong in this score figure')
    plt.rcParams.update({'font.size':10,'pdf.fonttype':42,'ps.fonttype':42})
    fig,axes=plt.subplots(1,2,figsize=(10,4.1),sharey=True,constrained_layout=True)
    x=np.arange(3);axes[0].bar(x,[area[k]['score']for k in order],color='#3679ad',width=.58)
    axes[0].set_title('Area profile\n100% area')
    bottom=np.zeros(3)
    for key,weight,label,color in [('area_component',.6,'Area contribution','#3679ad'),('throughput_component',.3,'Throughput contribution','#e9a23b'),('latency_component',.1,'Latency contribution','#55996c')]:
        values=np.asarray([arch[k][key]*weight for k in order])
        axes[1].bar(x,values,bottom=bottom,width=.58,label=label,color=color);bottom+=values
    axes[1].set_title('Architecture profile\n60% area / 30% throughput / 10% latency')
    for ax,rows in zip(axes,[area,arch]):
        ax.set_xticks(x,labels);ax.set_ylim(0,1.05);ax.set_axisbelow(True);ax.grid(axis='y',alpha=.2)
        ax.spines[['top','right']].set_visible(False)
        for i,k in enumerate(order):ax.text(i,rows[k]['score']+.025,f"{rows[k]['score']:.3f}\nPASS",ha='center',fontsize=9)
    axes[0].set_ylabel('Hardware quality score (independent profile scales)')
    axes[1].legend(loc='upper right',fontsize=8,frameon=False)
    fig.suptitle('FFT64, P_in = P_out = 1, ASAP7 RVT/TT\nNative VCS/DC/PrimeTime; pre-layout area and ideal-interconnect STA',fontsize=11)
    fig.savefig(root/'score_comparison.pdf');fig.savefig(root/'score_comparison.png',dpi=240);plt.close(fig)

if __name__=='__main__':main()
