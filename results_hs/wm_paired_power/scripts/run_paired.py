#!/usr/bin/env python3
"""Serial, resumable matched-window WM evaluation; no RTL or original TB edits."""
import argparse, fcntl, gzip, hashlib, json, os, pathlib, re, shutil, subprocess, time

ap = argparse.ArgumentParser()
ap.add_argument('--stage', default='/root/ppa-wm-paired12')
ap.add_argument('--platform', default='/root/ppa-tools/ORFS/flow/platforms/asap7')
ap.add_argument('--limit', type=int, default=7)
a = ap.parse_args()
root = pathlib.Path(a.stage).resolve(); os.chdir(root)
lock = open(root/'runner.lock', 'w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
out = root/'paired_results'; out.mkdir(exist_ok=True)
run = root/'paired_run'; run.mkdir(exist_ok=True)
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024), b''): h.update(b)
    return h.hexdigest()
def save(p,x):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False));tmp.replace(p)
def status(phase, **kw):
    save(out/'status.json',dict(phase=phase,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),pid=os.getpid(),**kw))
    print(phase,kw,flush=True)
def execute(cmd,log,env=None):
    start=time.monotonic()
    with open(log,'w') as f: subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,check=True)
    return time.monotonic()-start
groups={'easy':[8,10,18,22], 'med':[2,3,5,24], 'hard':[0,1,4,9]}
jobs=[('base_control','baseline',[0,1,2,3])]
for g,ids in groups.items():
    jobs.extend([(f'ada_{g}','adapath',ids),(f'base_{g}','baseline',ids)])
gold={}
for line in (root/'weights/golden_reference.txt').read_text().splitlines():
    if not line or line.startswith('#'):continue
    v=list(map(int,line.split()));gold[v[0]]=v
expected=[list(map(int,x.split())) for x in (root/'data/wm_expect.txt').read_text().splitlines() if x.strip()]
manifest=json.loads((root/'input_manifest.json').read_text())
for n,v in manifest['files'].items():
    assert sha(root/n.replace('\\','/'))==v['sha256'],n
fingerprint=sha(root/'input_manifest.json')+sha(root/'tb_gl_wm.v')
environ=dict(os.environ,PLATFORM_DIR=a.platform)
envinfo={'platform':a.platform,'input_fingerprint':fingerprint,'jobs':jobs}
for tag,cmd in [('openroad',['openroad','-version']),('iverilog',['iverilog','-V']),('os',['uname','-a']),('cpu',['lscpu'])]:
    envinfo[tag]=subprocess.check_output(cmd,stderr=subprocess.STDOUT).decode(errors='replace')
envinfo['libraries']={str(p.relative_to(a.platform)):sha(p) for p in pathlib.Path(a.platform).rglob('*') if p.is_file() and (('RVT_TT' in p.name and '.lib' in p.name) or p.suffix=='.lef')}
save(out/'environment.json',envinfo)
statepath=out/'runs.json';records=json.loads(statepath.read_text()) if statepath.exists() else []
for variant in ('baseline','adapath'):
    binary=run/f'{variant}.vvp'; stamp=run/f'{variant}.compile.json'
    if binary.exists() and stamp.exists() and json.loads(stamp.read_text())['input_fingerprint']==fingerprint:continue
    status('compile',variant=variant)
    net=run/f'{variant}_wm_net.v'
    with gzip.open(root/f'{variant}_wm_net.v.gz','rb') as src, open(net,'wb') as dst:shutil.copyfileobj(src,dst)
    cmd=['iverilog','-g2012',f'-DDATA="{root}/weights/"',f'-DWM_INPUT="{root}/data/wm_input_954.txt"']
    if variant=='baseline':cmd+=['-DTOP_BASELINE']
    cmd+=['-o',str(binary),str(net)]+[str(p) for p in sorted((root/'std_cell_fn').glob('*.v'))]+[str(root/'tb_gl_wm.v')]
    secs=execute(cmd,out/f'compile_{variant}.log')
    save(stamp,dict(input_fingerprint=fingerprint,wall_seconds=secs,command=cmd,netlist_sha256=sha(net)))
