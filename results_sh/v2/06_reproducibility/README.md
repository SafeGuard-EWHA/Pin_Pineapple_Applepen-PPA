# 작업 6: 재현성 부록

검토 기준 main `4990d117fcc571183000605a514ad5d9c7d5c98a`. 저장소 파일만 정적으로 검토하였으며 하드웨어 도구를 설치·실행하거나 과거 버전을 현재 PC에서 추정하지 않았다. 사용 근거의 SHA-256/Git blob은 source_hashes.json, 원문 행 번호는 source_excerpts.csv에 기록하였다. 원본 쉘 스크립트에는 작성자의 절대 경로와 stage 폴더가 있으므로 그대로 실행 가능하다고 안내하지 않는다.

## 도구 버전

| 도구 | 기존 결과의 버전 | 근거 | 이번 분석 환경 |
|---|---|---|---|
| Yosys / ABC | 확인 필요 | 합성 통계/스크립트는 있으나 버전 배너와 커밋 없음 | 실행하지 않음 |
| OpenROAD | 26Q3-1305-gf552262465 | orfs/reports_final/adapath_A_sta.rpt:1 및 power_A_easy.rpt:1 | 실행하지 않음 |
| OpenSTA | OpenROAD 내장 사용; 독립 OpenSTA 버전은 확인 필요 | flow_scripts/vcd_power_odb.tcl:6–7, openroad report_power | 실행하지 않음 |
| Icarus Verilog | 확인 필요 | glsim/run_*.sh의 iverilog/vvp 명령, 버전 출력 없음 | 실행하지 않음 |
| Vivado | 2023.1 (문서·캡처 표기), build 세부값 확인 필요 | evidence/README.md:5, 보고서 3.4·그림 7 | 실행하지 않음 |
| Python | 학습 당시 확인 필요 | 원본 환경 lock/버전 로그 없음 | 3.12.14 |
| PyTorch | 학습 당시 확인 필요 | 체크포인트에는 state/arch만 존재 | 2.9.1+cpu |

## 실행 명령 및 입력 조건

