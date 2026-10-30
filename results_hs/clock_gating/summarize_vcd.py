"""Stream VCD timestamps and clock transitions without loading waveforms in RAM."""
import argparse
import hashlib
import json
from pathlib import Path
import re

p = argparse.ArgumentParser()
p.add_argument('vcd', type=Path)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--clock-pattern', default=r'(^|\.)clk$|clk_backend|gclk|GCLK')
a = p.parse_args()
pattern = re.compile(a.clock_pattern)
scope, names, counters, state = [], {}, {}, {}
first = last = None
timescale = ''
reading_scale = False
header = True
h = hashlib.sha256()
with a.vcd.open('rb') as f:
    for raw in f:
        h.update(raw)
        line = raw.decode('ascii', errors='replace').strip()
        if header:
            if line.startswith('$timescale'):
                reading_scale = True
            if reading_scale:
                timescale += ' ' + line.replace('$timescale', '').replace('$end', '')
                if '$end' in line:
                    reading_scale = False
            if line.startswith('$scope'):
                scope.append(line.split()[2])
            elif line.startswith('$upscope'):
                scope.pop()
            elif line.startswith('$var'):
                fields = line.split()
                name = '.'.join(scope + [fields[4]])
                if fields[2] == '1' and pattern.search(name):
                    names.setdefault(fields[3], []).append(name)
            elif line.startswith('$enddefinitions'):
                header = False
                counters = {k: {'rises_01': 0, 'falls_10': 0, 'unknown_events': 0}
                            for k in names}
            continue
        if line.startswith('#'):
            last = int(line[1:])
            if first is None:
                first = last
        elif line and line[0].lower() in '01xz' and line[1:] in names:
            code, value = line[1:], line[0].lower()
            old = state.get(code)
            if old == '0' and value == '1':
                counters[code]['rises_01'] += 1
            if old == '1' and value == '0':
                counters[code]['falls_10'] += 1
            if value in 'xz':
                counters[code]['unknown_events'] += 1
            state[code] = value
scale = re.fullmatch(r'\s*(\d+)\s*(s|ms|us|ns|ps|fs)\s*', timescale)
if scale is None or first is None or last is None:
    raise SystemExit('Cannot establish the VCD observation duration')
seconds = int(scale[1]) * {'s': 1, 'ms': 1e-3, 'us': 1e-6,
                          'ns': 1e-9, 'ps': 1e-12, 'fs': 1e-15}[scale[2]]
result = {'file': str(a.vcd), 'bytes': a.vcd.stat().st_size, 'sha256': h.hexdigest(),
          'timescale': timescale.strip(), 'first_timestamp': first, 'last_timestamp': last,
          'duration_seconds': (last-first)*seconds,
          'clocks': [{'names': names[k], **counters[k], 'final_state': state.get(k)}
                     for k in names]}
a.output.write_text(json.dumps(result, indent=2))
print(json.dumps({'duration_seconds': result['duration_seconds'],
                  'clock_codes': len(names), 'sha256': result['sha256']}))
