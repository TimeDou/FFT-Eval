"""Measured score comparison and explicitly separate scorer-only controls."""
from pathlib import Path
import copy,csv,hashlib,json,sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'engine/fft64_benchmark/tools'))
from scoring import score_result,performance,make_calibration,normalized,profile_policy


def write_csv(path,rows):
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='')as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)


def main():
    campaign=json.loads((ROOT/'campaign.json').read_text())
    calibration=json.loads((ROOT/'calibration.json').read_text())
    out=ROOT/'analysis';out.mkdir(exist_ok=True)
    cases=[dict(c,result_path=ROOT/'measurements'/c['id']/'result.json')for c in campaign['cases']]
    supplemental=json.loads((ROOT/'supplementary_cases.json').read_text())
    for c in supplemental['cases']:
        cases.append(dict(c,name='Accurate folded FFT, '+('default ABC mapping'if c['id']=='abc_default'else'resyn2-style ABC mapping'),
            role='candidate',result_path=ROOT/'supplementary'/c['id']/'measurement/result.json'))
    rows=[];measured={}
    for case in cases:
        p=case['result_path']
        if not p.exists():raise RuntimeError('Candidate still pending: '+case['id'])
        result=json.loads(p.read_text());grade=score_result(result,calibration)
        if grade['evaluation_outcome']in ['INCOMPLETE','UNSCORED_INFRASTRUCTURE']:
            raise RuntimeError('Candidate not rankable: '+case['id']+' '+grade['reason'])
        perf=grade.get('performance',{});ppa=result.get('ppa',{});components=grade.get('components',{})
        row=dict(id=case['id'],name=case['name'],role=case['role'],resolved=grade['resolved'],score_valid=grade['score_valid'],
            score=grade['score'],status=result['status'],area_um2=ppa.get('area_um2'),
            min_sqnr_db=result.get('quality',{}).get('minimum_frame_sqnr_db'),
            period_ns=perf.get('certified_period_ns'),fmax_mhz=perf.get('certified_setup_fmax_MHz'),
            frame_ii=perf.get('verified_frame_II_cycles'),throughput_ffts_s=perf.get('effective_throughput_ffts_per_second'),
            first_output_cycles=perf.get('first_output_cycles'),latency_10ns_ns=perf.get('first_output_latency_ns'),
            latency_at_certified_period_ns=perf.get('first_output_latency_at_certified_clock_ns'),
            area_component=components.get('area'),throughput_component=components.get('throughput'),latency_component=components.get('latency'),
            weighted_area=.6*components.get('area',0),weighted_throughput=.3*components.get('throughput',0),weighted_latency=.1*components.get('latency',0),
            result_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),mapped_sha256=ppa.get('mapped_sha256'),
            physical_flow_id=ppa.get('physical_flow_id'),reason=grade['reason'])
        rows.append(row);measured[case['id']]=result
        (out/(case['id']+'_grade.json')).write_text(json.dumps(grade,indent=2)+'\n')
    write_csv(out/'measured_scores.csv',rows)
    base=measured['exact_folded'];base_grade=score_result(base,calibration);controls=[]
    for hint in [64,128,320,384]:
        result=copy.deepcopy(base);result.setdefault('source',{})['frame_ii_cycles']=hint
        grade=score_result(result,calibration)
        controls.append(dict(kind='SCORER_REPLAY_ONLY',control='agent_claimed_ii',value=hint,score=grade['score'],
            score_valid=grade['score_valid'],expected='same score as measured exact folded',pass_check=grade['score']==base_grade['score']))
    for db in [50.,60.,100.]:
        result=copy.deepcopy(base);result['quality']['minimum_frame_sqnr_db']=db
        grade=score_result(result,calibration)
        controls.append(dict(kind='SCORER_REPLAY_ONLY',control='sqnr_above_threshold_no_bonus',value=db,score=grade['score'],
            score_valid=grade['score_valid'],pass_check=grade['score']==base_grade['score']))
    for name in ['informational_frequency_estimate','producer_reported_area']:
        result=copy.deepcopy(base)
        if name=='informational_frequency_estimate':result['ppa']['prelayout_fmax_estimate_MHz']=999999.
        else:result.setdefault('source',{})['producer_reported_area_um2']=1.
        grade=score_result(result,calibration)
        controls.append(dict(kind='SCORER_REPLAY_ONLY',control=name,score=grade['score'],
            score_valid=grade['score_valid'],pass_check=grade['score']==base_grade['score'],
            expected='Informational claim cannot replace measured cells or the existing STA certificate'))
    bad_calibration=copy.deepcopy(calibration);bad_calibration['policy_sha256']='not-the-frozen-policy'
    grade=score_result(base,bad_calibration)
    controls.append(dict(kind='SCORER_REPLAY_ONLY',control='mismatched_calibration',score=grade['score'],
        score_valid=grade['score_valid'],pass_check=not grade['score_valid'],expected='exclude from ranking'))
    result=copy.deepcopy(base);result.update(status='UNSCORED_INFRASTRUCTURE',failure='Injected scorer control; not a real tool fault')
    grade=score_result(result,calibration)
    controls.append(dict(kind='SCORER_REPLAY_ONLY',control='infrastructure_outcome',score=grade['score'],
        score_valid=grade['score_valid'],pass_check=not grade['score_valid'],expected='exclude from ranking'))
    assert all(c['pass_check']for c in controls)
    write_csv(out/'scorer_controls.csv',controls)

    accurate={k:measured[k]for k in campaign['calibration_designs']}
    area_calibration=make_calibration(accurate,'area')
    profiles=[]
    for row in rows:
        result=copy.deepcopy(measured[row['id']]);result['profile']='area'
        grade=score_result(result,area_calibration)
        profiles.append(dict(id=row['id'],kind='DERIVED_DIAGNOSTIC_FROM_MEASURED_HARDWARE',
            architecture_score=row['score'],area_profile_score=grade['score'],area_profile_valid=grade['score_valid'],
            warning='Separate objectives/calibrations; never mix profiles in one ranking'))
    write_csv(out/'profile_comparison.csv',profiles)

    refs=calibration['references'];targets=calibration['targets'];sensitivity=[]
    for row in rows:
        if not row['resolved']:continue
        cert=measured[row['id']]['ppa']['fmax_certificate'];passing=cert['passing_period_ns'];failing=cert['failing_period_ns']
        throughput_high=1e9/(row['frame_ii']*failing)if failing else row['throughput_ffts_s']
        upper=.6*row['area_component']+.1*row['latency_component']+.3*normalized(throughput_high,
            refs['throughput_ffts_per_second'],targets['throughput_ffts_per_second'],False)
        sensitivity.append(dict(id=row['id'],kind='CLOCK_GRID_SENSITIVITY_BOUND_NOT_AN_ALTERNATE_VALID_SCORE',
            measured_score=row['score'],conservative_passing_period_ns=passing,failing_period_ns=failing,
            upper_bound_from_scan_bracket=upper,maximum_clock_grid_score_span=upper-row['score']))
    write_csv(out/'clock_grid_sensitivity.csv',sensitivity)
    feasible=[r for r in rows if r['resolved']and r['score_valid']]
    scores=[r['score']for r in feasible]
    summary=dict(status='COMPLETE',measured_cases=rows,scorer_controls_passed=all(c['pass_check']for c in controls),
        feasible_count=len(feasible),valid_invalid_count=sum(r['score_valid']and not r['resolved']for r in rows),
        score_min=min(scores),score_max=max(scores),score_range=max(scores)-min(scores),
        unique_scores_at_6dp=len({round(s,6)for s in scores}),
        area_floor_cases=[r['id']for r in feasible if r['area_component']==0],
        area_saturated_cases=[r['id']for r in feasible if r['area_component']==1],
        throughput_saturated_cases=[r['id']for r in feasible if r['throughput_component']==1],
        calibration_references=refs,calibration_targets=targets,
        quality_scope='8192 independent hidden random frames plus 192 directed, mandatory service, all 321 II values x 1024 RTL frames, representative mapped checks; finite empirical validation',
        implementation_scope='Same frozen engine, library, corner, input protocol and measurement flow; pre-layout ideal-interconnect STA',
        policy_changed_to_separate_scores=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items()if k!='measured_cases'},indent=2))
    figures(out,feasible,calibration)


