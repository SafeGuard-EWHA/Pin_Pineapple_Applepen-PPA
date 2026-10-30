"""Independent single-image windows. No changes to original RTL or report."""
import argparse,gzip,hashlib,json,os,re,shutil,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=80);a=p.parse_args()
root=Path(__file__).resolve().parent
stage=Path('/root/ppa-clockgate-per-image40');stage.mkdir(exist_ok=True)
old=Path('/root/ppa-clockgate-buffered');net=Path('/root/ppa-clockgate/buffered_v2')
prior=root.parent/'clock_gating'
plan=json.loads((root.parent/'clock_gating_sample_expansion/sampling_plan.json').read_text())
def sha(f):
    with Path(f).open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
for f,h in plan['sources_sha256'].items():assert sha(f)==h,f
assert sha(old/'ref_data/input_1000.txt')==plan['input_sha256']
for n in ['dataA','ref_data','std_cell_fn']:
    if not (stage/n).exists():(stage/n).symlink_to(old/n)
for n in ['tb_gl_selected.v','power_10ns.sdc']:shutil.copyfile(old/n,stage/n)
rows={int(s.split()[1]):s for s in (old/'ungated_full.log').read_text().splitlines() if s.startswith('img ')}
records=json.loads((stage/'runs.json').read_text()) if (stage/'runs.json').exists() else []
done={(r['index'],r['variant']) for r in records}
for v in ['ungated','gated']:
    cmd=['iverilog','-g2012','-DN_IMG=1','-s','tb_gatelevel','-o',v+'.vvp',str(net/(v+'.v'))]+[str(f) for f in sorted((stage/'std_cell_fn').glob('*.v'))]+['tb_gl_selected.v']
    if not (stage/(v+'.vvp')).exists():
        with (stage/(v+'_compile.log')).open('w') as log:subprocess.run(cmd,cwd=stage,stdout=log,stderr=subprocess.STDOUT,check=True)
indices=plan['easy_indices']+plan['hard_indices']
assert len(set(indices))==40
(stage/'protocol.json').write_text(json.dumps({'indices':indices,'window':'one image per fresh simulation, reset/start included; no batch division','compile_define':'N_IMG=1','source_plan':plan},indent=2))
for idx in indices:
    for v in ['ungated','gated']:
        if (idx,v) in done:continue
        if len(records)>=a.limit:print('LIMIT reached',len(records),flush=True);sys.exit()
        assert shutil.disk_usage(stage).free>4*1024**3,'Insufficient disk space'
        name=f'{v}_{idx:03d}';wave=stage/(name+'.vcd')
        assert not wave.exists(),'Unfinished waveform exists; inspect before retry'
        cmd=['vvp',v+'.vvp',f'+I0={idx}','+VCD='+name+'.vcd']
        start=time.monotonic();print('SIM',name,flush=True)
        with (stage/(name+'_simulation.log')).open('w') as log:subprocess.run(cmd,cwd=stage,stdout=log,stderr=subprocess.STDOUT,check=True)
        actual=[s for s in (stage/(name+'_simulation.log')).read_text().splitlines() if s.startswith('img ')]
        assert actual==[rows[idx]],name
        subprocess.run([sys.executable,str(prior/'summarize_vcd.py'),str(wave),'--output',str(stage/(name+'_vcd.json')),'--clock-pattern',r'(^|\.)clk$|clk_backend$|\.GCLK$|\.gclk$'],check=True)
        env=os.environ.copy();env.update(PLATFORM_DIR='/root/ppa-tools/ORFS/flow/platforms/asap7',ODB=str(net/(v+'.odb')),SDC=str(stage/'power_10ns.sdc'),VCD=str(wave),SCOPE='tb_gatelevel/dut',POWER_JSON=str(stage/(name+'_power.json')),PROPAGATE_CLOCKS='1')
        env.pop('SKIP_POWER',None);env.pop('GATE_PIN',None)
        if v=='gated':env['GATE_PIN']='u.u_backend_icg.u_icg/GCLK'
        print('POWER',name,flush=True)
        with (stage/(name+'_power.log')).open('w') as log:subprocess.run(['openroad','-exit',str(prior/'power_audit.tcl')],cwd=stage,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        log=(stage/(name+'_power.log')).read_text()
        assert re.search(r'^unannotated\s+0\s*$',log,re.M) and 'VIOLATED' not in log
        for marker in ['AUDIT_WNS','AUDIT_MIN_SLACK']:assert float(re.search(marker+r' ([^\n]+)',log)[1])>=0
        power=json.loads((stage/(name+'_power.json')).read_text());meta=json.loads((stage/(name+'_vcd.json')).read_text())
        gz=wave.with_suffix('.vcd.gz')
        with wave.open('rb') as src,gzip.open(gz,'wb',compresslevel=1) as out:shutil.copyfileobj(src,out)
        # Verify lossless compression before removing only this script's uncompressed output.
        with gzip.open(gz,'rb') as src:assert hashlib.file_digest(src,'sha256').hexdigest()==meta['sha256']
        assert wave.resolve().parent==stage.resolve();wave.unlink()
        records.append(dict(index=idx,variant=v,mode='easy' if idx in plan['easy_indices'] else 'hard',command=cmd,transactions=actual,rtl_match=True,power=power,vcd=meta,energy_nJ=power['Total']['total']*meta['duration_seconds']*1e9,elapsed_seconds=time.monotonic()-start,finished_utc=datetime.now(timezone.utc).isoformat(),compressed_vcd=str(gz)))
        (stage/'runs.json').write_text(json.dumps(records,indent=2));print('PASS',name,records[-1]['energy_nJ'],records[-1]['elapsed_seconds'],flush=True)
print('COMPLETE 80 image/design measurements',flush=True)
