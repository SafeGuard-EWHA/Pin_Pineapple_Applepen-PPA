# 최신 보고서·파형·근거 재검토

기준 커밋: `4990d117fcc571183000605a514ad5d9c7d5c98a` (main, 2026-10-29). 보고서 개정: `5bedaf3`; 파형 추가: `734d775`; 근거 로그 추가: `1be27ca`. 이 문서는 원본을 수정하거나 실험을 재실행하지 않고 자료를 대조한 결과다.

## 검토한 파일

- `report/결과보고서_PPA.docx`, `report/결과보고서_PPA.pdf` (17쪽)
- `report/make_final_report.py`, `report/results.json`
- `out/fig_vivado_console.png`, `fig_vivado_ref_vs_ada.png`, `fig_vivado_detail_easy_hard.png`, `fig_vivado_detail_hard.png`
- `vivado/submit/PPA_AdaPath_NPU_A.zip` 내부 `PPA_AdaPath_NPU_A/sim/top_tb.v`
- `vivado/submit/adawave.tcl`, `refwave.tcl`, `detail.tcl`, `make_submit.tcl`
- `evidence/README.md`와 `evidence/gatelevel/`의 5개 텍스트 파일
- `python/train.py`, `python/data_wm811k.py`; 실제 실행 명령·학습 결과 재생성은 미수행

다운로드한 DOCX/PDF의 Git blob 해시는 저장소 트리와 일치한다. DOCX에서 추출한 그림 7–10은 아래 이미지 blob과 일치 여부를 검사했다. 모든 링크는 아래 기준 커밋으로 열어야 후속 변경과 혼동하지 않는다.

