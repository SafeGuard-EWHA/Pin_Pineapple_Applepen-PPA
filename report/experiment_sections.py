"""Validated model-A RTL experiments used by make_final_report.py.

Tables are derived from committed CSVs; this module does not rerun simulation.
"""
import csv
from pathlib import Path


def load_results(root):
    root = Path(root)
    def read(name):
        with (root / 'rtl' / name).open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            for k in row:
                if k not in ('kind', 'design'):
                    row[k] = float(row[k]) if k in ('level', 'avg_cycles') else int(row[k])
        return rows
    sweep = read('sweep_A.csv')
    robust = read('robustness_A.csv')
    expected = [0, 10, 20, 30, 40, 50, 63, 80, 100, 119, 140, 170, 200, 250, 300, 400]
    assert [r['TH'] for r in sweep] == expected
    assert all(r['TL'] == r['TH'] and r['med'] == 0 for r in sweep)
    assert len(robust) == 34
    levels = {'contrast': [1., .7, .5, .4, .3, .2], 'blur': [0., 1., 2., 3., 4.],
              'gauss': [0., 20., 40., 60., 80., 100.]}
    by = {(r['kind'], r['level'], r['design']): r for r in robust}
    assert len(by) == 34
    assert set(by) == {(k, lv, design) for k, ls in levels.items() for lv in ls for design in ('ada', 'base')}
    for r in sweep + robust:
        assert r['easy'] + r['med'] + r['hard'] == 1000
        assert r['med'] == 0 and 0 <= r['correct'] <= 1000
        if r.get('design') == 'base':
            assert r['hard'] == 1000 and r['avg_cycles'] == 985
        else:
            # RTL text output may truncate, rather than round, the last decimal.
            assert abs(r['avg_cycles'] - (845 + 171 * r['hard'] / 1000)) < .0101
    def gate(r, correct, cycles, easy, hard):
        assert (r['correct'], r['avg_cycles'], r['easy'], r['hard']) == (correct, cycles, easy, hard)
    gate(sweep[6], 970, 851.84, 960, 40)
    gate(by['contrast', 1., 'ada'], 970, 851.84, 960, 40)
    gate(by['contrast', .3, 'ada'], 930, 909.98, 620, 380)
    return sweep, by, levels


