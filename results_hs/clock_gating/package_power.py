"""Collect completed measurement evidence; never modify report or original RTL."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

p = argparse.ArgumentParser()
p.add_argument('--stage', type=Path, required=True)
p.add_argument('--orfs', type=Path, required=True)
p.add_argument('--netlist-dir', type=Path, required=True)
p.add_argument('--original-stage', type=Path, required=True)
a = p.parse_args()
dest = Path(__file__).resolve().parent / 'power_results'
dest.mkdir(exist_ok=True)
def copy(source, relative):
    target = dest / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
validation = json.loads((a.stage / 'gatelevel_validation.json').read_text())
expected = {(v,w) for v in ('ungated','gated') for w in ('easy','mixed','hard')}
assert {(r['variant'],r['window']) for r in validation} == expected
assert len(validation) == 6 and all(r['rtl_match'] for r in validation)
copy(a.stage / 'gatelevel_validation.json', 'gatelevel_validation.json')
copy(a.stage / 'tb_gl_selected.v', 'tb_gl_selected.v')
copy(a.stage / 'power_10ns.sdc', 'power_10ns.sdc')
copy(a.original_stage / 'synthesis_attempt_3/runs.json', 'synthesis/runs.json')
manifest = []
for variant in ('ungated','gated'):
    for suffix in ('.v','.odb'):
        f = a.netlist_dir / (variant+suffix)
        manifest.append({'kind':'final_netlist' if suffix=='.v' else 'final_odb',
                         'path':str(f.resolve()),'bytes':f.stat().st_size,'sha256':sha(f)})
        if suffix == '.v':
            target = dest / (variant+'.v.gz')
            with f.open('rb') as src, target.open('wb') as raw:
                with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as out:
                    shutil.copyfileobj(src,out)
    copy(a.original_stage / ('synthesis_attempt_3/'+variant+'.log'), 'synthesis/'+variant+'.log')
    stat = a.orfs / ('flow/reports/asap7/cg_a_'+variant+'/base/synth_stat.txt')
    copy(stat, 'synthesis/'+variant+'_stat.txt')
    copy(a.stage/(variant+'_gl_compile.log'), 'logs/'+variant+'_compile.log')
    for window in ('easy','mixed','hard'):
        name = variant+'_'+window
        meta = json.loads((a.stage/(name+'_vcd.json')).read_text())
        manifest.append({'kind':'vcd','path':meta['file'],'bytes':meta['bytes'],'sha256':meta['sha256']})
        copy(a.stage/(name+'.log'), 'logs/'+name+'_simulation.log')
        copy(a.stage/(name+'_vcd.json'), name+'_vcd.json')
        copy(a.stage/('power_propagated/'+name+'.json'), name+'_power.json')
        copy(a.stage/('power_propagated/'+name+'.log'), 'logs/'+name+'_power.log')
copy(a.stage/'power_propagated/runs.json','power_runs.json')
(dest/'raw_artifact_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Packaged',dest)
