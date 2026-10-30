# 배치 및 전역 배선 후 결과 (Reference, AdaPath_A)

- 흐름: ORFS(OpenROAD-flow-scripts) 전체 흐름, ASAP7, 두 설계 모두 같은 SDC 규칙(입출력 지연 = 주기의 20 %)과 클럭 주기 2,000 ps, CORE_UTILIZATION 40 %.
- 실행 스크립트: `flow_scripts/postlayout.sh` (설계 별칭 refchip_pl, adapath_A_pl).
- 배치, CTS, 전역 배선(5_1_grt)까지 완료하였다. 상세 배선(5_2_route)은 WSL 메모리(10 GB) 한도로 두 설계 모두 중단되었다(peak 약 10.4 GB).
- 아래 값은 `5_global_route.rpt`(전역 배선 기반 기생 추정, 전파된 클럭)와 `5_1_grt.json`에서 읽었다.

| 항목 | Reference | AdaPath_A |
|---|---:|---:|
| 표준셀 면적 (µm²) | 32,330.1 | 50,614.2 |
| 합성 직후 면적 (µm²) | 32,084.9 | 49,857.7 |
| 2,000 ps에서 최악 setup slack (ps) | +259.86 | +37.59 |
| 최악 hold slack (ps) | +36.19 | +25.20 |
| setup clock skew (ps) | 40.37 | 55.13 |
| 임계 경로 | fully_connected.out_idx -> comparator.buffer | u_fsm.state -> u_conv2 MAC 출력 레지스터 |
| 최소 주기 = 2,000 − slack (ps) | 1,740.1 | 1,962.4 |
| 환산 Fmax (MHz) | 574.7 | 509.6 |

두 임계 경로 모두 레지스터 간 경로이므로 입출력 지연 규칙과 무관하게 최소 주기 = 2,000 ps − slack 으로 환산하였다. 2 ns 목표로 최적화한 배치 결과에서의 환산값이며, 더 짧은 목표 주기로 다시 구현할 때의 Fmax와는 다를 수 있다. 리포트의 전력(report_power)은 기본 활동률 가정 값이므로 사용하지 않았다.
