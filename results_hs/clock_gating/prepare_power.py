"""Prepare isolated A ungated/gated sources; never edit repository RTL.

Run under Linux: python3 prepare_power.py --orfs /path/to/ORFS --stage /new/path
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

p = argparse.ArgumentParser()
p.add_argument('--orfs', type=Path, required=True)
p.add_argument('--stage', type=Path, required=True)
a = p.parse_args()
repo = Path(__file__).resolve().parents[2]
flow = a.orfs.resolve() / 'flow'
stage = a.stage.resolve()
stage.mkdir(parents=True, exist_ok=False)
manifest = {}
for variant in ('ungated', 'gated'):
    name = 'cg_a_' + variant
    src = flow / 'designs/src' / name
    cfg = flow / 'designs/asap7' / name
    src.mkdir(parents=True, exist_ok=False)
    cfg.mkdir(parents=True, exist_ok=False)
    for f in (repo / 'rtl').glob('*.v'):
        # Copy only the modules used by the known synthesis source set.
        if (repo / 'orfs/src/adapath' / f.name).exists():
            shutil.copy2(f, src / f.name)
    shutil.copytree(repo / 'orfs/src/adapath/ref', src / 'ref')
    for f in (repo / 'orfs/designs_final/src/adapath_A').glob('*.vh'):
        shutil.copy2(f, src / f.name)
    wrapper = (repo / 'orfs/designs_final/src/adapath_A/adapath_A_npu.v').read_text()
    if variant == 'gated':
        for f in (Path(__file__).parent / 'rtl').glob('*.v'):
            shutil.copy2(f, src / f.name)
        shutil.copy2(Path(__file__).parent / 'icg_asap7.v', src / 'icg_latch.v')
        wrapper = wrapper.replace('    adapath_top #(', '    adapath_top_cg #(')
    (src / 'adapath_A_npu.v').write_text(wrapper)
    config = (repo / 'orfs/designs_final/cfg/adapath_A/config.mk').read_text()
    config = config.replace('adapath_A/', name + '/').replace('/src/adapath_A\n', '/src/' + name + '\n').replace('= adapath_A\n', '= ' + name + '\n')
    config += '\n# Matched comparison; TT power and synthesis corner, one synthesis job.\n'
    config += 'export CORNER = TC\nexport NUM_CORES = 2\n'
    (cfg / 'config.mk').write_text(config)
    shutil.copy2(repo / 'orfs/designs_final/cfg/adapath_A/constraint.sdc', cfg / 'constraint.sdc')
    manifest[name] = {str(f.relative_to(src)): hashlib.sha256(f.read_bytes()).hexdigest()
                      for f in sorted(src.rglob('*')) if f.is_file()}
shutil.copytree(repo / 'out/rtl_data_mnist_A', stage / 'dataA')
(stage / 'ref_data').mkdir()
tb = (repo / 'glsim/tb_gl_A.v').read_text()
(stage / 'tb_gl_A.v').write_text(tb)
shutil.copy2(repo / 'flow_scripts/constraint_10ns.sdc', stage / 'power_10ns.sdc')
(stage / 'source_manifest.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps({'stage': str(stage), 'sources': list(manifest)}, indent=2))
