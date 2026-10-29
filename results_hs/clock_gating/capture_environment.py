"""Capture reproducibility metadata after tools are installed (Linux)."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--orfs', type=Path, required=True)
p.add_argument('--stage', type=Path, required=True)
a = p.parse_args()
repo = Path(__file__).resolve().parents[2]
def run(*cmd):
    r = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {'command': list(cmd), 'returncode': r.returncode, 'output': r.stdout}
def digest(f):
    with f.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
files = [f for f in (a.orfs / 'flow/platforms/asap7/lib/NLDM').glob('*RVT_TT*.lib*')
         if '_FAKE.' not in f.name]
files += list((a.stage / 'dataA').glob('*.txt'))
files += [a.stage / 'ref_data/input_1000.txt', a.stage / 'tb_gl_A.v', a.stage / 'power_10ns.sdc']
if (a.stage / 'tb_gl_selected.v').exists():
    files += [a.stage / 'tb_gl_selected.v']
files += [a.orfs / 'flow/platforms/asap7/lef/asap7_tech_1x_201209.lef',
          a.orfs / 'flow/platforms/asap7/lef/asap7sc7p5t_28_R_1x_220121a.lef']
sources = {}
for variant in ('ungated', 'gated'):
    name = 'cg_a_' + variant
    src = a.orfs / 'flow/designs/src' / name
    sources[name] = {str(f.relative_to(src)): digest(f) for f in sorted(src.rglob('*')) if f.is_file()}
    files += list((a.orfs / 'flow/designs/asap7' / name).glob('*'))
(a.stage / 'source_manifest.json').write_text(json.dumps(sources, indent=2))
result = {'platform': platform.platform(),
          'os_release': Path('/etc/os-release').read_text(),
          'orfs_commit': run('git', '-C', str(a.orfs), 'rev-parse', 'HEAD'),
          'yosys': run('yosys', '-V'), 'openroad': run('openroad', '-version'),
          'iverilog': run('iverilog', '-V'),
          'memory': run('free', '-h'),
          'experiment_sources': {f.name: digest(f) for f in sorted(Path(__file__).parent.iterdir())
                                 if f.suffix in ('.py', '.v', '.tcl')},
          'sha256': {str(f): digest(f) for f in sorted(files)}}
(a.stage / 'environment.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print('Recorded', len(files), 'input/library hashes')
