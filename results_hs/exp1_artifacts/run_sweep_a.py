from pathlib import Path
import subprocess, hashlib, json, csv, time, concurrent.futures, re
from datetime import datetime

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT/'PPA_Codex_Handoff/project'
RTL=PROJECT/'rtl'
OUT=ROOT.parent/'outputs/sweep_A_run'
LOG=OUT/'logs'
LOG.mkdir(parents=True,exist_ok=True)
BIN=ROOT/'iverilog/bin'
THS=[0,10,20,30,40,50,63,80,100,119,140,170,200,250,300,400]
CORE='mac_tree.v conv1_engine.v conv2_engine.v maxpool_relu_n.v fmap_buffer.v early_classifier.v fc_engine.v top2_finder.v score_margin_calc.v difficulty_decoder.v mode_control_fsm.v adapath_top.v ref/conv1_buf.v ref/conv2_buf.v'.split()
source=PROJECT/'verilog_ref/data/input_1000.txt'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='cccf35e29a63989cd74b7c949a15bf87457700f82178e2afcc233495ef499cca'
files=[RTL/p for p in CORE+['tb_threshold_sweep.v','run_sweep.sh']]+list((PROJECT/'out/rtl_data_mnist_A').glob('*.txt'))+[source]
hashes={p.relative_to(PROJECT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
manifest=dict(experiment_commit='5b9d9d2ce36e86ef7d3a3dfd46eac903435a209f',thresholds=THS,sha256=hashes,started_at=datetime.now().astimezone().isoformat(),parallel_jobs=4,protocol='Same compiler flags and thresholds as run_sweep.sh A; Windows Python orchestration; TH=63 validated first.',initial_estimate_minutes=[40,70])
mp=OUT/'manifest.json'
if mp.exists(): assert json.loads(mp.read_text())['sha256']==hashes,'Input/code changed'
else: mp.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
cmd=[str(BIN/'iverilog.exe'),'-g2012','-I.','-DMODEL_A','-DDATA="../out/rtl_data_mnist_A/"','-o','codex_sweep_A.vvp',*CORE,'tb_threshold_sweep.v']
r=subprocess.run(cmd,cwd=RTL,capture_output=True)
(LOG/'compile.log').write_bytes(r.stdout+r.stderr);r.check_returncode()
def run(th):
    record=LOG/f'TH_{th}.json'
    if record.exists():
        d=json.loads(record.read_text());print('REUSE '+str(th),flush=True);return d
    start=time.monotonic();log=LOG/f'TH_{th}.log'
    args=[str(BIN/'vvp.exe'),'codex_sweep_A.vvp',f'+TL={th}',f'+TH={th}']
    with log.open('wb') as f:r=subprocess.run(args,cwd=RTL,stdout=f,stderr=subprocess.STDOUT)
    raw=log.read_text(encoding='utf-8',errors='replace')
    lines=[x.split(',')[1:] for x in raw.splitlines() if x.startswith('SWEEP,')]
    assert r.returncode==0 and len(lines)==1 and not re.search(r'ERROR|WARNING|FATAL',raw,re.I),str(log)
    row=lines[0];assert len(row)==7 and row[:2]==[str(th),str(th)] and sum(map(int,row[4:]))==1000 and row[5]=='0',row
    assert re.search(r'valid_out[^\n]*1000 / 1000',raw),raw
    if th==63:assert row==['63','63','970','851.84','960','0','40'],'STOP: TH=63 mismatch; no full sweep'
    d=dict(row=row,elapsed_seconds=time.monotonic()-start,command=args,completed_at=datetime.now().astimezone().isoformat())
    record.write_text(json.dumps(d,indent=2),encoding='utf-8');print(json.dumps(d),flush=True);return d
results=[run(63)]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results+=list(pool.map(run,[x for x in THS if x!=63]))
assert len(results)==16
with (OUT/'sweep_A.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow('TL,TH,correct,avg_cycles,easy,med,hard'.split(','));w.writerows(sorted((d['row'] for d in results),key=lambda x:int(x[1])))
assert all(hashlib.sha256((PROJECT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
(OUT/'completed.json').write_text(json.dumps(dict(status='complete',completed_at=datetime.now().astimezone().isoformat(),runs=results),indent=2),encoding='utf-8')
print('SWEEP COMPLETE: 16 validated conditions',flush=True)
