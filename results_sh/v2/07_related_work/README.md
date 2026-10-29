# 선택 작업 7: 관련 연구 비교

원문과 학회 공식 자료로 서지·판단 지표·구현 범위를 확인한 3편만 포함하였다. 수치 성능을 다른 공정·데이터셋 사이에서 직접 순위화하지 않았다. seed는 문헌 검토에 해당하지 않으며 본 설계의 기준 커밋은 `4990d117fcc571183000605a514ad5d9c7d5c98a`이다.

| 연구 | 판단 지표 | 경로/출구 수 | 구현 | 평가 방식 |
|---|---|---|---|---|
| BranchyNet | softmax entropy | LeNet 2; AlexNet/ResNet 3 | CPU/GPU 평가; 전용 RTL 구현은 제시하지 않음 | MNIST/CIFAR-10 정확도 및 평균 추론 시간 |
| CascadeCNN | 정렬 확률의 generalized Best-vs-Second-Best (gBvSB) | 저정밀도 종료 / 고정밀도 재계산의 2단계 | FPGA CNN + ARM CPU softmax/CEU | ImageNet, AlexNet/VGG-16; ZC706/ZCU102 실측 성능·오류 허용량 |
| Shallow-Deep Networks | 최대 클래스 확률 (confidence) | 내부 분류기 6 + 최종 1 = 7 | 소프트웨어 모델 분석; 전용 RTL 구현은 제시하지 않음 | CIFAR-10/100, Tiny ImageNet; 정확도–FLOPs 예산, unlabeled holdout으로 임계값 설정 |
| AdaPath-NPU | 정수 로짓 Top-1 − Top-2 Margin | 선정 A: 2 / B: 3 | Verilog RTL, ASAP7 pre-layout 합성·STA 및 대표 VCD 전력 추정 | MNIST/WM 정확도·MAC; 이번 2-fold 분석; 주최 TB 기능 검증 |

## 보고서 반영 문단

BranchyNet은 entropy 기반 조기 종료와 여러 출구의 공동 학습을 제시하였고, Shallow-Deep Networks는 최대 클래스 확률에 따른 조기 종료와 과도한 후단 계산의 영향을 분석하였다. CascadeCNN은 확률 벡터의 generalized Best-vs-Second-Best로 저정밀도 추론과 고정밀도 재계산을 선택하였다. 따라서 조기 종료 또는 상위 점수 차이의 사용 자체를 새로운 개념으로 주장하지 않았다. 본 설계는 정수 로짓 차이의 비교·감산 회로와 공유 전단부, 제한된 경로 선택 및 주최 인터페이스를 통합하고, ASAP7 합성·STA와 대표 VCD 기반 전력 추정까지 연결한 구현에 초점을 두었다. CascadeCNN의 평가에서는 softmax와 confidence evaluation을 ARM CPU에서 수행하였다는 점을 구분하였다. 플랫폼·모델 규모·평가셋이 달라 논문 간 절감률이나 면적의 직접 우열은 주장하지 않았다.

권장 위치: **1.2 설계 동기 다음의 관련 연구 문단**, 상세 표는 부록 B.

표/그림 캡션: **조기 종료 및 동적 추론 선행 연구와 본 설계의 판단 지표, 경로 수, 구현·평가 범위 비교. FPGA 실측, CPU/GPU 실행과 ASIC pre-layout 추정을 구분하였다.**

## 검증한 서지 및 원문 위치

- **BranchyNet: Fast Inference via Early Exiting from Deep Neural Networks** — Surat Teerapittayanon; Bradley McDanel; H. T. Kung. ICPR 2016. [서지/원문](https://doi.org/10.1109/ICPR.2016.7900006), [PDF](https://arxiv.org/pdf/1709.01686). 확인 위치: Sec. III-C, IV; Table I.
- **CascadeCNN: Pushing the Performance Limits of Quantisation in Convolutional Neural Networks** — Alexandros Kouris; Stylianos I. Venieris; Christos-Savvas Bouganis. FPL 2018. [서지/원문](https://arxiv.org/abs/1807.05053), [PDF](https://arxiv.org/pdf/1807.05053). 확인 위치: 첫 페이지 학회 표기; Sec. III-C Eq.(2), IV-A/C.
- **Shallow-Deep Networks: Understanding and Mitigating Network Overthinking** — Yigitcan Kaya; Sanghyun Hong; Tudor Dumitras. ICML 2019, PMLR 97:3301–3310. [서지/원문](https://proceedings.mlr.press/v97/kaya19a.html), [PDF](https://proceedings.mlr.press/v97/kaya19a/kaya19a.pdf). 확인 위치: Sec. 3.1, 5.1; Table 3.

CascadeCNN의 학회 정보는 FPL 2018 채택을 명시한 저자 원문 첫 페이지에서 확인하였다. BranchyNet의 arXiv 게시 연도는 2017이지만 학회 발표 연도는 ICPR 2016이다. 전체 논문 PDF는 저장소에 복제하지 않았다. 재실행: `python results_sh/v2/07_related_work/analyze.py`. 이 스크립트는 검증 기록을 재표시하며 인터넷 내용을 자동 검증하는 프로그램은 아니다.
