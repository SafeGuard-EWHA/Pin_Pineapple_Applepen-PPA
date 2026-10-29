# 작업 3: 통계적 비교

출처: main `4990d117fcc571183000605a514ad5d9c7d5c98a`, 제공 테스트 NPZ와 모델 체크포인트, 고정 float 추론(seed=2026). 파일 해시·버전은 `../provenance/manifest.json`. 기존 25-분위수 보고점의 비반올림 임계값(`../01_independence/reported_points.json`)을 사용하였다. 요청된 모델 A literal 1.161과 B/WM의 소수 3자리 값에 대한 차이는 `rounded_threshold_sensitivity.csv`에 별도 제공한다.

Wilson 구간은 z=1.959963984540054를 사용했다. b=Full 정답·AdaPath 오답, c=Full 오답·AdaPath 정답으로 정의하였다. McNemar exact는 discordant b+c에 대한 Binomial(n=b+c,p=0.5)의 **양측 검정**이며 b+c=0이면 p=1로 정의하였다. 세 비교에 대해 Holm 보정도 함께 제공하였다.

| 대상 | n | Ada 정답 | Full 정답 | b | c | 차이 %p | 양측 p | Holm p |
|---|---|---|---|---|---|---|---|---|
| mnist_A | 10000 | 9747 | 9753 | 58 | 52 | -0.0600 | 0.6338 | 1 |
| mnist_B | 10000 | 9812 | 9851 | 54 | 15 | -0.3900 | 0.0000 | 0.0000 |
| wm811k_B | 954 | 775 | 778 | 19 | 16 | -0.3145 | 0.7359 | 1 |

## 보고서 반영 문단

mnist_A(n=10000)의 AdaPath 정확도는 97.47% (Wilson 95% CI 97.14–97.76%), Full 정확도는 97.53% (97.21–97.82%)로 나타났다. Full만 정답인 쌍 b=58, AdaPath만 정답인 쌍 c=52에 대한 양측 McNemar exact p-value는 0.633756였다(Holm 보정 p=1).

mnist_B(n=10000)의 AdaPath 정확도는 98.12% (Wilson 95% CI 97.83–98.37%), Full 정확도는 98.51% (98.25–98.73%)로 나타났다. Full만 정답인 쌍 b=54, AdaPath만 정답인 쌍 c=15에 대한 양측 McNemar exact p-value는 2.61285e-06였다(Holm 보정 p=7.83854e-06).

wm811k_B(n=954)의 AdaPath 정확도는 81.24% (Wilson 95% CI 78.64–83.59%), Full 정확도는 81.55% (78.97–83.88%)로 나타났다. Full만 정답인 쌍 b=19, AdaPath만 정답인 쌍 c=16에 대한 양측 McNemar exact p-value는 0.735879였다(Holm 보정 p=1).

주최 측 input_1000.txt는 고유 100장을 10회 반복한 자료이므로 1,000개의 독립 표본으로 간주할 수 없어 본 통계 검정에서 제외하였다.

**해석 제한:** 기존 동작점은 같은 테스트 라벨을 사용해 선정되었으므로 이 구간과 p-value는 사후 기술적 비교이며 선택 편향이 제거된 확증 검정이 아니다. 비유의 결과는 동등성이나 0.5%p 비열등성의 증거가 아니다. 작업 1의 교차 평가는 임계값 선택 독립성에 관한 별도 근거로 제시하며, 공유된 선정 데이터 때문에 단순 OOF Binomial p-value를 새 확증 결과로 만들지 않았다. WM은 공정 lot/wafer 계보가 없는 NPZ이므로 표본 간 공정 상관을 반영하지 못한 이미지 단위 구간이다.

권장 위치: **3.3 표 7 다음**, WM 값은 **3.9 표 14 다음**, 한계는 **4.2**.

그림 캡션: **기존 선정 동작점의 AdaPath와 Full 정확도 및 이미지 단위 Wilson 95% 구간. 구간 중첩 여부 대신 같은 이미지의 불일치 쌍에 대한 McNemar exact 결과를 별도 표에 제시하였다.**

재실행: `python results_sh/v2/03_statistics/analyze.py --cache <cache>`.
