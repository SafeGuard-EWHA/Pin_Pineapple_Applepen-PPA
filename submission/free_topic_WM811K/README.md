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
| 평균 전력 (mW, 100 MHz) | 2.970 | Easy 2.395 / Medium 2.865 / Hard 3.213 | - | ASAP7 게이트레벨 VCD + OpenROAD `report_power` (`power/power_results/`) |
| **추론당 에너지 (nJ)** | **29.46** | **26.86** | **−8.8 %** | WM 넷리스트 게이트레벨 VCD 기반 추정 (3절) |
| (참고) 이전 대리 추정 에너지 (nJ) | 33.4 | 26.2 | −21.7 % | 모델 B 모드별 에너지에 WM 모드 비율 가중 |
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
- **전력/에너지:** Baseline_WM과 AdaPath_WM의 ORFS 합성 넷리스트(보고서 면적과 같은 합성)를 ASAP7 셀 기능 모델로 100 MHz 게이트레벨 시뮬레이션(Icarus Verilog 12)하여 VCD를 얻고, OpenROAD `read_vcd` + `report_power`(ASAP7 RVT TT)로 평균 전력을 구하였다. 이미지당 에너지 = 평균 전력 × 관측 시간 ÷ 4 (이미지마다 리셋 12 cycle 포함, 지정주제와 같은 방법). AdaPath_WM은 Easy, Medium, Hard 각 4장 구간(테스트 인덱스 8/10/18/22, 2/3/5/24, 0/1/4/9)의 이미지당 에너지를 Vivado RTL 모드 비율(404 / 167 / 383)로 가중하였고, Baseline_WM은 인덱스 0~3의 4장 구간 평균이다. AdaPath_WM 12장의 게이트레벨 판정, 모드, Margin은 `wm_expect.txt`와 모두 일치하였다. 배치 전(클럭 트리, 배선 기생 성분 미포함) 추정이며, 표본은 모드별 4장이다. 실행 스크립트(run_wm.sh → power_wm.sh → energy_wm.py)와 결과는 `power/`에 있다. 전력 재현에 필요한 압축 넷리스트, 표준셀 기능 모델, 가중치, 입력 및 SDC를 `power/`에 함께 포함하였다. 테스트벤치는 원본과 동일하며 실행 스크립트가 컴파일 옵션으로 데이터 경로만 지정한다. 포함 파일의 출처와 SHA-256은 `power/input_manifest.json`에 기록하였다.  `power/power_results/`의 리포트와 로그는 실제 실행 출력이다.
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

- 패키지 정리 과정에서는 합성과 STA를 다시 실행하지 않았다. WM 게이트레벨 전력은 10/31에 새로 측정하였다(`power/`). `reports/`의 수치는 원래 실행에서 나온 도구 출력이다.
- 정리 내용: 스크립트의 작성자 PC 절대경로를 환경변수와 스크립트 기준 상대경로로 바꾸고, WM과 무관한 설계(지정주제 설계의 블록 전력, 다른 모델 합성)를 실행하던 부분과 기존 결과를 지우던 동작(`rm -rf`, `clean_synth`)을 제거하였다. 호출하는 Tcl(`sta_odb.tcl`, `sta_sweep.tcl`)은 원래 실행에 사용한 파일과 같다(줄바꿈 문자만 정리).
- 확인한 것: ZIP 무결성, 스크립트가 호출하는 파일의 존재, bash 문법 검사(`bash -n`), 스크립트의 개인 경로 잔존 여부, RTL과 설정, Vivado 프로젝트의 정리 전후 SHA-256 동일성.
- `reports/synth/*.txt` 앞부분의 `Found gzip magic in file /home/...` 줄은 원래 실행 환경의 도구 로그이며 실행에 쓰이지 않는다.

## 8. WM 게이트레벨 전력 재현 (독립 패키지)

패키지를 Linux/WSL의 짧은 영문 경로(예: `/tmp/ppa-wm`)에 풀고 실행한다. Icarus Verilog 12, Python 3, OpenROAD 및 ASAP7 RVT TT 플랫폼은 외부 설치가 필요하다. 원시 VCD는 수 GB이므로 여유 공간을 확보한다. 기존 결과를 보존하려면 패키지 사본에서 실행한다.

```bash
export ORFS=$HOME/OpenROAD-flow-scripts
bash power/run_wm.sh
bash power/power_wm.sh
python3 power/energy_wm.py power/run
```

시뮬레이션은 메모리 부담을 줄이기 위해 네 구간을 순차 실행한다. `power/run/`에 컴파일 로그, 시뮬레이션 로그 및 VCD가 생성된다. 전력 스크립트는 원래 `power_results/`의 결과를 갱신하므로 원본 증거는 보존한 사본으로 비교한다. 소스 코드만 제공하는 것이 아니라 넷리스트 두 개와 셀 모델도 포함하여 저장소의 다른 폴더에 의존하지 않는다. 원본 TB와 기존 RTL은 수정하지 않았다.

포함된 결과 수치는 57cf580의 기존 실행 결과이다. 패키지 경로 교정 자체가 새 전력 측정 완료를 뜻하지 않는다. 보고서의 기존 8.8%는 서로 다른 소수 입력 구성의 비교이며, 동일 입력 비교 결과와 구분한다.
