from pathlib import Path
import subprocess, json, csv, time, concurrent.futures, os, hashlib

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / 'PPA_Codex_Handoff/project'
RTL = PROJECT / 'rtl'
OUT = ROOT.parent / 'outputs/robustness_run'
OUT.mkdir(exist_ok=True)
LOG = OUT / 'logs'
LOG.mkdir(exist_ok=True)
checks = json.loads((ROOT.parent / 'outputs/baseline_verification/summary.json').read_text())
assert len(checks)==2 and all(x['passed'] for x in checks), 'Baseline gate failed'
checkpoint = OUT / 'paused.json'
if checkpoint.exists():
    saved = json.loads(checkpoint.read_text(encoding='utf-8'))
    for name, digest in saved['sha256'].items():
        assert hashlib.sha256((PROJECT/name).read_bytes()).hexdigest()==digest, f'Changed since pause: {name}'

def cached_row(kind, level, design):
    record=LOG/f'{kind}_{level}_{design}.json'
    if not record.exists(): return None
    row=json.loads(record.read_text())['row']
    assert row[:3]==[kind,level,design] and len(row)==8, record
    raw=(LOG/f'{kind}_{level}_{design}.log').read_text(encoding='utf-8',errors='replace')
    assert 'ERROR' not in raw and raw.count('SWEEP,')==1, record
    assert f"SWEEP,63,63,{','.join(row[3:])}" in raw, record
    assert sum(map(int,row[5:]))==1000 and int(row[6])==0, record
    assert 0<=int(row[3])<=1000, record
    if design=='base': assert row[7]=='1000',record
    return row

if '--check-resume' in os.sys.argv:
    completed=[]
    for p in sorted((RTL/'noisy').glob('input_1000_*.txt')):
        kind,level=p.stem.removeprefix('input_1000_').split('_')
        for d in ['ada','base']:
            row=cached_row(kind,level,d)
            if row: completed.append(row)
    print(f'Resume check passed: {len(completed)} completed, {34-len(completed)} remaining. No simulation started.')
    raise SystemExit(0)
BIN = ROOT / 'iverilog/bin'
core = 'mac_tree.v conv1_engine.v conv2_engine.v maxpool_relu_n.v fmap_buffer.v early_classifier.v fc_engine.v top2_finder.v score_margin_calc.v difficulty_decoder.v mode_control_fsm.v adapath_top.v ref/conv1_buf.v ref/conv2_buf.v'.split()
for design in ['ada','base']:
    cmd = [str(BIN/'iverilog.exe'), '-g2012','-I.','-DMODEL_A','-DDATA="../out/rtl_data_mnist_A/"']
    if design=='base': cmd.append('-DBASELINE')
    cmd += ['-o', f'codex_rob_{design}.vvp', *core, 'tb_threshold_sweep.v']
    r = subprocess.run(cmd,cwd=RTL,capture_output=True)
    (LOG/f'compile_{design}.log').write_bytes(r.stdout+r.stderr)
    r.check_returncode()
def run(job):
    f,design=job
    kind,level=f.stem.removeprefix('input_1000_').split('_')
    cached=cached_row(kind,level,design)
    if cached:
        print('REUSE '+','.join(cached),flush=True)
        return cached
    log=LOG/f'{kind}_{level}_{design}.log'
    if log.exists():
        stamp=time.time_ns()
        log.rename(LOG/f'{kind}_{level}_{design}.interrupted_{stamp}.log')
    start=time.monotonic()
    with log.open('wb') as stream:
        r=subprocess.run([str(BIN/'vvp.exe'),f'codex_rob_{design}.vvp','+TL=63','+TH=63',f'+IMG=noisy/{f.name}'],cwd=RTL,stdout=stream,stderr=subprocess.STDOUT)
    raw=log.read_text(encoding='utf-8',errors='replace')
    lines=[x.split(',')[3:] for x in raw.splitlines() if x.startswith('SWEEP,')]
    assert r.returncode==0 and 'ERROR' not in raw and len(lines)==1, log
    vals=lines[0]
    assert len(vals)==5 and sum(map(int,vals[2:]))==1000 and int(vals[3])==0, log
    if design=='base': assert int(vals[4])==1000,log
    row=[kind,level,design,*vals]
    (LOG/f'{kind}_{level}_{design}.json').write_text(json.dumps(dict(row=row,seconds=time.monotonic()-start)))
    print(','.join(row),flush=True)
    return row
jobs=[(p,d) for p in sorted((RTL/'noisy').glob('input_1000_*.txt')) for d in ['ada','base']]
assert len(jobs)==34
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    rows=list(pool.map(run,jobs))
assert len(set((r[0],r[1],r[2]) for r in rows))==34
with (OUT/'robustness_A.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow('kind,level,design,correct,avg_cycles,easy,med,hard'.split(','));w.writerows(sorted(rows,key=lambda r:(r[0],float(r[1]),r[2])))
env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'python-packages');env['MPLCONFIGDIR']=str(ROOT/'mplconfig')
subprocess.run([os.sys.executable,str(PROJECT/'python/plot_robustness.py'),'--csv',str(OUT/'robustness_A.csv'),'--out',str(OUT)],env=env,check=True)
print('COMPLETE: 34 verified rows and two plots',flush=True)
