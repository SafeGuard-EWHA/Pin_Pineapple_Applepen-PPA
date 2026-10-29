"""Prepare a fresh observer run without changing repository sources or ZIPs."""
from pathlib import Path
import argparse,zipfile,shutil,json,hashlib
p=argparse.ArgumentParser()
p.add_argument('--workdir',required=True,help='New empty ASCII path, e.g. C:/Temp/ppa_monitor_repeat')
p.add_argument('--vivado-root',default='C:/Xilinx/Vivado/2024.1')
a=p.parse_args()
here=Path(__file__).resolve().parent;repo=here.parents[1]
dest=Path(a.workdir).resolve()
if dest.exists():raise SystemExit('Work directory must not already exist; choose a new path.')
str(dest).encode('ascii')
manifest=json.loads((here.parent/'submit_check/manifest_before.json').read_text())
dest.mkdir(parents=True)
shutil.copy2(here/'control_monitor.v',dest/'control_monitor.v')
for model in ['A','WM']:
    archive=repo/f'vivado/submit/PPA_AdaPath_NPU_{model}.zip'
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=manifest['archives'][model]['zip_sha256']:
        raise SystemExit(f'{model}: archive differs from audited version')
    with zipfile.ZipFile(archive) as z:z.extractall(dest)
    shutil.copy2(here/f'audit_{model}.v',dest/f'audit_{model}.v')
    script=(here/f'run_{model}.tcl').read_text().replace('C:/Temp/ppa_observer_20261030',dest.as_posix()).replace('C:/Xilinx/Vivado/2024.1',a.vivado_root.replace('\\','/'))
    (dest/f'run_{model}.tcl').write_text(script)
    print(f'& "{a.vivado_root}/bin/vivado.bat" -mode batch -source "{dest.as_posix()}/run_{model}.tcl" -log "{dest.as_posix()}/{model}.log" -journal "{dest.as_posix()}/{model}.jou"')
