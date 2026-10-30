"""Compute paired energy ratios from OpenSTA Watts and observed VCD durations."""
import json
import math
from pathlib import Path
import re

root = Path(__file__).resolve().parent
data = root / 'power_results'
rows = []
for window in ('easy','mixed','hard'):
    values = {}
    for variant in ('ungated','gated'):
        name = variant+'_'+window
        power = json.loads((data/(name+'_power.json')).read_text())
        vcd = json.loads((data/(name+'_vcd.json')).read_text())
        log = (data/('logs/'+name+'_power.log')).read_text()
        total = power['Total']
        assert all(math.isfinite(v) and v >= 0 for v in total.values())
        assert math.isclose(sum(total[k] for k in ('internal','switching','leakage')),
                            total['total'],rel_tol=1e-7)
        group_sum = sum(v['total'] for k,v in power.items() if k != 'Total')
        # OpenSTA accumulates the global and category totals separately.
        # Record the residual; bound it to 0.01%, rather than silently replacing Total.
        residual_percent = (group_sum/total['total']-1)*100
        assert abs(residual_percent) < 0.01, 'Excessive category/global discrepancy'
        text_total = re.search(r'^Total\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)',log,re.M)
        assert text_total and float(text_total[4]) == total['total']
        annotated = re.search(r'Annotated (\d+) pin activities',log)
        assert annotated and int(annotated[1]) > 0
        unannotated = re.search(r'^unannotated\s+(\d+)',log,re.M)
        assert unannotated, 'Missing coverage report'
        wns = float(re.search(r'AUDIT_WNS ([^\n]+)',log)[1])
        hold = float(re.search(r'AUDIT_MIN_SLACK ([^\n]+)',log)[1])
        assert wns >= 0 and hold >= 0, 'Timing violation in final load model'
        assert 'VIOLATED' not in log, 'Inspect electrical/timing violations'
        values[variant] = {'total_mW':total['total']*1000,
                           'duration_us':vcd['duration_seconds']*1e6,
                           'energy_nJ_per_image':total['total']*vcd['duration_seconds']/4*1e9,
                           'power_W':power,'category_sum_residual_percent':residual_percent,
                           'annotated_pins':int(annotated[1]),
                           'unannotated_pins':int(unannotated[1]),
                           'setup_slack_ps':wns,'hold_slack_ps':hold,
                           'vcd_sha256':vcd['sha256']}
    assert values['ungated']['duration_us'] == values['gated']['duration_us']
    reduction = (1-values['gated']['energy_nJ_per_image']/values['ungated']['energy_nJ_per_image'])*100
    rows.append({'window':window,**values,'power_and_energy_reduction_percent':reduction})
(data/'summary.json').write_text(json.dumps(rows,indent=2))
lines = ['| 구간 | 기준 전력 (mW) | ICG 전력 (mW) | 기준 에너지 (nJ/장) | ICG 에너지 (nJ/장) | 감소율 (%) |',
         '|---|---:|---:|---:|---:|---:|']
labels = {'easy':'Easy 4장','mixed':'Easy 3장 + Hard 1장','hard':'Hard 4장'}
for r in rows:
    u,g=r['ungated'],r['gated']
    lines.append(f"| {labels[r['window']]} | {u['total_mW']:.6f} | {g['total_mW']:.6f} | {u['energy_nJ_per_image']:.6f} | {g['energy_nJ_per_image']:.6f} | {r['power_and_energy_reduction_percent']:.3f} |")
(data/'RESULT_TABLE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
