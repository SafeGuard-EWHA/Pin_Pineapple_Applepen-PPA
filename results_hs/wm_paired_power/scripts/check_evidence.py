"""Check archived input provenance, compiled netlists, and raw-log hashes."""
from pathlib import Path
import gzip, hashlib, json, re, subprocess

root = Path(__file__).resolve().parents[1]
repo = root.parents[1]
package = repo/'submission/free_topic_WM811K/power'
raw = root/'raw'
sha = lambda b: hashlib.sha256(b).hexdigest()
manifest = json.loads((raw/'input_manifest.json').read_text())
checked = {}
newline_only_sources = []
for name, info in manifest['files'].items():
    local = (package/name).read_bytes()
    original = subprocess.check_output(['git','show',manifest['source_commit']+':'+info['source']],cwd=repo)
    assert sha(local)==info['sha256'], name
    if local != original:
        assert local.replace(b'\r\n',b'\n')==original.replace(b'\r\n',b'\n'), name
        newline_only_sources.append(name)
    checked[name]=sha(local)
tb = (package/'tb_gl_wm.v').read_bytes()
original_tb = subprocess.check_output(['git','show','57cf580:glsim/wm/tb_gl_wm.v'],cwd=repo)
assert tb.replace(b'\r\n',b'\n')==original_tb.replace(b'\r\n',b'\n')
fingerprint = sha((raw/'input_manifest.json').read_bytes())+sha(tb)
env = json.loads((raw/'environment.json').read_text())
runs = json.loads((raw/'runs.json').read_text())
assert all(r['input_fingerprint']==fingerprint for r in runs)
assert env['input_fingerprint']==fingerprint
netlists={}
for variant in ('baseline','adapath'):
    stamp=json.loads((raw/f'{variant}.compile.json').read_text())
    net=gzip.decompress((package/f'{variant}_wm_net.v.gz').read_bytes())
    assert sha(net)==stamp['netlist_sha256'] and stamp['input_fingerprint']==fingerprint
    # These FAKE Liberty cell families are loaded by the original wildcard but must not be used by the design.
    fake_occurrences=re.findall(rb'\bDFFHQN(?:V2X|V4X|H2V2X)\w*',net)
    assert not fake_occurrences, fake_occurrences[:5]
    netlists[variant]={'sha256':sha(net),'fake_cell_family_occurrences':len(fake_occurrences)}
result=dict(status='PASS',source_commit=manifest['source_commit'],input_files_verified=len(checked),
    original_tb_identical_after_newline_normalization=True,tb_sha256=sha(tb),input_fingerprint=fingerprint,netlists=netlists,
    source_files_with_only_crlf_lf_difference=newline_only_sources,
    raw_sha256={p.name:sha(p.read_bytes()) for p in sorted(raw.iterdir()) if p.is_file()},
    raw_vcd_archive_location='/root/ppa-wm-paired12/paired_run/*.vcd.gz',
    vcd_note='SHA256 and sizes in raw/runs.json; runner verified decompressed content before removing its uncompressed VCD.',
    timing_scope='Functional cycle and observation duration only; no setup/hold, SDF, STA closure or Fmax claim.',
    platform_orfs_commit='7bf5a814e47c54ec6c64692b464d398184d99891')
(root/'evidence_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ('status','input_files_verified','original_tb_identical_after_newline_normalization','netlists')},indent=2))
