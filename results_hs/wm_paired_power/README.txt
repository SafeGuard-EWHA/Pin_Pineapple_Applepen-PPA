WM 동일 입력 전력 비교 — 실행 계획

기존 결과 57cf580은 AdaPath 모드별 4장과 Baseline 인덱스 0~3의 서로 다른 입력을 비교하였다. 본 작업은 같은 12개 입력과 동일한 관측 조건을 두 설계에 적용하여 입력 구성 차이를 제거한다. 기존 RTL, 합성 넷리스트 및 TB는 수정하지 않는다.

Easy [8,10,18,22], Medium [2,3,5,24], Hard [0,1,4,9] 각 구간을 두 설계에서 실행한다. Baseline [0,1,2,3]은 기존 결과와 환경 차이를 확인하는 대조 구간이며, 최종 같은 입력 평균에는 넣지 않는다. 로컬 도구 버전 차이로 양쪽 설계를 모두 재측정한다. 입력과 가중치, 셀 모델 및 넷리스트 SHA-256을 검증한다.

AdaPath는 wm_expect.txt와 decision/mode/margin을 비교하고, Baseline은 golden_reference.txt의 pred_full과 비교한다. 에너지는 구간 평균 전력×관측 시간÷4이며 이미지별 에너지가 아니다. 12장 선택표본 평균과 RTL954장 모드 비율로 가중한 추정치를 따로 보고한다. 선택 표본은 AdaPath에서 정답인 앞쪽 4장이므로 선택 편향과 작은 표본의 한계가 남는다.

현재 상태: 2026-11-01 KST, 7구간 실행과 독립 검산 완료. 10시간짜리 A 넷리스트1000회 실험은 수행하지 않았다. 보고서 원문 및 main은 수정하지 않았다. 보고서 반영용 문단은 HANDOFF.txt에 있다.

결과 (배치 전 VCD 활동도 기반 추정, 100 MHz)
구간       입력 수   Baseline 전력(mW) AdaPath 전력(mW) Baseline 에너지(nJ/장) AdaPath 에너지(nJ/장) 에너지 감소율
Easy           4         2.915011         2.395013          28.913994              20.403116           29.4352 %
Medium         4         2.919898         2.865052          28.962468              29.134714           -0.5947 %
Hard           4         2.881079         3.213441          28.577423              32.677482          -14.3472 %
음의 감소율은 증가를 뜻한다. 전력과 에너지는 서로 다른 지표다. Medium의 평균 전력은 1.8784 % 감소했으나 관측 시간이 길어져 에너지는 0.5947 % 증가하였다.

12개 선택 입력의 균등 평균: 28.817962 → 27.405104 nJ/장, 4.9027 % 감소.
RTL954장 모드 비율 404:167:383을 양쪽에 똑같이 적용한 추정: 28.787357 → 26.859362 nJ/장, 6.6974 % 감소.
두 평균은 추정 대상이 다르다. 후자는 954장의 전력을 전부 측정한 값이 아니다. 기존 8.8212 %는 다른 입력인 Baseline0~3을 공통 분모로 사용한 비교였으며, 같은 입력 비교값으로는 본 6.6974 %를 사용한다. 서로 합산하지 않는다.

