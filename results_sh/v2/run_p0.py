"""Reproducible P0 analyses from prepare.py caches (CPU float, no RTL)."""
from common import *
import argparse
from scipy.stats import rankdata,binomtest

def wilson(k,n):
    z=1.959963984540054;p=k/n;den=1+z*z/n;mid=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return 100*(mid-half),100*(mid+half)

def verify_optimizer():
    rng=np.random.default_rng(11)
    for n in [9,25,40]:
        for rep in range(12):
            d={'y':rng.integers(0,3,n),'margin':rng.integers(0,8,n).astype(float),'macs':np.array([10,18,30]),'baseline_mac':29,**{p:rng.integers(0,3,n) for p in ['pred_early','pred_light','pred_full']}}
            idx=np.arange(n);th,_,_=boundary(d,idx)
            for two in [True,False]:
                q=pick(d,idx,two);rows=[summarize(d,t,t2) for i,t in enumerate(th) for t2 in ([t] if two else th[i:])];ok=[r for r in rows if r['correct']>=q['full_correct']-int(np.floor(.005*n))];expected=min(ok,key=lambda r:(r['avg_mac'],-r['correct'],r['t_low'],r['t_high']))
                assert q==expected,(q,expected)
    return {'random_tied_cases':36,'path_variants':2,'comparisons':72,'result':'PASS','seed':11}

def reported(d,key):
    # Recover unrounded quantile thresholds underlying existing table_modes files.
    qs={'mnist_A':(.06,.06),'mnist_B':(.10,.18),'wm811k_B':(.42,.58)}[key]
    lo,hi=np.quantile(d['margin'],qs);return summarize(d,lo,hi)

def folds_for(n,seed):
    ix=np.random.default_rng(seed).permutation(n);half=n//2
    return [ix[:half],ix[half:]]

