# 자유주제 결과 제출 자료: WM-811K 웨이퍼맵 결함 분류 (AdaPath_WM)

팀 PPA (Pin_Pineapple_Applepen), 경북대 IDEC 2026 창의 회로설계 챌린지 디지털 분야.
결과보고서 3.9절 자유주제 설계의 설계 파일, 툴/스크립트/제약조건, 기법 적용 전후 PPA와 측정 방법을 정리한 폴더이다.

- 기법 적용 전: **Baseline_WM** (`baseline_wm_npu`, 항상 전체 경로)
- 기법 적용 후: **AdaPath_WM** (`adapath_wm_npu`, 지정주제와 같은 Score Margin 기반 Easy / Medium / Hard 경로 선택)
- 두 설계는 같은 RTL 소스(`rtl/adapath_top.v`)에서 파라미터(VARIANT, N_CLASS = 4)로 생성한다.

## 1. 기법 적용 전후 PPA

| 항목 | Baseline_WM | AdaPath_WM | 변화 | 측정 방법 |
|---|---:|---:|---:|---|
| Cell Area (µm²) | 75,765 | 92,892 | +22.6 % | Yosys 합성 통계 (`reports/synth/*_synth_stat.txt`) |
| 추정 Fmax (MHz) | 484.5 | 495.3 | +2.2 % | OpenROAD STA 클럭 주기 스윕, slack = 0 보간 (`reports/sta/sweep_*_wm.txt`) |
| 평균 MAC / 이미지 | 82,112 | 62,848 | −23.5 % | 테스트 954장의 모드별 MAC 가중 평균 (Python) |
| 추론당 에너지 (nJ) | 33.4 | 26.2 | −21.7 % | **대리 추정** (3절 참고). WM 자체 전력 평가는 미완료 |
| 정확도 (954장) | 81.55 % (float) | 81.24 % (float), RTL 774 / 954 = 81.13 % | −0.31 %p | Python float / Vivado RTL |
| 모드 (Easy / Medium / Hard) | 0 / 0 / 954 | RTL 404 / 167 / 383 | - | Vivado RTL |

## 2. 필수 도구와 확인된 버전

| 용도 | 도구 | 이 결과를 만든 버전 |
|---|---|---|
| 합성, STA | OpenROAD-flow-scripts (Yosys, OpenROAD 포함) | ORFS 6101364b2, OpenROAD 26Q3-1305-gf552262465, Yosys 0.68+ (git a5af9d690) |
| 공정 | ASAP7 (ORFS `flow/platforms/asap7`에 포함) | RVT, TT corner, NLDM |
| RTL 시뮬레이션 | Vivado | 2023.1 (작성), 2024.1 (다른 PC에서 같은 결과 재현) |
| 데이터 준비, 학습 | Python 3, PyTorch, NumPy, pandas | `python/` 스크립트 |
| 실행 환경 | Ubuntu 22.04 (WSL2 포함)의 bash | 합성과 STA |

외부에서 별도로 받아야 하는 것:
- **OpenROAD-flow-scripts** 설치본(ASAP7 플랫폼 포함). 설치 경로를 `ORFS` 환경변수로 지정한다.
- **Vivado** (2024.1 권장).
- **WM-811K 원본 데이터**(`LSWMD.pkl`, 공개 데이터셋): 학습을 다시 할 때만 필요하다. 하드웨어 검증에 쓰는 입력은 Vivado 프로젝트의 `data/`에 포함되어 있다.

## 3. 측정 방법

- **면적:** ORFS 합성 후 Yosys `synth_stat`의 Chip area. 가중치는 지정주제 비교와 같이 입력 포트로 둔 NPU 코어 기준이다.
- **Fmax:** `orfs/scripts/sta_sweep.tcl`로 1_synth.odb에 대해 클럭 주기를 1.0~2.4 ns로 바꾸며 STA를 수행하고, 최악 slack이 0이 되는 주기를 인접 두 점의 선형 보간으로 구하였다. 입출력 지연은 클럭 주기의 20 %로 지정주제와 같다.
- **전력/에너지 (대리 추정):** WM 넷리스트 자체의 게이트레벨 전력 평가는 완료하지 못하였다. 표의 에너지는 같은 구조의 10-class 확장 모델(AdaPath_B)에서 ASAP7 게이트레벨 VCD로 얻은 모드별(Easy / Medium / Hard) 추론당 에너지에 WM 테스트셋의 모드 비율을 가중한 값이며, Baseline_WM 값은 AdaPath_B의 Hard 에너지이다. 따라서 WM에서 직접 검증한 전력 감소율이 아니다. `reports/sta/*_sta.rpt`에 있는 전력값은 고정 활동도 가정의 정적 추정이므로 에너지 개선 근거로 쓰지 않는다.
- **기능:** Vivado 프로젝트(`vivado/PPA_AdaPath_NPU_WM.zip`)의 `tb_wm`으로 테스트 954장을 처리하여 정수 Golden과 판정, 모드, Score Margin 954 / 954 일치를 확인하였다.

