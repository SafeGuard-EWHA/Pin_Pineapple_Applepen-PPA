# 합성 넷리스트의 Vivado 기능 검증 (설명회 Sample Flow의 functionality 단계)

- 대상: 제출 chip(AdaPath_A, 가중치 상수)을 ORFS로 합성한 넷리스트 + 주최 측 ASAP7 표준셀 Verilog(지연 0 기능 모델) + 원본 `top_tb_1000`(TB 파일 무수정), Vivado 2023.1 xsim
- `scripts/xfill.v`: 시뮬레이션 전용 모듈. TB가 X 픽셀을 내보내는 경우(첫 비채점 이미지, 인덱스 1000)에만 DUT 입력을 0으로 치환하고, 채점 출력마다 이미지 인덱스와 판정을 `OBS` 줄로 기록한다. 이 모듈이 없으면 X가 제어 FSM까지 전파되어 valid_out이 1이 되지 않아 시뮬레이션이 시작 직후 멈춘다.
- `scripts/trace.tcl`: 10 ns 단위 단계 실행. 실행 폴더에 `stop.flag`가 생기면 정상 종료한다.
- 실행: `xvlog 1_synth.v asap7sc7p5t_*.v top_tb.v xfill.v` → `xelab top_tb_1000 xfill -timescale 1ns/1ps -debug typical -s netfill` → `xsim netfill [-sv_seed N] -tclbatch trace.tcl`
- `logs/net_seed*.log`: 넷리스트 실행 로그(기본 시드, -sv_seed 2~5). `logs/rtl_xfill_seed_default.log`: 같은 모듈을 적용한 RTL 실행(기존 Vivado 로그와 1,000개 출력 시각 동일, 879번째 인덱스 1000 이미지의 판정만 10→5, 정답 966 동일)
- `summarize.py`: 각 OBS 출력을 같은 인덱스의 RTL 결과(`results_hs/corrected_tb/sequential.csv`)와 판정 및 처리 cycle로 대조하여 `summary.json` 생성

## 2026-10-31 집계 교정

5개 시드의 부분 실행 합계는 판정 1,007/1,007 일치, cycle 1,006/1,006 일치이다. 기본 시드 n=123, 인덱스 1000의 치환 출력은 기준 cycle이 없어 대조에서 제외하였다. 이전 집계가 기준값 없는 출력을 자동으로 일치에 포함한 부분을 수정하였다. `cycle_checked`와 `cycle_excluded`에 실제 대조 범위를 기록한다. 첫 채점 출력은 첫 비채점 출력 시각 10,175 ps를 기준으로 기존 집계와 같은 방식으로 계산한다.

이는 원본 TB 한 번의 1,000회 실행 완료가 아니다. xfill은 X 또는 Z가 포함된 입력 바이트만 0으로 치환하는 시뮬레이션 전용 처리이다. 원시 로그와 화면 캡처는 보존하였으며 교정 근거와 보고서 반영 위치는 `results_hs/final_cycle_scope_correction/`에 있다.