def independence(data):
    folder=OUT/'01_independence';rows=[];oofrows=[];baselines=[];splits={};points={}
    for key,d in data.items():
        n=len(d['y']);idx=np.arange(n);two=key=='mnist_A';points[key]=reported(d,key)
        for name in ['reported_quantile','legacy_grid25','exact']:
            q=points[key] if name=='reported_quantile' else pick(d,idx,two,name)
            baselines.append({'model':key,'protocol':name,**q})
        splits[key]={}
        for seed in SEEDS:
            folds=folds_for(n,seed);splits[key][seed]={'A':folds[0].tolist(),'B':folds[1].tolist()}
            assert not np.intersect1d(*folds).size
            assert np.array_equal(np.sort(np.r_[tuple(folds)]),idx)
            for method in ['exact','legacy_grid25']:
                op=np.empty(n,dtype=int);om=np.empty(n,dtype=int)
                for fold in range(2):
                    cal=folds[fold];test=folds[1-fold];q=pick(d,cal,two,method);r=summarize(d,q['t_low'],q['t_high'],test)
                    rows.append({'model':key,'method':method,'seed':seed,'direction':['A_to_B','B_to_A'][fold],'calibration_n':len(cal),'calibration_accuracy_pct':q['accuracy_pct'],'calibration_full_pct':q['full_accuracy_pct'],'fallback_all_hard':q.get('fallback_all_hard',False),**r})
                    op[test],om[test]=route(d,q['t_low'],q['t_high'],test)
                acc=100*np.mean(op==d['y']);full=100*np.mean(d['pred_full']==d['y']);mac=float(d['macs'][om].mean());cnt=np.bincount(om,minlength=3)
                oofrows.append({'model':key,'method':method,'seed':seed,'n':n,'correct':int(np.sum(op==d['y'])),'accuracy_pct':acc,'full_accuracy_pct':full,'delta_pp':acc-full,'avg_mac':mac,'mac_saving_hard_pct':100*(1-mac/d['macs'][2]),'mac_saving_baseline_pct':100*(1-mac/float(d['baseline_mac'])),'easy_pct':100*cnt[0]/n,'medium_pct':100*cnt[1]/n,'hard_pct':100*cnt[2]/n,'budget_violation':bool(acc<full-.5-1e-10)})
        print('independence',key,flush=True)
    summaries=[]
    for key in data:
        for method in ['exact','legacy_grid25']:
            rr=[r for r in oofrows if r['model']==key and r['method']==method];s={'model':key,'method':method,'repeats':5,'budget_violation_repeats':sum(r['budget_violation'] for r in rr)}
            for m in ['accuracy_pct','delta_pp','avg_mac','mac_saving_hard_pct','mac_saving_baseline_pct','easy_pct','medium_pct','hard_pct']:
                s[m+'_mean']=float(np.mean([r[m] for r in rr]));s[m+'_sd']=float(np.std([r[m] for r in rr],ddof=1))
            summaries.append(s)
    csvwrite(folder/'fold_results.csv',rows);csvwrite(folder/'oof_by_seed.csv',oofrows);csvwrite(folder/'summary.csv',summaries);csvwrite(folder/'same_set_comparison.csv',baselines);dump(folder/'split_indices.json',splits);dump(folder/'reported_points.json',points)
    plt=plotsetup();fig,axs=plt.subplots(1,2,figsize=(11,4.5));x=np.arange(3)
    for j,(field,label) in enumerate([('delta_pp','Full 대비 평가 정확도 차이 (%p)'),('mac_saving_hard_pct','Hard 대비 평균 MAC 절감 (%)')]):
        for off,method,color in [(-.12,'exact','#16845c'),(.12,'legacy_grid25','#657b91')]:
            s=[r for r in summaries if r['method']==method];axs[j].errorbar(x+off,[r[field+'_mean'] for r in s],yerr=[r[field+'_sd'] for r in s],fmt='o',capsize=4,color=color,label=method+' 2-fold')
        ref=[r for r in baselines if r['protocol']=='reported_quantile'];axs[j].scatter(x,[r[field] for r in ref],marker='x',c='#b14646',label='기존 동일셋 선정');axs[j].set_xticks(x,list(data));axs[j].set_ylabel(label);axs[j].grid(alpha=.15)
    axs[0].axhline(-.5,color='#a73f58',ls='--',lw=1,label='선정 손실 예산 -0.5%p');axs[0].legend(fontsize=8);fig.suptitle('임계값 선정·평가 분리: 5개 seed의 OOF 평균 ± 표준편차');fig.tight_layout();savefig(fig,folder,'fig_twofold');plt.close(fig)
    texts=[]
    for s in summaries:
        if s['method']!='exact':continue
        q=points[s['model']];texts.append(f"{s['model']}에서 기존 동일셋 동작점의 정확도 {q['accuracy_pct']:.2f}% 및 Hard 대비 MAC 절감 {q['mac_saving_hard_pct']:.2f}%와 비교하여, 경계 전수 탐색의 교차 평가 정확도는 {s['accuracy_pct_mean']:.2f} ± {s['accuracy_pct_sd']:.2f}%, MAC 절감은 {s['mac_saving_hard_pct_mean']:.2f} ± {s['mac_saving_hard_pct_sd']:.2f}%로 나타났다. Full 대비 차이는 {s['delta_pp_mean']:+.2f} ± {s['delta_pp_sd']:.2f}%p였으며, 0.5%p 손실 예산을 넘은 반복은 5회 중 {s['budget_violation_repeats']}회였다.")
    md=f'''# 작업 1: 임계값 선정의 독립성

출처: main `{BASE_COMMIT}`, `out/adapath_*.pt`, `data_test/*_test.npz`, 원본 `collect()` / `model.py` / `arch.mode_macs()`. 파일 SHA와 환경은 `../provenance/manifest.json`. 추론 seed={INFERENCE_SEED}, 분할 seed={SEEDS}.

## 방법

고정 가중치를 사용하고 각 seed의 무작위 순열을 반으로 나누어 A에서 선정/B에서 평가, B에서 선정/A에서 평가하였다. MNIST는 5,000/5,000장, WM은 477/477장이다. 클래스 층화는 적용하지 않았다. 두 평가 절반을 합친 OOF 결과 한 개가 반복 한 회이며, 5회 표준편차는 ddof=1이다. 같은 데이터를 재사용하므로 5회가 독립 데이터셋이거나 표준편차가 평균의 신뢰구간이라는 의미는 아니다.

선정은 **선정 절반의 Full 정답 수 − floor(0.005×선정 표본 수)** 이상을 만족하는 최소 MAC이다. 평가 절반에서 0.5%p 조건은 강제하지 않는다. 모델 A는 T_low=T_high, 모델 B/WM은 두 임계값을 탐색하였다. exact 동점은 MAC, 높은 정확도, 낮은 T_low, 낮은 T_high 순으로 결정하였다. legacy_grid25는 원본과 같이 MAC 동률 중 순회상 첫 후보를 사용하였다.

`exact`는 동일 점수 묶음을 분리하지 않는 모든 경계(전부 Easy/Hard 포함)를 대상으로 한다. 2차원 최적화는 정확도 누적합과 prefix-max로 각 T_high의 최소 feasible T_low를 찾아 전수 결과와 동일한 최적값을 계산한다. 작은 무작위·동점 사례 72개에서 독립적인 이중 루프와 대조했다(`../provenance/algorithm_checks.json`). `legacy_grid25`는 기존 코드의 2~98 분위수 25개 후보를 선정 절반에서만 만들었다. 후보 해상도 차이와 데이터 분할 차이를 분리하여 읽어야 한다.

**한계:** 이 절차는 고정 모델에 대한 임계값 선택/평가 누출을 줄인 사후 재분할이다. 기존 테스트셋이 이미 모델 설계 과정에서 관찰되었으므로 완전히 미사용된 외부 테스트셋을 새로 확보한 것은 아니다. train.py는 epoch마다 test를 출력하지만 마지막 epoch를 저장한다. 별도 재학습·모델 선택 검증은 수행하지 않았다.

## 기존/동일셋 비교

기존 보고서의 반올림 임계값을 다시 입력하면 경계 표본이 달라질 수 있어 원래 분위수(A 6/6%, B 10/18%, WM 42/58%)를 비반올림 값으로 재구성하였다. `reported_points.json`에 정확한 값을 남겼다. literal 1.161/1.599/2.593/0.210/0.643 결과도 통계 작업 파일에 별도로 저장한다.

{table(baselines,[('model','대상'),('protocol','선정 방식'),('t_low','T_low'),('t_high','T_high'),('accuracy_pct','정확도 %'),('avg_mac','평균 MAC'),('mac_saving_hard_pct','Hard 대비 %'),('mac_saving_baseline_pct','Baseline 대비 %'),('easy_pct','Easy %'),('medium_pct','Medium %'),('hard_pct','Hard %')])}

## 5회 교차 평가 요약

평균 ± 표준편차는 summary.csv에 모두 저장하였다. 아래는 평균과 정확도 SD이며, 방향별 선정 임계값은 [fold_results.csv](fold_results.csv)에 60개 결과를 제공한다.

{table(summaries,[('model','대상'),('method','탐색'),('accuracy_pct_mean','정확도 평균 %'),('accuracy_pct_sd','SD %p'),('mac_saving_hard_pct_mean','MAC 절감 평균 %'),('mac_saving_hard_pct_sd','SD %p'),('easy_pct_mean','Easy 평균 %'),('medium_pct_mean','Medium 평균 %'),('hard_pct_mean','Hard 평균 %'),('budget_violation_repeats','예산 초과 /5')])}

## 보고서 반영 문단

임계값 선택과 평가의 직접적인 재사용을 줄이기 위하여 고정 가중치 모델에 대해 2-fold 교차 평가를 수행하였다. 각 분할의 절반에서 Full 정확도 대비 손실 0.5%p 이내의 최소 MAC 동작점을 선정한 뒤 다른 절반에 고정 적용하였으며, 5개의 seed로 반복하였다.

'''+ '\n\n'.join(texts)+'''

MAC은 arch.mode_macs()를 사용하였다. Hard에는 Early FC 비용이 포함되므로, 이를 제외한 물리 Baseline 대비 절감률을 별도 열로 제시하였다. MAC 변화는 새 에너지·지연 측정 결과가 아니다.

권장 위치: **3.3 표 7 다음**, WM 결과는 3.9에 함께 인용; 4.2의 “미수행” 한계를 위 범위로 갱신.

그림 캡션: **고정 모델의 임계값 선택·평가를 분리한 2-fold 결과. 점과 오차막대는 5개 분할 seed의 OOF 평균과 표본 표준편차이며, 기존 동일셋 동작점을 함께 표시하였다.**

원시 결과: fold_results.csv(30개 방향별 결과×2 탐색법), oof_by_seed.csv(반복별 통합), summary.csv(평균·SD), split_indices.json(모든 sample ID). 재실행: `python results_sh/v2/01_independence/analyze.py --cache <cache>`.
'''
    (folder/'README.md').write_text(md,encoding='utf8');return points

