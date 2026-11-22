from pathlib import Path
import json,hashlib,shutil
root=Path.cwd();sub=root/'submission';selection=json.loads((sub/'frozen_selection.json').read_text());best=selection['candidate'];r=json.loads((sub/'public_verification.json').read_text());g=r['grade'];perf=g['performance'];names=['F003','S001','S003','R001','C001','C002','C003','C004','C005','C006','C007']
results={}
for n in names:
 p=root/'runs'/('arch_'+n)/'result.json'
 if p.exists():
  v=json.loads(p.read_text())
  if v.get('status')=='COMPLETE' and v.get('grade',{}).get('resolved') and v['grade'].get('score_valid'):results[n]=v
assert best in results and g['score']==max(x['grade']['score']for x in results.values())
qall=[]
for p in (root/'runs').glob('*/result.json'):
 d=json.loads(p.read_text())
 if d.get('source',{}).get('source_sha256')==selection['source_sha256'] and d.get('quality',{}).get('minimum_frame_sqnr_db')is not None:qall.append((p.parent.name,d['quality']['minimum_frame_sqnr_db']))
worst=min(x[1]for x in qall)
old=root/'experiments/DESIGN_PLAN_history.md'
if not old.exists():shutil.copy2(sub/'DESIGN_PLAN.md',old)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=[]
def e(x=''):s.append(x)
e('# FFT64-Quant: design and measured selection')
e('')
e('## Objective and constraints')
e('')
e('Architecture profile: S=0.60*S_A+0.30*S_T+0.10*S_L, with S_A=clip(3500/(A+3000)), S_T=clip(ln(T/260416.66666666666)/ln(240)), S_L=clip((300-L)/237). All values below are commercial public previews using the fixed ASAP7 RVT/TT libraries; none is an official hidden grade. SQNR above 50 dB has no score bonus. The 500 um2, 62.5 M FFT/s and 63-cycle scales are aspirational anchors.')
e('')
e('Mandatory contract: complete 64-point forward unscaled FFT, natural input/output, signed 16-bit input and 24-bit output with 15 fractional bits; each tested nonzero frame >=50 dB, exact zero frame; synchronous high reset aborts inflight work; 64 consecutive outputs, 384-cycle service, first output<=300 and last<=364, setup and hold at 10 ns.')
e('')
e('## Initial competing hypotheses and numerical screens')
e('')
e('- Folded radix2 with one shared butterfly minimizes arithmetic, but bank muxes and 192 compute cycles can lose throughput and latency credit.')
e('- Two shared butterflies with four parity banks trade duplicated arithmetic for 96 compute cycles and shorter bank muxes.')
e('- Streaming SDF can earn enough II/frequency credit to justify more storage and arithmetic; radix2-squared pairing and a single alternating reorder buffer may limit its area cost.')
e('')
e('F001 used 20-bit Q13 storage and Q13 twiddles with truncation; numerical screen failed at 48.353385 dB. F002 rounded inputs/products and passed at 50.620292 dB, first/last 256/319. Its complete area diagnostic passed mapped checks at 1767.56256 um2; no combined architecture score is claimed. F003 used two butterflies, four parity banks, Q14 data and Q11 twiddles. F004 replaced four real products by three exact products; area fell from 2213.14194 to 2108.98242 um2 but fixed-clock STA path estimate worsened from 3.6779 to 4.3187 ns. The diagnostic alone did not justify selecting F004; it has no full combined score.')
e('')
e('S002 began natural-order reads 14 cycles sooner than S001. S003 reduced coefficient precision to 9 fractional bits. R001 paired radix2 stages into radix2-squared, removing two nontrivial complex multipliers. R002 tried half-up stage rounding at Q14->Q13->Q12 and passed at 51.304864 dB; R003 changed input and stage boundaries to nearest-even and passed at 53.254771 dB. R004 predecoded coefficients and registered three exact real products; numerical output stayed the same, with two added cycles. R005/C005 tested one-hot output memory reads. R006/C006 and R007/C007 quantized only final reorder storage to Q10 and Q11 respectively. The Q10 screen passed at 50.220814 dB; independent public-seed 8192-frame screens gave 50.284084 dB (Q10) and 51.954103 dB (Q11). These are public development inputs, not hidden evaluation data.')
e('')
e('## Complete architecture measurements')
e('')
e('| Candidate | Area um2 | Worst SQNR dB | Verified II | Certified ns | First / last cycles | Public score |')
e('|---|---:|---:|---:|---:|---:|---:|')
for n,v in results.items():
 p=v['grade']['performance'];q=v['quality']['minimum_frame_sqnr_db'];lat=v['latency']
 e(f"| {n}{' (selected)'if n==best else ''} | {p['area_um2']:.5f} | {q:.6f} | {p['verified_frame_II_cycles']} | {p['certified_period_ns']:.9f} | {lat['maximum_first_output_latency_cycles']} / {lat['maximum_frame_completion_cycles']} | {v['grade']['score']:.9f} |")
