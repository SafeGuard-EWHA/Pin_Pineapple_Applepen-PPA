# 실제 클럭 게이팅 구현 및 전력 재측정 — 진행 중

**현재 단계: 별도 RTL 구현·기능 대조 완료 / 합성 및 VCD 전력 재측정 미실행.** 이 폴더는 최종 전력 결과가 아닌 재부팅 전 작업 체크포인트이다. 보고서의 28.7% 상한 추정을 실측 감소율로 대체할 근거는 아직 없다.

## 구현

기존 `rtl/adapath_top.v`에서 별도 모듈 `rtl/adapath_top_cg.v`를 생성하였다. Conv2, 후단 Pooling, Full FC, Light FC 네 인스턴스의 클럭에 하나의 후단 게이트를 적용하였다. 전단부, 경로 판단 FSM, 특징 버퍼 및 최종 argmax는 원래 클럭을 사용한다. 게이트 enable은 `!rst_n | start | conv2_en | fsm_done`으로 구성하여 리셋·시작·후단 완료 처리를 보존하였다.

`icg_latch.v`는 low 구간에서 enable을 저장하는 latch와 AND 기반의 **기술 독립적 클럭 게이팅 모델**이다. 아직 ASAP7의 특성화된 ICG 셀에 매핑되었다고 주장하지 않는다. 합성 후 실제 latch/gating 셀 구조와 생성 클럭, clock-gating timing check 및 게이트 수준 기능 검증을 확인해야 한다. FPGA 제출 프로젝트의 클럭 구조로 교체하는 작업이 아니며 원본 RTL·제출 ZIP·보고서를 수정하지 않았다.

## RTL 기능 검증

Vivado 2024.1에서 원본 제출 TB와 원본 DUT를 그대로 두고, 동일 입력을 받는 별도 `chip_cg` DUT를 추가하였다. 원본 TB의 계층 이름을 유지하였다. 매 상승 에지 후 1 ps에 valid_out 타이밍을 비교하고, 원본 출력 유효 시 decision·mode·margin을 비교하였다. Case inequality로 X 불일치도 검출하였다.

| 항목 | A | WM |
|---|---:|---:|
| 유효 출력 대조 횟수 | 1,001* | 954 |
| valid_out 타이밍 불일치 | 0 | 0 |
| decision·mode·margin 불일치 | 0 | 0 |
| Easy / Medium / Hard 커버리지 | 960 / 0 / 41* | 404 / 167 / 383 |
| 전체 관측 root clock 상승 횟수 | 856,644 | 895,926 |
| 후단 gated clock 상승 횟수 | 10,016 | 96,474 |

\* A에는 원본 TB가 채점에서 제외하는 초기 출력 1회가 포함된다. 채점 대상 1,000회의 로그는 이전 ZIP 실행과 완전히 같으며 966/1,000을 유지하였다. 초기의 미정 출력이 양쪽에서 같다는 것은 유효한 정답 판정을 뜻하지 않는다. WM은 원본 정확도 774/954, Golden 954/954를 유지하였다.

클럭 상승 횟수는 전체 시뮬레이션 관측 구간(reset·시작·경계 포함)의 신호 활동도이다. 이 비율을 전력/에너지 절감률로 해석해서는 안 된다. 추가된 게이트의 전력, 셀 면적, 클럭 부하 및 지연은 합성·전력 단계에서 별도로 평가해야 한다.

원문: [A 로그](logs/rtl_lockstep_A.log), [WM 로그](logs/rtl_lockstep_WM.log), [집계 JSON](rtl_validation.json). JSON의 `glitches`는 gated 상승이 root clock=1이 아닌 시점에 발생하는지만 검사한 보조 카운터이다. 전체 타이밍 안전성의 증명이 아니다.

별도 Icarus Verilog 12.0(devel) 시험 `tb_icg.v`에서는 enable/test_enable을 클럭 high 중에도 바꾸어 상승·하강이 root edge에 맞는지 검사하였다. 5개 펄스에서 위반 0건을 확인하였다([로그](logs/icg_test.log)). 셀 지연이 포함된 검증은 아직 수행하지 않았다.

