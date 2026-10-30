"""Audit byte-identical image repetition in the exact simulation input."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('input', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
tokens = a.input.read_text().split()
if len(tokens) != 1000*784:
    raise SystemExit('Unexpected number of pixels')
groups = defaultdict(list)
for i in range(1000):
    pixels = bytes(int(v, 16) for v in tokens[i*784:(i+1)*784])
    groups[hashlib.sha256(pixels).hexdigest()].append(i)
result = {'input_sha256': hashlib.sha256(a.input.read_bytes()).hexdigest(),
          'transactions': 1000, 'pixels_per_image': 784, 'unique_pixel_arrays': len(groups),
          'multiplicity_histogram': dict(Counter(map(len, groups.values()))),
          'groups': dict(groups),
          'scope': 'Only this exact input file; no inference about other datasets.'}
a.output.write_text(json.dumps(result, indent=2))
print(json.dumps({k:v for k,v in result.items() if k != 'groups'}, indent=2))
