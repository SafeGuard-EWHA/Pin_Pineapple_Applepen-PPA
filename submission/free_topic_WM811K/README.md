# 자유주제 결과 제출 자료: WM-811K 웨이퍼맵 결함 분류 (AdaPath_WM)

팀 PPA (Pin_Pineapple_Applepen), 경북대 IDEC 2026 창의 회로설계 챌린지 디지털 분야.
결과보고서 3.9절의 자유주제 설계에 대한 설계 파일, 툴/스크립트/제약조건, 기법 적용 전후 PPA를 정리한 폴더이다.

- 기법 적용 전: **Baseline_WM** (`baseline_wm_npu`, 항상 전체 경로)
- 기법 적용 후: **AdaPath_WM** (`adapath_wm_npu`, Score Margin 기반 Easy / Medium / Hard 경로 선택)
- 두 설계는 같은 RTL 소스(`rtl/adapath_top.v`)에서 파라미터(VARIANT, N_CLASS = 4)로 생성하였다.

## 1. 기법 적용 전후 PPA

| 항목 | Baseline_WM | AdaPath_WM | 변화 | 측정 방법 |
|---|---:|---:|---:|---|
| Cell Area (µm²) | 75,765 | 92,892 | +22.6 % | Yosys 합성 통계 (`reports/synth/*_synth_stat.txt`) |
| 추정 Fmax (MHz) | 484.5 | 495.3 | +2.2 % | OpenROAD STA, 클럭 주기 1.0~2.4 ns 스윕 후 slack = 0 보간 (`reports/sta/sweep_*_wm.txt`) |
| 평균 MAC / 이미지 | 82,112 | 62,848 | −23.5 % | 테스트 954장의 모드별 MAC 가중 평균 |
| 추론당 에너지 (nJ) | 33.4 | 26.2 | −21.7 % | 대리 추정 (아래 3절) |
| 정확도 (954장) | 81.55 % (float) | 81.24 % (float), RTL 774 / 954 = 81.13 % | −0.31 %p | Python float / Vivado RTL |
| 모드 (Easy / Medium / Hard) | 0 / 0 / 954 | RTL 404 / 167 / 383 | - | Vivado RTL (`vivado/PPA_AdaPath_NPU_WM.zip`) |

## 2. 툴 및 버전

| 용도 | 툴 | 버전 |
|---|---|---|
| 합성 | Yosys (ORFS 내장) | 0.68+ (git a5af9d690), ABC area 스크립트 |
| STA, 배치 | OpenROAD / OpenROAD-flow-scripts | 26Q3-1305-gf552262465 / ORFS 6101364b2 |
| 공정 | ASAP7 | RVT, TT corner (NLDM) |
| RTL 시뮬레이션 | Vivado | 2023.1 (작성), 2024.1 (다른 PC에서 재현) |
| 학습, 정수화 | Python, PyTorch | `python/` 스크립트 |

## 3. 측정 방법

- **면적:** `orfs/<design>/config.mk`로 ORFS 합성 후 Yosys `synth_stat`의 Chip area. 가중치는 지정주제와 같이 입력 포트로 둔 NPU 코어 기준이다.
- **Fmax:** `orfs/scripts/sta_sweep.tcl`로 합성 결과(1_synth.odb)에 대해 클럭 주기를 1.0~2.4 ns로 바꾸며 STA를 수행하고, 최악 slack이 0이 되는 주기를 인접 두 점의 선형 보간으로 구하였다. SDC 규칙(`constraint.sdc`)은 입출력 지연 = 클럭 주기의 20 %로 지정주제와 같다.
- **전력/에너지:** WM 설계의 직접 게이트레벨 VCD 전력은 수행하지 못하였다. 같은 구조의 10-class 확장 모델(AdaPath_B)에서 ASAP7 게이트레벨 VCD로 측정한 모드별(Easy / Medium / Hard) 추론당 에너지에, WM 테스트셋의 모드 비율을 가중한 대리 추정값이다. Baseline_WM은 AdaPath_B의 Hard 에너지를 사용하였다. 전력 측정 흐름(게이트레벨 시뮬레이션 → VCD → OpenROAD `read_vcd` + `report_power`)은 지정주제와 같으며 결과보고서 3.7절과 저장소 `glsim/`, `flow_scripts/vcd_power_odb.tcl`에 있다.
- **기능:** Vivado 프로젝트(`vivado/PPA_AdaPath_NPU_WM.zip`)에서 `tb_wm`으로 테스트 954장을 처리하여 정수 Golden과 판정, 모드, Score Margin 954 / 954 일치를 확인하였다.

## 4. 가중치 저장 방식

- **Vivado 제출 설계 (chip 래퍼):** 주최 측 chip 인터페이스를 유지하되, 학습한 INT8 가중치를 래퍼 내부 상수(`adapath_weights_wm.vh`)로 고정하였다. 가중치 입력 포트는 호환용으로만 두고 사용하지 않는다.
- **ORFS PPA 합성:** 지정주제 비교와 같은 조건을 위해 가중치를 입력 포트로 둔 NPU 코어(`adapath_wm_npu`, `baseline_wm_npu`)를 합성하였다.

## 5. 폴더 구성과 실행

| 폴더 | 내용 |
|---|---|
| `rtl/` | 합성에 사용한 RTL (ORFS `designs/src/adapath_wm`) |
| `orfs/adapath_wm`, `orfs/baseline_wm` | ORFS `config.mk`, `constraint.sdc` |
| `orfs/scripts/` | 합성 및 STA 스윕 스크립트 |
| `reports/synth`, `reports/sta` | 합성 통계, STA 리포트, 주기 스윕 결과 |
| `vivado/` | WM Vivado 제출 프로젝트(zip), 프로젝트 생성 Tcl, 테스트벤치 |
| `python/` | 데이터 준비(`data_wm811k.py`), 학습, 정수화, ORFS 소스 생성 스크립트 |

```bash
# ORFS (OpenROAD-flow-scripts/flow에서)
make DESIGN_CONFIG=./designs/asap7/adapath_wm/config.mk synth
make DESIGN_CONFIG=./designs/asap7/baseline_wm/config.mk synth
# 주기 스윕 STA
ODB=results/asap7/adapath_wm/base/1_synth.odb OUTF=sweep_adapath_wm.txt \
  PERIODS="1000 1200 1400 1500 1600 1700 1800 1900 2000 2100 2200 2400" openroad -exit sta_sweep.tcl
```

Vivado: `vivado/PPA_AdaPath_NPU_WM.zip`의 압축을 풀고 `.xpr`을 연 뒤 Run Behavioral Simulation을 실행하면 Tcl 콘솔에 정확도와 Golden 일치 결과가 출력된다.
