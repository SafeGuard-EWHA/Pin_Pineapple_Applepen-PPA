"""Class-wise and error analyses; repository-only reproducibility audit."""
from common import *
from run_p0 import reported
import argparse,re
from collections import Counter

def wm_classes(data):
    folder=OUT/'04_wm_classes';d=data['wm811k_B'];q=reported(d,'wm811k_B');pred,mode=route(d,q['t_low'],q['t_high']);classes=d['classes'].tolist();rows=[];matrices={}
    for label,pp in [('Baseline_Full',d['pred_full']),('AdaPath',pred)]:
        cm=np.zeros((4,4),int);np.add.at(cm,(d['y'],pp),1);matrices[label]=cm
        csvwrite(folder/('confusion_'+label+'.csv'),[{'true_class':classes[i],**{classes[j]:int(cm[i,j]) for j in range(4)}} for i in range(4)])
    for i,name in enumerate(classes):
        ix=d['y']==i;n=int(ix.sum());cnt=np.bincount(mode[ix],minlength=3);aa=int(np.sum(pred[ix]==i));bf=int(np.sum(d['pred_full'][ix]==i));rows.append({'class':name,'n':n,'easy_n':int(cnt[0]),'medium_n':int(cnt[1]),'hard_n':int(cnt[2]),'easy_pct':100*cnt[0]/n,'medium_pct':100*cnt[1]/n,'hard_pct':100*cnt[2]/n,'full_correct':bf,'ada_correct':aa,'full_accuracy_pct':100*bf/n,'ada_accuracy_pct':100*aa/n,'delta_pp':100*(aa-bf)/n,'median_margin':float(np.median(d['margin'][ix]))})
    csvwrite(folder/'class_results.csv',rows);csvwrite(folder/'per_image.csv',({'sample_id':i,'class':classes[int(d['y'][i])],'y':int(d['y'][i]),'margin':float(d['margin'][i]),'mode':int(mode[i]),'pred_full':int(d['pred_full'][i]),'pred_adapath':int(pred[i])} for i in range(len(pred))))
    dump(folder/'results.json',{'base_commit':BASE_COMMIT,'seed':INFERENCE_SEED,'thresholds':q,'classes':rows,'confusion':matrices})
    plt=plotsetup();fig,axs=plt.subplots(1,2,figsize=(11,4.6));x=np.arange(4);bottom=np.zeros(4)
    for mode_name,col in [('Easy','#188657'),('Medium','#e2b339'),('Hard','#be4b4d')]:
        yy=np.array([r[mode_name.lower()+'_pct'] for r in rows]);axs[0].bar(x,yy,bottom=bottom,color=col,label=mode_name)
        for i,v in enumerate(yy):
            if v>7:axs[0].text(i,bottom[i]+v/2,f'{v:.1f}%',ha='center',va='center',fontsize=9,color='white' if mode_name!='Medium' else '#333333')
        bottom+=yy
    axs[0].set(ylim=(0,112),ylabel='클래스 내부 경로 비율 (%)',title='클래스별 계산 배분');axs[0].set_xticks(x,[r['class']+f"\n(n={r['n']})" for r in rows]);axs[0].legend(ncol=3,fontsize=8,loc='upper center')
    for off,key,color,label in [(-.17,'full_accuracy_pct','#737b82','Baseline / Full'),(.17,'ada_accuracy_pct','#188657','AdaPath')]:
        vals=[r[key] for r in rows];axs[1].bar(x+off,vals,width=.34,color=color,label=label)
        for i,v in enumerate(vals):axs[1].text(i+off,v+1,f'{v:.1f}',ha='center',fontsize=8)
    axs[1].set_xticks(x,classes);axs[1].set(ylim=(0,110),ylabel='클래스별 정답률 / recall (%)',title='동일 클래스·동일 입력 비교');axs[1].legend(fontsize=8);fig.tight_layout();savefig(fig,folder,'fig_wm_class_modes');plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10,4.5))
    for ax,(name,cm) in zip(axs,matrices.items()):
        norm=100*cm/cm.sum(1,keepdims=True);im=ax.imshow(norm,vmin=0,vmax=100,cmap='Blues')
        for i in range(4):
            for j in range(4):ax.text(j,i,f'{cm[i,j]}\n{norm[i,j]:.1f}%',ha='center',va='center',color='white' if norm[i,j]>55 else '#222222',fontsize=9)
        ax.set_xticks(np.arange(4),classes,rotation=20);ax.set_yticks(np.arange(4),classes);ax.set(xlabel='예측 클래스',ylabel='실제 클래스',title=name)
    fig.tight_layout();savefig(fig,folder,'fig_wm_confusion');plt.close(fig)
    easiest=max(rows,key=lambda r:r['easy_pct']);hardest=max(rows,key=lambda r:r['hard_pct']);fb=int(matrices['Baseline_Full'][1:,0].sum());ab=int(matrices['AdaPath'][1:,0].sum())
    md=f'''# 작업 4: WM-811K 클래스별 분석

출처: `{BASE_COMMIT}`, `data_test/wm811k_test.npz` 954장, `out/adapath_wm811k_B.pt`, 추론 seed={INFERENCE_SEED}. 입력 해시·모델 환경은 `../provenance/manifest.json`. T_low={q['t_low']:.15g}, T_high={q['t_high']:.15g}인 **기존 보고 동작점**을 기술적으로 분석하였다. 작업 1의 새 교차 평가 임계값과 혼합하지 않는다. Baseline은 같은 가중치의 Full head이며 별도 학습한 모델이 아니다.

{table(rows,[('class','클래스'),('n','n'),('easy_pct','Easy %'),('medium_pct','Medium %'),('hard_pct','Hard %'),('full_accuracy_pct','Full %'),('ada_accuracy_pct','AdaPath %'),('delta_pp','차이 %p')])}

## 보고서 반영 문단

클래스별 경로 배분을 분석한 결과, {easiest['class']}의 Easy 비율이 {easiest['easy_pct']:.2f}%로 가장 높았으며 {hardest['class']}의 Hard 비율이 {hardest['hard_pct']:.2f}%로 가장 높았다. 따라서 계산 배분의 난이도는 클래스의 물리적 복잡성 자체가 아니라 현재 학습된 전단 분류기의 구분 능력과 관련됨을 확인하였다. 클래스별 Full 대비 정확도 차이는 위 표와 같으며, 전체 정확도만으로 결함 종류별 손실을 대표할 수 없었다. 결함 클래스를 none으로 예측한 수는 Full {fb}건에서 AdaPath {ab}건으로 변화하였다. 공정 검사에서는 결함을 정상으로 놓치는 비용이 크므로 평균 MAC 최적화만으로 출하 판정 성능을 보장할 수 없으며, 클래스별 recall 및 정상 오판율 제약을 함께 검토할 필요가 있다.

명확한 패턴을 조기 종료하고 애매한 입력에 후단 계산을 배분하는 설계 의도와 관측된 클래스별 차이를 연결할 수 있으나, 이 결과만으로 실제 공정 lot에서 동일한 이득을 얻는다고 단정하지 않았다. 원자료에서 클래스 균형 추출 후 무작위 분할하였으므로 테스트셋의 클래스별 n은 완전히 같지 않다. 원본 wafer/lot ID가 없어 공정 그룹 단위 독립성은 확인 필요이다.

권장 위치: **3.9 표 14 다음**, 한계는 **4.2**.

그림 캡션 1: **기존 WM 동작점의 클래스별 Easy/Medium/Hard 비율 및 Full/AdaPath recall. 비율의 분모는 각 실제 클래스의 표본 수이다.**

그림 캡션 2: **WM-811K 4-class 혼동 행렬. 각 칸에 표본 수와 실제 클래스 기준 행 정규화 비율을 함께 표시하였다.**

재실행: `python results_sh/v2/04_wm_classes/analyze.py --cache <cache> --repo .`. 이는 기존 테스트셋 동작점의 사후 분석으로 독립 평가를 대체하지 않는다.
''';(folder/'README.md').write_text(md,encoding='utf8');print('WM classes',rows,flush=True)

