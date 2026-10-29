# PPA 비교 조건 및 검증 근거 대조

검토 기준: main `9b192246ef0cde397824c757ad552d779532b549` (2026-10-29). 기존 교정안의 "원시 로그 미확보" 상태에서 진전하여, 이번에는 아래 저장소 원시 전력·STA·합성 리포트와 실행 코드를 직접 읽고 대조했다. **실험 재실행은 하지 않았다.** 링크는 검사한 커밋에 고정했다.

## 이번에 추가 확인한 사실

| 항목 | 확인한 근거 | 판정·보고서에 쓸 수 있는 범위 | 남은 조치 |
|---|---|---|---|
| 최신 결과 버전 | [results.json](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/report/results.json) | 기존 5b9d9d2 검토 때와 에너지·cycle 주요 값 동일. 최신 main은 Vivado 파형·portable 프로젝트 추가 | 후속 변경 시 커밋과 결과 파일 동시 고정 |
| A 전력 총합 | [power_A_easy.rpt](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/orfs/reports_final/power_A_easy.rpt), [power_A_hard.rpt](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/orfs/reports_final/power_A_hard.rpt), [power_Abase.rpt](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/orfs/reports_final/power_Abase.rpt) | 1.839716 / 2.012354 / 2.084039 mW로 JSON 일치. Hard 태그는 1H+3E 혼합 런이므로 순수 Hard 순간 전력으로 부르지 않음 | P0: 런 종류를 캡션·측정표에 명시 |
| VCD 적용 증거 | 위 power 리포트에 A 1,506,829개, Baseline_A 1,386,264개 pin activity annotation 기록 | VCD가 적용됐다는 증거 있음. 전체 핀 수·미주석 수가 없으므로 100% coverage라고 단정 불가 | P0: 미주석 신호·기본 activity 적용 여부 확인 |
| Reference 전력 | [power_ref_a.rpt](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/orfs/reports_final/power_ref_a.rpt), 같은 폴더 ref_b/ref_c | 각각 1.309291 / 1.316679 / 1.328517 mW. JSON ref_a와 일치 | 원본 VCD duration과 결합해야 nJ 검산 가능 |
| 시뮬레이션 clock | [tb_gl_A.v](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/glsim/tb_gl_A.v), [tb_gl_ref.v](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/glsim/tb_gl_ref.v) | timescale 1ns/1ps, always #5로 두 TB 모두 100 MHz | 합성 목표 1 GHz 및 역산 Fmax와 구분 |
| 전력 분석 SDC·코너 | [power_A.sh](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/flow_scripts/power_A.sh), [vcd_power_odb.tcl](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/flow_scripts/vcd_power_odb.tcl), [constraint_10ns.sdc](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/flow_scripts/constraint_10ns.sdc) | A 실행 스크립트는 10 ns SDC, ASAP7 RVT_TT liberty와 1_synth.odb를 사용 | P0: 실제 사용 liberty 목록·전압·온도·원본 명령 로그를 묶어서 제공 |
| 런별 입력 집합 | [run_A.sh](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/glsim/run_A.sh), [run_ref.sh](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/glsim/run_ref.sh) | A Easy·Baseline_A: index 1–4, A 혼합 Hard: 5–8. Reference: 1–4,15–18,5–8의 총 12개. 모두 같은 데이터 파일이지만 평균에 사용한 집합이 동일하지 않음 | P0: "동일 이미지"를 런별 대응 범위로 한정. 가능하면 세 설계를 동일 입력 목록으로 직접 평균 |
| reset과 측정 창 | 위 두 TB와 [make_results.py](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/report/make_results.py) | 이미지마다 reset low 12 clocks; A에는 별도 start sequence 있음. 덤프는 추론 반복 전 시작. 에너지 코드는 VCD 마지막 timestamp를 사용하므로 reset/start 구간을 별도로 제외하지 않음 | P0: reset 포함 추론당 런 평균으로 정의. raw VCD timescale·시작·끝 timestamp 보관 |
| 모드 에너지 분리 | make_results.py | A_easy=E(4E)/4, A_hard=E(H+3E)−3A_easy. 제공 runs_nJ와 산술상 일치 | 다른 이미지의 Easy 에너지 차이를 무시하는 근사. 동일 Hard 다수 입력 직접 측정으로 보강 |
| A·Baseline_A 셀 면적 | [adapath_A_synth_stat.txt](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/orfs/reports_final/adapath_A_synth_stat.txt), [baseline_A_synth_stat.txt](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/orfs/reports_final/baseline_A_synth_stat.txt) | 49,857.738840 / 45,501.001560 µm², JSON 일치 | Reference 면적은 생성 코드 fallback 상수 사용. 원본 합성 면적 로그 연결 필요 |
| WNS 값과 API | [sta_odb.tcl](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/flow_scripts/sta_odb.tcl), reports_final의 *_sta.txt | sta::worst_slack -max 호출 확인. A −673.131442 ps, Baseline_A −672.502612 ps, Ref −604.025610 ps로 JSON 산식과 일치. 이전의 "WNS 함수 확인 필요"를 해소 | Fmax 역산의 I/O 제약 유지 조건은 아래 별도 확인 |
| 임계 경로 위치 | [adapath_A_sta.rpt](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/blob/9b192246ef0cde397824c757ad552d779532b549/orfs/reports_final/adapath_A_sta.rpt) | w_conv2[999] 입력→Conv2 MAC register, 입력 외부 지연 200 ps 포함. 이 보고 경로는 Top-2 판단 회로가 아님 | P0: 외부 가중치 포트가 있는 합성 top과 상수 가중치 chip 래퍼를 구분 |
| Fmax의 해석 | 동일 rpt, designs_final/cfg의 세 SDC | 1 GHz에서 고정된 I/O 지연 200 ps를 유지한 1000−slack 계산은 보고 숫자와 일치. SDC가 I/O 지연을 주기의 20%로 계산하므로 주기를 바꾸며 비율도 유지하면 같은 Fmax가 보장되지 않음 | P0: 고정 I/O 지연 기준 추정 Fmax라고 명시하거나 주기 스윕으로 타이밍 통과점 검증 |
| 클럭망·후배치 | 전력 rpt Clock=0, STA ideal clock, 1_synth.odb | pre-layout 분석과 일치. 실제 배선·클럭망을 반영한 실리콘 측정은 아님 | post-layout은 향후 과제로 구분 |
| 재현 스크립트 | make_results.py의 GL 절대 경로, power 파일명 .log; 저장소 리포트는 .rpt | 현재 저장소 파일만 그대로 지정하면 파일명·VCD·개인 PC 경로 때문에 재생성 불가 | P0: 경로 인자화, .rpt/.log 호환, VCD 확보. 원본 스크립트는 이번에 변경하지 않음 |

