# 표 6. ASAP7 7nm Pre-layout PPA 비교

조건: 동일 RTL 소스(VARIANT 파라미터만 상이), 동일 INT8 규약, 동일 SDC,
Yosys(ABC area 모드) 합성 + OpenROAD pre-layout STA. 전력은 400 MHz(2.5 ns) 기준.

| 지표 | Baseline | Early-Exit | AdaPath |
|---|---|---|---|
| Cell Area (µm²) | 65825 | 71081 | 76963 |
| Cell 수 | 546303 | 589019 | 640064 |
| Area vs Baseline | +0.0 % | +8.0 % | +16.9 % |
| 임계경로 (ps) | 2044 | 4064 | 4204 |
| 최대 동작 주파수 (MHz) | 489 | 246 | 238 |
| 정적 추정 전력 @400 MHz (mW, 주2) | 6.7 | 16.3 | 31.3 |
| 평균 MAC / 이미지 | 83360 | 50822 | 49235 |
| 평균 Cycle / 이미지 | 985 | 876 | 876 |
| Energy / Inference | (주2) | (주2) | (주2) |

**난이도 판단 회로(Region 2: Top-2 Finder + Margin + Decoder + FSM) 단독 합성**
- Cell Area **385 µm²** (3864 cells) = AdaPath 전체의 **0.50 %**
- 설계 목표 '판단 회로 오버헤드 5 % 이내'를 큰 여유로 달성

주:
- (주2) 벡터 없는 정적(vectorless) 전력 추정은 모든 조합 로직이 상시 스위칭한다고
  가정하므로, 본 설계의 핵심인 모드 게이팅(Easy 82 %에서 후단 완전 정지)이 반영되지
  않는다. 즉 위 전력 값은 '전 블록 상시 활성' 가정의 보수적 상한이다. MAC 활동에
  비례하는 1차 근사로는 평균 MAC 40.9 % 절감이 그대로 동적 에너지 절감으로 이어지며,
  스위칭 파형(VCD) 기반의 정밀 Energy/Inference 산출은 결과보고서에서 수행한다(4장).
- 평균 MAC/Cycle 은 선정 동작점 모드 비율(Easy 82 % / Med 8 % / Hard 10 %)과
  RTL 시뮬 실측 사이클(Easy 845 / Med·Hard 1,016 / Baseline 985)로 계산.
- 전력은 벡터 없는 정적 추정: 가중치 포트 활동률 0(추론 중 고정), 픽셀 0.25, 제어 0.05.
- Early-Exit 변형은 Medium 입력을 Hard 경로로 처리(2단계).
- Area 증가분은 Early Classifier FC·Light FC 등 분기 자체의 면적이 대부분이며,
  판단 회로(Region 2)의 기여는 위와 같이 1 % 미만이다.