def errors(data,repo):
    folder=OUT/'05_error_analysis';d=data['mnist_A'];q=reported(d,'mnist_A');pred,mode=route(d,q['t_low'],q['t_high']);x=np.load(repo/'data_test/mnist_test.npz')['x'];wrong=(mode==0)&(pred!=d['y']);ids=np.flatnonzero(wrong);ordered=ids[np.lexsort((ids,-d['margin'][ids]))];hard=np.flatnonzero(mode==2);hard=hard[np.argsort(d['margin'][hard],kind='stable')];hard_selected=hard[np.linspace(0,len(hard)-1,6,dtype=int)];chosen=[('Easy 오답',int(i)) for i in ordered[:6]]+[('Hard 경로',int(i)) for i in hard_selected]
    cnt=Counter((int(d['y'][i]),int(pred[i])) for i in ids);pairs=[{'true_digit':a,'pred_digit':b,'count':c,'fraction_of_easy_errors_pct':100*c/len(ids)} for (a,b),c in sorted(cnt.items(),key=lambda q:(-q[1],q[0]))]
    csvwrite(folder/'easy_error_pairs.csv',pairs);csvwrite(folder/'all_easy_errors.csv',({'sample_id':int(i),'y':int(d['y'][i]),'early_pred':int(pred[i]),'full_pred':int(d['pred_full'][i]),'margin':float(d['margin'][i])} for i in ordered));csvwrite(folder/'selected_examples.csv',({'group':g,'sample_id':i,'y':int(d['y'][i]),'early_pred':int(d['pred_early'][i]),'full_pred':int(d['pred_full'][i]),'margin':float(d['margin'][i])} for g,i in chosen))
    plt=plotsetup();fig,axs=plt.subplots(2,6,figsize=(12.5,6.5))
    for ax,(group,i) in zip(axs.flat,chosen):
        ax.imshow(x[i],cmap='gray',vmin=0,vmax=255);ax.set_xticks([]);ax.set_yticks([]);ax.set_title(f"#{i}  정답 {d['y'][i]}\nEarly {d['pred_early'][i]} / Full {d['pred_full'][i]}\nm={d['margin'][i]:.3f}",fontsize=9)
    fig.text(.01,.72,'Easy 오답\nMargin 상위 6개',rotation=90,va='center',fontsize=10,color='#a73f58');fig.text(.01,.27,'Hard 경로\nMargin 구간별 사례',rotation=90,va='center',fontsize=10,color='#657b91');fig.suptitle(f'MNIST 모델 A: 높은 확신의 오분류와 후단 경로 입력 (T={q["t_high"]:.3f})');fig.subplots_adjust(left=.055,right=.995,bottom=.025,top=.83,hspace=.65,wspace=.15);savefig(fig,folder,'fig_error_examples');plt.close(fig)
    e=int(np.sum(mode==0));n=len(mode);recover=int(np.sum(d['pred_full'][wrong]==d['y'][wrong]));summary={'source_commit':BASE_COMMIT,'inference_seed':INFERENCE_SEED,'n':n,'easy_n':e,'hard_n':len(hard),'easy_wrong_n':len(ids),'easy_wrong_pct_all':100*len(ids)/n,'easy_wrong_pct_easy':100*len(ids)/e,'full_would_recover_easy_errors':recover,'easy_errors_also_wrong_full':len(ids)-recover,'max_margin_easy_error':float(d['margin'][ordered[0]]),'threshold':q['t_high']};dump(folder/'summary.json',summary)
    top='; '.join(f"{r['true_digit']}→{r['pred_digit']} {r['count']}건" for r in pairs[:5])
    md=f'''# 작업 5: 모델 A 오류 분석

출처: `{BASE_COMMIT}`, `data_test/mnist_test.npz`, `out/adapath_mnist_A.pt`, 원본 float 추론(seed={INFERENCE_SEED}); 파일 해시는 `../provenance/manifest.json`. 기존 임계값 T={q['t_high']:.15g}를 적용하였다. literal 1.161도 이 데이터에서 같은 경로 배분을 보인다.

## 보고서 반영 문단

Easy로 판정한 {e:,}장 중 {len(ids)}장이 오분류되었으며, 이는 전체 {n:,}장의 {100*len(ids)/n:.2f}%, Easy 입력의 {100*len(ids)/e:.2f}%에 해당하였다. 높은 Margin의 오분류가 존재하므로 Margin을 정답의 보증으로 해석할 수 없었다. 주요 실제→예측 숫자 쌍은 {top}이었다. 이 Easy 오답 가운데 {recover}건은 Full 경로가 정답을 예측했으며 {len(ids)-recover}건은 Full에서도 오분류되었다. 따라서 조기 종료가 막은 수정 기회와 두 head에 공통인 오류를 분리하였다. 가장 높은 오답 Margin은 {d['margin'][ordered[0]]:.3f}였다.

수치 없이 “매우 드물다”라고 표현하지 않고 위 분모별 비율을 제시하였다. 높은 확신 오류는 학습 분포·모델 표현의 한계를 반영할 수 있으나, 그림만으로 필체나 전처리가 원인이라고 인과적으로 단정하지 않았다. 후단으로 보낸 입력은 낮은 Margin의 모호성을 완화할 기회를 제공하지만 Full도 완전한 분류기는 아니다.

| 항목 | 수치 |
|---|---|
| 전체 / Easy / Hard | {n} / {e} / {len(hard)} |
| Easy 오답 | {len(ids)} |
| 전체 대비 / Easy 내부 오류율 | {100*len(ids)/n:.2f}% / {100*len(ids)/e:.2f}% |
| Full로 회복 가능한 Easy 오답 | {recover} |

권장 위치: **3.5 검증 결과 다음** 또는 **4.2의 정확도 한계**.

그림 캡션: **위 행은 Easy 오답 중 Margin 내림차순 상위 6개, 아래 행은 Hard 입력의 Margin 정렬 위치 0/20/40/60/80/100% 부근 사례이다. 숫자는 원본 NPZ의 0-based sample ID이며 정답, Early·Full 예측과 float Margin을 함께 표시하였다. 표본 선택 규칙을 고정하여 사례만으로 빈도를 판단하는 오류를 피하였다.**

재실행: `python results_sh/v2/05_error_analysis/analyze.py --cache <cache> --repo .`.
''';(folder/'README.md').write_text(md,encoding='utf8');print('errors',summary,flush=True)