| 단계 | 기록된 명령/재현 명령 | 데이터·분할 | 임계값 | 확인 범위 | 출처 |
|---|---|---|---|---|---|
| Training | cd python; python train.py --arch A --n_class 10 --prefix mnist | MNIST train/test NPZ; test는 epoch별 출력 | 없음 | README 명령 예시; 실제 실행 CLI·seed 확인 필요 | README.md; python/train.py |
| Original threshold selection | cd python; python analyze_margin.py --arch A --prefix mnist --out <model_and_data_folder> | MNIST 10000; WM 954, 같은 셋 선정·평가 | A 1.1608357596/1.1608357596; B 1.5987654805/2.5930354309; WM .2098419857/.6432941723 | 이번 float 추론으로 기존 보고 동작점 재현 | python/analyze_margin.py; out/archA/table_modes_mnist.md; out/table_modes*.md |
| Integer export | python export_int8.py --arch A --prefix mnist --t_low 1.161 --t_high 1.161 | 학습 체크포인트; 정수화 calibration 자료는 export 코드 참조 | RTL A 63/63; B 71/119; WM 13/41 | 설정 파일 확인, 이번 정수화 재실행 없음 | README.md; out/rtl_data_*/thresholds.vh |
| Synthesis | make DESIGN_CONFIG=./designs/asap7/<variant>/config.mk clean_synth synth | ORFS staged sources + ASAP7 | 각 variant의 thresholds.vh | 스크립트 명령 확인, stage 절대 경로 치환·원본 외부 파일 필요 | flow_scripts/queue_final.sh:17; synth_v3.sh:20 |
| STA | PLATFORM_DIR=<...> ODB=<...>/1_synth.odb SDC=<...> REPORT=<...> openroad -exit <...>/sta_odb.tcl | 합성 ODB; 1000 ps 및 참고 2500 ps SDC | 해당 설계 고정 설정 | 스크립트에 저장된 호출; 환경 경로 조정 필요 | flow_scripts/sta_one.sh:8–11 |
| A gate simulation | iverilog -g2012 -I. -o gl_adA.vvp adapath_A_net.v std_cell_fn/*.v tb_gl_A.v; vvp gl_adA.vvp +START=1 +VCD=gl_adA_easy.vcd | 주최 input_1000.txt의 지정 구간 | A 63/63 | run_A.sh·대표 런 로그 확보; 컴파일 넷리스트/셀 모델 별도 | glsim/run_A.sh:4–9 |
| B / Reference gate simulation | bash glsim/run_adapath.sh; bash glsim/run_ref.sh | START 1/15/5, 각 4장 | B 71/119; Reference 해당 없음 | 스크립트는 외부 idec_glsim 디렉터리 기준; 복사·경로 조정 필요 | glsim/run_adapath.sh; glsim/run_ref.sh |
| VCD power | PLATFORM_DIR=<...> ODB=<...> SDC=<10ns.sdc> VCD=<run.vcd> SCOPE=tb_gatelevel/dut openroad -exit flow_scripts/vcd_power_odb.tcl | 100 MHz, 이미지마다 reset 12 cycle 포함 | A/B의 고정 RTL 설정 | 대표 런 기반 추정; VCD 원본과 파일 해시 저장소에 없음 | flow_scripts/power_A.sh; queue_final.sh; vcd_power_odb.tcl |
| Vivado project | vivado -mode batch -source vivado/submit/make_submit.tcl -tclargs <project_folder> <project_name> | top_tb_1000; 고유 100장×10회 입력 | 학습 가중치 상수와 threshold header | 프로젝트 생성 명령 확인; 실행 로그 4개는 README에만 열거 | vivado/submit/make_submit.tcl:1; evidence/README.md |
| This P0 analysis | python results_sh/v2/prepare.py --repo . --cache work/v2_cache; python results_sh/v2/run_p0.py --cache work/v2_cache | 고정 NPZ; 2-fold×5 seeds 2026–2030 | 보고 동작점·exact·legacy 구분 | 이번 실행 완료; CPU 2 threads, inference seed 2026 | results_sh/v2/provenance/manifest.json |
| This P1 analysis | python results_sh/v2/run_p1.py --repo . --cache work/v2_cache | P0와 같은 float 예측·NPZ | 기존 보고 동작점 | 이번 실행 완료; 새 추론/RTL 실험 없음 | results_sh/v2/run_p1.py |

## 데이터 분할·학습 설정의 확인 범위

MNIST 준비 코드는 공식 train 60,000장 / test 10,000장 구분을 그대로 저장한다. `data_mnist.py --seed`는 인터페이스에 있으나 build 내부에서 분할에 사용하지 않는다. WM 준비 코드는 클래스당 동일 수를 추출한 뒤 전체를 섞어 20%를 test로 저장하며, `data_wm811k.py`의 seed 기본값은 0이다. 실제 생성 당시 seed 및 원본 wafer/lot ID는 체크포인트·NPZ에 저장되지 않았으므로 확인 필요이다. 이번 분석은 이미 제공된 test 954장을 고정하고 새 2-fold 분할 seed 2026–2030만 바꾸었다.

`train.py`의 기본값은 epochs=30, batch size=128, lr=0.002, Early/Light loss 가중치 각각 0.5이며 Adam 및 CosineAnnealingLR를 사용한다. 이는 코드 기본값이며 각 체크포인트의 실제 학습 명령·seed를 입증하는 실행 로그가 아니다. test 정확도를 epoch마다 출력하므로 모델 개발 단계의 테스트셋 관찰 가능성은 남는다. INT8 export의 기본 calibration 수는 64장이지만 실제 export CLI는 별도 확인 필요이다.

## VCD 런 구성

| 설계 | 런 | 입력 index | n | 모드 구성 | VCD 파일 | 출처 |
|---|---|---|---|---|---|---|
| AdaPath_A | Easy | 1–4 | 4 | Easy 4 | gl_adA_easy.vcd | glsim/run_A.sh:7 |
| AdaPath_A | Hard mix | 5–8 | 4 | Hard 1 + Easy 3 | gl_adA_hard.vcd | glsim/run_A.sh:8 |
| Baseline_A | Full | 1–4 | 4 | Full 4 | gl_baA.vcd | glsim/run_A.sh:9 |
| AdaPath_B | Easy | 1–4 | 4 | Easy 4 | gl_ad_easy.vcd | glsim/run_adapath.sh |
| AdaPath_B | Medium mix | 15–18 | 4 | Medium 2 + Easy 2 | gl_ad_med.vcd | glsim/run_adapath.sh; evidence/gatelevel/adapath_B_runs.txt |
| AdaPath_B | Hard mix | 5–8 | 4 | Hard 1 + Easy 3 | gl_ad_hard.vcd | glsim/run_adapath.sh |
| Reference | a/b/c | 1–4,15–18,5–8 | 12 | Full 12 | gl_ref_a/b/c.vcd | glsim/run_ref.sh |

glsim TB의 timescale은 1ns/1ps, always #5이므로 주기 10 ns(100 MHz)이다. reset은 이미지마다 12 cycle이다. 전력 Tcl은 ASAP7 RVT_TT Liberty를 읽는다. 상세 공정·전압·온도 수치와 정확한 PDK/ORFS commit은 별도 확인 필요이며 라이브러리 이름만으로 값을 지어내지 않는다. 보고서의 STA는 1 GHz 제약에서 실패한 slack을 이용한 pre-layout 역산값이며, 100 MHz VCD 평가와 구분한다. 제출 Vivado TB의 1ps 단위 기능 시뮬레이션과도 다르다.

A의 Hard 및 B의 Medium/Hard 모드 에너지는 혼합 런에서 Easy 에너지를 차감한 추정으로 입력별 Easy 에너지가 같다는 가정이 있다. Reference는 합계 12장, Baseline_A는 4장으로 구성되어 있으므로 전체 독립 테스트셋의 직접 전력 평균이 아니다. WM은 B 모드 에너지로 대리 추정했으며 별도 WM VCD 런이 확인되지 않는다.

## 보고서 반영 문단

재현성을 확보하기 위하여 모델 체크포인트·테스트 데이터·분석 코드의 해시와 분할 seed, 동작점 및 입력별 예측을 함께 보존하였다. 하드웨어 결과의 실행 스크립트와 전력 런 구성을 별도 표로 정리하였으며, 저장소 리포트에서 확인한 OpenROAD 버전은 26Q3-1305-gf552262465였다. 확인되지 않은 Yosys/ABC·Icarus 및 학습 당시 Python/PyTorch 버전은 확인 필요로 남겼다. 이번 Python 분석의 실행 환경은 원본 하드웨어 평가 환경과 분리하여 기록하였다. 주최 TB 로그 4개는 evidence README에 열거되어 있으나 실제 파일이 없으므로 전체 로그의 추가 확보가 필요하였다.

권장 위치: **부록 A: 실행 환경과 재현 절차**; 3.6·3.7에서 표를 참조한다.

그림 캡션: **평가 단계별 재현성 근거와 미확인 항목. 연한 녹색은 이번에 추가한 Python 분석 기록이며, 원본 하드웨어 실험을 재실행했다는 의미가 아니다.**

재실행: `python results_sh/v2/06_reproducibility/analyze.py --repo <repository> --cache <cache>`.
