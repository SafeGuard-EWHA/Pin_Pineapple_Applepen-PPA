"""Create explicit zero-delay ASAP7 models for Icarus (no SDF/timing claim).

The upstream models connect delayed_* through specify timing checks, which
Icarus does not implement. In copies only, bypass these delayed pins and
remove specify blocks. Liberty files used for power/STA remain unmodified.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('destination', type=Path)
a = p.parse_args()
a.destination.mkdir(parents=True, exist_ok=False)
manifest = {}
for src in sorted(a.source.glob('asap7sc7p5t_*RVT_TT*.v')):
    original = src.read_text()
    text = re.sub(r'\bspecify\b.*?\bendspecify\b', '', original, flags=re.S)
    pins = []
    def bypass(match):
        declaration = match.group(0)
        signals = re.findall(r'\bdelayed_(\w+)\b', declaration)
        pins.extend(signals)
        return declaration + '\n' + '\n'.join(
            'assign delayed_' + pin + ' = ' + pin + ';' for pin in signals)
    text = re.sub(r'\bwire\s+delayed_\w+[^;]*;', bypass, text)
    out = a.destination / src.name
    out.write_text(text)
    manifest[src.name] = {'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
                         'model_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
                         'bypassed_pin_instances': len(pins)}
(a.destination / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