## 재현

`python results_hs/clock_gating/prepare_rtl_check.py --workdir C:/Temp/ppa_clockgate_repeat`로 존재하지 않는 ASCII 작업 경로를 준비한다. 생성된 `run_A.tcl`, `run_WM.tcl`을 Vivado 2024.1 batch 모드에서 실행한다. 기존 저장소 RTL 및 제출 ZIP은 읽기만 하고 실험용 새 모듈과 별도 압축 해제본을 사용한다. 현재 Tcl에는 이 PC의 Vivado 설치 경로가 명시되어 있다.

## 설치 상태와 재부팅 후 재개

- 사용자 승인으로 Microsoft WSL 2.7.14.0 설치 완료(winget `Microsoft.WSL`).
- Windows VirtualMachinePlatform 활성화 완료. DISM 로그에 `Reboot required=yes`, `Restart suppressed by /NoRestart` 확인(2026-10-30 04:52 KST).
- **Windows 재부팅 필요.** 자동 재부팅은 실행하지 않았다.
- Ubuntu 24.04 배포판 설치 및 OpenROAD/Yosys/ORFS 설치는 재부팅 후 이어서 확인·진행한다.
- 원본 보고서는 서현 단독 편집 원칙에 따라 그대로 두었다. 결과는 `exp-hyunseo-final`로 전달한다.

재개 순서: (1) `wsl --status`, `wsl -l -v` 확인 → (2) Ubuntu 24.04 설치/초기화 → (3) ORFS 및 ASAP7 라이브러리·Yosys·OpenROAD 준비 → (4) 기준/게이팅 설계 동일 조건 합성 → (5) gate-level 기능·클럭 파형 확인 및 VCD 생성 → (6) 전력·에너지·면적·타이밍 대조 → (7) 결과·근거·한계와 서현 전달 문단 작성.

공식 설치 기준: [Microsoft WSL 설치](https://learn.microsoft.com/en-us/windows/wsl/install), [ORFS 사전 빌드 도구](https://openroad-flow-scripts.readthedocs.io/en/latest/user/BuildWithPrebuilt.html).

## 전력 실험에서 지킬 비교 조건

1. 우선 지정주제 A의 ungated/gated를 같은 입력·라이브러리 corner·합성 설정·SDC·툴 버전에서 재합성한다. 기존 보고서의 Reference 대비 개선율도 제시하려면 Reference를 같은 흐름으로 재측정하거나 동등성을 별도로 입증한다.
2. 기존 `glsim/tb_gl_A.v`의 대표 구간 START=1 및 START=5를 재현하되, 후자는 순수 Hard가 아니라 Hard와 Easy가 섞인 구간임을 명시한다. 같은 N과 reset 포함 창을 양쪽에 사용하고, 가능하면 경로별 층화 표본을 확장한다.
3. 정적 vectorless 추정이나 RTL clock edge 수로 전력 값을 대체하지 않는다. 합성 넷리스트 VCD와 annotation coverage를 보존한다. gated clock이 전력 엔진에서 실제로 읽혔는지 확인한다.
4. ICG/latch·AND 셀 매핑, 생성 클럭, STA의 unconstrained path 및 gating check를 확인한다. 같은 주파수 조건에서 전력과 에너지를 비교하고 최대 주파수 수치와 혼용하지 않는다.
5. 결과는 pre-layout gate-level VCD 기반 **추정 전력/에너지**로 표시한다. 실리콘 측정값이나 CTS 이후 실측값으로 표현하지 않는다.

## 서현 전달용 중간 문단

후단 클럭 활동을 줄이기 위해 별도 실험 설계에 latch 기반 클럭 게이팅을 추가하고 원본과 동일 입력에서 기능을 비교하였다. A 및 WM에서 관측된 valid_out 타이밍과 decision·mode·margin의 불일치는 없었다. 다만 이 결과는 RTL 기능 검증 단계에 해당하며, 게이트 삽입 오버헤드를 포함하는 합성 넷리스트 기반 전력·면적·타이밍 결과가 확보되기 전까지 에너지 절감률의 실측 근거로 사용하지 않았다.
