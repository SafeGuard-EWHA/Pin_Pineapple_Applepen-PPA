"""Run the two prepared A variants sequentially and retain failures verbatim."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--orfs', type=Path, required=True)
p.add_argument('--stage', type=Path, required=True)
p.add_argument('--attempt', type=int, default=1)
a = p.parse_args()
flow = a.orfs.resolve() / 'flow'
logs = a.stage.resolve() / ('synthesis' if a.attempt == 1 else 'synthesis_attempt_' + str(a.attempt))
logs.mkdir(exist_ok=False)
tools = {k: shutil.which(k) for k in ('yosys', 'openroad')}
if not all(tools.values()):
    raise SystemExit('Both yosys and openroad must be installed first')
records = []
for variant in ('ungated', 'gated'):
    name = 'cg_a_' + variant
    cmd = ['make', 'DESIGN_CONFIG=designs/asap7/' + name + '/config.mk',
           'OPENROAD_EXE=' + tools['openroad'], 'YOSYS_EXE=' + tools['yosys'], 'synth']
    record = {'variant': variant, 'command': cmd, 'cwd': str(flow),
              'started_utc': datetime.now(timezone.utc).isoformat()}
    start = time.monotonic()
    print('START', variant, record['started_utc'], flush=True)
    with (logs / (variant + '.log')).open('w') as log:
        result = subprocess.run(cmd, cwd=flow, stdout=log, stderr=subprocess.STDOUT)
    record.update(returncode=result.returncode, elapsed_seconds=time.monotonic()-start,
                  ended_utc=datetime.now(timezone.utc).isoformat())
    records.append(record)
    (logs / 'runs.json').write_text(json.dumps(records, indent=2))
    print('END', variant, json.dumps(record), flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