## 4. 가중치 저장 방식

- **Vivado 제출 설계 (chip 래퍼):** 주최 측 chip 인터페이스를 유지하고, 학습한 INT8 가중치를 래퍼 내부 상수(`src/adapath_weights.vh`, WM 가중치)로 고정하였다. 가중치 입력 포트는 호환용으로만 둔다.
- **ORFS PPA 합성:** 지정주제 비교와 같은 조건을 위해 가중치를 입력 포트로 둔 NPU 코어(`adapath_wm_npu`, `baseline_wm_npu`)를 합성하였다.

## 5. 폴더 구성

| 폴더 | 내용 |
|---|---|
| `rtl/` | ORFS 합성에 사용한 RTL (`ref/`는 Conv 버퍼) |
| `orfs/adapath_wm/`, `orfs/baseline_wm/` | ORFS `config.mk`, `constraint.sdc` |
| `orfs/scripts/` | `env.sh`, `install_wm.sh`, `synth_wm.sh`, `sta_wm.sh`, `sta_odb.tcl`, `sta_sweep.tcl` |
| `reports/synth/`, `reports/sta/` | 보고서 수치의 원본 도구 출력 (합성 통계, STA, 주기 스윕) |
| `vivado/` | WM Vivado 제출 프로젝트(zip), 프로젝트 생성 Tcl(참고용), 테스트벤치 |
| `python/` | 데이터 준비(`data_wm811k.py`), 학습, 정수화, ORFS 소스 생성 스크립트 |

## 6. 실행 방법

### 6.1 합성과 STA (Ubuntu bash, 이 폴더에서)
```bash
export ORFS=$HOME/OpenROAD-flow-scripts      # ORFS 설치 경로
source orfs/scripts/env.sh                   # PLATFORM_DIR, PATH 설정
bash orfs/scripts/install_wm.sh              # RTL과 설정을 ORFS에 배치 (기존 폴더가 있으면 중단, OVERWRITE=1로 백업 후 배치)
bash orfs/scripts/synth_wm.sh                # Baseline_WM, AdaPath_WM 합성
bash orfs/scripts/sta_wm.sh                  # 단일 STA(1,000 / 2,500 ps)와 주기 스윕
```
파일 배치 위치:
- `rtl/` → `$ORFS/flow/designs/src/adapath_wm/`
- `orfs/adapath_wm/`, `orfs/baseline_wm/` → `$ORFS/flow/designs/asap7/<design>/`

예상 출력:
- 합성 결과: `$ORFS/flow/results/asap7/<design>/base/1_2_yosys.v`, `1_synth.odb`
- 합성 통계와 STA: `OUT` 환경변수 폴더(기본 `./out`)에 `<design>_synth_stat.txt`, `<design>_sta.txt`, `<design>_sta25.txt`, `sweep_<design>.txt`

주기 스윕 결과(`sweep_<design>.txt`)의 각 줄은 `모드 주기(ps) 최악slack(ps) 시작점`이며, `io20` 줄에서 slack이 0을 지나는 두 주기를 선형 보간하면 표의 Fmax가 된다.

### 6.2 Vivado 기능 검증
`vivado/PPA_AdaPath_NPU_WM.zip`의 압축을 풀고 `.xpr`을 연 뒤 Run Behavioral Simulation을 실행하면, Tcl 콘솔에 정확도와 Golden 일치 결과가 출력된다(`data/wm_expect.txt`와 비교).

## 7. 검증 범위 (이번 정리)

- 이번 정리에서는 합성, STA, 시뮬레이션, 전력 분석을 **다시 실행하지 않았다.** `reports/`의 수치는 원래 실행에서 나온 도구 출력이다.
- 정리 내용: 스크립트의 작성자 PC 절대경로를 환경변수와 스크립트 기준 상대경로로 바꾸고, WM과 무관한 설계(지정주제 설계의 블록 전력, 다른 모델 합성)를 실행하던 부분과 기존 결과를 지우던 동작(`rm -rf`, `clean_synth`)을 제거하였다. 호출하는 Tcl(`sta_odb.tcl`, `sta_sweep.tcl`)은 원래 실행에 사용한 파일과 같다(줄바꿈 문자만 정리).
- 확인한 것: ZIP 무결성, 스크립트가 호출하는 파일의 존재, bash 문법 검사(`bash -n`), 스크립트의 개인 경로 잔존 여부, RTL과 설정, Vivado 프로젝트의 정리 전후 SHA-256 동일성.
- `reports/synth/*.txt` 앞부분의 `Found gzip magic in file /home/...` 줄은 원래 실행 환경의 도구 로그이며 실행에 쓰이지 않는다.
