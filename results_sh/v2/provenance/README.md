# 출처와 검산

- 기준 main 커밋: `4990d117fcc571183000605a514ad5d9c7d5c98a`.
- manifest.json: 사용 파일의 SHA-256/Git blob, 실제 Python·PyTorch·NumPy 환경, 모델 shape·클래스·모드별 MAC.
- *_predictions.csv: 원본 NPZ의 0-based sample ID, 정답, 세 head 예측, Margin, 모든 Early 로짓. 독립적으로 임계값 적용·통계를 다시 계산할 수 있다.
- algorithm_checks.json: 작은 무작위·동점 데이터에서 2차원 최적화와 단순 이중 탐색을 비교한 72개 검산.
- validation.json: 입력 blob 일치, 기존 정확도·동작점, CI 및 통계 재계산, 그림 dpi 검사 결과.

로컬 Git 인증 도우미가 실행되지 않아 main ZIP을 로그인된 GitHub 브라우저로 내려받았다. 사용한 입력 파일은 연결된 GitHub API의 고정 커밋 트리와 blob 해시를 대조하였다. `git pull`이 성공했다고 주장하지 않는다. 새 브랜치의 커밋은 해당 main 커밋을 부모로 GitHub Git Data API를 통해 생성한다.

모든 분석은 inference seed 2026 및 CPU 2 threads를 사용한다. 2-fold split seeds는 2026, 2027, 2028, 2029, 2030이다. 알고리즘 검산용 합성 데이터 seed는 11이다. 새 학습·RTL 시뮬레이션은 수행하지 않았다.
