# 제출용 Vivado ZIP 3종 독립 PC 실행 검증

## 결론

2026-10-30(KST), 작성자와 다른 사용자 PC에서 제출 ZIP 3종을 새 디렉터리에 풀어 Vivado 2024.1 GUI의 Behavioral Simulation으로 실행하였다. 세 설계 모두 전달받은 기대값을 재현하였다. 보고서 원문 및 제출 ZIP은 수정하지 않았다.

| 제출 프로젝트 | 기대값 | 이 PC 실제 결과 | 판정 |
|---|---|---|---|
| AdaPath A | 966/1,000, 콘솔 96%, accuracy=3c6 | 966/1,000, 콘솔 96%, accuracy=3c6 | 일치 |
| AdaPath B | 999/1,000, 콘솔 99% | 999/1,000, 콘솔 99%, accuracy=3e7 | 일치 |
| AdaPath WM | 774/954 = 81.13% | 774/954 = 81.13% | 일치 |
| WM Golden: decision, mode, margin | 954/954 | 954/954 | 일치 |
| WM Easy / Medium / Hard | 404 / 167 / 383 | 404 / 167 / 383 | 일치 |

A/B 콘솔은 TB의 정수 연산 때문에 각각 96%, 99%로 표시된다. 정답 수로 계산한 값은 96.6%, 99.9%이다. 이를 별도의 순차 1,000장 평가 결과와 혼용하지 않는다. 본 검증은 동봉 입력과 기존 TB에 대한 패키지 재현성 확인이며, hidden 입력 정확도나 합성·구현·실보드 동작 검증을 의미하지 않는다.

## 검증 대상과 방법

- 기준 main: `8f77e7f54ee999db10fbbb4d210db5e0f08ecb18` (84be9d5 이후 커밋).
- 실행 환경: Windows, Vivado 2024.1. 권장 버전 2023.1과 구분하여 기록한다.
- 원본: 기준 커밋의 `vivado/submit/PPA_AdaPath_NPU_{A,B,WM}.zip`.
- 새 경로: `C:/Temp/ppa_final_verify_20261030/`. 이전 시뮬레이션 생성물을 재사용하지 않고 압축을 해제하였다.
- GUI 실행 시 `scripts/run_*.tcl`의 `open_project`, `launch_simulation -mode behavioral`로 Run Behavioral Simulation과 동일한 실행 흐름을 사용하였다. 기존 프로젝트의 runtime=all 설정을 유지하였다.
- A/B는 종료 시점의 TB `accuracy`, `cnt`를 `get_value`로 읽었다. WM은 원본 TB의 최종 출력으로 대조하였다.
- `manifest_before.json`: ZIP SHA-256 및 모든 압축 멤버의 원본 SHA-256. `integrity_after.json`: 실행 후 원본 멤버 비교 결과.
- A 48개, B 48개, WM 23개 파일 중 각 `.xpr`만 Vivado 버전 전환으로 변경되었다. RTL, TB, 가중치·입력 데이터 및 README는 모두 원본 해시와 일치하였다. 변경된 실행용 `.xpr`은 제출 ZIP에 반영하지 않았다.

## 로그와 캡처

| 설계 | 실제 콘솔 캡처 | 전체 Vivado 로그 |
|---|---|---|
| A | [A_console.jpg](captures/A_console.jpg) | [A_vivado.log](logs/A_vivado.log) |
| B | [B_console.jpg](captures/B_console.jpg) | [B_vivado.log](logs/B_vivado.log) |
| WM | [WM_console.jpg](captures/WM_console.jpg) | [WM_vivado.log](logs/WM_vivado.log) |

컴파일·elaboration·시뮬레이션 로그와 Tcl journal도 `logs/`에 보존하였다. 세 실행 모두 컴파일/실행을 중단시키는 오류 없이 종료되었다. 보드 카탈로그의 미설치 part 경고, 이동된 프로젝트 경로/버전 갱신 안내, 대형 입력 배열의 파형 표시 제한 경고는 실제 로그에 남겼다. 파형 표시 제한은 입력 배열의 화면 표시 제한이며, 이번 시뮬레이션의 데이터 로드 실패가 아니다. 원본 TB의 `$stop`(A/B), `$finish`(WM)는 예정된 종료 지점이다.

## 서현 전달: 보고서 반영 문단·권장 위치·캡션

**권장 위치:** 검증 및 재현성 절의 제출 패키지 검증 항목 또는 해당 절 마지막 문단. 기존 정확도 실험 표를 대체하지 않는다.

**반영 문단:** 제출 패키지의 이식성과 재현성을 확인하기 위해, 작성자와 다른 PC의 Vivado 2024.1에서 A·B·WM 프로젝트 ZIP을 각각 새 경로에 압축 해제하여 Behavioral Simulation을 수행하였다. 패키지에 포함된 RTL·테스트벤치·가중치·입력 데이터의 SHA-256 일치를 확인하였으며, A와 B는 기존 테스트벤치에서 각각 966/1,000 및 999/1,000의 정답 수를 재현하였다. WM은 774/954(81.13%)의 분류 정확도와 decision·mode·margin의 Golden 일치 954/954를 재현하였고, Easy/Medium/Hard 사용 횟수는 각각 404/167/383이었다. 본 결과는 동봉 테스트 입력에 대한 제출 패키지 실행 재현성을 뒷받침하며, 비공개 평가 입력에 대한 정확도를 보증하는 결과로 해석하지 않았다.

**캡션 A/B:** 독립 PC의 Vivado 2024.1에서 제출 ZIP A/B를 실행한 최종 콘솔. 정답 수는 각각 966/1,000, 999/1,000이며 콘솔 백분율은 원본 TB의 정수 연산으로 표시된다.

**캡션 WM:** 독립 PC의 Vivado 2024.1에서 제출 ZIP WM을 실행한 결과. 정확도 774/954(81.13%), decision·mode·margin Golden 일치 954/954, 경로 사용 횟수 Easy/Medium/Hard=404/167/383을 재현하였다.

## 범위와 후속 작업

- P1-1 제출 ZIP 3종 실행 검증: 완료.
- HWP 이식: 제출 형식이 HWP임이 확인되고 서현의 최종 DOCX가 전달되는 경우에만 수행한다. 현재 이 검증의 완료 조건에는 포함하지 않았다.
- 보고서 원문은 서현 단독 편집 원칙에 따라 수정하지 않았다. 추가 결과는 본 브랜치에서 전달한다.
