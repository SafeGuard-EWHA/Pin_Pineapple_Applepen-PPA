"""Analytical mixture model, not a new simulation.
Run: python results_sh/energy_analysis/analyze_energy.py [--input path/to/results.json]
Uses pinned source_results.json by default; outputs derived JSON/CSV and PNG/SVG.
"""
from pathlib import Path
import argparse, json, csv, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,default=HERE/'source_results.json');args=parser.parse_args()
R=json.loads(args.input.read_text(encoding='utf8'));E=R['energy_nJ']; C=R['cycles']
ee,eh,er,eb=(E[x] for x in ['A_easy','A_hard','ref','Abase'])
assert eh>ee>0 and er>0 and eb>0
def avg(p):return p*ee+(1-p)*eh
def cross(target):return (eh-target)/(eh-ee)
pr,pb=cross(er),cross(eb);p0=R['mode_ratio']['A']['easy'];e0=avg(p0)
assert math.isclose(avg(pr),er,abs_tol=1e-10)
assert math.isclose(avg(pb),eb,abs_tol=1e-10)
assert math.isclose(avg(0),eh) and math.isclose(avg(1),ee)
summary={'analysis_kind':'fixed conditional energy mixture; no new simulation',
 'source_main_commit':'9b192246ef0cde397824c757ad552d779532b549',
 'input_file':args.input.name,'easy_energy_nJ':ee,'hard_energy_nJ':eh,
 'reference_energy_nJ':er,'baseline_A_energy_nJ':eb,
 'break_even_easy_fraction_vs_reference':pr,'break_even_easy_fraction_vs_baseline_A':pb,
 'reported_easy_fraction':p0,'reported_mixture_energy_nJ':e0,
 'saving_vs_reference_pct':100*(1-e0/er),'saving_vs_baseline_A_pct':100*(1-e0/eb),
 'maximum_saving_vs_reference_pct':100*(1-ee/er),
 'energy_reduction_per_1pp_easy_nJ':(eh-ee)/100,
 'energy_headroom_vs_reference_at_reported_mix_nJ':er-e0,
 'cycle_break_even_easy_fraction_vs_baseline_A':(C['hard']-C['base'])/(C['hard']-C['easy']),
 'cycle_vs_reference_all_hard_pct':100*(1-C['hard']/C['ref'])}
