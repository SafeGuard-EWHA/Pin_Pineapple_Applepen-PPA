# 작업 2: 난이도 지표 비교 (모델 A)

출처: main `4990d117fcc571183000605a514ad5d9c7d5c98a`, MNIST 10,000장, `collect()` 호출의 원본 AdaPathNet forward hook으로 Early 로짓을 수집하였다. 추론 seed=2026; 파일·환경 해시: `../provenance/manifest.json`. 네 지표는 같은 가중치·이미지·후단 예측·MAC을 사용한다. 온도 보정은 수행하지 않았고 softmax 온도는 1이다. 엔트로피는 자연로그를 사용하며, 순위를 “높을수록 쉬움”으로 통일하기 위해 -entropy를 탐색하였다. 따라서 원래 엔트로피의 Easy 조건은 H≤-threshold이다.

AUROC는 Early 정답을 양성으로 하여 동점 평균 순위로 계산했다. 전수 곡선은 각 지표의 모든 점수 경계(동점 묶음, 전부 Easy/Hard 포함)를 평가하였다. **그림의 Pareto와 선정점은 동일셋 탐색 결과로 낙관 편향 가능성이 있다.** 같은 절차의 독립 절반 평가를 5 seed로 수행한 `oof_summary.csv`도 함께 제공한다. 각 지표의 정확도 제약은 Full 대비 -0.5%p이며 동률 규칙은 작업 1과 같다.

| 지표 | AUROC | 정확도 % | 평균 MAC | Hard 절감 % | Easy 임계값 |
|---|---|---|---|---|---|
| Score Margin | 0.9496 | 97.0300 | 44078.7840 | 24.7289 | 0.5128 |
| Max softmax | 0.9529 | 97.0300 | 44105.5680 | 24.6831 | 0.5661 |
| Negative entropy | 0.9499 | 97.0300 | 44255.8560 | 24.4265 | -0.8847 |
| Top-1 logit | 0.8931 | 97.0300 | 44529.6480 | 23.9589 | 1.1743 |

| 지표 | OOF 정확도 평균 | SD | OOF MAC 절감 평균 % | SD %p |
|---|---|---|---|---|
| Score Margin | 97.0220 | 0.0356 | 24.6750 | 0.0221 |
| Max softmax | 96.9920 | 0.0585 | 24.6928 | 0.0307 |
| Negative entropy | 96.9840 | 0.0477 | 24.4875 | 0.0445 |
| Top-1 logit | 97.0000 | 0.1243 | 23.6271 | 0.4420 |

## 분석적 회로 비용

| 지표 | 연산 종류·개수 | 구현 주의 |
|---|---|---|
| Score Margin | 16-leaf RTL: 15 merge nodes, each 3 comparison expressions (winner + two candidate maxima), mux; 1 subtraction | 45 syntactic comparisons before constant folding, not a measured gate count; no exp/log/div |
| Max softmax (direct) | 10 exp; 9 sum additions; 10 divisions (or 1 reciprocal + 10 multiplications); max via 9 comparisons | Finite-precision exp and reciprocal approximation/LUT or iterative arithmetic |
| Entropy (direct) | softmax above + 10 log + 10 multiplications + 9 additions + sign reversal | exp/log/reciprocal approximations; optimized identities reduce counts |
| Top-1 logit | 9 comparisons for max; no margin subtraction | No transcendental approximation |

위 수는 순진한 직접 수식 또는 저장소 RTL 구조의 연산 수이며 합성 후 셀 수·면적·지연·사이클 수가 아니다. 모든 방식의 임계값 비교 1개는 공통 비용으로 생략하였다. Margin은 최대값뿐 아니라 2위가 필요하므로 Top-1 logit보다 단순하다고 할 수 없다. 10개 입력 Top-2를 별도 최적화하면 고정 토너먼트에서 최대값 탐색 9회와 승자에게 진 후보 최대 3회 비교로 구현할 수도 있으나 본 RTL의 실제 합성 게이트 수를 뜻하지 않는다.

max-softmax의 **판정만** 필요하면 최대값을 빼서 exp(최대)=1로 두고 나머지 9개 exp의 합과 역임계값을 비교하여 나눗셈을 제거할 수도 있다. 엔트로피도 H=log Z−Σp_i z_i의 항등식으로 log 호출 수를 줄일 수 있다. 따라서 “반드시 exp 10개와 나눗셈 10개를 별도 회로로 구현해야 한다”는 주장은 피한다. LUT/구간 근사·시간 다중화 역시 가능하며, 비용의 실제 우열은 정밀도와 합성 조건에 따라 달라진다. 본 분석에서는 측정하지 않은 면적·지연 수치를 제시하지 않는다.

## 보고서 반영 문단

동일 Early Classifier의 로짓을 이용하여 Score Margin, 최대 softmax 확률, 엔트로피 및 Top-1 로짓을 비교하였다. Score Margin의 Early 정답 예측 AUROC는 0.9496였으며, Full 대비 정확도 손실 0.5%p 이내에서 정확도 97.03%, 평균 44078.78 MAC을 얻었다. 동일 제약의 최소 MAC 지표는 Score Margin이었고, Margin과의 차이는 0.00 MAC/이미지(0.000%)였다. 네 선정점의 정확도 범위 폭은 0.00%p였다. Score Margin은 확률 정규화·초월함수를 사용하지 않는다는 구현상 이점이 있으나, Top-1 로짓보다 연산 수가 적지는 않으므로 네 지표 중 절대 최소 회로 비용이라고 결론짓지 않았다. 회로 비용과 예측 성능의 절충으로 해석하였다.

권장 위치: **3.2 말미 또는 3.3 표 7 뒤**, 1장의 엔트로피 일반화 문장도 함께 수정.

Max softmax 대비 Margin의 MAC은 26.78개(0.061%) 적었다. Negative entropy 대비 Margin의 MAC은 177.07개(0.400%) 적었다. Top-1 logit 대비 Margin의 MAC은 450.86개(1.013%) 적었다. 그러나 AUROC는 Max softmax가 가장 높았다. 2-fold OOF 평균 정확도는 Margin 97.022%, Max softmax 96.992%, -entropy 96.984%, Top-1 97.000%였으며 모든 지표가 일부 분할에서 선정 예산을 벗어났다. 따라서 동일셋 MAC 순위를 독립 평가의 일관된 우월성으로 확대하지 않았다.

그림 캡션: **모델 A의 네 난이도 지표에 대한 동일셋 정확도–MAC Pareto와 Early 정답 예측 AUROC. 점은 Full 대비 손실 0.5%p 예산의 최소 MAC 동작점이다. MAC에는 지표 산출 회로의 비-MAC 연산을 포함하지 않았다.**

재실행: `python results_sh/v2/02_metrics/analyze.py --cache <cache>`.
