"""Reproduce the analytical score curves from the public policy alone."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
policy = json.loads((ROOT/'profiles/policy.json').read_text())
p = policy['public_normalization']
plt.rcParams.update({'font.size': 13, 'pdf.fonttype': 42, 'ps.fonttype': 42})
fig, axes = plt.subplots(1, 3, figsize=(18, 5.8))
area = np.linspace(p['area_ideal_um2'], 16000, 500)
score = np.minimum(1, (p['area_half_credit_um2']-p['area_ideal_um2'])/
                   (area+p['area_half_credit_um2']-2*p['area_ideal_um2']))
axes[0].plot(area, score, lw=2.5)
axes[0].axvline(p['area_half_credit_um2'], color='0.5', ls='--', lw=1.3)
axes[0].set(xlabel='Mapped area (μm²)', ylabel='Area component', xticks=[0, 4000, 8000, 12000, 16000])
axes[0].xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
throughput = np.geomspace(p['throughput_min_ffts_per_second'], p['throughput_ideal_ffts_per_second'], 500)
axes[1].semilogx(throughput/1e6, np.log(throughput/p['throughput_min_ffts_per_second'])/
                np.log(p['throughput_ideal_ffts_per_second']/p['throughput_min_ffts_per_second']), lw=2.5)
axes[1].set(xlabel='Throughput (million FFT/s)', ylabel='Throughput component',
            xticks=[p['throughput_min_ffts_per_second']/1e6, 1, 4, 16, 62.5],
            xticklabels=['0.2604', '1', '4', '16', '62.5'])
latency = np.linspace(p['first_output_ideal_cycles'], p['first_output_max_cycles'], 500)
axes[2].plot(latency, (p['first_output_max_cycles']-latency)/
             (p['first_output_max_cycles']-p['first_output_ideal_cycles']), lw=2.5)
axes[2].set(xlabel='First-output latency (cycles)', ylabel='Latency component',
            xticks=[63, 100, 150, 200, 250, 300])
for ax in axes:
    ax.set_ylim(-0.02, 1.05)
    ax.grid(alpha=0.2)
fig.suptitle('Public score normalization | area 60%, throughput 30%, latency 10%', fontsize=18, y=0.98)
fig.text(0.5, 0.025, 'Analytical curves, not new hardware measurements | FFT64, P=1 | ASAP7 RVT/TT | '
         '10 ns service contract | pre-layout scoring', ha='center', fontsize=11)
fig.subplots_adjust(left=0.055, right=0.985, bottom=0.22, top=0.85, wspace=0.30)
fig.savefig(ROOT/'normalization.png', dpi=200)
fig.savefig(ROOT/'normalization.pdf', metadata={'CreationDate': None, 'ModDate': None})