def reproducibility(repo):
    folder=OUT/'06_reproducibility';folder.mkdir(parents=True,exist_ok=True);manifest=json.loads((OUT/'provenance/manifest.json').read_text(encoding='utf8'))
    sources=['README.md','python/train.py','python/data_mnist.py','python/data_wm811k.py','python/analyze_margin.py','python/export_int8.py','flow_scripts/queue_final.sh','flow_scripts/synth_v3.sh','flow_scripts/power_A.sh','flow_scripts/sta_one.sh','flow_scripts/vcd_power_odb.tcl','orfs/sta_prelayout.tcl','orfs/reports_final/adapath_A_sta.rpt','orfs/reports_final/power_A_easy.rpt','orfs/designs_final/cfg/adapath_A/config.mk','orfs/designs_final/cfg/adapath_A/constraint.sdc','glsim/run_A.sh','glsim/run_adapath.sh','glsim/run_ref.sh','glsim/tb_gl_A.v','glsim/tb_gl_adapath.v','vivado/submit/make_submit.tcl','vivado/submit/adawave.tcl','evidence/README.md','evidence/gatelevel/model_A_runs.txt','evidence/gatelevel/adapath_B_runs.txt','evidence/gatelevel/sta_and_power_B_ref.txt','out/rtl_data_mnist_A/thresholds.vh','out/rtl_data_mnist/thresholds.vh','out/rtl_data_wm811k/thresholds.vh']
    dump(folder/'source_hashes.json',{'base_commit':BASE_COMMIT,'files':{p:provenance(repo/p) for p in sources}})
    hits=[];pattern=re.compile(r'version|OpenROAD |Yosys |iverilog|vvp |openroad |make DESIGN_CONFIG|read_vcd|clk_period|repeat \(12\)|T_LOW|T_HIGH|--seed|--epochs|--lr|torch.save',re.I)
    for rel in sources:
        for i,line in enumerate((repo/rel).read_text(encoding='utf8',errors='replace').splitlines(),1):
            if pattern.search(line):hits.append({'source':rel,'line':i,'text':line})
    csvwrite(folder/'source_excerpts.csv',hits)
    versions=[{'tool':'Yosys / ABC','original_result_version':'확인 필요','source':'합성 통계/스크립트는 있으나 버전 배너와 커밋 없음','this_analysis':'실행하지 않음'}, {'tool':'OpenROAD','original_result_version':'26Q3-1305-gf552262465','source':'orfs/reports_final/adapath_A_sta.rpt:1 및 power_A_easy.rpt:1','this_analysis':'실행하지 않음'}, {'tool':'OpenSTA','original_result_version':'OpenROAD 내장 사용; 독립 OpenSTA 버전은 확인 필요','source':'flow_scripts/vcd_power_odb.tcl:6–7, openroad report_power','this_analysis':'실행하지 않음'}, {'tool':'Icarus Verilog','original_result_version':'확인 필요','source':'glsim/run_*.sh의 iverilog/vvp 명령, 버전 출력 없음','this_analysis':'실행하지 않음'}, {'tool':'Vivado','original_result_version':'2023.1 (문서·캡처 표기), build 세부값 확인 필요','source':'evidence/README.md:5, 보고서 3.4·그림 7','this_analysis':'실행하지 않음'}, {'tool':'Python','original_result_version':'학습 당시 확인 필요','source':'원본 환경 lock/버전 로그 없음','this_analysis':manifest['python']}, {'tool':'PyTorch','original_result_version':'학습 당시 확인 필요','source':'체크포인트에는 state/arch만 존재','this_analysis':manifest['torch']}]
    csvwrite(folder/'tool_versions.csv',versions)
    commands=[
        {'stage':'Training','command':'cd python; python train.py --arch A --n_class 10 --prefix mnist','data':'MNIST train/test NPZ; test는 epoch별 출력','threshold':'없음','status':'README 명령 예시; 실제 실행 CLI·seed 확인 필요','source':'README.md; python/train.py'},
        {'stage':'Original threshold selection','command':'cd python; python analyze_margin.py --arch A --prefix mnist --out <model_and_data_folder>','data':'MNIST 10000; WM 954, 같은 셋 선정·평가','threshold':'A 1.1608357596/1.1608357596; B 1.5987654805/2.5930354309; WM .2098419857/.6432941723','status':'이번 float 추론으로 기존 보고 동작점 재현','source':'python/analyze_margin.py; out/archA/table_modes_mnist.md; out/table_modes*.md'},
        {'stage':'Integer export','command':'python export_int8.py --arch A --prefix mnist --t_low 1.161 --t_high 1.161','data':'학습 체크포인트; 정수화 calibration 자료는 export 코드 참조','threshold':'RTL A 63/63; B 71/119; WM 13/41','status':'설정 파일 확인, 이번 정수화 재실행 없음','source':'README.md; out/rtl_data_*/thresholds.vh'},
        {'stage':'Synthesis','command':'make DESIGN_CONFIG=./designs/asap7/<variant>/config.mk clean_synth synth','data':'ORFS staged sources + ASAP7','threshold':'각 variant의 thresholds.vh','status':'스크립트 명령 확인, stage 절대 경로 치환·원본 외부 파일 필요','source':'flow_scripts/queue_final.sh:17; synth_v3.sh:20'},
        {'stage':'STA','command':'PLATFORM_DIR=<...> ODB=<...>/1_synth.odb SDC=<...> REPORT=<...> openroad -exit <...>/sta_odb.tcl','data':'합성 ODB; 1000 ps 및 참고 2500 ps SDC','threshold':'해당 설계 고정 설정','status':'스크립트에 저장된 호출; 환경 경로 조정 필요','source':'flow_scripts/sta_one.sh:8–11'},
        {'stage':'A gate simulation','command':'iverilog -g2012 -I. -o gl_adA.vvp adapath_A_net.v std_cell_fn/*.v tb_gl_A.v; vvp gl_adA.vvp +START=1 +VCD=gl_adA_easy.vcd','data':'주최 input_1000.txt의 지정 구간','threshold':'A 63/63','status':'run_A.sh·대표 런 로그 확보; 컴파일 넷리스트/셀 모델 별도','source':'glsim/run_A.sh:4–9'},
        {'stage':'B / Reference gate simulation','command':'bash glsim/run_adapath.sh; bash glsim/run_ref.sh','data':'START 1/15/5, 각 4장','threshold':'B 71/119; Reference 해당 없음','status':'스크립트는 외부 idec_glsim 디렉터리 기준; 복사·경로 조정 필요','source':'glsim/run_adapath.sh; glsim/run_ref.sh'},
        {'stage':'VCD power','command':'PLATFORM_DIR=<...> ODB=<...> SDC=<10ns.sdc> VCD=<run.vcd> SCOPE=tb_gatelevel/dut openroad -exit flow_scripts/vcd_power_odb.tcl','data':'100 MHz, 이미지마다 reset 12 cycle 포함','threshold':'A/B의 고정 RTL 설정','status':'대표 런 기반 추정; VCD 원본과 파일 해시 저장소에 없음','source':'flow_scripts/power_A.sh; queue_final.sh; vcd_power_odb.tcl'},
        {'stage':'Vivado project','command':'vivado -mode batch -source vivado/submit/make_submit.tcl -tclargs <project_folder> <project_name>','data':'top_tb_1000; 고유 100장×10회 입력','threshold':'학습 가중치 상수와 threshold header','status':'프로젝트 생성 명령 확인; 실행 로그 4개는 README에만 열거','source':'vivado/submit/make_submit.tcl:1; evidence/README.md'},
        {'stage':'This P0 analysis','command':'python results_sh/v2/prepare.py --repo . --cache work/v2_cache; python results_sh/v2/run_p0.py --cache work/v2_cache','data':'고정 NPZ; 2-fold×5 seeds 2026–2030','threshold':'보고 동작점·exact·legacy 구분','status':'이번 실행 완료; CPU 2 threads, inference seed 2026','source':'results_sh/v2/provenance/manifest.json'},
        {'stage':'This P1 analysis','command':'python results_sh/v2/run_p1.py --repo . --cache work/v2_cache','data':'P0와 같은 float 예측·NPZ','threshold':'기존 보고 동작점','status':'이번 실행 완료; 새 추론/RTL 실험 없음','source':'results_sh/v2/run_p1.py'}]
    csvwrite(folder/'commands.csv',commands)
    runs=[{'design':'AdaPath_A','run':'Easy','start':1,'n':4,'images':'1–4','mix':'Easy 4','vcd':'gl_adA_easy.vcd','source':'glsim/run_A.sh:7'}, {'design':'AdaPath_A','run':'Hard mix','start':5,'n':4,'images':'5–8','mix':'Hard 1 + Easy 3','vcd':'gl_adA_hard.vcd','source':'glsim/run_A.sh:8'}, {'design':'Baseline_A','run':'Full','start':1,'n':4,'images':'1–4','mix':'Full 4','vcd':'gl_baA.vcd','source':'glsim/run_A.sh:9'}, {'design':'AdaPath_B','run':'Easy','start':1,'n':4,'images':'1–4','mix':'Easy 4','vcd':'gl_ad_easy.vcd','source':'glsim/run_adapath.sh'}, {'design':'AdaPath_B','run':'Medium mix','start':15,'n':4,'images':'15–18','mix':'Medium 2 + Easy 2','vcd':'gl_ad_med.vcd','source':'glsim/run_adapath.sh; evidence/gatelevel/adapath_B_runs.txt'}, {'design':'AdaPath_B','run':'Hard mix','start':5,'n':4,'images':'5–8','mix':'Hard 1 + Easy 3','vcd':'gl_ad_hard.vcd','source':'glsim/run_adapath.sh'}, {'design':'Reference','run':'a/b/c','start':'1/15/5','n':12,'images':'1–4,15–18,5–8','mix':'Full 12','vcd':'gl_ref_a/b/c.vcd','source':'glsim/run_ref.sh'}]
    csvwrite(folder/'vcd_runs.csv',runs);dump(folder/'audit.json',{'base_commit':BASE_COMMIT,'inference_seed':INFERENCE_SEED,'tool_versions':versions,'commands':commands,'vcd_runs':runs,'missing_vivado_logs':[s for s in ['reference_top_tb_1000.log','adapath_A_top_tb_1000.log','adapath_B_top_tb_1000.log','adapath_A_relocated_copy.log'] if not list(repo.rglob(s))]})
    plt=plotsetup();fig,axs=plt.subplots(2,3,figsize=(11,4.6));cards=[('Training','원본 Python/PyTorch 버전: 확인 필요\n체크포인트·구조는 고정 파일로 제공','#eeeeee'),('Threshold selection','기존: 같은 테스트셋에서 선택·평가\n이번: 2-fold × 5 seed 추가','#dceee6'),('Synthesis / STA','OpenROAD 26Q3-1305-gf552262465\nYosys/ABC 버전: 확인 필요','#eeeeee'),('VCD / Power','100 MHz, reset 12 cycle\nVCD 원본·Icarus 버전: 확인 필요','#eeeeee'),('Vivado','2023.1 표기 / top_tb_1000\n전체 실행 로그: 추가 확보 필요','#eeeeee'),('Python analysis v2',f"Python {manifest['python']} / Torch {manifest['torch']}\n파일 해시·분할·예측 기록 저장",'#dceee6')]
    for ax,(name,note,color) in zip(axs.flat,cards):ax.set_facecolor(color);ax.text(.5,.72,name,ha='center',va='center',fontsize=12,weight='bold');ax.text(.5,.35,note,ha='center',va='center',fontsize=9);ax.set_xticks([]);ax.set_yticks([]);[sp.set_visible(False) for sp in ax.spines.values()]
    fig.suptitle('재현성 근거: 원본 하드웨어 흐름과 이번 Python 분석을 구분');fig.tight_layout();savefig(fig,folder,'fig_reproducibility');plt.close(fig)
    md=f'''# 작업 6: 재현성 부록

검토 기준 main `{BASE_COMMIT}`. 저장소 파일만 정적으로 검토하였으며 하드웨어 도구를 설치·실행하거나 과거 버전을 현재 PC에서 추정하지 않았다. 사용 근거의 SHA-256/Git blob은 source_hashes.json, 원문 행 번호는 source_excerpts.csv에 기록하였다. 원본 쉘 스크립트에는 작성자의 절대 경로와 stage 폴더가 있으므로 그대로 실행 가능하다고 안내하지 않는다.

## 도구 버전

{table(versions,[('tool','도구'),('original_result_version','기존 결과의 버전'),('source','근거'),('this_analysis','이번 분석 환경')])}

## 실행 명령 및 입력 조건

{table(commands,[('stage','단계'),('command','기록된 명령/재현 명령'),('data','데이터·분할'),('threshold','임계값'),('status','확인 범위'),('source','출처')])}

## 데이터 분할·학습 설정의 확인 범위

MNIST 준비 코드는 공식 train 60,000장 / test 10,000장 구분을 그대로 저장한다. `data_mnist.py --seed`는 인터페이스에 있으나 build 내부에서 분할에 사용하지 않는다. WM 준비 코드는 클래스당 동일 수를 추출한 뒤 전체를 섞어 20%를 test로 저장하며, `data_wm811k.py`의 seed 기본값은 0이다. 실제 생성 당시 seed 및 원본 wafer/lot ID는 체크포인트·NPZ에 저장되지 않았으므로 확인 필요이다. 이번 분석은 이미 제공된 test 954장을 고정하고 새 2-fold 분할 seed 2026–2030만 바꾸었다.

`train.py`의 기본값은 epochs=30, batch size=128, lr=0.002, Early/Light loss 가중치 각각 0.5이며 Adam 및 CosineAnnealingLR를 사용한다. 이는 코드 기본값이며 각 체크포인트의 실제 학습 명령·seed를 입증하는 실행 로그가 아니다. test 정확도를 epoch마다 출력하므로 모델 개발 단계의 테스트셋 관찰 가능성은 남는다. INT8 export의 기본 calibration 수는 64장이지만 실제 export CLI는 별도 확인 필요이다.

## VCD 런 구성

{table(runs,[('design','설계'),('run','런'),('images','입력 index'),('n','n'),('mix','모드 구성'),('vcd','VCD 파일'),('source','출처')])}

glsim TB의 timescale은 1ns/1ps, always #5이므로 주기 10 ns(100 MHz)이다. reset은 이미지마다 12 cycle이다. 전력 Tcl은 ASAP7 RVT_TT Liberty를 읽는다. 상세 공정·전압·온도 수치와 정확한 PDK/ORFS commit은 별도 확인 필요이며 라이브러리 이름만으로 값을 지어내지 않는다. 보고서의 STA는 1 GHz 제약에서 실패한 slack을 이용한 pre-layout 역산값이며, 100 MHz VCD 평가와 구분한다. 제출 Vivado TB의 1ps 단위 기능 시뮬레이션과도 다르다.

A의 Hard 및 B의 Medium/Hard 모드 에너지는 혼합 런에서 Easy 에너지를 차감한 추정으로 입력별 Easy 에너지가 같다는 가정이 있다. Reference는 합계 12장, Baseline_A는 4장으로 구성되어 있으므로 전체 독립 테스트셋의 직접 전력 평균이 아니다. WM은 B 모드 에너지로 대리 추정했으며 별도 WM VCD 런이 확인되지 않는다.

## 보고서 반영 문단

재현성을 확보하기 위하여 모델 체크포인트·테스트 데이터·분석 코드의 해시와 분할 seed, 동작점 및 입력별 예측을 함께 보존하였다. 하드웨어 결과의 실행 스크립트와 전력 런 구성을 별도 표로 정리하였으며, 저장소 리포트에서 확인한 OpenROAD 버전은 26Q3-1305-gf552262465였다. 확인되지 않은 Yosys/ABC·Icarus 및 학습 당시 Python/PyTorch 버전은 확인 필요로 남겼다. 이번 Python 분석의 실행 환경은 원본 하드웨어 평가 환경과 분리하여 기록하였다. 주최 TB 로그 4개는 evidence README에 열거되어 있으나 실제 파일이 없으므로 전체 로그의 추가 확보가 필요하였다.

권장 위치: **부록 A: 실행 환경과 재현 절차**; 3.6·3.7에서 표를 참조한다.

그림 캡션: **평가 단계별 재현성 근거와 미확인 항목. 연한 녹색은 이번에 추가한 Python 분석 기록이며, 원본 하드웨어 실험을 재실행했다는 의미가 아니다.**

재실행: `python results_sh/v2/06_reproducibility/analyze.py --repo <repository> --cache <cache>`.
''';(folder/'README.md').write_text(md,encoding='utf8');print('reproducibility complete',flush=True)

def main(task='all'):
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True,type=Path);p.add_argument('--cache',required=True);a=p.parse_args();data=load_cache(a.cache)
    if task in ['all','wm']:wm_classes(data)
    if task in ['all','errors']:errors(data,a.repo)
    if task in ['all','repro']:reproducibility(a.repo)
if __name__=='__main__':main()
