import json, sys, time
paths = sys.argv[1:]
deadline = time.time() + 2700
while time.time() < deadline:
    states = []
    for p in paths:
        try:
            states.append(json.load(open(p + '/result.json'))['status'])
        except Exception:
            states.append('MISSING')
    if all(s not in ('RUNNING', 'MISSING') for s in states):
        break
    time.sleep(20)
for p in paths:
    r = json.load(open(p + '/result.json'))
    g = r.get('grade', {})
    perf = g.get('performance', {})
    print(p.split('/')[-1], r['status'], 'score', g.get('score'), g.get('components'))
    print('   ', {k: perf.get(k) for k in ['area_um2', 'certified_period_ns', 'verified_frame_II_cycles', 'first_output_cycles']},
          'sqnr', r.get('quality', {}).get('minimum_frame_sqnr_db'), 'comp', r.get('latency', {}).get('maximum_frame_completion_cycles'), 'fail', r.get('failure'))
