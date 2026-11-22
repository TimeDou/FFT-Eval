"""Sample measurement/prefetch process trees without changing EDA commands."""
from pathlib import Path
import json
import os
import time

ROOT = Path(__file__).resolve().parent
TICKS = os.sysconf('SC_CLK_TCK')
PAGE = os.sysconf('SC_PAGE_SIZE')


def snapshot():
    rows = {}
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            text = (path/'stat').read_text()
            values = text[text.rfind(')')+2:].split()
            rows[int(path.name)] = dict(ppid=int(values[1]), cpu_ticks=int(values[11])+int(values[12]),
                threads=int(values[17]), rss_bytes=int(values[21])*PAGE,
                command=(path/'comm').read_text().strip())
        except (OSError, ValueError, IndexError):
            continue
    roots = {int((ROOT/name).read_text()) for name in ['driver.pid','prefetch.pid'] if (ROOT/name).exists()}
    selected = set(roots)
    while True:
        added = {pid for pid,row in rows.items() if row['ppid'] in selected}-selected
        if not added:
            break
        selected.update(added)
    return {str(pid):rows[pid] for pid in sorted(selected) if pid in rows}


def main():
    started = time.monotonic()
    samples = []
    peak = 0
    while True:
        rows = snapshot()
        total = sum(value['rss_bytes'] for value in rows.values())
        peak = max(peak, total)
        samples.append(dict(elapsed_seconds=time.monotonic()-started, rss_sum_bytes=total,
                            threads=sum(value['threads'] for value in rows.values()), processes=rows))
        try:
            state = json.loads((ROOT/'status.json').read_text())['status']
        except (OSError, ValueError):
            state = 'UNKNOWN'
        record = dict(status='COMPLETE' if state in {'COMPLETE','INCOMPLETE'} else 'RUNNING',
            observed_from_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(time.time()-(time.monotonic()-started))),
            sampling_interval_seconds=10, clock_ticks_per_second=TICKS,
            maximum_observed_rss_sum_bytes=peak, samples=samples,
            scope='Sampled summed RSS of measurement-driver and frequency-prefetch process trees, including EDA subprocesses; shared pages may be counted multiple times. Not an exact cgroup/container peak. Sampling began after source setup and may miss earlier peaks.')
        temporary = ROOT/'process_resources.tmp'
        temporary.write_text(json.dumps(record, indent=2)+'\n')
        temporary.replace(ROOT/'process_resources.json')
        if state in {'COMPLETE','INCOMPLETE'}:
            return
        time.sleep(10)


if __name__ == '__main__':
    main()
