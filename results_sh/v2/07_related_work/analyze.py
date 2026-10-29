"""Render a manually source-verified literature comparison; no performance extrapolation."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import *

rows=[
 {'name':'BranchyNet','title':'BranchyNet: Fast Inference via Early Exiting from Deep Neural Networks','authors':'Surat Teerapittayanon; Bradley McDanel; H. T. Kung','venue_year':'ICPR 2016','url':'https://doi.org/10.1109/ICPR.2016.7900006','primary_pdf':'https://arxiv.org/pdf/1709.01686','metric':'softmax entropy','paths':'LeNet 2; AlexNet/ResNet 3','hardware':'CPU/GPU 평가; 전용 RTL 구현은 제시하지 않음','evaluation':'MNIST/CIFAR-10 정확도 및 평균 추론 시간','evidence':'Sec. III-C, IV; Table I','verified_date':'2026-10-29'},
 {'name':'CascadeCNN','title':'CascadeCNN: Pushing the Performance Limits of Quantisation in Convolutional Neural Networks','authors':'Alexandros Kouris; Stylianos I. Venieris; Christos-Savvas Bouganis','venue_year':'FPL 2018','url':'https://arxiv.org/abs/1807.05053','primary_pdf':'https://arxiv.org/pdf/1807.05053','metric':'정렬 확률의 generalized Best-vs-Second-Best (gBvSB)','paths':'저정밀도 종료 / 고정밀도 재계산의 2단계','hardware':'FPGA CNN + ARM CPU softmax/CEU','evaluation':'ImageNet, AlexNet/VGG-16; ZC706/ZCU102 실측 성능·오류 허용량','evidence':'첫 페이지 학회 표기; Sec. III-C Eq.(2), IV-A/C','verified_date':'2026-10-29'},
 {'name':'Shallow-Deep Networks','title':'Shallow-Deep Networks: Understanding and Mitigating Network Overthinking','authors':'Yigitcan Kaya; Sanghyun Hong; Tudor Dumitras','venue_year':'ICML 2019, PMLR 97:3301–3310','url':'https://proceedings.mlr.press/v97/kaya19a.html','primary_pdf':'https://proceedings.mlr.press/v97/kaya19a/kaya19a.pdf','metric':'최대 클래스 확률 (confidence)','paths':'내부 분류기 6 + 최종 1 = 7','hardware':'소프트웨어 모델 분석; 전용 RTL 구현은 제시하지 않음','evaluation':'CIFAR-10/100, Tiny ImageNet; 정확도–FLOPs 예산, unlabeled holdout으로 임계값 설정','evidence':'Sec. 3.1, 5.1; Table 3','verified_date':'2026-10-29'},
 {'name':'AdaPath-NPU','title':'AdaPath-NPU (본 설계)','authors':'본 프로젝트 팀','venue_year':'IDEC 결과보고서 2026','url':f'https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/tree/{BASE_COMMIT}','primary_pdf':'report/결과보고서_PPA.pdf','metric':'정수 로짓 Top-1 − Top-2 Margin','paths':'선정 A: 2 / B: 3','hardware':'Verilog RTL, ASAP7 pre-layout 합성·STA 및 대표 VCD 전력 추정','evaluation':'MNIST/WM 정확도·MAC; 이번 2-fold 분석; 주최 TB 기능 검증','evidence':'보고서 2.3, 3.4–3.9; results_sh/v2','verified_date':'2026-10-29'}]
folder=Path(__file__).resolve().parent
csvwrite(folder/'comparison.csv',rows);dump(folder/'sources.json',{'base_commit':BASE_COMMIT,'seed':'해당 없음: 문헌 검토','verified_on':'2026-10-29','papers':rows})
md='''# 선택 작업 7: 관련 연구 비교

원문과 학회 공식 자료로 서지·판단 지표·구현 범위를 확인한 3편만 포함하였다. 수치 성능을 다른 공정·데이터셋 사이에서 직접 순위화하지 않았다. seed는 문헌 검토에 해당하지 않으며 본 설계의 기준 커밋은 `'''+BASE_COMMIT+'''`이다.

'''+table(rows,[('name','연구'),('metric','판단 지표'),('paths','경로/출구 수'),('hardware','구현'),('evaluation','평가 방식')])+'''

## 보고서 반영 문단

BranchyNet은 entropy 기반 조기 종료와 여러 출구의 공동 학습을 제시하였고, Shallow-Deep Networks는 최대 클래스 확률에 따른 조기 종료와 과도한 후단 계산의 영향을 분석하였다. CascadeCNN은 확률 벡터의 generalized Best-vs-Second-Best로 저정밀도 추론과 고정밀도 재계산을 선택하였다. 따라서 조기 종료 또는 상위 점수 차이의 사용 자체를 새로운 개념으로 주장하지 않았다. 본 설계는 정수 로짓 차이의 비교·감산 회로와 공유 전단부, 제한된 경로 선택 및 주최 인터페이스를 통합하고, ASAP7 합성·STA와 대표 VCD 기반 전력 추정까지 연결한 구현에 초점을 두었다. CascadeCNN의 평가에서는 softmax와 confidence evaluation을 ARM CPU에서 수행하였다는 점을 구분하였다. 플랫폼·모델 규모·평가셋이 달라 논문 간 절감률이나 면적의 직접 우열은 주장하지 않았다.

권장 위치: **1.2 설계 동기 다음의 관련 연구 문단**, 상세 표는 부록 B.

표/그림 캡션: **조기 종료 및 동적 추론 선행 연구와 본 설계의 판단 지표, 경로 수, 구현·평가 범위 비교. FPGA 실측, CPU/GPU 실행과 ASIC pre-layout 추정을 구분하였다.**

## 검증한 서지 및 원문 위치

'''
for r in rows[:3]:md+=f"- **{r['title']}** — {r['authors']}. {r['venue_year']}. [서지/원문]({r['url']}), [PDF]({r['primary_pdf']}). 확인 위치: {r['evidence']}.\n"
md+='\nCascadeCNN의 학회 정보는 FPL 2018 채택을 명시한 저자 원문 첫 페이지에서 확인하였다. BranchyNet의 arXiv 게시 연도는 2017이지만 학회 발표 연도는 ICPR 2016이다. 전체 논문 PDF는 저장소에 복제하지 않았다. 재실행: `python results_sh/v2/07_related_work/analyze.py`. 이 스크립트는 검증 기록을 재표시하며 인터넷 내용을 자동 검증하는 프로그램은 아니다.\n'
(folder/'README.md').write_text(md,encoding='utf8')
plt=plotsetup();fig,ax=plt.subplots(figsize=(13.5,4.7));ax.axis('off')
cells=[['BranchyNet','Entropy','2 / 3','CPU / GPU','정확도·추론 시간'],['CascadeCNN','Probability gBvSB','2','FPGA + ARM CPU','실측 처리량·정확도'],['Shallow-Deep\nNetworks','Max probability','7','소프트웨어 모델','정확도·FLOPs'],['AdaPath-NPU','Integer logit margin','A: 2 / B: 3','RTL / ASAP7','합성·STA·VCD 추정\n정확도·MAC·교차 평가']]
t=ax.table(cellText=cells,colLabels=['Design','Decision metric','Paths / exits','Implementation','평가 범위'],cellLoc='center',colWidths=[.18,.24,.12,.22,.24],bbox=[0,.06,1,.86]);t.auto_set_font_size(False);t.set_fontsize(10)
for (i,j),cell in t.get_celld().items():cell.set_edgecolor('#d7dadd');cell.set_facecolor('#e9ecef' if i==0 else '#e1f0e8' if i==4 else 'white')
ax.set_title('구현과 평가 조건을 구분한 관련 연구 비교',fontsize=13);savefig(fig,folder,'fig_related_work');plt.close(fig)