def auc(y,s):
    n1=int(y.sum());n0=len(y)-n1
    return float((rankdata(s)[y].sum()-n1*(n1+1)/2)/(n1*n0))

def metrics(data):
    folder=OUT/'02_metrics';rows=[];sweep=[];cvs=[];plt=plotsetup();fig,axs=plt.subplots(1,2,figsize=(11.5,4.7));d=data['mnist_A'];idx=np.arange(len(d['y']));z=d['early_logits'].astype(float);shift=z-z.max(1,keepdims=True);p=np.exp(shift);p/=p.sum(1,keepdims=True);entropy=-np.sum(p*np.log(p),1);scores={'Score Margin':d['margin'],'Max softmax':p.max(1),'Negative entropy':-entropy,'Top-1 logit':z.max(1)};correct=d['pred_early']==d['y']
    for name,s in scores.items():
        q=pick(d,idx,True,score=s);q.update(metric=name,auroc=auc(correct,s));rows.append(q)
        th,k,(ce,cl,cf)=boundary(d,idx,s);c=cf+ce[-1]-ce;mac=(d['macs'][2]*k+d['macs'][0]*(len(idx)-k))/len(idx);acc=100*c/len(idx)
        pareto=acc>np.r_[-np.inf,np.maximum.accumulate(acc)[:-1]]
        for j in range(len(th)):sweep.append({'metric':name,'threshold':th[j],'n_hard':k[j],'correct':c[j],'accuracy_pct':acc[j],'avg_mac':mac[j],'pareto':bool(pareto[j])})
        axs[0].plot(mac[pareto]/1000,acc[pareto],label=name,c=COLORS[name],lw=1.5);axs[0].scatter(q['avg_mac']/1000,q['accuracy_pct'],c=COLORS[name],s=26)
        for seed in SEEDS:
            ff=folds_for(len(idx),seed);op=np.empty(len(idx),int);om=np.empty(len(idx),int)
            for i in range(2):
                q2=pick(d,ff[i],True,score=s);op[ff[1-i]],om[ff[1-i]]=route(d,q2['t_low'],q2['t_high'],ff[1-i],s)
            cvs.append({'metric':name,'seed':seed,'accuracy_pct':100*np.mean(op==d['y']),'avg_mac':float(d['macs'][om].mean()),'hard_saving_pct':100*(1-d['macs'][om].mean()/d['macs'][2])})
    axs[0].axhline(100*np.mean(d['pred_full']==d['y']),ls=':',c='#777777',label='Full accuracy');axs[0].set(xlabel='평균 MAC / 이미지 (천)',ylabel='정확도 (%)',title='동일셋 경계 전수 탐색 Pareto');axs[0].legend(fontsize=8);axs[0].grid(alpha=.2)
    axs[1].barh([r['metric'] for r in rows],[r['auroc'] for r in rows],color=[COLORS[r['metric']] for r in rows]);axs[1].set(xlim=(.5,1),xlabel='Early 정답 예측 AUROC',title='정답=양성, 높은 값=쉬움')
    for i,r in enumerate(rows):axs[1].text(r['auroc']+.004,i,f"{r['auroc']:.4f}",va='center',fontsize=9)
    fig.tight_layout();savefig(fig,folder,'fig_metric_comparison');plt.close(fig)
    csvwrite(folder/'operating_points.csv',rows);csvwrite(folder/'all_thresholds.csv',sweep);csvwrite(folder/'oof_by_seed.csv',cvs)
    csvwrite(folder/'metric_scores.csv',({'sample_id':int(i),'early_correct':bool(correct[i]),**{n:float(s[i]) for n,s in scores.items()}} for i in idx))
    cvsummary=[]
    for name in scores:
        rr=[r for r in cvs if r['metric']==name];cvsummary.append({'metric':name,**{m+'_mean':float(np.mean([r[m] for r in rr])) for m in ['accuracy_pct','avg_mac','hard_saving_pct']},**{m+'_sd':float(np.std([r[m] for r in rr],ddof=1)) for m in ['accuracy_pct','avg_mac','hard_saving_pct']}})
    csvwrite(folder/'oof_summary.csv',cvsummary)
    costs=[{'metric':'Score Margin','operation_count':'16-leaf RTL: 15 merge nodes, each 3 comparison expressions (winner + two candidate maxima), mux; 1 subtraction','approximation':'45 syntactic comparisons before constant folding, not a measured gate count; no exp/log/div'}, {'metric':'Max softmax (direct)','operation_count':'10 exp; 9 sum additions; 10 divisions (or 1 reciprocal + 10 multiplications); max via 9 comparisons','approximation':'Finite-precision exp and reciprocal approximation/LUT or iterative arithmetic'}, {'metric':'Entropy (direct)','operation_count':'softmax above + 10 log + 10 multiplications + 9 additions + sign reversal','approximation':'exp/log/reciprocal approximations; optimized identities reduce counts'}, {'metric':'Top-1 logit','operation_count':'9 comparisons for max; no margin subtraction','approximation':'No transcendental approximation'}]
    csvwrite(folder/'hardware_operations.csv',costs)
    marginrow=rows[0];best=min(rows,key=lambda r:r['avg_mac']);diff=marginrow['avg_mac']-best['avg_mac'];span=max(r['accuracy_pct'] for r in rows)-min(r['accuracy_pct'] for r in rows)
    comparisons=' '.join(f"{r['metric']} 대비 Margin의 MAC은 {r['avg_mac']-marginrow['avg_mac']:.2f}개({100*(r['avg_mac']-marginrow['avg_mac'])/r['avg_mac']:.3f}%) 적었다." for r in rows[1:])
    md=f'''# 작업 2: 난이도 지표 비교 (모델 A)

출처: main `{BASE_COMMIT}`, MNIST 10,000장, `collect()` 호출의 원본 AdaPathNet forward hook으로 Early 로짓을 수집하였다. 추론 seed={INFERENCE_SEED}; 파일·환경 해시: `../provenance/manifest.json`. 네 지표는 같은 가중치·이미지·후단 예측·MAC을 사용한다. 온도 보정은 수행하지 않았고 softmax 온도는 1이다. 엔트로피는 자연로그를 사용하며, 순위를 “높을수록 쉬움”으로 통일하기 위해 -entropy를 탐색하였다. 따라서 원래 엔트로피의 Easy 조건은 H≤-threshold이다.

AUROC는 Early 정답을 양성으로 하여 동점 평균 순위로 계산했다. 전수 곡선은 각 지표의 모든 점수 경계(동점 묶음, 전부 Easy/Hard 포함)를 평가하였다. **그림의 Pareto와 선정점은 동일셋 탐색 결과로 낙관 편향 가능성이 있다.** 같은 절차의 독립 절반 평가를 5 seed로 수행한 `oof_summary.csv`도 함께 제공한다. 각 지표의 정확도 제약은 Full 대비 -0.5%p이며 동률 규칙은 작업 1과 같다.

{table(rows,[('metric','지표'),('auroc','AUROC'),('accuracy_pct','정확도 %'),('avg_mac','평균 MAC'),('mac_saving_hard_pct','Hard 절감 %'),('t_high','Easy 임계값')])}

{table(cvsummary,[('metric','지표'),('accuracy_pct_mean','OOF 정확도 평균'),('accuracy_pct_sd','SD'),('hard_saving_pct_mean','OOF MAC 절감 평균 %'),('hard_saving_pct_sd','SD %p')])}

## 분석적 회로 비용

{table(costs,[('metric','지표'),('operation_count','연산 종류·개수'),('approximation','구현 주의')])}

위 수는 순진한 직접 수식 또는 저장소 RTL 구조의 연산 수이며 합성 후 셀 수·면적·지연·사이클 수가 아니다. 모든 방식의 임계값 비교 1개는 공통 비용으로 생략하였다. Margin은 최대값뿐 아니라 2위가 필요하므로 Top-1 logit보다 단순하다고 할 수 없다. 10개 입력 Top-2를 별도 최적화하면 고정 토너먼트에서 최대값 탐색 9회와 승자에게 진 후보 최대 3회 비교로 구현할 수도 있으나 본 RTL의 실제 합성 게이트 수를 뜻하지 않는다.

max-softmax의 **판정만** 필요하면 최대값을 빼서 exp(최대)=1로 두고 나머지 9개 exp의 합과 역임계값을 비교하여 나눗셈을 제거할 수도 있다. 엔트로피도 H=log Z−Σp_i z_i의 항등식으로 log 호출 수를 줄일 수 있다. 따라서 “반드시 exp 10개와 나눗셈 10개를 별도 회로로 구현해야 한다”는 주장은 피한다. LUT/구간 근사·시간 다중화 역시 가능하며, 비용의 실제 우열은 정밀도와 합성 조건에 따라 달라진다. 본 분석에서는 측정하지 않은 면적·지연 수치를 제시하지 않는다.

## 보고서 반영 문단

동일 Early Classifier의 로짓을 이용하여 Score Margin, 최대 softmax 확률, 엔트로피 및 Top-1 로짓을 비교하였다. Score Margin의 Early 정답 예측 AUROC는 {marginrow['auroc']:.4f}였으며, Full 대비 정확도 손실 0.5%p 이내에서 정확도 {marginrow['accuracy_pct']:.2f}%, 평균 {marginrow['avg_mac']:.2f} MAC을 얻었다. 동일 제약의 최소 MAC 지표는 {best['metric']}이었고, Margin과의 차이는 {diff:.2f} MAC/이미지({100*diff/best['avg_mac']:.3f}%)였다. 네 선정점의 정확도 범위 폭은 {span:.2f}%p였다. Score Margin은 확률 정규화·초월함수를 사용하지 않는다는 구현상 이점이 있으나, Top-1 로짓보다 연산 수가 적지는 않으므로 네 지표 중 절대 최소 회로 비용이라고 결론짓지 않았다. 회로 비용과 예측 성능의 절충으로 해석하였다.

권장 위치: **3.2 말미 또는 3.3 표 7 뒤**, 1장의 엔트로피 일반화 문장도 함께 수정.

{comparisons} 그러나 AUROC는 Max softmax가 가장 높았다. 2-fold OOF 평균 정확도는 Margin 97.022%, Max softmax 96.992%, -entropy 96.984%, Top-1 97.000%였으며 모든 지표가 일부 분할에서 선정 예산을 벗어났다. 따라서 동일셋 MAC 순위를 독립 평가의 일관된 우월성으로 확대하지 않았다.

그림 캡션: **모델 A의 네 난이도 지표에 대한 동일셋 정확도–MAC Pareto와 Early 정답 예측 AUROC. 점은 Full 대비 손실 0.5%p 예산의 최소 MAC 동작점이다. MAC에는 지표 산출 회로의 비-MAC 연산을 포함하지 않았다.**

재실행: `python results_sh/v2/02_metrics/analyze.py --cache <cache>`.
''';(folder/'README.md').write_text(md,encoding='utf8')

