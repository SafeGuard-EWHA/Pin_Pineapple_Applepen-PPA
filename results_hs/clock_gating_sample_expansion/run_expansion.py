"""Prespecified paired power sample expansion; original RTL/report untouched."""
import argparse, hashlib, json, os, random, re, shutil, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--stage',type=Path,required=True)
p.add_argument('--prepare-only',action='store_true')
a=p.parse_args()
root=Path(__file__).resolve().parent
previous=root.parent/'clock_gating'
old=Path('/root/ppa-clockgate-buffered')
net=Path('/root/ppa-clockgate/buffered_v2')
orfs=Path('/root/ppa-tools/ORFS')
stage=a.stage.resolve()
def digest(f):
    with f.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
audit=json.loads((previous/'input_audit.json').read_text())
allrows={int(line.split()[1]):line for line in (old/'ungated_full.log').read_text().splitlines() if line.startswith('img ')}
representatives=sorted(min(v) for v in audit['groups'].values())
easy=[i for i in representatives if 'mode=0 ' in allrows[i]]
hard=[i for i in representatives if 'mode=2 ' in allrows[i]]
assert len(easy)==96 and hard==[5,37,51,62]
assert digest(old/'ref_data/input_1000.txt')==audit['input_sha256']
chosen=random.Random(20261030).sample(easy,36)
plan={'seed':20261030,'sampling':'SRS without replacement within 96 unique Easy inputs; census of 4 unique Hard inputs',
      'population_unique':100,'population_modes':{'easy':96,'hard':4},
      'easy_indices':chosen,'hard_indices':hard,'hard_source':'Reused paired Hard run from commit 1a6d910; not new independent observations',
      'input_sha256':audit['input_sha256'],
      'new_windows':[{'batch':f'easy_{j//4+1:02d}','indices':chosen[j:j+4]} for j in range(0,36,4)],
      'sources_sha256':{str(f):digest(f) for f in [previous/'power_audit.tcl',previous/'summarize_vcd.py',old/'tb_gl_selected.v',old/'power_10ns.sdc',net/'ungated.v',net/'gated.v',net/'ungated.odb',net/'gated.odb',old/'ungated_gl.vvp',old/'gated_gl.vvp']}}
if a.prepare_only:
    stage.mkdir(exist_ok=False,parents=True)
    for name in ('dataA','ref_data','std_cell_fn','ungated_gl.vvp','gated_gl.vvp'):
        (stage/name).symlink_to(old/name)
    shutil.copyfile(old/'power_10ns.sdc',stage/'power_10ns.sdc')
    (root/'sampling_plan.json').write_text(json.dumps(plan,indent=2))
    (stage/'sampling_plan.json').write_text(json.dumps(plan,indent=2))
    print(json.dumps(plan,indent=2));sys.exit()
assert plan==json.loads((stage/'sampling_plan.json').read_text()),'Inputs/tools changed after plan freeze'
records=[]
assert not (stage/'runs.json').exists(),'Refusing implicit resume or overwrite'
for group in plan['new_windows']:
    for variant in ('ungated','gated'):
        name=variant+'_'+group['batch']
        command=['vvp',variant+'_gl.vvp','+VCD='+name+'.vcd']+[f'+I{k}={v}' for k,v in enumerate(group['indices'])]
        record={'variant':variant,**group,'command':command,'started_utc':datetime.now(timezone.utc).isoformat()}
        print('SIM',name,flush=True);start=time.monotonic()
        with (stage/(name+'_simulation.log')).open('w') as f:
            subprocess.run(command,cwd=stage,stdout=f,stderr=subprocess.STDOUT,check=True)
        rows=[s for s in (stage/(name+'_simulation.log')).read_text().splitlines() if s.startswith('img ')]
        assert rows==[allrows[i] for i in group['indices']], 'Output/cycle mismatch: '+name
        record.update(rtl_match=True,transactions=rows,simulation_seconds=time.monotonic()-start)
        subprocess.run([sys.executable,str(previous/'summarize_vcd.py'),str(stage/(name+'.vcd')),'--output',str(stage/(name+'_vcd.json')),'--clock-pattern',r'(^|\.)clk$|clk_backend$|\.GCLK$|\.gclk$'],check=True)
        env=os.environ.copy()
        env.update(PLATFORM_DIR=str(orfs/'flow/platforms/asap7'),ODB=str(net/(variant+'.odb')),SDC=str(stage/'power_10ns.sdc'),VCD=str(stage/(name+'.vcd')),SCOPE='tb_gatelevel/dut',POWER_JSON=str(stage/(name+'_power.json')),PROPAGATE_CLOCKS='1')
        env.pop('SKIP_POWER',None);env.pop('GATE_PIN',None)
        if variant=='gated':env['GATE_PIN']='u.u_backend_icg.u_icg/GCLK'
        print('POWER',name,flush=True);start=time.monotonic()
        with (stage/(name+'_power.log')).open('w') as f:
            subprocess.run(['openroad','-exit',str(previous/'power_audit.tcl')],env=env,cwd=stage,stdout=f,stderr=subprocess.STDOUT,check=True)
        log=(stage/(name+'_power.log')).read_text()
        assert re.search(r'^unannotated\s+0\s*$',log,re.M)
        assert 'VIOLATED' not in log
        for marker in ('AUDIT_WNS','AUDIT_MIN_SLACK'):
            assert float(re.search(marker+r' ([^\n]+)',log)[1])>=0
        record.update(power_seconds=time.monotonic()-start,power=json.loads((stage/(name+'_power.json')).read_text()),vcd=json.loads((stage/(name+'_vcd.json')).read_text()))
        records.append(record)
        (stage/'runs.json').write_text(json.dumps(records,indent=2))
        print('PASS',name,record['power']['Total']['total'],flush=True)
print('COMPLETE 18 new paired-window runs; merge with 2 existing Hard-window runs',flush=True)
