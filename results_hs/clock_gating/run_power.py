"""Run OpenROAD power only after all six gate-level windows match RTL."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--orfs', type=Path, required=True)
p.add_argument('--stage', type=Path, required=True)
p.add_argument('--odb-dir', type=Path)
p.add_argument('--gate-pin', required=True, help='Exact mapped ICG GCLK pin, inspected in the netlist')
p.add_argument('--clock-mode', choices=('ideal', 'propagated'), default='ideal')
a = p.parse_args()
stage = a.stage.resolve()
validated = json.loads((stage / 'gatelevel_validation.json').read_text())
if len(validated) != 6 or not all(r['rtl_match'] for r in validated):
    raise SystemExit('All six gate-level windows must match RTL before power analysis')
out = stage / ('power_' + a.clock_mode)
out.mkdir(exist_ok=False)
records = []
for variant in ('ungated', 'gated'):
    for window in ('easy', 'mixed', 'hard'):
        name = variant + '_' + window
        env = os.environ.copy()
        env.update(PLATFORM_DIR=str(a.orfs.resolve() / 'flow/platforms/asap7'),
                   ODB=str(a.orfs.resolve() / 'flow/results/asap7' / ('cg_a_' + variant) / 'base/1_synth.odb'),
                   SDC=str(stage / 'power_10ns.sdc'), VCD=str(stage / (name + '.vcd')),
                   SCOPE='tb_gatelevel/dut', POWER_JSON=str(out / (name + '.json')),
                   PROPAGATE_CLOCKS='1' if a.clock_mode == 'propagated' else '0')
        env.pop('SKIP_POWER', None)
        if a.odb_dir is not None:
            env['ODB'] = str(a.odb_dir.resolve() / (variant + '.odb'))
        env.pop('GATE_PIN', None)
        if variant == 'gated':
            env['GATE_PIN'] = a.gate_pin
        cmd = ['openroad', '-exit', str(Path(__file__).with_name('power_audit.tcl'))]
        record = {'variant': variant, 'window': window, 'clock_mode': a.clock_mode,
                  'started_utc': datetime.now(timezone.utc).isoformat(), 'command': cmd,
                  'environment': {k:env[k] for k in ('PLATFORM_DIR','ODB','SDC','VCD','SCOPE','POWER_JSON','PROPAGATE_CLOCKS')},
                  'gate_pin': env.get('GATE_PIN')}
        print('POWER', name, a.clock_mode, flush=True)
        start = time.monotonic()
        with (out / (name + '.log')).open('w') as log:
            r = subprocess.run(cmd, cwd=stage, env=env, stdout=log, stderr=subprocess.STDOUT)
        record.update(returncode=r.returncode, elapsed_seconds=time.monotonic()-start)
        records.append(record)
        (out / 'runs.json').write_text(json.dumps(records, indent=2))
        if r.returncode:
            raise SystemExit('Power analysis failed: ' + name)
        data = json.loads((out / (name + '.json')).read_text())
        if 'Total' not in data:
            raise SystemExit('Unexpected power JSON format')
        print('POWER_DONE', name, data['Total'], flush=True)
