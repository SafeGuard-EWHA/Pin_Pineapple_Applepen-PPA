"""Compile and run matched pre-layout, zero-delay VCD windows sequentially."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

p = argparse.ArgumentParser()
p.add_argument('--orfs', type=Path, required=True)
p.add_argument('--stage', type=Path, required=True)
p.add_argument('--netlist-dir', type=Path)
p.add_argument('--variants', nargs='+', choices=['ungated', 'gated'], default=['ungated', 'gated'])
a = p.parse_args()
stage = a.stage.resolve()
validation_path = stage / 'gatelevel_validation.json'
records = json.loads(validation_path.read_text()) if validation_path.exists() else []
for variant in a.variants:
    netlist = a.orfs.resolve() / 'flow/results/asap7' / ('cg_a_' + variant) / 'base/1_2_yosys.v'
    if a.netlist_dir is not None:
        netlist = a.netlist_dir.resolve() / (variant + '.v')
    if not netlist.is_file():
        raise SystemExit('Missing synthesis netlist: ' + str(netlist))
    cmd = ['iverilog', '-g2012', '-s', 'tb_gatelevel', '-o', variant + '_gl.vvp', str(netlist)]
    cmd += [str(f) for f in sorted((stage / 'std_cell_fn').glob('*.v'))]
    cmd += ['tb_gl_selected.v']
    print('COMPILE', variant, flush=True)
    with (stage / (variant + '_gl_compile.log')).open('w') as log:
        subprocess.run(cmd, cwd=stage, stdout=log, stderr=subprocess.STDOUT, check=True)
    for window, indices in (('easy', [1,2,3,4]), ('mixed', [5,6,7,8]), ('hard', [5,37,51,62])):
        name = variant + '_' + window
        if (stage / (name + '.vcd')).exists():
            raise SystemExit('Refusing to overwrite existing waveform: ' + name)
        cmd = ['vvp', variant + '_gl.vvp', '+VCD=' + name + '.vcd']
        cmd += ['+I' + str(i) + '=' + str(index) for i, index in enumerate(indices)]
        record = {'variant': variant, 'window': window, 'indices': indices,
                  'command': cmd, 'started_utc': datetime.now(timezone.utc).isoformat()}
        print('SIMULATE', name, record['started_utc'], flush=True)
        before = time.monotonic()
        with (stage / (name + '.log')).open('w') as log:
            subprocess.run(cmd, cwd=stage, stdout=log, stderr=subprocess.STDOUT, check=True)
        record['elapsed_seconds'] = time.monotonic() - before
        lines = (stage / (name + '.log')).read_text().splitlines()
        rows = [line for line in lines if line.startswith('img ')]
        all_rows = {int(line.split()[1]): line for line in (stage / 'ungated_full.log').read_text().splitlines()
                    if line.startswith('img ')}
        expected = [all_rows[index] for index in indices]
        record['transactions'] = rows
        record['rtl_match'] = rows == expected and len(rows) == 4
        records.append(record)
        (stage / 'gatelevel_validation.json').write_text(json.dumps(records, indent=2))
        if not record['rtl_match']:
            raise SystemExit('Gate-level outputs differ from RTL: ' + name)
        subprocess.run([sys.executable, str(Path(__file__).with_name('summarize_vcd.py')),
                        str(stage / (name + '.vcd')), '--output', str(stage / (name + '_vcd.json'))], check=True)
        print('PASS', name, flush=True)
