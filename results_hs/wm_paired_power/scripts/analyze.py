"""Independently validate archived logs and calculate matched-window energy.

Run from any directory: python scripts/analyze.py
Requires only the Python standard library. Does not run a simulation.
"""
from pathlib import Path
from decimal import Decimal as D
import collections
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'raw'
PACKAGE = ROOT.parents[1] / 'submission/free_topic_WM811K/power'
plan = json.loads((ROOT / 'sampling_plan.json').read_text(encoding='utf-8'))
runs = json.loads((RAW / 'runs.json').read_text(encoding='utf-8'))
assert len(runs) == 7 and len({r['tag'] for r in runs}) == 7
expected = [list(map(int, s.split())) for s in (PACKAGE/'data/wm_expect.txt').read_text().splitlines() if s.strip()]
gold = {int(s.split()[0]): list(map(int, s.split())) for s in (PACKAGE/'weights/golden_reference.txt').read_text().splitlines() if s.strip() and not s.startswith('#')}
assert len(expected) == 954
assert collections.Counter(x[2] for x in expected) == {0:404, 1:167, 2:383}
pixels = (PACKAGE/'data/wm_input_954.txt').read_text().split()
assert len(pixels) == 954*784
selected = [i for ids in plan['groups'].values() for i in ids]
hashes = {i: hashlib.sha256(bytes(int(x,16) for x in pixels[i*784:(i+1)*784])).hexdigest() for i in selected}
assert len(selected) == len(set(selected)) == len(set(hashes.values())) == 12
for mode, group in enumerate(('easy','med','hard')):
    assert [i for i,x in enumerate(expected) if x[2]==mode and x[0]==x[1]][:4] == plan['groups'][group]

def dec_text(x):
    return format(x, 'f') if isinstance(x,D) else x

verified = {}
for r in runs:
    tag = r['tag']
    text = (RAW/f'{tag}_simulation.log').read_text()
    report = (RAW/f'{tag}_power.rpt').read_text()
    assert not re.search(r'ERROR|FATAL', text)
    assert not re.search(r'\[ERROR|\bERROR\b', report)
    rows = [list(map(int,m)) for m in re.findall(r'img (\d+) : decision=(\d+) mode=(\d+) margin=(\d+) cycles=(\d+)',text)]
    assert rows == r['transactions'] and len(rows)==4
    ids = [x[0] for x in rows]
    assert ids == r['indices']
    group = tag.split('_')[1]
    assert ids == (plan['control_baseline'] if group=='control' else plan['groups'][group])
    for idx, decision, mode, margin, cycles in rows:
        if r['variant']=='adapath':
            assert [decision,mode,margin] == expected[idx][1:4]
            assert cycles == (839 if mode==0 else 1004)
        else:
            assert decision == gold[idx][5] and mode==2 and cycles==979
    finish_ps = D(re.search(r'\$finish called at (\d+) \(1ps\)',text)[1])
    duration = finish_ps / D(1000000)
    # Full four-image window includes reset/start overhead; do not substitute just compute cycles.
    assert duration == D(sum(x[4] for x in rows)+4*13)*D('0.01')-D('0.004')
    totals = re.findall(r'^Total\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)',report,re.M)
    assert len(totals)==1
    components = list(map(D,totals[0]))
    residual = sum(components[:3])-components[3]
    assert abs(residual) <= D('0.000000002')
    power = components[3]*1000
    energy = power*duration/4
    assert abs(energy-D(str(r['energy_nJ_per_image']))) < D('0.000000001')
    activities = int(re.search(r'Annotated (\d+) pin activities',report)[1])
    assert activities==r['annotated_pin_activities'] and activities>0
    verified[tag] = dict(power_mW=power,duration_us=duration,energy_nJ_per_image=energy,
                         annotated_pin_activities=activities,component_sum_residual_W=residual,
                         warnings=sorted(set(re.findall(r'^.*\[WARNING.*$',report,re.M))))

pairs = {}
for group in ('easy','med','hard'):
    a,b = verified['ada_'+group], verified['base_'+group]
    pairs[group] = dict(indices=plan['groups'][group],baseline_energy_nJ=b['energy_nJ_per_image'],
        adapath_energy_nJ=a['energy_nJ_per_image'],
        energy_reduction_pct=(1-a['energy_nJ_per_image']/b['energy_nJ_per_image'])*100,
        power_reduction_pct=(1-a['power_mW']/b['power_mW'])*100)

def aggregate(weights):
    a=sum(D(w)*pairs[g]['adapath_energy_nJ'] for g,w in weights.items())/sum(weights.values())
    b=sum(D(w)*pairs[g]['baseline_energy_nJ'] for g,w in weights.items())/sum(weights.values())
    return dict(baseline_energy_nJ=b,adapath_energy_nJ=a,energy_reduction_pct=(1-a/b)*100)

result = dict(validation='PASS',runs=7,paired_transactions=24,control_transactions=4,
    unique_selected_pixel_contents=12,pixel_sha256=hashes,per_run=verified,pairs=pairs,
    balanced_12_sample=aggregate(dict(easy=1,med=1,hard=1)),
    rtl_mode_weighted_estimate=aggregate(plan['mode_weights']),
    control_difference_from_original_nJ=verified['base_control']['energy_nJ_per_image']-D('29.458160368'),
    limitations=plan['limits'])
(ROOT/'summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,default=dec_text)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ('validation','pairs','balanced_12_sample','rtl_mode_weighted_estimate')},indent=2,default=dec_text))
