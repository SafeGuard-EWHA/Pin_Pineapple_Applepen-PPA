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