(HERE/'derived_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
with (HERE/'energy_curve.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['easy_fraction','hard_fraction','predicted_energy_nJ','saving_vs_reference_pct','saving_vs_baseline_A_pct','predicted_cycles'])
 for i in range(101):
  p=i/100;w.writerow([p,1-p,avg(p),100*(1-avg(p)/er),100*(1-avg(p)/eb),p*C['easy']+(1-p)*C['hard']])

font=font_manager.FontProperties(fname='C:/Windows/Fonts/malgun.ttf').get_name()
plt.rcParams.update({'font.family':font,'svg.fonttype':'path','axes.unicode_minus':False,'font.size':10})
green='#278353';yellow='#fff3ce';red='#f9e6e6';gray='#58636e';blue='#356995'
fig,axes=plt.subplots(1,2,figsize=(13,6.2),gridspec_kw={'width_ratios':[1.25,1]})
fig.subplots_adjust(left=.065,right=.975,top=.78,bottom=.25,wspace=.30)
fig.patch.set_facecolor('white')
fig.text(.065,.94,'AdaPath_A: Energy Break-even',fontsize=19,weight='bold',color='#202831')
fig.text(.065,.88,'모드별 에너지를 고정한 혼합 모델 · 100 MHz VCD 기반 제공 수치 · 새로운 시뮬레이션 아님',fontsize=10,color=gray)
x=list(range(101));ys=[avg(i/100) for i in x]
a=axes[0]
a.axvspan(0,pb*100,color=red,zorder=0);a.axvspan(pb*100,pr*100,color=yellow,zorder=0);a.axvspan(pr*100,100,color='#e8f4ec',zorder=0)
a.plot(x,ys,color=green,lw=2.8,label='AdaPath_A mixture')
a.axhline(er,color=gray,lw=1.6,ls='--',label=f'Reference ({er:.2f} nJ)')
a.axhline(eb,color=blue,lw=1.6,ls=':',label=f'Baseline_A ({eb:.2f} nJ)')
for p,target,col in [(pb,eb,blue),(pr,er,gray)]:
 a.scatter([p*100],[target],color=col,s=35,zorder=4)
 a.annotate(f'{p*100:.2f}%',(p*100,target),xytext=(-8,14),textcoords='offset points',ha='center',fontsize=10,color=col)
a.scatter([p0*100],[e0],color=green,s=55,zorder=5)
a.annotate(f'제공 동작점\nEasy {p0*100:.0f}% · {e0:.2f} nJ',(p0*100,e0),xytext=(49,15.1),textcoords='data',arrowprops={'arrowstyle':'-','color':green},fontsize=10,color=green)
a.set(xlim=(0,100),ylim=(14.5,27.8),xlabel='Easy 입력 비율 (%)',ylabel='평균 추론당 에너지 (nJ)')
a.set_title('(a) 평균 에너지와 두 비교 기준',loc='left',fontsize=11,pad=14)
a.legend(loc='upper right',frameon=False,fontsize=9)
b=axes[1]
b.plot(x,[avg(i/100)/eb for i in x],color=green,lw=2.6,label='Energy / Baseline_A')
b.plot(x,[(i/100*C['easy']+(1-i/100)*C['hard'])/C['base'] for i in x],color=blue,lw=2.6,label='Cycles / Baseline_A')
b.axhline(1,color=gray,ls='--',lw=1)
pc=summary['cycle_break_even_easy_fraction_vs_baseline_A']*100
b.axvspan(pc,pb*100,color=yellow,zorder=0)
for q in [pc,pb*100]:b.axvline(q,color=gray,lw=.8,ls=':')
b.text((pc+pb*100)/2,1.17,'cycle은 감소하지만\n에너지는 증가하는 구간',ha='center',fontsize=10,color='#805c00')
b.text(pc,.715,f'{pc:.2f}%',ha='center',fontsize=9,color=blue);b.text(pb*100,.715,f'{pb*100:.2f}%',ha='center',fontsize=9,color=green)
b.set(xlim=(0,100),ylim=(.69,1.26),xlabel='Easy 입력 비율 (%)',ylabel='Baseline_A 대비 비율')
b.set_title('(b) 처리 cycle 절감과 에너지 절감의 차이',loc='left',fontsize=11,pad=14)
b.legend(loc='upper right',frameon=False,fontsize=9)
for ax in axes:
 ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',color='#dce1e5',lw=.7,alpha=.7);ax.set_axisbelow(True)
fig.text(.065,.145,f'Reference보다 에너지 절감: Easy > {pr*100:.2f}%    |    Baseline_A보다 에너지 절감: Easy > {pb*100:.2f}%',fontsize=11,weight='bold',color='#202831')
fig.text(.065,.09,'가정: 모드별 평균 에너지와 비교 기준이 입력 분포·임계값 변화에도 일정. 정확도는 이 모델로 예측하지 않음.',fontsize=9,color=gray)
fig.text(.065,.05,'출처: report/results.json @ 9b192246 · reset 포함 런의 차감 추정값 사용 · 배치·배선 전 결과',fontsize=9,color=gray)
out=HERE.parents[1]/'figs_sh';out.mkdir(exist_ok=True)
fig.savefig(out/'fig_energy_breakeven.png',dpi=300,facecolor='white');fig.savefig(out/'fig_energy_breakeven.svg',facecolor='white');plt.close(fig)
print(json.dumps(summary,ensure_ascii=False,indent=2))
