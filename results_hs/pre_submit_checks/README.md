# 제출 전 원본 보존 진단

설계 기준: exp-hyunseo 8e37d22. 실행 명령 및 원본 TB 해시: provenance.json.

## 원본 주최 TB
vivado/submit/PPA_AdaPath_NPU_A.zip을 풀고 sim/top_tb.v의 top_tb_1000을 별도 official_observer와 함께 실행하였다. 원본 TB 및 설계 파일은 변경하지 않았다. Icarus 기본 난수열을 사용하며 Vivado의 이전 실행과 동등한 난수열이라고 주장하지 않는다. 관찰 결과는 official_run.log에 있다: 출력 관측 1001, X decision 1, 이미지 1000 선택 2, 읽기 구간 범위 밖 접근 및 X 데이터 1570, TB accuracy 카운터 960. 이 카운터를 정상 1000회 정확도로 환산하지 않는다.

## Medium
rtl/tb_adapath.v 및 현재 모델 B 가중치로 9개 사례(Easy/Hard/Medium 각 3)를 실행하였다. Golden 비교 9 PASS, 0 FAIL. Medium 출력 3, BACK 513 cycle, 검사 위반 0. 관찰 범위는 medium_observer.v에 명시하였다. 전체 입력 공간의 형식 검증이 아니다.

medium_trace.vcd.gz는 실제 파형의 gzip 보존본이다. out/fig_medium_verified.png는 첫 Medium 입력의 VCD 시각화이며 EDA 도구 화면 캡처가 아니다. 원본 VCD 해시는 상위 report_integration_validation.json에 기록하였다. 빈 compile.log는 컴파일 오류가 없었음을 뜻한다. 실행 환경의 절대 경로는 다른 PC에서 조정해야 한다.
