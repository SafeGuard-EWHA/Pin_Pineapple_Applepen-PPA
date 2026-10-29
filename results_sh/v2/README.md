# AdaPath-NPU 보고서 보강 분석 v2

기준: main `4990d117fcc571183000605a514ad5d9c7d5c98a`의 README 및 17쪽 통합 보고서. 분석 결과는 **exp-seohyun-2**에만 추가하며 원본 보고서·RTL을 수정하지 않는다. Python 고정 체크포인트 분석이며 재학습·RTL 스윕·열화 입력 실험·새 PPA 측정은 하지 않았다.

## 읽는 순서

1. [임계값 선택/평가 분리](01_independence/README.md): 세 모델의 2-fold × 5 seed, 기존 후보 방식과 경계 전수 탐색을 병기.
2. [난이도 지표 비교](02_metrics/README.md): 모델 A 4지표 Pareto·AUROC·분석적 회로 연산 수 및 추가 교차 평가.
3. [통계적 비교](03_statistics/README.md): 기존 동작점 Wilson 95% 구간, 불일치 쌍, McNemar exact 및 Holm 보정.
4. [WM 클래스별 분석](04_wm_classes/README.md): 경로 비율, 클래스별 recall, Full/AdaPath 혼동 행렬.
5. [MNIST 오류 분석](05_error_analysis/README.md): 높은 Margin의 Easy 오답과 Hard 사례, 숫자 쌍별 원시 기록.
6. [재현성 부록](06_reproducibility/README.md): 확인한 도구 버전·명령·분할·VCD 런 및 미확인 항목.
7. [관련 연구 3편](07_related_work/README.md): 실제 원문으로 확인한 판단 지표·경로·구현·평가 방식 비교.

각 작업 README에는 보고서 삽입 문단, 권장 절, 그림 캡션이 있다. CSV/JSON은 반올림 전 수치와 sample ID를 포함한다. 모든 그림은 흰 배경, Malgun Gothic, PNG 300 dpi 및 SVG이다. 결과의 출처는 [manifest](provenance/manifest.json)에 체크포인트/데이터/코드 Git blob 및 SHA-256, 추론 seed, 분할 seed와 실제 실행 환경으로 기록하였다.

## 핵심 해석

- 제공된 체크포인트와 데이터에서 보고서의 세 head 정확도가 재현되었다.
- 모델 A의 기존 25개 후보 방식은 5회 교차 평가에서 손실 예산을 유지했지만, 더 촘촘한 경계 탐색은 일부 반복에서 초과하였다. 모델 B 및 WM은 두 탐색법 모두 평가 시 5회 전부 손실 예산을 초과하였다. **선정셋 제약이 미사용 평가 절반의 보장을 뜻하지 않는다.**
- Margin은 동일셋 0.5%p 예산에서 네 지표 중 가장 작은 평균 MAC을 보였다. AUROC는 max-softmax가 더 높았다. Top-1 logit은 Margin보다 연산이 단순하므로 “Margin이 모든 지표 중 최소 회로 비용”이라는 주장은 쓰지 않는다.
- 기존 동작점에서 모델 B의 Full 대비 정확도 하락은 양측 exact test에서도 드러났다. A/WM의 비유의 결과는 동등성이나 비열등성의 증명이 아니다. 같은 테스트셋으로 임계값을 선정했던 사후 통계라는 한계를 함께 명시한다.
- 주 절감률 분모는 요청한 `arch.mode_macs()['Hard']`이며, Early FC를 제외한 물리 Baseline 대비 값도 별도 제공한다. MNIST B의 40.94%와 40.59%는 서로 다른 분모이며 단순 수치 오류가 아니다.
- WM Edge-Ring의 Easy 비율은 84.35%였지만 none의 Hard 비율은 83.27%였다. Scratch recall은 Full 63.60%에서 AdaPath 60.53%로 감소하였다. 클래스별 한계를 전체 평균과 함께 제시한다.
- A의 Easy 오답은 전체의 1.29%(129장), Easy 내부의 1.37%이며 그중 58장은 Full이라면 회복 가능했다. 높은 Margin도 정답을 보증하지 않는다.

## 재실행

저장소 루트에서 Python 환경에 numpy, scipy, matplotlib, CPU PyTorch를 설치하고 Malgun Gothic을 사용할 수 있도록 한다. 이번 실제 버전은 manifest 및 requirements.txt를 확인한다.

```bash
python results_sh/v2/prepare.py --repo . --cache work/v2_cache
python results_sh/v2/run_p0.py --cache work/v2_cache
python results_sh/v2/run_p1.py --repo . --cache work/v2_cache
python results_sh/v2/07_related_work/analyze.py
python results_sh/v2/validate.py
```

prepare.py는 `<prefix>_test.npz`와 `adapath_<prefix>_<arch>.pt`를 cache 한 폴더에 복사하고, **원본 collect()를 그대로 호출**한다. 글로벌 read-only forward hook으로 해당 호출의 Early 로짓을 포착하여 추가 모델 재구현을 피하였다. 데이터는 x/255, CPU float32 추론이며 점수·통계 계산은 float64이다. 새 임계값을 RTL용 정수로 변환하거나 적용하지 않았다.

재생성 결과는 이 README와 같은 `results_sh/v2/`에 저장된다. cache는 중간 파일이며 커밋하지 않는다. 파형·전력 결과와 Python MAC/정확도 결과를 혼합하지 않는다.

## 분석 범위

2-fold는 **임계값 선택**을 평가 표본과 분리한다. 이미 관찰된 테스트셋을 사후 분할한 것이므로 모델 구조 선택까지 독립인 신규 외부 검증은 아니다. 반복 seed는 분할 민감도를 나타내며 모델 재학습 seed가 아니다. 윌슨 구간과 exact test는 표본 독립성 가정을 가진 이미지 단위 분석이다. 원본 학습 데이터와 제조 lot 계보가 제공되지 않아 학습/테스트 중복이나 공정 상관은 완전히 감사하지 못하였다.