for tag,variant,ids in jobs[:a.limit]:
    if any(x['tag']==tag and x['input_fingerprint']==fingerprint for x in records):continue
    # Keep one uncompressed VCD at a time; protect the Windows-backed virtual disk.
    available=shutil.disk_usage('/mnt/c').free
    if available<7*1024**3:raise RuntimeError('Windows disk free space below 7 GiB; do not start another VCD')
    status('simulation',tag=tag,completed=len(records),total=len(jobs))
    vcd=run/f'{tag}.vcd'; simlog=out/f'{tag}_simulation.log'
    secs=execute(['vvp',str(run/f'{variant}.vvp')]+[f'+I{i}={n}' for i,n in enumerate(ids)]+[f'+VCD={vcd}'],simlog)
    txt=simlog.read_text(); rows=[list(map(int,m)) for m in re.findall(r'img (\d+) : decision=(\d+) mode=(\d+) margin=(\d+) cycles=(\d+)',txt)]
    assert len(rows)==4 and [x[0] for x in rows]==ids,(tag,rows)
    for idx,dec,mode,margin,cycles in rows:
        assert cycles<4000
        if variant=='adapath':assert [dec,mode,margin]==expected[idx][1:4],(tag,idx,'AdaPath mismatch')
        else:assert dec==gold[idx][5] and mode==2,(tag,idx,'Baseline mismatch')
    assert not re.search(r'ERROR|FATAL',txt)
    t_end=int(re.search(r'\$finish called at (\d+) \(1ps\)',txt).group(1))
    with open(vcd,'rb') as f:
        head=f.read(512);f.seek(max(0,vcd.stat().st_size-8000));tail=f.read()
    assert re.search(rb'\$timescale\s+1ps\s+\$end',head),head
    assert max(map(int,re.findall(rb'^#(\d+)',tail,re.M)))==t_end
    status('power',tag=tag,completed=len(records),total=len(jobs),simulation_seconds=secs)
    report=out/f'{tag}_power.rpt'
    env=dict(environ,NET=str(run/f'{variant}_wm_net.v'),TOP=f'{variant}_wm_npu',SDC=str(root/'constraint_10ns.sdc'),VCD=str(vcd),SCOPE='tb_gatelevel/dut')
    powersecs=execute(['openroad','-exit',str(root/'vcd_power_net.tcl')],report,env)
    rpt=report.read_text();assert not re.search(r'\bERROR\b|\[ERROR',rpt),rpt[-2000:]
    totals=re.findall(r'^Total\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)',rpt,re.M)
    assert len(totals)==1 and 'Annotated' in rpt
    p=float(totals[0][3])*1000; t=t_end*1e-6
    record=dict(tag=tag,variant=variant,indices=ids,transactions=rows,input_fingerprint=fingerprint,power_mW=p,duration_us=t,energy_nJ_per_image=p*t/4,simulation_seconds=secs,power_seconds=powersecs,vcd_bytes=vcd.stat().st_size,vcd_sha256=sha(vcd),power_components_W=totals[0],annotated_pin_activities=int(re.search(r'Annotated (\d+) pin activities',rpt).group(1)))
    status('compress_vcd',tag=tag)
    gz=vcd.with_suffix('.vcd.gz')
    with open(vcd,'rb') as src,gzip.open(gz,'wb',compresslevel=1) as dst:shutil.copyfileobj(src,dst,8*1024*1024)
    record['vcd_gz_sha256']=sha(gz);record['vcd_gz_bytes']=gz.stat().st_size
    # Only remove this runner's generated uncompressed VCD after a gzip integrity check.
    with gzip.open(gz,'rb') as src:
        digest=hashlib.sha256()
        for b in iter(lambda:src.read(8*1024*1024),b''):digest.update(b)
    assert digest.hexdigest()==record['vcd_sha256']
    assert vcd.parent==run and vcd.name==tag+'.vcd';vcd.unlink()
    records.append(record);save(statepath,records)
    status('run_complete',tag=tag,completed=len(records),total=len(jobs),energy_nJ_per_image=record['energy_nJ_per_image'])
status('complete' if len(records)==len(jobs) else 'pilot_complete',completed=len(records),total=len(jobs))