def figures(out,rows,calibration):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42})
    names=dict(exact_folded='Folded: accurate',exact_sdf='R2SDF: accurate',twiddle9_folded='Folded: Q9 twiddles',
        quantized_banked='Banking + precision',pipelined_folded='Folded: pipelined',timing2ns_folded='DC: 2 ns synthesis',
        abc_default='ABC: default',abc_resyn2='ABC: resyn2-style')
    rows=sorted(rows,key=lambda r:r['score']);labels=[names[r['id']]for r in rows];y=np.arange(len(rows))
    fig,ax=plt.subplots(figsize=(7.4,4.2));left=np.zeros(len(rows))
    for field,label,color in [('weighted_area','Area (60%)','#4477aa'),('weighted_throughput','Throughput (30%)','#228833'),('weighted_latency','Latency (10%)','#ccbb44')]:
        values=np.array([r[field]for r in rows]);ax.barh(y,values,left=left,label=label,color=color);left+=values
    ax.set(yticks=y,yticklabels=labels,xlabel='Calibrated architecture score',xlim=(0,1))
    for i,row in enumerate(rows):ax.text(row['score']+.012,i,f"{row['score']:.4f}",va='center',fontsize=8)
    ax.legend(loc='lower right',frameon=False);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    fig.suptitle('FFT64 | ASAP7 RVT/TT | measured VCS/DC/PrimeTime')
    fig.text(.5,.008,'External P=1 | SQNR >= 50 dB | 10 ns required | pre-layout, ideal interconnect | accurate-reference calibration',ha='center',fontsize=6.3)
    fig.tight_layout(rect=(0,.045,1,1));fig.savefig(out/'score_components.pdf');fig.savefig(out/'score_components.png',dpi=300);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(10,3.2))
    fields=[('area_um2','Mapped area (um2)'),('throughput_ffts_s','Effective throughput (FFT/s)'),('first_output_cycles','Max first-output latency (cycles)')]
    for ax,(field,label)in zip(axes,fields):
        for i,row in enumerate(rows):ax.scatter(row[field],row['score'],s=35);ax.annotate(str(i+1),(row[field],row['score']),xytext=(4,3),textcoords='offset points',fontsize=7)
        ax.set(xlabel=label,ylabel='Architecture score');ax.grid(alpha=.2)
    fig.suptitle('Pre-layout hardware measurements; input/output P=1; common 10 ns service contract')
    fig.text(.5,.008,'N=64 | ASAP7 RVT/TT | SQNR >= 50 dB | VCS/DC/PrimeTime | symbols numbered in ascending score order',ha='center',fontsize=6.3)
    fig.tight_layout(rect=(0,.05,1,1));fig.savefig(out/'hardware_vs_score.pdf');fig.savefig(out/'hardware_vs_score.png',dpi=300);plt.close(fig)
    refs=calibration['references'];goals=calibration['targets'];fig,axes=plt.subplots(1,3,figsize=(9,2.8))
    spec=[('area_um2',True,.25,2.,'Area / accurate reference'),('throughput_ffts_per_second',False,0,1.5,'Throughput / frozen target'),('first_output_latency_ns',True,63/300,1.,'Latency / mandatory deadline')]
    for ax,(key,lower,start,end,label)in zip(axes,spec):
        denominator=refs[key]if lower else goals[key];x=np.linspace(start,end,301)
        ax.plot(x,[normalized(t*denominator,refs[key],goals[key],lower)for t in x],color='#4477aa')
        ax.set(xlabel=label,ylabel='Normalized component',ylim=(-.03,1.03));ax.grid(alpha=.2)
    fig.suptitle('Analytical score transfer functions; no additional hardware results')
    fig.tight_layout();fig.savefig(out/'normalization_sensitivity.pdf');fig.savefig(out/'normalization_sensitivity.png',dpi=300);plt.close(fig)


if __name__=='__main__':main()