e('')
e('All full runs use 1024 independent random frames plus 192 directed frames, 1024-frame continuous mandatory service, all 321 integer IIs 64..384 with 1024 consecutive RTL frames each, representative mapped comparisons from initial modes 0, 1, 20261121, and fixed-netlist PrimeTime clock scans. The smallest passing II is independently measured. Failed optional intervals are not mandatory violations. Quick screens and area diagnostics are separate rows in measurements.csv and have no combined score.')
e('')
e('## Weighted decisions')
e('')
e('| Comparison | 0.60 delta area | 0.30 delta throughput | 0.10 delta latency | Delta total |')
e('|---|---:|---:|---:|---:|')
for a,b in [('F003','S001'),('S001','S003'),('S003','R001'),('S003','C001'),('R001','C002'),('C002','C003'),('C003','C004'),('C004','C005'),('C005','C006'),('C005','C007')]:
 if a in results and b in results:
  x,y=results[a]['grade'],results[b]['grade'];d={k:y['weighted_components'][k]-x['weighted_components'][k]for k in ['area','throughput','latency']}
  e(f"| {a} -> {b} | {d['area']:+.9f} | {d['throughput']:+.9f} | {d['latency']:+.9f} | {y['score']-x['score']:+.9f} |")
e('')
e('Choose the highest completed feasible combined preview, even when another candidate has lower area, more SQNR or shorter latency. All selected score components are below saturation; II 64 is already the lower boundary of the tested serial-interface range.')
e('')
e('The narrower final buffers were retained only as experiments: fewer storage bits do not imply smaller complete mapped area. Their rounding logic and resulting timing-driven mapping must be included. The selected design is chosen by the full combined score, with no SQNR bonus.')
e('')
e('## Final implementation')
e('')
e(f"Selected **{best}**, score **{g['score']:.12f}**, resolved=true, score_valid=true, scoring_scope=public_preview, official_score=false. Mapped area {perf['area_um2']:.9f} um2; II {perf['verified_frame_II_cycles']}; certified period {perf['certified_period_ns']:.12f} ns; effective throughput {perf['effective_throughput_ffts_per_second']:.3f} FFT/s; worst first/last {r['latency']['maximum_first_output_latency_cycles']}/{r['latency']['maximum_frame_completion_cycles']} cycles. Minimum SQNR across all matching-source public runs is {worst:.9f} dB. Zero-frame output is exact.")
e('')
e(f"Final components: S_A={g['components']['area']:.12f}, S_T={g['components']['throughput']:.12f}, S_L={g['components']['latency']:.12f}. Weighted contributions are {g['weighted_components']['area']:.12f}, {g['weighted_components']['throughput']:.12f}, {g['weighted_components']['latency']:.12f} respectively.")
e('')
e('The final radix2-squared SDF pipeline has feedback depths 32, 16, 8, 4, 2, 1 complex samples. For each paired group a=x0+x2, b=x1+x3, c=x0-x2, d=x1-x3: the first stage applies only exact -j to d; the second forms a+b, a-b, c-j*d, c+j*d in four quarters, followed by twiddle exponents 0, 2*j, j, 3*j. There are two nontrivial complex rotations. Each uses three exact real products with no intermediate quantization, registered coefficients/products, and one post-product quantization boundary.')
e('')
precision={'C001':'Uniform Q14 internal data and 21-bit Q14 reorder storage, Q9 twiddles.','C002':'Uniform Q14 internal data and 21-bit Q14 reorder storage, Q9 twiddles.','C003':'Nearest-even Q15->Q14 at input, Q14->Q13 after stage 2 and Q13->Q12 after stage 4; 19-bit Q12 final reorder storage; outputs shift left 3 into external Q15.','C004':'Nearest-even Q15->Q14 at input, Q14->Q13 after stage 2 and Q13->Q12 after stage 4; 19-bit Q12 final reorder storage; outputs shift left 3 into external Q15.','C005':'Nearest-even Q15->Q14 at input, Q14->Q13 after stage 2 and Q13->Q12 after stage 4; 19-bit Q12 final reorder storage; outputs shift left 3 into external Q15.','C006':'Nearest-even Q15->Q14 at input, Q14->Q13 after stage 2, Q13->Q12 after stage 4, and Q12->Q10 before the 17-bit final reorder memory. Output reconstruction shifts left 5 into signed 24-bit Q15.','C007':'Nearest-even Q15->Q14 at input, Q14->Q13 after stage 2, Q13->Q12 after stage 4, and Q12->Q11 before the 18-bit final reorder memory. Output reconstruction shifts left 4 into signed 24-bit Q15.'}
e(precision.get(best,'See matching RTL.'))
e('A guard bit is added at each butterfly. Twiddle factors have 9 fractional bits in signed 10-bit coefficients; unit and quarter rotations bypass multiplication exactly. Fixed-point representation shifts preserve external FFT gain. Products use half-up nearest rounding, while the explicitly named narrowing boundaries use nearest-even. No gate pruning or approximate arithmetic compressors are used.')
e('')
e('Natural-order output uses one 64-word complex flop memory. Successive frames alternate sequential and bit-reversed write addresses; each following frame overwrites in the preceding read order, safely supporting II 64 without a second frame buffer. Since max(bit_reverse(k)-k)=49, the first read at offset 50 is safe and yields one 64-cycle output burst. All buffers, read/write muxes, coefficient logic and control are counted.')
e('')
e('All state uses the specified positive-edge clock. Reset clears valid/start chains, counters and reorder state; data arrays need no reset because a fresh complete transaction overwrites each valid datum before use. Long idle gaps do not advance a free-running frame timer. All reset and gap tests passed.')
e('')
e('## Synthesis and provenance')
e('')
e('The custom DC recipe flattens hierarchy, sets a 0.5 ns synthesis target, fixes multiple-port nets, keeps the direct clock, runs compile_ultra with a timing request, then incremental hold repair. The installed DC reports its timing_high_effort_script flag as ignored; clock steering and legal mapping still produce the measured implementation. The 0.5 ns target is an optimization request, not a timing claim. Independent grading imports the structural netlist without recipe execution, applies the fixed 10 ns SDC and certifies the actual period above. Constraints, libraries, scorer and reference were never changed.')
e('')
e(f"RTL source SHA256: `{selection['source_sha256']}`.")
e(f"Submitted mapped SHA256: `{selection['mapped_sha256']}`.")
for f in ['flow/dc_opt.tcl','implementation/manifest.json']:e(f"{f} SHA256: `{sha(sub/f)}`.")
e(f"Authoritative public report: `runs/arch_{best}/result.json`, copied byte-for-byte to `submission/public_verification.json`. Selection/report hashes are in `frozen_selection.json`. All experiments and source snapshots remain under `experiments/`; full measurements and per-component scores are in `measurements.csv`.")
e('')
e('Reproduce with `bash run_synopsys_debug.sh submission --profile architecture --out runs/reproduce_final` from FFT-Bench. To regenerate the export with the matching recipe use `bash synopsys.sh build submission --export --out runs/rebuild_final`, then independently evaluate in a fresh output directory.')
e('')
e('The selected C005 build timing report identifies the stage3 pre-add/combined-product path as the remaining frequency bottleneck (bf_reg_re to prod_combined). The producer requested 0.5 ns and did not meet it; only the independently certified period above is used in the score. The exact three-product transformation was also checked offline against existing R003/R004 public simulation traces: all 77,824 scored complex outputs matched bit-for-bit across 1,216 frames after accounting for the two added latency cycles; see experiments/three_product_equivalence.json.')
e('')
pending=[n for n in names if (root/'runs'/('arch_'+n)/'result.json').exists() and json.loads((root/'runs'/('arch_'+n)/'result.json').read_text()).get('status')=='RUNNING']
e('## Limits and next action' if pending else '## Limits and stopping decision')
e('')
e(f"{'Active work: wait for '+', '.join(pending)+' to finish; currently '+str(len(results))+' complete architecture candidates.' if pending else 'Stopped after '+str(len(results))+' completed architecture candidates plus numerical and area screens.'} The selected candidate has the highest complete feasible public score in this search. No global optimality or hidden-test acceptance is claimed. SQNR margin on the worst observed matching-source public frame is {worst-50:.6f} dB; this is finite empirical coverage. Timing/area are pre-layout ideal-interconnect measurements, not routed/silicon performance or power. Formal equivalence and P&R were not run; required multi-initial-state mapped simulation and STA passed. No private FFT-Eval resources, calibration or hidden inputs were accessed.")
(sub/'DESIGN_PLAN.md').write_text('\n'.join(s)+'\n')
print('Wrote final plan for',best,'with',len(results),'complete candidates; worst SQNR',worst)