검증과 관측 조건
- 12개 입력 인덱스와 픽셀 바이트의 SHA256을 확인하여 실제 픽셀 내용도 12종임을 확인하였다.
- AdaPath 12/12 decision, mode, margin 일치. Baseline 12/12 pred_full 일치. 별도 대조 구간 4/4 일치. 이는 서로 다른 설계의 판정이 전부 같다는 뜻이 아니다. Medium idx3은 AdaPath3, Baseline0으로 각각의 Golden과 일치한다.
- 각 모드에서 AdaPath 정답인 앞쪽 4장을 선택하였다. 무작위 추출이 아니며 선택 편향이 있다.
- 원본 TB는 이미지마다 12클럭 reset을 수행한다. 전체 4장 관측창에는 reset과 start 오버헤드가 포함된다. 동일 입력과 절차를 적용하되 실제 길이는 Easy34.076us, Medium/Hard40.676us, Baseline39.676us로 다르다.
- 실행에 사용한 패키지63파일은 manifest SHA256과 일치하였다. 57cf580 원본 Git blob과는 텍스트61파일에 CRLF/LF 차이만 있었으며 내용은 같았다. 원본 TB도 줄바꿈을 정규화해 내용 일치를 확인하였다. 합성 넷리스트2개는 압축 파일과 컴파일에 사용한 해제 파일의 해시를 각각 검증하였다.
- E=P*T/4로 독립 재계산하였다. 이 값은 4장 구간 평균이며 개별 이미지 에너지, 이미지별 표준편차 또는 모집단 신뢰구간을 제공하지 않는다.
- 기능 cycle은 Easy839, Medium/Hard1004, Baseline979였다. 이는 zero-delay 기능 검증이며 setup/hold, SDF 또는 Fmax 재검증이 아니다.
- Icarus12.0, OpenROAD26Q2-1164-g08f67ee5ec, ORFS7bf5a814e47c54ec6c64692b464d398184d99891을 사용하였다. 기존 OpenROAD26Q3 결과와 섞지 않고 두 설계를 재계산하였다.
- Baseline0~3 대조 구간은 29.458160368nJ/장으로 기존 값과 일치하였다. AdaPath Medium은 기존29.136127279에서29.134713788로 약0.00485% 차이가 있었다. 버전 영향만으로 원인을 단정하지 않는다.
- ASAP7 RVT TT Liberty의 time_unit은1ps, nominal0.7V/25도이다. 공통 SDC period10000은10ns이고 I/O delay는20%다. 이 설정은 타이밍 통과의 증거가 아니다.
- 컴파일의 ifnone/timing check 미지원 경고, Liberty STA-1212, LEF 중복 VIARULE/unknown site/undefined LIG 경고를 원문 로그에 보존하였다. 배치 및 배선, CTS, 기생 RC 없이 수행했으며 물리 구현이나 경고 없는 사인오프를 주장하지 않는다.
- 활동도 주석 수는 Baseline2,182,483핀, AdaPath2,745,470핀이다. 이 수만으로 전체 핀의100% 커버리지 또는 X/Z 없음은 증명되지 않는다. Clock 그룹0W는 클럭망을 구현하지 않은 모델의 출력이며 실제 클럭 에너지가0이라는 뜻이 아니다.

재현
1. 이 결과가 포함된 커밋의 submission/free_topic_WM811K/power 전체를 Linux 작업 폴더에 복사한다. input_manifest.json의 모든 파일을 유지한다.
2. Icarus12.0 및 위 OpenROAD/ASAP7 환경을 준비한다. raw/environment.json에 라이브러리와 LEF SHA256, CPU 및 운영체제 정보가 있다.
3. python3 scripts/run_paired.py --stage <복사한 power 폴더> --platform <ASAP7 플랫폼 폴더>
   이 명령은 오래 걸리는 시뮬레이션이다. 기존 완료 기록이 있는 동일 stage에서는 재실행을 건너뛴다. 기본 limit7이며 완료된 기록을 지우지 않는다.
4. 분석만 재현: python scripts/analyze.py (추가 패키지 불필요). 저장소의 power/data 및 weights를 읽고 raw 로그를 검증하여 summary.json을 다시 생성한다.
5. 근거 파일 검증: python scripts/check_evidence.py. Git 기록의57cf580 원본과 패키지 내용, 입력 해시, 컴파일 넷리스트 및 원문 로그 해시를 확인한다.

파일
- raw/: 시뮬레이션, 컴파일, 전력 원문 로그, 실행 기록 및 환경/입력 해시.
- scripts/: 실행 코드 및 독립 검산 코드.
- summary.json: 구간 수치, 양쪽 동일 가중 평균, 검산 결과 및 경고.
- HANDOFF.txt: 서현에게 전달할 문단, 권장 위치 및 캡션.
- evidence_checks.json: 패키지/로그/넷리스트 해시 추가 확인.
원시 VCD는 크기 때문에 GitHub에 넣지 않았다. /root/ppa-wm-paired12/paired_run/*.vcd.gz에 보존했고 SHA256과 바이트 수는 raw/runs.json에 있다. 압축 후 해제한 SHA256을 원본 VCD와 대조하였다.