## 팀원에게 받을 최소 자료

1. **P0 — 런 manifest:** 실제 netlist·ODB·RTL 커밋/해시, 가중치·입력 파일 해시, 실행 명령, 도구 버전, liberty 목록, SDC 경로.
2. **P0 — 에너지 측정 창:** 각 VCD의 timescale, 시작·끝 timestamp, 처리 이미지 index 목록, mode/decision/cycle 로그. 원본 VCD가 크면 이 요약부터 공유하되 원본은 보관.
3. **P0 — 조건 통일:** 세 설계를 같은 입력 집합·reset 정책으로 평가했는지, 다르면 보고서에 차이를 명시. Reference 12장과 Baseline_A 4장 평균의 차이를 숨기지 않음.
4. **P1 — 활동률:** annotated/unannotated 핀 수와 미주석 신호에 적용되는 기본 activity를 확인.
5. **P1 — 추가 스윕 결과:** 임계값·정확도·모드 횟수·평균 cycle을 함께 전달하면 새 에너지 모델에 실험 동작점을 연결 가능.

## 당장 추가할 비교 조건 각주

전력은 ASAP7 RVT_TT 라이브러리와 합성 후 회로의 100 MHz 게이트레벨 시뮬레이션 VCD에 기반한 pre-layout 추정이다. 에너지는 reset/start 구간을 포함한 런 에너지에서 계산하였으며, AdaPath_A의 모드 에너지는 대표 입력의 4장 Easy 런과 1 Hard+3 Easy 런을 이용해 분리하였다. Reference는 세 런 총 12개 입력, Baseline_A는 한 런 4개 입력의 평균이다. 따라서 본 비교는 동일 1,000개 입력에 대한 직접 평균 에너지 측정과 구분한다. 입력 분포에 따른 에너지 곡선은 이 모드별 추정값을 고정한 계산 모델이다.

## 작업 범위

이 분석은 원본 보고서·RTL·실행 스크립트를 수정하지 않는다. main의 최신 실험을 exp-seohyun에 병합하지 않고, 검사한 main 커밋을 명시한 분석 산출물만 추가한다. 과거 proofread의 페이지 번호·그림 번호는 이전 PDF 기준이며, 최신 main의 Vivado 파형 추가로 변할 수 있으므로 최종 통합 시 재대조한다.