def statistics(data,points):
    folder=OUT/'03_statistics';rows=[];pairs=[];rounded=[]
    literal={'mnist_A':(1.161,1.161),'mnist_B':(1.599,2.593),'wm811k_B':(.210,.643)}
    for key,d in data.items():
        q=points[key];pred,_=route(d,q['t_low'],q['t_high']);full=d['pred_full']==d['y'];ada=pred==d['y'];b=int(np.sum(full&~ada));c=int(np.sum(~full&ada));n=len(ada);p=binomtest(b,b+c,.5).pvalue if b+c else 1.;lo,hi=wilson(int(ada.sum()),n);fl,fh=wilson(int(full.sum()),n)
        r={'model':key,'n':n,'t_low':q['t_low'],'t_high':q['t_high'],'ada_correct':int(ada.sum()),'full_correct':int(full.sum()),'ada_accuracy_pct':100*ada.mean(),'ada_wilson_low_pct':lo,'ada_wilson_high_pct':hi,'full_accuracy_pct':100*full.mean(),'full_wilson_low_pct':fl,'full_wilson_high_pct':fh,'b_full_correct_ada_wrong':b,'c_full_wrong_ada_correct':c,'both_correct':int(np.sum(full&ada)),'both_wrong':int(np.sum(~full&~ada)),'delta_pp':100*(ada.mean()-full.mean()),'mcnemar_exact_two_sided_p':p};rows.append(r)
        for i in range(n):pairs.append({'model':key,'sample_id':i,'full_correct':bool(full[i]),'ada_correct':bool(ada[i]),'y':int(d['y'][i]),'pred_full':int(d['pred_full'][i]),'pred_adapath':int(pred[i])})
        rounded.append({'model':key,'protocol':'literal_rounded_report_threshold',**summarize(d,*literal[key])})
    # Holm familywise adjustment across the 3 requested comparisons.
    order=np.argsort([r['mcnemar_exact_two_sided_p'] for r in rows]);running=0
    for rank,i in enumerate(order):running=max(running,min(1,(3-rank)*rows[i]['mcnemar_exact_two_sided_p']));rows[i]['holm_adjusted_p']=running
    csvwrite(folder/'statistics.csv',rows);csvwrite(folder/'paired_predictions.csv',pairs);csvwrite(folder/'rounded_threshold_sensitivity.csv',rounded);dump(folder/'statistics.json',{'source_commit':BASE_COMMIT,'seed':INFERENCE_SEED,'rows':rows})
    plt=plotsetup();fig,axs=plt.subplots(1,3,figsize=(10,4.4))
    for ax,r in zip(axs,rows):
        for x,prefix,color,label in [(0,'full','#717780','Full'),(1,'ada','#16845c','AdaPath')]:
            v=r[prefix+'_accuracy_pct'];lo=r[prefix+'_wilson_low_pct'];hi=r[prefix+'_wilson_high_pct'];ax.errorbar(x,v,yerr=[[v-lo],[hi-v]],fmt='o',color=color,capsize=4);ax.annotate(f'{v:.2f}%',(x,v),xytext=(10,0),textcoords='offset points',fontsize=8)
        ax.set_xticks([0,1],['Full','AdaPath']);ax.set_xlim(-.4,1.6);ax.set_title(r['model']+'\n'+f"n={r['n']}, exact p={r['mcnemar_exact_two_sided_p']:.3g}",fontsize=10);ax.grid(alpha=.15)
    axs[0].set_ylabel('정확도 및 Wilson 95% 구간 (%)');fig.suptitle('기존 선정 동작점: 같은 입력에 대한 쌍 비교 (패널별 y축 범위 상이)');fig.tight_layout();savefig(fig,folder,'fig_accuracy_ci');plt.close(fig)
    paras=[]
    for r in rows:paras.append(f"{r['model']}(n={r['n']})의 AdaPath 정확도는 {r['ada_accuracy_pct']:.2f}% (Wilson 95% CI {r['ada_wilson_low_pct']:.2f}–{r['ada_wilson_high_pct']:.2f}%), Full 정확도는 {r['full_accuracy_pct']:.2f}% ({r['full_wilson_low_pct']:.2f}–{r['full_wilson_high_pct']:.2f}%)로 나타났다. Full만 정답인 쌍 b={r['b_full_correct_ada_wrong']}, AdaPath만 정답인 쌍 c={r['c_full_wrong_ada_correct']}에 대한 양측 McNemar exact p-value는 {r['mcnemar_exact_two_sided_p']:.6g}였다(Holm 보정 p={r['holm_adjusted_p']:.6g}).")
    md=f'''# 작업 3: 통계적 비교

출처: main `{BASE_COMMIT}`, 제공 테스트 NPZ와 모델 체크포인트, 고정 float 추론(seed={INFERENCE_SEED}). 파일 해시·버전은 `../provenance/manifest.json`. 기존 25-분위수 보고점의 비반올림 임계값(`../01_independence/reported_points.json`)을 사용하였다. 요청된 모델 A literal 1.161과 B/WM의 소수 3자리 값에 대한 차이는 `rounded_threshold_sensitivity.csv`에 별도 제공한다.

Wilson 구간은 z=1.959963984540054를 사용했다. b=Full 정답·AdaPath 오답, c=Full 오답·AdaPath 정답으로 정의하였다. McNemar exact는 discordant b+c에 대한 Binomial(n=b+c,p=0.5)의 **양측 검정**이며 b+c=0이면 p=1로 정의하였다. 세 비교에 대해 Holm 보정도 함께 제공하였다.

{table(rows,[('model','대상'),('n','n'),('ada_correct','Ada 정답'),('full_correct','Full 정답'),('b_full_correct_ada_wrong','b'),('c_full_wrong_ada_correct','c'),('delta_pp','차이 %p'),('mcnemar_exact_two_sided_p','양측 p'),('holm_adjusted_p','Holm p')])}

## 보고서 반영 문단

'''+ '\n\n'.join(paras)+'''

주최 측 input_1000.txt는 고유 100장을 10회 반복한 자료이므로 1,000개의 독립 표본으로 간주할 수 없어 본 통계 검정에서 제외하였다.

**해석 제한:** 기존 동작점은 같은 테스트 라벨을 사용해 선정되었으므로 이 구간과 p-value는 사후 기술적 비교이며 선택 편향이 제거된 확증 검정이 아니다. 비유의 결과는 동등성이나 0.5%p 비열등성의 증거가 아니다. 작업 1의 교차 평가는 임계값 선택 독립성에 관한 별도 근거로 제시하며, 공유된 선정 데이터 때문에 단순 OOF Binomial p-value를 새 확증 결과로 만들지 않았다. WM은 공정 lot/wafer 계보가 없는 NPZ이므로 표본 간 공정 상관을 반영하지 못한 이미지 단위 구간이다.

권장 위치: **3.3 표 7 다음**, WM 값은 **3.9 표 14 다음**, 한계는 **4.2**.

그림 캡션: **기존 선정 동작점의 AdaPath와 Full 정확도 및 이미지 단위 Wilson 95% 구간. 구간 중첩 여부 대신 같은 이미지의 불일치 쌍에 대한 McNemar exact 결과를 별도 표에 제시하였다.**

재실행: `python results_sh/v2/03_statistics/analyze.py --cache <cache>`.
''';(folder/'README.md').write_text(md,encoding='utf8')

def main(task='all'):
    p=argparse.ArgumentParser();p.add_argument('--cache',required=True);a=p.parse_args();data=load_cache(a.cache);dump(OUT/'provenance'/'algorithm_checks.json',verify_optimizer())
    points={k:reported(d,k) for k,d in data.items()}
    if task in ['all','independence']:points=independence(data)
    if task in ['all','metrics']:metrics(data)
    if task in ['all','statistics']:statistics(data,points)
    print('P0 complete',task,flush=True)
if __name__=='__main__':main()
