"""Mode-weighted ENERGY MODEL, not a per-threshold power measurement."""
import csv, json, hashlib
from decimal import Decimal as D
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parent
repo=root.parents[1]
source=repo/'rtl/sweep_A.csv'
calibration=root.parent/'clock_gating_sample_expansion/power_results/summary.json'
s=json.loads(calibration.read_text(),parse_float=D)
rows=list(csv.DictReader(source.open(encoding='utf-8-sig')))
assert len(rows)==16
output=[]
for variant in ['ungated','gated']:
    e=s['variants'][variant]
    for r in rows:
        n=sum(int(r[k]) for k in ['easy','med','hard'])
        assert n==1000 and int(r['med'])==0 and r['TL']==r['TH']
        energy=(int(r['easy'])*e['easy_nJ']+int(r['hard'])*e['hard_nJ'])/n
        # Independent float implementation guards against weighting/unit mistakes.
        independent=float(e['easy_nJ'])+(float(e['hard_nJ'])-float(e['easy_nJ']))*int(r['hard'])/n
        assert abs(float(energy)-independent)<1e-10
        output.append(dict(variant=variant,TH=int(r['TH']),correct=int(r['correct']),accuracy_percent=float(D(r['correct'])/10),easy=int(r['easy']),hard=int(r['hard']),avg_cycles=float(r['avg_cycles']),estimated_nJ=float(energy)))
def dominates(a,b):
    return a['accuracy_percent']>=b['accuracy_percent'] and a['estimated_nJ']<=b['estimated_nJ'] and (a['accuracy_percent']>b['accuracy_percent'] or a['estimated_nJ']<b['estimated_nJ'])
for r in output:
    r['pareto_within_variant']=not any(dominates(q,r) for q in output if q['variant']==r['variant'])
    r['pareto_across_variants']=not any(dominates(q,r) for q in output)
for v in ['ungated','gated']:
    assert [r['TH'] for r in output if r['variant']==v and r['pareto_within_variant']]==[0,10,20,30]
    t=next(r for r in output if r['variant']==v and r['TH']==63)
    assert t['correct']==970 and t['easy']==960 and t['hard']==40
    assert abs(t['estimated_nJ']-float(s['variants'][v]['weighted_nJ']))<1e-10
with (root/'pareto_model.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
manifest={'model':'E(TH)=p_easy(TH)*mean_E_easy_at_TH63+p_hard(TH)*mean_E_hard_at_TH63','calibration_commit':'676aab3','units':'nJ/image, including per-window reset/start overhead','sources':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,calibration]},'rows':len(output),'pareto_thresholds_within_each_variant':[0,10,20,30],'global_frontier':'gated TH=0,10,20,30 under the fixed mode-energy model only'}
(root/'provenance.json').write_text(json.dumps(manifest,indent=2))
fig,ax=plt.subplots(figsize=(10,5.8))
for v,color,label in [('ungated','#536b91','Without ICG'),('gated','#008b80','With ICG')]:
    rr=[r for r in output if r['variant']==v]
    ax.plot([r['estimated_nJ'] for r in rr],[r['accuracy_percent'] for r in rr],'-o',color=color,label=label,ms=5,alpha=.8)
    low=rr[0]; chosen=next(r for r in rr if r['TH']==63)
    ax.scatter(chosen['estimated_nJ'],97,marker='*',s=230,color=color,edgecolor='black',zorder=5)
    ax.annotate('TH=0/10/20/30',(low['estimated_nJ'],98),xytext=(5,10),textcoords='offset points',fontsize=9,color=color)
    ax.annotate('TH=63',(chosen['estimated_nJ'],97),xytext=(0,20),textcoords='offset points',ha='center',fontsize=9,color=color)
    ax.annotate('TH=400',(rr[-1]['estimated_nJ'],97),xytext=(0,-22),textcoords='offset points',ha='center',fontsize=9,color=color)
ax.set(xlabel='Estimated energy (nJ/image; fixed mode-energy model)',ylabel='RTL accuracy (%)',ylim=(96.75,98.35),title='Model A: accuracy–energy trade-off (16 thresholds)')
ax.grid(alpha=.2);ax.legend(loc='upper right')
fig.text(.5,.015,'Energy is modeled from TH=63 calibration; each threshold was NOT power-simulated.\nAccuracy: 1,000 file entries / 100 unique pixel arrays. Star: selected TH=63.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.07,1,1));fig.savefig(root/'accuracy_energy_pareto.png',dpi=200);plt.close(fig)
print('Validated 32 modeled points; TH63 reproduces item4 weighted energy. Frontiers: TH0/10/20/30.')
