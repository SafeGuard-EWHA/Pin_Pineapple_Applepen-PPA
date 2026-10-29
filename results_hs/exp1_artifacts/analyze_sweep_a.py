from pathlib import Path
import csv,json,hashlib,sys,shutil,os
from collections import defaultdict
from datetime import datetime
ROOT=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(ROOT/'mplconfig')
sys.path.insert(0,str(ROOT/'python-packages'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=ROOT.parent/'outputs/sweep_A_run'
PKG=ROOT.parent/'outputs/sweep_A_publish'
(PKG/'rtl').mkdir(parents=True,exist_ok=True)
(PKG/'out').mkdir(exist_ok=True)
(PKG/'results_hs/exp1_artifacts').mkdir(parents=True,exist_ok=True)
rows=list(csv.DictReader((OUT/'sweep_A.csv').open()))
assert len(rows)==16 and len({r['TH'] for r in rows})==16
for r in rows:
    for k in ['TL','TH','correct','easy','med','hard']:r[k]=int(r[k])
    r['avg_cycles']=float(r['avg_cycles']);r['accuracy']=r['correct']/10
selected=next(r for r in rows if r['TH']==63)
assert [selected[k] for k in ['correct','avg_cycles','easy','med','hard']]==[970,851.84,960,0,40]
front=[r for r in rows if not any(s['avg_cycles']<=r['avg_cycles'] and s['correct']>=r['correct'] and (s['avg_cycles']<r['avg_cycles'] or s['correct']>r['correct']) for s in rows)]
groups=defaultdict(list)
for r in rows:groups[(r['avg_cycles'],r['accuracy'])].append(r['TH'])
plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'font.size':11})
fig,ax=plt.subplots(figsize=(12,7))
ax.plot([r['avg_cycles'] for r in rows],[r['accuracy'] for r in rows],color='#aab7c4',lw=1,zorder=1)
ax.scatter([r['avg_cycles'] for r in rows],[r['accuracy'] for r in rows],s=48,color='#2166ac',zorder=3)
ax.axhline(97,color='#777777',ls='--',lw=1.3,label='Reference 정확도 97.0%')
ax.scatter([selected['avg_cycles']],[97],marker='*',s=260,color='#d95f02',edgecolor='white',zorder=5,label='사전 지정 동작점 TH=63')
for i,((x,y),ths) in enumerate(groups.items()):
    label='TH='+','.join(map(str,ths))
    tx=(i+.5)/len(groups)
    ty=.95 if i%2==0 else .05
    ax.annotate(label,(x,y),xytext=(tx,ty),textcoords='axes fraction',ha='center',fontsize=9,color='#d95f02' if 63 in ths else '#333333',arrowprops={'arrowstyle':'-','color':'#999999','lw':.6},bbox={'facecolor':'white','edgecolor':'none','pad':2},zorder=6)