def add_experiments(doc, root, para, h2, table, figure):
    root = Path(root)
    sweep, by, levels = load_results(root)
    doc.add_page_break()
    h2(doc, '3.10 임계값에 따른 정확도와 처리 cycle')
    para(doc, 'Score Margin 임계값이 경로 사용률과 정확도–처리시간 절충에 미치는 영향을 평가하였다. '
         '본 실험의 연구 질문은 임계값을 높여 Full 경로 사용을 늘리는 것이 정확도 향상으로 이어지는지, '
         '그리고 사전 지정 동작점 TH=63이 평가 입력에서 어떤 위치에 놓이는지이다.', indent=True)
    para(doc, '모델 A의 가중치와 기존 RTL을 고정하고 TL=TH를 16개 값으로 변화시켰다. '
         '입력 1,000회를 순차 실행하였으며 각 조건에서 정상 출력 수 1,000개와 모드 합을 검증하였다. '
         'TH=63에서 970개 정답, 851.84 cycle, Easy/Medium/Hard=960/0/40을 먼저 재현한 뒤 나머지 조건을 실행하였다. '
         '평균 cycle은 테스트벤치가 정의한 start 이후 valid_out까지의 관측값이다. '
         'TL=TH이므로 Medium 구간은 비어 있으며 본 절은 Easy/Hard 두 경로를 평가한다.', indent=True)
    table(doc, '모델 A 임계값 스윕의 전체 결과',
          ['TL=TH', '정답 / 1,000', '정확도 (%)', '평균 cycle', 'Easy', 'Hard'],
          [[r['TH'], r['correct'], f"{r['correct']/10:.1f}", f"{r['avg_cycles']:.2f}", r['easy'], r['hard']] for r in sweep],
          [1.8, 2.8, 2.7, 3.1, 2.5, 2.5], hl_rows=(6,), size=9,
          note='모든 조건에서 Medium=0이다. 입력은 고유 100장의 10회 반복으로, 독립 표본 1,000장에 대한 평가와 구분한다.')
    para(doc, 'Hard 비율을 p_H라 하면 평균 cycle은 C = 845(1−p_H) + 1016p_H = 845 + 171p_H로 표현된다. '
         '관측된 16개 조건은 CSV의 표시 정밀도 범위에서 이 관계와 일치하였다. '
         'TH가 0에서 400으로 증가할 때 Hard 비율은 0%에서 73%로 증가하고 평균 cycle은 845.00에서 969.83으로 증가하였다. '
         '반면 정확도는 98.0%에서 97.0%로 낮아진 뒤 유지되어, 추가 계산이 정확도 개선을 보장하지 않음을 확인하였다.', indent=True)
    figure(doc, str(root / 'out/fig_sweep_A.png'),
           '모델 A의 임계값별 정확도와 평균 cycle. 동일 좌표의 TH는 묶어 표기하였다. '
           '점선은 기존 Reference 정확도 97.0%이며 새 Reference 실행 결과가 아니다.', 16.5)
    para(doc, '정확도를 최대화하고 cycle을 최소화하는 두 목적에서 TH=0, 10, 20, 30은 동일한 비지배 동작점이었다. '
         '이들은 TH=63보다 정확도가 1.0%p 높고 평균 cycle이 6.84 적었다. 따라서 TH=63을 이번 입력의 최적값으로 해석하지 않았다. '
         'TH=63은 기존 결과와 열화 실험을 연결하기 위한 사전 지정 기준점으로 유지하였다. '
         '동일 입력에서 탐색한 낮은 TH의 성능은 사후 선택 결과이며, 이를 새로운 입력의 최적값으로 일반화하려면 '
         '독립 검증셋에서 임계값을 고정한 뒤 미사용 테스트셋으로 평가해야 한다.', indent=True)
    para(doc, 'Full 경로는 Early 경로보다 연산량이 많지만 모든 입력에서 더 정확한 분류기를 뜻하지는 않는다. '
         '정확도 변화의 원인을 확정하려면 동일 이미지의 Early/Full 예측과 margin을 대응시켜 분석해야 한다. '
         '본 실험은 경로 선택의 동작과 처리 cycle을 검증하며, 통계적 유의성·전력 절감·3경로의 우월성을 입증하는 실험은 아니다.', indent=True)

    doc.add_page_break()
    h2(doc, '3.11 입력 열화에 따른 경로 배분과 정확도')
    para(doc, '입력 열화가 심해질수록 Hard 경로의 사용이 증가하는지, 그리고 해당 계산 증가가 '
         '항상 전체 경로를 실행하는 Baseline_A 대비 정확도 손실을 억제하는지 평가하였다. '
         '두 설계는 같은 모델 A 가중치와 동일한 열화 입력을 사용하였고, AdaPath_A는 TL=TH=63으로 고정하였다. '
         'Baseline_A는 VARIANT=0으로 Early Classifier 없이 전체 경로를 실행한다. '
         '주최 측 Reference와의 비교 또는 별도 학습 모델 간 비교와 구분하였다.', indent=True)
    table(doc, '입력 열화의 생성 조건', ['종류', '수준', '변환 및 처리'], [
        ['대비 축소', '1.0, 0.7, 0.5, 0.4, 0.3, 0.2', '픽셀값에 계수 c를 곱함'],
        ['평균 블러', '0, 1, 2, 3, 4회', '영 패딩 3×3 평균 필터를 반복 적용'],
        ['가우시안 잡음', 'σ=0, 20, 40, 60, 80, 100', '픽셀 단위 N(0, σ²) 가산, seed=2026'],
    ], [2.5, 6.4, 7.1], size=9,
        note='변환 후 np.rint로 반올림하고 [0,255]로 포화시켰다. σ는 8-bit 픽셀값 단위이다. '
             '종류별 수준을 나열된 순서로 생성하며 잡음 생성기의 상태를 이어 사용하였다. '
             '17조건×2설계의 총 34회 실행이며 세 종류의 무열화 기준점이 중복 포함된다.')
    para(doc, '원본과 대비 0.3의 필수 기준값을 검증하였으며, 34개 조합 모두에서 정상 출력 1,000개와 모드 합 1,000개를 확인하였다. '
         'Baseline_A는 모든 조건에서 985.00 cycle이었다. 아래 cycle 감소율은 '
         '(985−C_AdaPath)/985×100으로 계산하였으며, MAC·전력·에너지 감소율을 의미하지 않는다.', indent=True)
    labels = {'contrast': '대비', 'blur': '블러', 'gauss': '잡음 σ'}
    rows = []
    for k, ls in levels.items():
        for lv in ls:
            a, b = by[k, lv, 'ada'], by[k, lv, 'base']
            rows.append([f'{labels[k]} {lv:g}', f"{a['correct']/10:.1f}", f"{b['correct']/10:.1f}",
                         f"{(a['correct']-b['correct'])/10:+.1f}", f"{a['hard']/10:.1f}",
                         f"{a['avg_cycles']:.2f}", f"{(985-a['avg_cycles'])/985*100:.2f}"])
    table(doc, '모델 A의 열화 조건별 정확도와 처리 cycle',
          ['조건', 'AdaPath\n정확도 (%)', 'Baseline\n정확도 (%)', '차이\n(%p)', 'Hard\n(%)', 'AdaPath\n평균 cycle', 'cycle\n감소 (%)'],
          rows, [2.2, 2.5, 2.5, 1.5, 1.5, 3.0, 2.8], hl_rows=(0, 4, 10, 16), size=8.5,
          note='차이는 AdaPath−Baseline이다. 모든 AdaPath 조건에서 Medium=0이며 Easy 비율은 100−Hard(%)이다. '
               '정확도는 각 조건의 1,000회 입력에 대한 정답 비율이다.')
    figure(doc, str(root / 'out/fig_robustness_modes.png'),
           '열화 수준에 따른 Hard 비율과 평균 cycle. 기준점 TH=63에서 경로 배분의 변화를 관측하였다.', 17.0)
    para(doc, '대비가 1.0에서 0.2로 감소하면 Hard 비율은 4.0%에서 72.0%로 증가하고, '
         '평균 cycle은 851.84에서 968.12로 증가하였다. Baseline_A 대비 cycle 이득은 13.52%에서 1.71%로 축소되었다. '
         '블러와 잡음에서도 평가한 수준이 강해질수록 Hard 비율이 증가하였다. '
         '이는 입력 조건에 따른 계산 배분을 보여주지만, 계산 배분과 오류 억제의 성립 여부는 별도로 평가해야 한다.', indent=True)
    figure(doc, str(root / 'out/fig_robustness_acc.png'),
           '동일 열화 입력에 대한 AdaPath_A와 Baseline_A의 정확도. 강한 블러·잡음에서 조기 종료의 정확도 손실이 관측되었다.', 17.0)
    para(doc, '대비 0.3에서는 두 설계의 정확도가 93.0%로 같았고 AdaPath_A는 평균 909.98 cycle로 7.62%의 cycle 감소를 보였다. '
         '그러나 블러 4회에서는 87.0% 대 90.0%, 잡음 σ=100에서는 74.9% 대 83.0%로 각각 3.0%p와 8.1%p의 정확도 손실이 발생하였다. '
         '특히 σ=100에서 7.96%의 cycle 감소와 8.1%p의 정확도 손실이 함께 나타났다. '
         '따라서 무열화 조건의 정확도 유지 결과를 열화 분포 전체의 정확도 유지로 확장할 수 없다.', indent=True)
    para(doc, 'Score Margin은 확률로 보정된 신뢰도가 아니므로 큰 margin을 갖는 오분류도 가능하다. '
         '강한 잡음에서의 손실은 “Early Classifier가 확신을 갖고 틀리는 경우”와 양립하나, '
         '여기서 확신은 큰 점수 차이를 뜻하며 정답 확률을 뜻하지 않는다. '
         '집계 CSV만으로 개별 오류의 원인이나 오류가 발생한 경로를 확정하지 않았다. '
         '후속 분석에서는 동일 입력의 margin·mode·Early/Full 예측을 대응시켜 확인해야 한다.', indent=True)
    para(doc, '정확도는 열화 수준에 대해 단조 감소하지 않았다. 대비 0.5에서는 두 설계가 모두 99.0%로 원본의 97.0%보다 높았고, '
         '대비 0.2에서는 AdaPath_A 80.0%, Baseline_A 76.0%로 상대적 순위가 바뀌었다. '
         '이 결과는 해당 입력 집합에 대한 관측으로 기술하였으며, 대비 축소가 일반적으로 정확도를 개선한다는 주장으로 해석하지 않았다.', indent=True)

    h2(doc, '3.12 실험 재현성과 해석 범위')
    para(doc, '실험 1·2는 커밋 5b9d9d2ce36e86ef7d3a3dfd46eac903435a209f의 기존 RTL과 '
         'out/rtl_data_mnist_A/ 가중치를 고정하여 수행하였다. Python 3.12.14와 Icarus Verilog 12.0(devel)을 사용하였고, '
         '기존 설계 .v 파일은 수정하지 않았다. 실험 1은 원본 run_sweep.sh A와 같은 테스트벤치·컴파일 인수·16개 임계값을 '
         'Windows 실행기로 구동하였다. 실험 2는 make_noisy_inputs.py의 변환과 같은 RTL 비교 조건을 사용하였다. '
         '입력·소스·가중치 해시와 실행별 로그는 results_hs/exp1_artifacts/ 및 results_hs/exp2_artifacts/에 보존하였다. '
         '본 절의 표는 rtl/sweep_A.csv와 rtl/robustness_A.csv를 직접 읽어 생성하였다.', indent=True)
    para(doc, '원본 입력의 고유 이미지는 100장이다. 대비와 블러는 결정적 변환이므로 반복 입력을 독립 표본으로 취급할 수 없다. '
         '잡음은 반복 입력에도 서로 다른 실현값을 가하지만 원본 이미지의 다양성을 늘리지는 않으며, '
         '단일 seed 결과로 잡음 실현에 대한 변동성도 평가할 수 없다. '
         '따라서 본 결과에 독립 1,000표본을 전제한 신뢰구간이나 유의성 검정을 부여하지 않았다. '
         '또한 소프트웨어 float 평가, 정수 RTL 평가, 주최 TB의 복원 무작위 추출 결과는 입력과 수치 규약이 달라 분리하여 보고하였다.', indent=True)
