# 제어 불변 조건 검증 — A 및 WM 제출 RTL

## 연구 질문과 결론

원본 제출 RTL이 실제 입력을 처리하는 동안 경로 선택·채널 마스크·결과 선택·응답 제한을 지키는지 확인하였다. Vivado 2024.1에서 always 블록 기반 관측 모듈을 독립 최상위로 추가하여 실행한 결과, 아래의 **실제로 검사된 네 조건에서 위반 0건**을 관측하였다. 이는 유한 입력에 대한 시뮬레이션 검증이며 모든 입력에 대한 형식 증명은 아니다. Medium이 실행되지 않은 A는 해당 조건의 통과 근거로 사용하지 않는다.

## 방법과 재현성

1. 기준 main `8f77e7f54ee999db10fbbb4d210db5e0f08ecb18`의 A/WM 제출 ZIP을 별도 경로에 압축 해제하였다. 원본 RTL, TB, 가중치, 입력의 SHA-256 일치를 확인하였다([integrity.json](integrity.json)). 실행용 `.xpr`에만 모니터 소스·시뮬레이션 설정을 추가하였고 원본 ZIP 및 보고서는 수정하지 않았다.
2. 원본 `top_tb_1000`/`tb_wm` 계층을 유지하고 `audit_top`을 별도 시뮬레이션 root로 추가하였다. `control_monitor.v`는 신호를 읽기만 하며 DUT/TB에 값을 구동하지 않는다. 모니터를 명시적으로 컴파일한 뒤 elaboration 및 simulation을 수행하였다.
3. 상승 에지 직전 start 및 모드 수락 조건을 저장하고 NBA 갱신 후 1 ps에 제어 신호를 검사하였다. 이 지연은 A의 10 ps, WM의 10 ns 클럭 주기보다 짧다. X도 잡도록 제어 비교에 case inequality(`!==`)를 사용하였다.
4. A의 최종 정확도는 966/1,000이며, 1,000개 채점 출력(라벨·decision·시각·성공 여부)이 [이전 원본 ZIP 실행](../submit_check/logs/A_vivado.log)과 완전히 동일함을 확인하였다. WM은 774/954(81.13%), Golden decision·mode·margin 954/954, 모드 404/167/383을 유지하였다.

초기 개발 중 TB를 하위 인스턴스로 감싼 방식에서는 A 채점이 967/1,000으로 달라졌다. 최종 결과에는 그 실행을 사용하지 않았다. 최종 독립 root 방식에서는 원본 TB 경로와 채점 로그 일치를 확인하였다. 제어 검증 때문에 원래 정확도 결과를 대체하거나 임계값을 변경하지 않았다.

## 조건별 검사 범위와 위반 수

| 조건 | 검사 시점/정의 | A 검사 수 | A 위반 | WM 검사 수 | WM 위반 |
|---|---|---:|---:|---:|---:|
| Easy 후 conv2 비활성 | FSM의 모드 수락 후 valid_out까지 매 cycle conv2_en=0 | 1,920 cycles | 0 | 808 cycles | 0 |
| Medium 하위 채널·Light FC 선택 | Medium S_BACK에서 ch_en=(1<<C2_MED)-1, conv2_en=1, fc_light_en=1, fc_full_en=0 | 0 (미실행) | N/A | 27,555 cycles | 0 |
| start 후 4,000 cycle 이내 응답 | start 에지를 0으로 두고 valid_out까지의 에지 간격을 계산 | 1,001 completed | 0* | 954 completed | 0 |
| result_sel과 선택 경로 일치 | S_BACK 및 결과를 소비하는 S_DONE에서 검사 | 8,012 cycles | 0 | 91,704 cycles | 0 |

`result_sel`은 S_FRONT/S_IDLE에서 기본값 Early로 돌아간다. 따라서 valid_out 시점의 IDLE 기본값을 직전 경로와 비교하여 오류로 오인하지 않고, 실제 결과 MUX가 소비되는 S_DONE 및 후단 활성 구간을 검사하였다. Medium의 채널 마스크는 S_BACK 활성 구간에 적용하였다. 후단 종료 후 ch_en=0은 정상 비활성 상태이다.

\* A는 종료 시점에 추가 start 1회가 남아 있다. 4,000 cycle이 지나기 전에 원본 TB가 `$stop`하므로 이 마지막 미완료 시작에 대한 응답 보장은 **미평가**이다. 0건은 관측 중 기한 위반이 없고 완료된 1,001회가 기한 이내였다는 뜻이며, 모든 start의 완료를 증명했다는 뜻이 아니다.

## 커버리지

| 항목 | A: 원본 주최 측 TB | WM: 원본 tb_wm |
|---|---:|---:|
| 관측 start / 완료 / 종료 시 진행 중 | 1,002 / 1,001 / 1 | 954 / 954 / 0 |
| 리셋으로 중단된 미완료 추론 | 0 | 0 |
| 완료된 Easy / Medium / Hard | 960 / 0 / 41 | 404 / 167 / 383 |
| 채점 대상 Easy / Medium / Hard | 960 / 0 / 40 | 404 / 167 / 383 |
| margin < TL | 39 | 383 |
| TL ≤ margin < TH | 0 (TL=TH=63) | 167 (TL=13, TH=41) |
| margin ≥ TH | 960 | 404 |
| margin 미정(X)인 완료 | 2 | 0 |
| 완료된 응답의 최대 에지 간격 | 1,016 cycles | 1,004 cycles |

