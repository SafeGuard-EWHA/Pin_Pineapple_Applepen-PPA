# 근거 로그

| 파일 | 내용 |
|---|---|
| vivado_logs/reference_top_tb_1000.log | 주최 측 chip.v, top_tb_1000 (Vivado 2023.1 xsim). 첫 'Final Accuracy' 블록이 유효 (967/1000). 그 뒤 출력은 $stop 이후 추가 run 으로 카운터가 한 바퀴 돈 것 |
| vivado_logs/adapath_A_top_tb_1000.log | 지정주제 제출 설계 AdaPath_A (966/1000) |
| vivado_logs/adapath_B_top_tb_1000.log | 확장 모델 AdaPath_B (999/1000) |
| vivado_logs/adapath_A_relocated_copy.log | 제출 프로젝트를 다른 폴더로 옮겨 원본을 숨긴 뒤 실행 (966/1000, 이식성 확인) |
| gatelevel/*_runs.txt | 게이트레벨 시뮬레이션(Icarus, 100 MHz, 이미지당 리셋 12 cycle) 런별 이미지 번호·판정·모드·cycle |
| gatelevel/sta_and_power_B_ref.txt, power_A.txt | OpenSTA read_vcd 전력 (Total 행: 내부 / 스위칭 / 누설 / 합계, W)과 VCD 종료 시각(ps) |

STA·전력 원본 리포트는 orfs/reports_final/ 에 있다 (*_sta.rpt: 임계 경로, power_*.rpt: report_power).
VCD 런 구성: A·B Easy = 이미지 1~4, Hard = 5~8 (5 Hard + 6~8 Easy), B Medium = 15~18 (15·18 Medium), Reference = 1~4, 5~8, 15~18 의 12장.
