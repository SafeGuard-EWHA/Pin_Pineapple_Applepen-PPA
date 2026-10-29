# WM Medium 경로의 실제 동작 파형

## 검증 대상

기준 main `8f77e7f54ee999db10fbbb4d210db5e0f08ecb18`의 제출 ZIP `PPA_AdaPath_NPU_WM.zip`을 Vivado 2024.1에서 실행하였다. 원본 RTL·TB·가중치·입력은 변경하지 않았다. `wm_expect.txt`의 세 번째 행(0-based index=2)은 `0 0 1 16`이다. 정답/기대 decision=0, 기대 mode=1, 기대 margin=16인 첫 Medium 표본이다.

| 관측 항목 | 실제 결과 |
|---|---|
| Score Margin | 16 |
| 임계값 | TL=13, TH=41: 13 ≤ 16 < 41 |
| mode | 1 (Medium) |
| 후단 활성 구간 | 28.605–30.255 µs |
| ch_en | 0x0F: 하위 4채널 활성 |
| conv2_en / fc_light_en / fc_full_en | 1 / 1 / 0 (후단 활성 구간) |
| valid_out_6 | 30.265–30.275 µs에 1 |
| 유효 출력 시 decision | 0 (정답 및 Golden 일치) |

후단 완료 후 ch_en·conv2_en·fc_light_en이 0으로 돌아온 다음 valid_out_6이 발생한다. 이후 TB가 다음 이미지를 위해 reset하므로 mode가 기본값 2로 돌아오는 것은 다음 입력 준비 과정이다. 화면의 최종 시점 값만 보고 해당 이미지가 Hard였다고 해석하지 않는다.

## 자료

- [Vivado 전체 입력 구간 캡처](vivado_medium_overview.jpg)
- [Vivado Medium 활성화 캡처](vivado_medium_activation.jpg)
- [Vivado 결과 출력 포함 캡처](vivado_medium_result.jpg)
- [실측 VCD 기반 정리 그림 PNG](medium_wave_measured.png), [PDF](medium_wave_measured.pdf)
- [원시 VCD, 첫 31 µs](medium_first3.vcd), [전이 시각 JSON](medium_events.json)
- [재렌더링 스크립트](render_wave.py), [GUI 파형 재현 Tcl](show_medium.tcl)
- [VCD를 생성한 실행 로그](vivado_wave_run.log)

정리 그림은 원시 VCD의 실제 전이 값을 그대로 그린 것이며, GUI 캡처와 구별하여 제공한다. `render_wave.py`는 Python+matplotlib 환경에서 이 폴더를 기준으로 실행한다. GUI Tcl은 WM 원본 프로젝트의 Behavioral Simulation이 열린 상태에서 실행한다. 화면 확대는 해당 표본이 있는 20.2–30.3 µs 구간 또는 제어가 시작되는 28.6 µs 부근으로 맞춘다.

## 서현 전달: 보고서 반영 문단·권장 위치·캡션

**권장 위치:** 기존 Easy/Hard 파형 다음에 Medium 동작 검증을 추가하거나, WM-811K 검증 절의 경로별 동작 설명에 배치한다.

**반영 문단:** WM-811K 평가 데이터의 세 번째 표본을 이용하여 Medium 경로의 제어 동작을 확인하였다. 해당 표본의 Score Margin은 16으로, TL=13 및 TH=41 사이에 위치하여 mode=1로 분류되었다. 후단 활성 구간에서 ch_en=0x0F가 유지되어 Conv2의 하위 4채널이 선택되었으며, conv2_en과 fc_light_en은 활성화되고 fc_full_en은 비활성 상태를 유지하였다. 후단 종료 후 valid_out_6에서 관측한 decision은 0으로 정답 및 Golden 예측과 일치하였다. 이 단일 표본의 파형과 별도로, 전체 954장에 대한 제어 모니터 결과는 어서션 검증 표에 제시하였다.

**GUI 캡처 캡션:** WM-811K 세 번째 표본(index 2)의 Medium 경로 동작 파형(Vivado 2024.1). margin=16에서 mode=1이 선택되고, 후단 활성 구간에 ch_en=0x0F, conv2_en=1, fc_light_en=1, fc_full_en=0을 관측하였다. valid_out_6의 유효 구간에서 decision=0을 확인하였다. 시간축은 원본 tb_wm의 10 ns 클럭을 사용하는 기능 시뮬레이션 기준이며, 물리 구현 주파수나 Fmax를 나타내지 않는다.

**정리 그림 캡션:** Vivado 2024.1의 실측 VCD로부터 추출한 Medium 경로 제어 신호 및 출력 펄스. 좌측은 후단 활성부터 결과 출력까지, 우측은 10 ns 출력 펄스의 확대 구간을 나타낸다. 원본 GUI 화면 캡처가 아닌 실측 데이터의 재도식화이며, 10 ns 기능 시뮬레이션 클럭 기준이다.
