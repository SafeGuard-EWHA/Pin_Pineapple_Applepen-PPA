# 보고서 그림 사용 안내

각 그림은 흰 배경, Malgun Gothic, PNG 300 dpi와 SVG로 제공한다. SVG 글자는 폰트가 없는 PC에서도 모양이 유지되도록 경로로 저장했다. 문구 수정은 draw_figures.py를 수정하고 다시 실행한다. 입력 데이터·시뮬레이션 파형을 합성한 그림이 아니라 RTL 구조와 설계 절차를 설명하는 도식이다.

| 파일 | 권장 위치 | 캡션 제안 |
|---|---|---|
| fig_arch.png / .svg | 3.1, 기존 전체 구조도 교체 | AdaPath-NPU의 데이터 및 제어 흐름. 공통 전단부 이후 Score Margin으로 후단 경로를 선택한다. Easy는 Early 점수로 종료하며 Medium/Hard는 특징 버퍼를 재생한다. 모델 A의 선정 동작점에서는 Medium을 선택하지 않는다. |
| fig_top2.png / .svg | 3.2, 개선 결과 표 앞 | Top-2 Finder의 직렬 비교 체인과 이진 토너먼트 트리. 낮은 index 우선 동점 규칙과 출력 레지스터를 유지하면서 병합 레벨을 줄였다. 하단 PPA는 Region 2 단독 합성 범위의 제공 결과이다. |
| fig_wrapper.png / .svg | 3.4 | 주최 측 chip 인터페이스를 유지하는 래퍼. 가중치 입력은 호환용 미사용 포트이며 학습 가중치는 내부 상수로 공급한다. clk에서 샘플링한 rst_n의 상승을 검출해 start를 생성한다. |
| fig_flow.png / .svg | 3장 도입 | 공동 학습, 임계값 탐색, 정수 Golden 생성, RTL 검증, 합성·STA, VCD 기반 전력 추정과 PPA 비교를 연결한 설계 흐름. |

`python draw_figures.py`로 재생성하며 Python 3, matplotlib 및 Windows Malgun Gothic이 필요하다. 제작 환경 matplotlib 3.11.2. 추가 데이터 파일은 필요 없다.

검토 기준은 main 495cd63560ee724df7e0b03f7a199d73be13bf7b의 RTL 및 보고서 생성 코드다. 그림의 400,000 벡터 동일성과 Vivado 실행 문구는 사용자 제공·저장소 서술에 근거하며 이번 작업에서 해당 실험을 재실행하지 않았다. 최종 로그 대조는 results_sh/proofread.md를 따른다.

새 그림을 삽입한 뒤 최종 보고서의 그림 번호와 본문 참조를 함께 갱신한다. 본 그림에는 제출본 그림 번호를 고정하지 않았다.