[검토 기준 트리](https://github.com/SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA/tree/4990d117fcc571183000605a514ad5d9c7d5c98a)

## 파형·콘솔에서 확인한 것

| 자료 | 직접 확인한 내용 | 해석 범위 및 조치 |
|---|---|---|
| 그림 7 / console | Objects의 accuracy=3c6, cnt=3e8; 콘솔 Accuracy 96%; top_tb.v 390행은 accuracy/10 정수 출력 | 966/1000=96.6%와 콘솔 96%는 모순이 아니다. 최종 정답 수는 그림으로 확인되지만 전체 실행 로그는 별도 필요 |
| 그림 8 / ref_vs_ada | 선택 시각 415.000 ns, accuracy 값 Reference=30 / AdaPath=46 | 두 값은 정답 누계다. 완료 이미지 수로 사용하려면 cnt/input_cnt 또는 valid_out 횟수와 대조. 초기 미정 실행과 오답 제외 여부를 명시 |
| 그림 9 / easy_hard | Easy 구간은 후단 enable 비활성, Hard 구간 margin=57, ch_en=111, replay 및 후단 enable 활성 | 해당 캡처 구간에서의 동작 근거로 사용 가능. 전체 데이터셋에서 전력 차단됨을 입증하는 자료는 아님 |
| 그림 10 / hard | 시간축 399,000~408,000 ps = 399~408 ns. margin=57, FSM BACK=3, replay, ch_en=111, valid_out 및 accuracy 44→45 | 본문의 이벤트 순서와 대체로 부합. 현재 확대에서 DECIDE/DONE 등 짧은 상태는 분해가 어려우므로 모든 상태 전이를 캡처만으로 검증 완료했다고 하지 않음 |
| 제출 A TB | 187행 timescale 1ps/1ps; 249행 always #5 | 주기 10 ps = 논리 시뮬레이션용 100 GHz. 415 ns=41,500 cycle이며 물리 회로가 100 GHz에서 동작했다는 결과가 아님 |
| 캡처 Tcl | adawave/refwave/detail 모두 run 415ns | 캡처 시간 단위 자체는 코드와 일치. 100 MHz 게이트레벨 전력 평가와 시간축이 다름을 캡션에 명시 |

권장 캡션 문구: **“주최 측 TB의 기능 시뮬레이션(클럭 주기 10 ps)에서 같은 41,500 cycle 구간을 비교한 파형이다. 시간축은 논리 검증용이며, 물리 동작 주파수 또는 100 MHz 전력 평가의 추론 시간으로 해석하지 않는다.”** 처리 완료 수가 확인되기 전에는 30/46을 “정답 누계”로 표시한다.

100 MHz로 단순 cycle 환산하면 41,500 cycle은 415 µs이다. 이것은 단위 환산이며 해당 주파수에서 새로운 처리량 실험을 수행했다는 뜻은 아니다. 그림 8의 46/30−1=53.3%와 전체 평균 cycle 기반 1336/854.8−1≈56.3%는 창 길이·입력 구성 등이 달라 반드시 일치할 필요는 없다.

## 추가 확인할 TB 경계 조건

ZIP의 top_tb_1000은 pixels[0:783999]를 선언하고, 375행에서 `$urandom_range(0,1000)`을 사용하며, 381행에서 `pixels[rand_num*784+img_idx]`를 읽는다. 이미지 1,000개에 대한 유효 인덱스는 0–999이므로 상한 1000이 선택되면 범위 밖 주소가 될 수 있다. 주최 측 TB 로직을 임의 변경하지 말고 실제 실행의 rand_num/주소/X 여부와 최종 채점 영향을 먼저 확인해야 한다. 이 정적 경계 지적만으로 특정 실행에서 오답이 발생했다고 단정하지 않는다.

“Hard 이미지 46”은 원본 데이터셋 index인지 실행 중 순번인지 구별해야 한다. 그림 10은 accuracy 44→45를 보여주므로 초기 실행 제외 규칙과 완료 카운터를 같이 제시하면 혼동을 줄일 수 있다.

## 새 로그로 해소된 부분과 남은 부분

| 항목 | 최신 증거 | 판정 |
|---|---|---|
| Reference 면적 | sta_and_power_B_ref.txt의 Chip area for module chip: 32084.864640 | 기존 fallback 상수만 확인했던 상태에서 진전. JSON 32,084.86464와 로그 일치 |
| A 모드·cycle | model_A_runs.txt: Easy 1–4 845 cycle; Hard 혼합 5–8에서 이미지 5는 mode 2 / margin 57 / 1016 cycle; Baseline 985 | 대표 입력 런의 실행 출력 확보. 1,000회 순차 전체 로그 확보와는 구분 |
| A 전력 | power_A.txt: Easy 1.839716 mW / 혼합 Hard 2.012354 mW / Baseline 2.084039 mW | JSON과 일치. 이 파일에는 A VCD 종료 시각이 없어 원시 시간 대조가 남음 |
| B·Reference 에너지 | sta_and_power_B_ref.txt에 B E/M/H 종료 34316000/37736000/36026000 ps, Reference 세 런 각 53836000 ps와 전력 | 시작 0 ps 및 명시된 ps 단위를 전제로 B 런 72.444610548/92.871767712/87.77500731 nJ와 Reference 평균 17.7411468443 nJ 산술 재현. 원본 VCD의 timescale·시작 시각 독립 검증은 남음 |
| Vivado 로그 | README가 vivado_logs의 Reference/A/B/relocated 4개 .log를 나열 | 기준 커밋 전체 트리에 해당 파일 없음. 파일명 안내와 실제 업로드를 구분. “모든 근거 로그 확보 완료”로 쓰지 않음 |
| 테스트셋 파일 | data_test/mnist_test.npz, wm811k_test.npz 추가 | 존재 확인. 새 데이터로 학습·정확도·스윕을 재실행하지 않음 |

## 보고서 반영 상태

수치 및 문서 구조의 반영 완료·잔여 항목은 [proofread.md](proofread.md)를 따른다. 이전 [PPA 근거 분석](ppa_evidence_matrix.md)은 main 9b19224 시점 기록이며, Reference 면적 로그 확보 등 최신 판정은 이 문서가 우선한다. 이전 12쪽 PDF의 페이지·그림 번호를 최신 17쪽 PDF에 그대로 적용하지 않는다.

이 검토는 보고서의 주장을 전달받은 증거와 대조한 것이며, 제출 프로젝트의 Vivado 이식 실행·합성·전력 재측정·형식 검증을 수행한 결과가 아니다.