A의 완료 1,001회에는 채점에서 제외되는 초기 출력 1회(Hard)가 포함된다. 이를 채점 표본이 1,001장인 오류로 기술하지 않는다. 각 완료 기록은 [A_transactions.csv](A_transactions.csv), [WM_transactions.csv](WM_transactions.csv)에 보존하였다. cycle은 start 수락 에지=0으로 센 간격이다. WM TB의 첫 에지를 포함한 `cyc` 값과는 1차이가 날 수 있으므로 기존 성능 표의 cycle 정의와 혼용하지 않는다.

## X 및 경계 관측 — 제어 검증과 구분

| 관측 항목 | A | WM |
|---|---:|---:|
| 추론 활성 중 제어 벡터 X 관측 cycle | 0 | 0 |
| 추론 활성 중 data_in X 관측 cycle | 2,096 | 221 |
| 완료 시 decision X | 1 (초기 비채점 출력) | 0 |

원본 TB의 초기화 및 스트리밍 경계에서 입력 X가 관측되었다. 따라서 본 결과를 “입력까지 모두 X가 없다” 또는 “원본 TB의 범위 밖 읽기를 해결하였다”로 기술하지 않는다. 이번 모니터는 입력 주소 범위를 고치거나 그 원인을 완전히 분해하는 검증이 아니다. 원본 TB를 유지한 조건에서 제어 불변 조건을 검사한 결과이다. 특히 A의 초기 출력과 채점된 1,000회는 분리하였다.

## 모니터 자체 검증

[monitor_selftest.v](monitor_selftest.v)를 Icarus Verilog 12.0(devel)의 `-g2012`로 컴파일·실행하였다. 정상 Easy/Medium/Hard 3회는 위반 없이 완료되었다. 이후 conv2 오활성, Medium의 잘못된 채널 마스크, 잘못된 result_sel, 4,000 cycle 초과의 네 오류를 모니터 입력에 각각 의도적으로 주입하여 각 1건을 탐지하였다. DUT에는 오류를 주입하지 않았다. 결과: [selftest.log](logs/selftest.log). 본 검증은 모니터가 비활성 상태여서 0건을 출력하는 경우를 점검하기 위한 것이며, 모든 모니터 버그가 없음을 보증하지 않는다.

## 재실행

`python results_hs/assertions/prepare_run.py --workdir C:/Temp/ppa_monitor_repeat`를 실행한 뒤 출력된 두 Vivado 명령을 실행한다. 작업 경로는 존재하지 않는 ASCII 경로여야 한다. 기본 설치 위치는 `C:/Xilinx/Vivado/2024.1`이며 `--vivado-root`로 바꿀 수 있다. 스크립트는 원본 ZIP SHA-256을 검사한다. 생성되는 `transactions.csv`는 각 프로젝트의 `.sim/sim_1/behav/xsim/`에 저장된다. `run_A.tcl`, `run_WM.tcl`에는 실제 실행 명령을 보존하였다. 로그의 `AUDIT` 행과 [summary.json](summary.json)을 대조할 수 있다.

전달용 `prepare_run.py`로 새 경로·빈 컴파일 캐시에서 A/WM을 재실행하여 전체 모니터 집계와 transaction CSV가 동일함을 확인하였다([clean_reproduction.json](clean_reproduction.json), `logs/clean_repro_*.log`). 원문 로그의 공백 및 경고는 근거 보존을 위해 그대로 두었다.

자체 검증은 `iverilog -g2012 -s monitor_selftest -o selftest.vvp control_monitor.v monitor_selftest.v` 및 `vvp selftest.vvp`로 실행한다. 이는 기존 RTL을 컴파일하지 않는 모니터 단독 시험이다. 전체 설계의 최종 결과는 Vivado 2024.1 실행 결과이다.

## 서현 전달: 문단·권장 위치·캡션

**권장 위치:** 설계 검증 절에서 정확도·Golden 일치 결과 다음, 또는 제출 패키지 재현성 검증 다음에 “제어 불변 조건 및 경로 커버리지” 항목으로 추가한다.

**반영 문단:** 원본 제출 RTL과 테스트벤치를 유지한 상태에서 독립적인 always 블록 기반 모니터를 추가하여 제어 불변 조건을 검사하였다. WM의 전체 954장(Easy/Medium/Hard=404/167/383)에 대해 Easy 후 conv2 비활성, Medium의 하위 4채널 및 Light FC 선택, 4,000 cycle 이내 응답, 결과 선택 신호의 경로 일치를 확인하였으며, 검사된 조건의 위반은 0건이었다. 특히 Medium 후단 활성 27,555 cycle을 검사하여 단일 대표 파형을 넘어 해당 경로의 실행 커버리지를 확인하였다. A에서도 검사된 조건의 위반은 없었으나, Medium 경로는 실행되지 않았으며 원본 TB 종료 시 추가 start 1회는 완료 여부가 미평가 상태로 남았다. 초기 비채점 출력과 입력 X 관측은 제어 조건의 통과와 구분하여 기록하였다. 이 결과는 평가 입력에 대한 시뮬레이션 검증으로 한정되며 모든 입력에 대한 형식적 보장을 의미하지 않는다.

**표 캡션:** A 및 WM의 제어 불변 조건별 실행 커버리지와 위반 횟수(Vivado 2024.1). 검사 수는 조건에 따라 활성 cycle 또는 완료된 추론 횟수이며, A의 Medium 미실행 및 종료 시 미완료 start는 통과로 집계하지 않았다. 초기 비채점 출력 및 입력 X 관측은 별도 경계 항목으로 분리하였다.
