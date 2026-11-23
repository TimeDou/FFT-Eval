"""Generate paper-ready figures exclusively from the collected scalar tables."""
from pathlib import Path
from datetime import datetime
import csv
import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main(directory):
    base=Path(directory);out=base/'figures';out.mkdir(exist_ok=True)
    rows=json.loads((base/'final_metrics.json').read_text())
    search=json.loads((base/'opus_public_iterations.json').read_text())
    late=json.loads((base/'late_search_analysis.json').read_text())
    plt.rcParams.update({'font.size':10,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    labels=['Claude\nDS-Flash','Codex 6.1\nSol-Max','Codex 6.2\nSol-Max','Claude\nOpus 5.5']
    colors=['#4c78a8','#f58518','#54a24b','#b279a2'];x=np.arange(4)
    def write(figure,name):
        figure.savefig(out/(name+'.png'),dpi=220)
        figure.savefig(out/(name+'.pdf'),metadata={'CreationDate':None,'ModDate':None})
        plt.close(figure)
    def grid(axis):axis.grid(axis='y',alpha=.18);axis.set_axisbelow(True)
    figure,axes=plt.subplots(2,2,figsize=(11.5,8))
    a=axes[0,0];seq=[r['sequential_cell_area_um2']for r in rows];comb=[r['combinational_cell_area_um2']for r in rows]
    a.bar(x,seq,color='#9ecae9',label='Sequential cells')
    a.bar(x,comb,bottom=seq,color='#3182bd',label='Combinational cells');a.legend(fontsize=8)
    a.set_ylabel('Complete mapped area (μm²)')
    a=axes[0,1];a.bar(x,[r['throughput_ffts_per_second']/1e6 for r in rows],color=colors)
    a.set_ylabel('STA-certified capability (million FFT/s)')
    a=axes[1,0];a.bar(x,[r['first_output_cycles']for r in rows],color=colors)
    a.set_ylabel('Worst first output (cycles at 10 ns)')
    a=axes[1,1];bottom=np.zeros(4)
    for field,color,label in [('weighted_area','#4c78a8','Area ×0.60'),('weighted_throughput','#f58518','Throughput ×0.30'),('weighted_latency','#54a24b','Latency ×0.10')]:
        value=np.array([r[field]for r in rows]);a.bar(x,value,bottom=bottom,color=color,label=label);bottom+=value
    for i,r in enumerate(rows):a.text(i,r['score']+.012,f"{r['score']:.4f}",ha='center',fontsize=10)
    a.set_ylabel('Independently validated final score');a.set_ylim(0,1);a.legend(fontsize=8)
    for axis in axes.flat:axis.set_xticks(x,labels);grid(axis)
    figure.suptitle('Four final FFT64 submissions under one fixed scoring protocol',fontsize=14)
    figure.text(.5,.012,'N=64, external P=1 | minimum SQNR≥50 dB | ASAP7 RVT/TT | pre-layout / ideal-interconnect STA',ha='center',fontsize=9)
    figure.tight_layout(rect=[0,.03,1,.95]);write(figure,'four_designs_hardware_score')

    figure,axes=plt.subplots(2,1,figsize=(10,7),sharex=False)
    for axis in axes:
        unique=[r for r in search if not r['confirmation_only']]
        times=[r['continuation_elapsed_hours']for r in unique]
        scores=[r['score']for r in unique]
        axis.step([r['continuation_elapsed_hours']for r in search],[r['best_public_score_so_far']for r in search],where='post',color='#4c78a8',label='Best completed public score')
        axis.scatter(times,scores,color='#4c78a8',s=32,zorder=3,label='Self-evaluated implementation')
        confirmations=[r for r in search if r['confirmation_only']]
        axis.scatter([r['continuation_elapsed_hours']for r in confirmations],[r['score']for r in confirmations],
                     facecolors='none',edgecolors='#666666',s=55,zorder=4,label='Installed-copy confirmation')
        axis.axvline(6,ls='--',color='#e45756',lw=1,label='6 h in observed continuation window')
        origin=datetime.fromisoformat(late['time_origin_utc'].replace('Z','+00:00'))
        stop=datetime.fromisoformat(late['stopping_instruction']['timestamp'].replace('Z','+00:00'))
        axis.axvline((stop-origin).total_seconds()/3600,ls=':',color='#555555',lw=1,label='User stop instruction')
        axis.set_ylabel('Public hardware score');grid(axis)
    axes[0].set_xlim(2.6,6.65);axes[0].set_ylim(.7455,.7580)
    axes[0].legend(loc='lower right',fontsize=8)
    for r in unique:
        if r['iteration']in {'E008','E016','E024_554','E030','E032'}:
            axes[0].annotate(r['iteration'],(r['continuation_elapsed_hours'],r['score']),xytext=(0,8),textcoords='offset points',ha='center',fontsize=8)
    axes[1].set_xlim(5.1,6.65);axes[1].set_ylim(.7555,.7571)
    axes[1].set_title('Late window: zoomed score scale',fontsize=10)
    axes[1].text(.03,.90,f"After 6 h: +{late['public_score_increment_after_six_hours']:.6f} completed-score increment",transform=axes[1].transAxes,fontsize=10)
    axes[1].set_xlabel('Hours since observed post-gap continuation (2026-11-23 00:01:15 UTC)')
    figure.suptitle('Opus iteration trajectory and diminishing late improvements',fontsize=14)
    figure.text(.5,.012,'Intermediate points accepted from Agent records; not independently rerun | final implementation independently hidden-validated',ha='center',fontsize=8)
    figure.tight_layout(rect=[0,.035,1,.95]);write(figure,'opus_convergence')

    figure,axes=plt.subplots(1,2,figsize=(11,4.6));a=axes[0]
    short=['DS-Flash','Codex 6.1','Codex 6.2','Opus 5.5']
    for r,color,label in zip(rows,colors,short):
        a.scatter(r['user_reported_seconds']/3600,r['score'],s=65,color=color)
        a.annotate(label,(r['user_reported_seconds']/3600,r['score']),xytext=(6,4),textcoords='offset points',fontsize=9)
    a.set(xlabel='User-reported dialogue time (hours)',ylabel='Final hardware score',xlim=(0,7.5),ylim=(.55,.79))
    a.grid(alpha=.18)
    a=axes[1];a.bar(x,[r['minimum_hidden_sqnr_db']for r in rows],color=colors)
    a.axhline(50,color='#333333',lw=1,ls='--',label='Common feasibility threshold')
    a.set_xticks(x,short,rotation=15);a.set_ylabel('Minimum hidden per-frame SQNR (dB)');a.set_ylim(0,75);a.legend(fontsize=8);grid(a)
    figure.suptitle('Observed run duration and numerical margin',fontsize=14)
    figure.text(.5,.012,'One run per label, unequal durations and stopping conditions; no equal-budget model-efficiency inference',ha='center',fontsize=8)
    figure.tight_layout(rect=[0,.04,1,.93]);write(figure,'time_and_quality')

    figure,axis=plt.subplots(figsize=(7.5,5))
    for r,color,label in zip(rows,colors,short):
        axis.scatter(r['area_um2'],r['throughput_ffts_per_second']/1e6,s=85,color=color,label=label)
        rightmost=r['area_um2']==max(q['area_um2']for q in rows)
        axis.annotate(f"II={r['verified_frame_ii']}",(r['area_um2'],r['throughput_ffts_per_second']/1e6),
                      xytext=(-7 if rightmost else 7,-14),textcoords='offset points',ha='right'if rightmost else'left',fontsize=9)
    axis.set(xlabel='Complete mapped cell area (μm²)',ylabel='STA-certified capability (million FFT/s)',title='Four feasible delivered circuits')
    axis.legend();axis.grid(alpha=.18);axis.margins(x=.12,y=.16)
    figure.text(.5,.015,'FFT64, P=1 | SQNR≥50 dB | pre-layout | circuit comparison, not a global optimum or model-wide ranking',ha='center',fontsize=8)
    figure.tight_layout(rect=[0,.04,1,1]);write(figure,'four_designs_area_throughput')

    public_file=base/'exploration_public_candidates.csv'
    if public_file.exists():
        with public_file.open()as stream:public=list(csv.DictReader(stream))
        figure,axis=plt.subplots(figsize=(9,5))
        for row,color,label in zip(rows,colors,short):
            series=[r for r in public if r['agent']==row['agent']]
            series.sort(key=lambda r:int(r['completed_public_evaluation_index']))
            indices=[int(r['completed_public_evaluation_index'])for r in series]
            axis.plot(indices,[float(r['best_score_so_far'])for r in series],color=color,label=label,lw=1.6)
            axis.scatter(indices,[float(r['score'])for r in series],color=color,s=25,alpha=.8)
        axis.set(xlabel='Completed full public evaluation index (within each run)',ylabel='Public hardware score',
                 title='Exploration records: reported candidates and best score so far',ylim=(.53,.78))
        axis.set_xticks(range(1,12));axis.legend();axis.grid(alpha=.18)
        figure.text(.5,.015,'Unequal pre-screening, runtimes and confirmations; this index is not a matched-compute or model-efficiency comparison',ha='center',fontsize=8)
        figure.tight_layout(rect=[0,.04,1,1]);write(figure,'four_search_trajectories')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',nargs='?')
    args=parser.parse_args()
    if args.directory:directory=args.directory
    elif os.environ.get('FFT_REVIEW_DATA'):directory=os.environ['FFT_REVIEW_DATA']
    else:directory=Path(json.loads((Path(__file__).parent/'state.json').read_text())['root'])/'analysis'
    main(directory)
