"""Sequential 1,000-input check of the actual ICG-cell variant, without VCD."""
import argparse
import json
from pathlib import Path
import re
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--orfs', type=Path, required=True)
p.add_argument('--stage', type=Path, required=True)
a = p.parse_args()
stage = a.stage.resolve()
tb = (stage / 'tb_gl_A.v').read_text()
tb = '\n'.join(line for line in tb.splitlines()
               if '$dumpfile(' not in line and '$dumpvars(' not in line)
tb = tb.replace('==== gate-level:', '==== RTL check:')
(stage / 'tb_rtl_full.v').write_text(tb + '\n')
results = {}
for variant in ('ungated', 'gated'):
    src = a.orfs / 'flow/designs/src' / ('cg_a_' + variant)
    sources = sorted(src.glob('*.v')) + sorted((src / 'ref').glob('*.v'))
    if variant == 'gated':
        sources += sorted((stage / 'std_cell_fn').glob('*.v'))
    compile_cmd = ['iverilog', '-g2012', '-DN_IMG=1000', '-s', 'tb_gatelevel',
                   '-I', str(src), '-o', variant + '_full.vvp']
    compile_cmd += [str(f) for f in sources] + ['tb_rtl_full.v']
    with (stage / (variant + '_full_compile.log')).open('w') as log:
        subprocess.run(compile_cmd, cwd=stage, stdout=log, stderr=subprocess.STDOUT, check=True)
    print('RUN', variant, flush=True)
    with (stage / (variant + '_full.log')).open('w') as log:
        subprocess.run(['vvp', variant + '_full.vvp', '+START=0'], cwd=stage,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    text = (stage / (variant + '_full.log')).read_text()
    lines = [line for line in text.splitlines() if line.startswith('img ')]
    if len(lines) != 1000:
        raise RuntimeError('Unexpected transaction count: ' + str(len(lines)))
    rows = [re.fullmatch(r'img (\d+) : decision=(\d+) \(label (\d+)\) mode=(\d+) margin=(\d+) cycles=(\d+)', line)
            for line in lines]
    if not all(rows):
        raise RuntimeError('Unknown output or unexpected transaction format')
    modes = [int(m[4]) for m in rows]
    results[variant] = {'count': len(rows), 'correct': sum(m[2] == m[3] for m in rows),
                        'modes': {str(k): modes.count(k) for k in (0, 1, 2)},
                        'average_cycles': sum(int(m[6]) for m in rows)/len(rows)}
    results[variant + '_lines'] = lines
different = sum(x != y for x, y in zip(results.pop('ungated_lines'), results.pop('gated_lines')))
results['transaction_mismatches'] = different
(stage / 'rtl_full_validation.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2), flush=True)
if different:
    raise SystemExit('ICG-cell variant differs from ungated RTL')
