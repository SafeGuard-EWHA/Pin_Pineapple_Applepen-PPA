"""Collect and independently validate the frozen expansion; run in WSL after completion."""
import json, hashlib, shutil, re, statistics
from decimal import Decimal as D
from pathlib import Path

root=Path(__file__).resolve().parent
stage=Path('/root/ppa-clockgate-expansion40')
old=root.parent/'clock_gating/power_results'
dest=root/'power_results'
dest.mkdir(exist_ok=True)
(dest/'logs').mkdir(exist_ok=True)
plan=json.loads((root/'sampling_plan.json').read_text())
records=json.loads((stage/'runs.json').read_text())
assert len(records)==18
assert {(r['variant'],r['batch']) for r in records}=={(v,f'easy_{i:02d}') for v in ['gated','ungated'] for i in range(1,10)}
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for path,digest in plan['sources_sha256'].items():assert sha(path)==digest,path
assert sha('/root/ppa-clockgate-buffered/ref_data/input_1000.txt')==plan['input_sha256']
assert len(set(plan['easy_indices']+plan['hard_indices']))==40
reference={int(s.split()[1]):s for s in Path('/root/ppa-clockgate-buffered/ungated_full.log').read_text().splitlines() if s.startswith('img ')}
energies={v:[] for v in ['gated','ungated']}
checks=[]; manifest=[]
for r in records:
    name=r['variant']+'_'+r['batch']
    assert r['indices']==next(x['indices'] for x in plan['new_windows'] if x['batch']==r['batch'])
    actual=[s for s in (stage/(name+'_simulation.log')).read_text().splitlines() if s.startswith('img ')]
    assert actual==r['transactions']==[reference[i] for i in r['indices']]
    log=(stage/(name+'_power.log')).read_text()
    assert re.search(r'^unannotated\s+0\s*$',log,re.M) and 'VIOLATED' not in log
    timing={k:float(re.search(k+r' ([^\n]+)',log)[1]) for k in ['AUDIT_WNS','AUDIT_MIN_SLACK']}
    assert min(timing.values())>=0
    p=json.loads((stage/(name+'_power.json')).read_text(),parse_float=D)
    total=p['Total']['total']
    residual=abs(sum(g['total'] for k,g in p.items() if k!='Total')-total)/total
    assert residual<D('0.0001')
    assert abs(sum(p['Total'][k] for k in ['internal','switching','leakage'])-total)/total<D('0.0001')
    # OpenSTA prints the same Total values in its textual report.
    lines=[s for s in log.splitlines() if s.strip().startswith('Total ')]
    assert any(any(abs(D(n)-total)/total<D('0.00001') for n in re.findall(r'\d+\.\d+[eE][+-]\d+',s)) for s in lines),name
    vcd=json.loads((stage/(name+'_vcd.json')).read_text())
    assert vcd==r['vcd'] and vcd['duration_seconds']==3.4316e-5
    energy=total*D(str(vcd['duration_seconds']))*D(10)**9/4
    assert abs(float(energy)-r['power']['Total']['total']*vcd['duration_seconds']*1e9/4)<1e-10
    energies[r['variant']].append(float(energy))
    checks.append(dict(name=name,energy_nJ=float(energy),power_mW=float(total*1000),group_residual_fraction=float(residual),**timing))
    manifest.append({k:vcd[k] for k in ['file','bytes','sha256']})
    for suffix in ['_simulation.log','_power.log']:
        shutil.copyfile(stage/(name+suffix),dest/'logs'/(name+suffix))
    for suffix in ['_power.json','_vcd.json']:
        shutil.copyfile(stage/(name+suffix),dest/(name+suffix))
summary={'new_runs':18,'new_transactions':72,'unique_inputs_including_reused_hard':40,'hard_source_commit':'1a6d910','checks':checks,'variants':{}}
for v in ['ungated','gated']:
    hp=json.loads((old/(v+'_hard_power.json')).read_text(),parse_float=D)
    hv=json.loads((old/(v+'_hard_vcd.json')).read_text())
    hard=float(hp['Total']['total']*D(str(hv['duration_seconds']))*D(10)**9/4)
    easy=statistics.mean(energies[v]); weighted=.96*easy+.04*hard
    summary['variants'][v]={'easy_nJ':easy,'easy_batch_sd_nJ':statistics.stdev(energies[v]),'easy_batch_min_nJ':min(energies[v]),'easy_batch_max_nJ':max(energies[v]),'hard_nJ':hard,'weighted_nJ':weighted,'weighted_mW':weighted/(.96*34316/4+.04*41156/4)*1000}
    for suffix in ['_power.json','_vcd.json']:shutil.copyfile(old/(v+'_hard'+suffix),dest/(v+'_hard'+suffix))
    for suffix in ['_simulation.log','_power.log']:shutil.copyfile(old/'logs'/(v+'_hard'+suffix),dest/'logs'/(v+'_hard'+suffix))
for mode in ['easy','hard','weighted']:
    summary[mode+'_reduction_percent']=100*(1-summary['variants']['gated'][mode+'_nJ']/summary['variants']['ungated'][mode+'_nJ'])
for name in ['runs.json','runner.log']:shutil.copyfile(stage/name,dest/name)
(dest/'summary.json').write_text(json.dumps(summary,indent=2))
(dest/'raw_artifact_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='checks'},indent=2))