ax.set(xlabel='평균 cycle / 이미지 (낮을수록 적은 연산 시간)',ylabel='정확도 (%)',title='모델 A 임계값 스윕: 정확도–평균 cycle')
ax.margins(x=.12,y=.35);ax.grid(alpha=.2);ax.spines[['top','right']].set_visible(False)
ax.legend(loc='center right',frameon=False)
fig.text(.5,.015,'TL=TH · 고유 100장 × 10회 반복 · 동일 좌표의 TH는 묶어 표기 · 연결선은 임계값 순서이며 보간 모델이 아님',ha='center',fontsize=9,color='#666666')
fig.tight_layout(rect=[0,.05,1,1]);fig.savefig(PKG/'out/fig_sweep_A.png',dpi=200);fig.savefig(PKG/'out/fig_sweep_A.svg');plt.close(fig)
table='| TL=TH | 정답/1000 | 정확도 (%) | 평균 cycle | Easy | Medium | Hard |\n|---:|---:|---:|---:|---:|---:|---:|\n'
for r in rows:table+='| '+ ' | '.join([str(r['TH']),str(r['correct']),f"{r['accuracy']:.1f}",f"{r['avg_cycles']:.2f}",str(r['easy']),str(r['med']),str(r['hard'])])+' |\n'
best=max(r['accuracy'] for r in rows);fast=min(rows,key=lambda r:r['avg_cycles']);hard=rows[-1]
front_th=', '.join(str(r['TH']) for r in front)
dom=selected not in front
interpret=f"TH=63에서 정답 970개, 정확도 97.0%, 평균 851.84 cycle, Easy/Medium/Hard=960/0/40을 재현하였다. 스윕 구간의 정확도는 {min(r['accuracy'] for r in rows):.1f}–{best:.1f}%였으며, 평균 사이클 범위는 {min(r['avg_cycles'] for r in rows):.2f}–{max(r['avg_cycles'] for r in rows):.2f} cycle로 측정되었다. TH=0과 TH=400의 Hard 개수는 각각 {rows[0]['hard']}개와 {hard['hard']}개였으며, 임계값 증가에 따른 경로 선택 변화가 관측되었다. 측정한 정확도–사이클 조합에서 비지배 동작점은 TH={front_th}에 해당하였으며, TH=63은 {'다른 측정 동작점에 의해 지배되었다' if dom else '비지배 동작점에 포함되었다'}. 이는 이 입력 집합과 스윕 범위에 한정한 비교이며, 새로운 입력에서의 최적 임계값이나 일반화 성능을 확정하지 않았다."
manifest=json.loads((OUT/'manifest.json').read_text());completed=json.loads((OUT/'completed.json').read_text())
wall_minutes=(datetime.fromisoformat(completed['completed_at'])-datetime.fromisoformat(manifest['started_at'])).total_seconds()/60
text=f'''# 실험 1: 모델 A 임계값에 따른 정확도–연산 시간 절충

## 연구 질문
Score Margin 임계값을 변화시켰을 때 모델 A의 분류 정확도와 이미지당 평균 사이클 및 경로 분포가 어떻게 변화하는지 평가하였다.

## 실험 방법
- 코드 커밋 `{manifest['experiment_commit']}`과 `out/rtl_data_mnist_A/` 가중치를 사용하였으며 기존 RTL .v 파일은 수정하지 않았다.
- 공식 입력 1,000장에 대해 TL=TH를 0, 10, 20, 30, 40, 50, 63, 80, 100, 119, 140, 170, 200, 250, 300, 400으로 설정하였다. 원본 `run_sweep.sh A`와 동일한 컴파일 옵션·테스트벤치·입력을 사용하고 Windows Python 실행기로 순서만 변경하여 TH=63 검증 후 4개 병렬로 실행하였다.
- TH=63의 필수 기준값을 먼저 검사하였고, 각 실행의 정상 출력 1,000/1,000, 모드 합 1,000, TL=TH에서 Medium=0 및 16조건 누락·중복 없음을 검증하였다.
- 입력은 고유 100장의 10회 반복으로 독립 표본 1,000장이 아니며, 테스트벤치가 정의한 start 이후 valid_out까지의 cycle을 평균하였다. 파형 기반 전력·실측 지연 또는 MAC 수를 측정한 실험은 아니다.

## 결과 표
{table}
## 그래프 해석
{interpret}

![모델 A 임계값 스윕](../out/fig_sweep_A.png)

그림 1. 모델 A에서 TL=TH를 변화시킨 정확도–평균 사이클 관계. 각 점의 TH를 표기하고 TH=63을 강조하였으며, 97.0% Reference 정확도를 점선으로 나타내었다. 동일 좌표의 임계값은 묶어서 표기하였다. Malgun Gothic, PNG 200 dpi이며 편집용 SVG를 함께 제공하였다.

## 한계 및 연구 해석
- 사전 지정점 대비 가장 빠른 측정점(TH={fast['TH']})의 정확도 차이는 {fast['accuracy']-selected['accuracy']:+.1f}%p, 평균 사이클 차이는 {fast['avg_cycles']-selected['avg_cycles']:+.2f} cycle이었다. 경로 적응 기능의 동작과 성능상의 이득을 구분하였으며, 원본 입력에서 TH=63이 더 우수하다고 주장하지 않았다.
- 비지배점은 정확도를 최대화하고 사이클을 최소화하는 두 목적에 대해 다른 측정점이 두 지표 모두 나쁘지 않으면서 하나 이상 더 좋은 경우를 제외하여 계산하였다. 같은 좌표를 갖는 TH는 동등한 측정점으로 유지하였다.
- 동일 입력 집합에서 임계값을 탐색하고 성능을 보고하였으므로, 사후 선택 동작점의 성능을 독립 테스트 결과로 해석하지 않았다. 일반화 주장에는 별도 validation/test 분리와 더 다양한 입력이 필요하다.
- Score Margin은 확률로 보정된 신뢰도가 아니다. Hard 경로 증가가 개별 입력의 정답을 보장하지 않으며 정확도는 임계값에 대해 단조 증가할 필요가 없다.
- TL=TH이므로 Medium 구간은 비어 있다. 본 결과로 3경로 설계의 이득이나 entropy 대비 우월성, 통계적 유의성을 입증하지 않았다.
- 그래프의 Reference 97.0%는 요청된 비교 기준선이다. 새로운 Reference 하드웨어 측정을 수행한 것으로 표시하지 않았다.

## 재현성 및 수행 시간
- 시작: {manifest['started_at']}; 완료: {completed['completed_at']}.
- 기준점 검증과 나머지 15조건을 포함한 실제 시뮬레이션 경과 시간은 약 {wall_minutes:.1f}분이었다. 분석·게시 시간은 여기에 포함하지 않았다.
- 착수 시 예상: 시뮬레이션·분석·그림 검토·게시 포함 40–70분. 예상과 실제를 구분하였다.
- [원시 CSV](../rtl/sweep_A.csv), [실행별 로그 및 시간](exp1_artifacts/run_evidence.json), [입력·RTL·가중치 SHA-256](exp1_artifacts/manifest.json), [실행기](exp1_artifacts/run_sweep_a.py), [분석·그림 생성기](exp1_artifacts/analyze_sweep_a.py). 실행기와 분석기는 실제 실행 이력이며 원래 work/outputs 디렉터리 배치를 전제로 한다. 이 artifacts 폴더에서 그대로 실행하는 용도는 아니다.
- 재실행은 명시된 실험 커밋의 별도 체크아웃에서 공식 입력을 배치한 뒤 `cd rtl` 및 `bash run_sweep.sh A`를 사용한다. 입력 파일은 저장소에 추가하지 않았다. Python 실행기의 스윕은 같은 결과를 얻도록 원본과 동일한 16개 임계값과 컴파일 인수를 사용하였다.
- Python 3.12.14, Icarus Verilog 12.0(devel), Matplotlib 3.10.8을 사용하였다. 기존 실험 2와 동일한 로컬 환경에서 수행하였다.
- 실험 1의 모델 A 결과만 포함하였다. 선택 항목인 모델 B 및 실험 3의 완료를 의미하지 않는다.
'''
(PKG/'results_hs/exp1_sweep_A.md').write_text(text,encoding='utf-8')
shutil.copy2(OUT/'sweep_A.csv',PKG/'rtl/sweep_A.csv')
evidence={p.name:p.read_text(encoding='utf-8',errors='replace') for p in sorted((OUT/'logs').glob('*'))}
(PKG/'results_hs/exp1_artifacts/run_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
for name in ['manifest.json','completed.json','include_hash.json','environment.json']:shutil.copy2(OUT/name,PKG/'results_hs/exp1_artifacts'/name)
for name in ['run_sweep_a.py','analyze_sweep_a.py']:shutil.copy2(ROOT/name,PKG/'results_hs/exp1_artifacts'/name)
print(json.dumps({'selected':selected,'frontier_thresholds':[r['TH'] for r in front],'accuracy_range':[min(r['accuracy'] for r in rows),best]},ensure_ascii=False))
