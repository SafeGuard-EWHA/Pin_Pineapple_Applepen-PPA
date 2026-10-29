# AdaPath-NPU — Score-Margin 기반 난이도 적응형 Tiny NPU Datapath

경북대학교 IDEC 2026 창의 회로설계 챌린지 (디지털) · 팀 **Pin_Pineapple_Applepen(PPA)**
이화여자대학교 전자전기공학과 윤현서 · 최서현 · 윤홍은 (지도교수 최종윤)

Early Classifier 점수의 Top-1 − Top-2 차이(Score Margin)로 입력 난이도를 판정해
Easy / Medium / Hard 경로를 선택하는 NPU 데이터패스. ASAP7 7nm(OpenROAD-flow-scripts)로
주최 측 레퍼런스 가속기와 PPA를 비교한다.

| 과제 | 모델 / 데이터 | 내용 |
|---|---|---|
| 지정주제 | 모델 A (레퍼런스와 동일 신경망: conv1 3ch, conv2 3ch, FC 48→10), MNIST | 동일 신경망에 AdaPath 적용 |
| 자유주제 | 모델 B (conv2 8ch), WM-811K 4-class | 적용 전·후 PPA |
| 확장 | 모델 B, MNIST | Medium 경로 효과 분석 |

## 폴더 구조

| 경로 | 내용 |
|---|---|
| `python/` | 데이터 준비(`data_mnist.py`, `data_wm811k.py`), 학습(`train.py`), 임계값 탐색(`analyze_margin.py`), INT8 export(`export_int8.py`), Early-Exit 대비 분석(`iso_accuracy.py`), chip 래퍼 가중치 생성(`gen_chip_weights.py`) |
| `rtl/` | 파라미터화 RTL(`adapath_top.v` 외), 주최 측 인터페이스 래퍼(`chip_adapath.v`), 테스트벤치, `run_sim.sh` |
| `rtl/ref/` | 주최 측 레퍼런스 conv1/conv2 line buffer 발췌 (출처 표기, 원저작자: Bo Young Kang) |
| `rtl/verify/` | Top-2 Finder 개선 전·후 동일성 검증 TB |
| `orfs/` | ORFS 설계 설정(`asap7/`), 합성용 소스(`src/`), STA/전력 Tcl, 중간보고서 시점 리포트 |
| `orfs/designs_final/` | 최종 비교용 설계 설정(레퍼런스, 모델 A, WM-811K) |
| `flow_scripts/` | WSL에서 실행한 합성·STA·VCD 전력 스크립트 |
| `glsim/` | 게이트레벨 시뮬레이션 TB(AdaPath A/B, 레퍼런스)와 실행 스크립트 |
| `vivado/` | Vivado 2023.1 프로젝트 생성·시뮬레이션 Tcl (주최 측 top_tb.v 사용) |
| `out/` | 그림, 결과 표, 학습 가중치(`.pt`), RTL용 INT8 데이터(`rtl_data_*`) |
| `report/` | 결과보고서 생성 스크립트 |
| `docs/` | 중간보고서 |

## 실행 요약

```bash
# 1) 학습 · 임계값 · INT8 (python/)
python data_mnist.py
python train.py --arch A --n_class 10 --prefix mnist
python analyze_margin.py --arch A --prefix mnist
python export_int8.py --arch A --prefix mnist --t_low 1.161 --t_high 1.161

# 2) RTL 시뮬레이션 (rtl/, Icarus Verilog)
bash run_sim.sh
```

## 저장소에 포함하지 않은 것

- 데이터셋 원본(MNIST, WM-811K `LSWMD.pkl`) — 공개 데이터, `python/data_*.py`로 재생성
- 주최 측 레퍼런스 RTL·데이터(`verilog_ref/`) — 대회 배포물
- 시뮬레이션 덤프(`.vcd`, `.vvp`)와 합성 넷리스트 — 용량이 크고 스크립트로 재생성 가능
