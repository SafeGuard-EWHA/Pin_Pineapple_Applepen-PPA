"""Independent result sanity checks, without rerunning training or RTL."""
from common import *
import math
from PIL import Image
def main():
    info={};expected={'mnist_A':(10000,9753,9747),'mnist_B':(10000,9851,9812),'wm811k_B':(954,778,775)}
    rows=list(csv.DictReader((OUT/'03_statistics'/'statistics.csv').open(encoding='utf8')))
    for r in rows:
        key=r['model'];n,full,ada=expected[key];b=int(r['b_full_correct_ada_wrong']);c=int(r['c_full_wrong_ada_correct']);p=min(1.,2*sum(math.comb(b+c,k) for k in range(min(b,c)+1))/2**(b+c)) if b+c else 1.
        assert int(r['n'])==n and int(r['full_correct'])==full and int(r['ada_correct'])==ada
        assert ada-full==c-b
        assert abs(p-float(r['mcnemar_exact_two_sided_p']))<1e-12
        info[key]={'counts_match_report':True,'paired_difference_identity':True,'mcnemar_direct_binomial_match':True}
    dpi=[]
    for p in OUT.rglob('*.png'):
        im=Image.open(p);d=im.info.get('dpi');assert d and min(d)>299.9;dpi.append({'path':p.relative_to(OUT).as_posix(),'size':im.size,'dpi':d})
    for p in OUT.rglob('*.json'):json.loads(p.read_text(encoding='utf8'))
    folds=list(csv.DictReader((OUT/'01_independence'/'fold_results.csv').open(encoding='utf8')))
    assert len(folds)==60
    for r in folds:assert float(r['calibration_accuracy_pct'])>=float(r['calibration_full_pct'])-.5-1e-8
    splits=json.loads((OUT/'01_independence'/'split_indices.json').read_text())
    for key,ss in splits.items():
        for seed,f in ss.items():
            assert len(f['A'])==len(f['B']);assert set(f['A']).isdisjoint(f['B']);assert sorted(f['A']+f['B'])==list(range(expected[key][0]))
    info.update({'calibration_budget_all_60':True,'all_split_partitions_verified':True,'png':dpi,'base_commit':BASE_COMMIT,'seed':INFERENCE_SEED,'split_seeds':SEEDS})
    if (OUT/'04_wm_classes/results.json').exists():
        wm=json.loads((OUT/'04_wm_classes/results.json').read_text(encoding='utf8'));rows=wm['classes'];cm=wm['confusion'];assert sum(r['n'] for r in rows)==954
        assert [sum(r[k] for r in rows) for k in ['easy_n','medium_n','hard_n']]==[401,152,401]
        for name,key,total in [('Baseline_Full','full_correct',778),('AdaPath','ada_correct',775)]:
            a=np.array(cm[name]);assert a.sum()==954 and np.trace(a)==total
            assert np.array_equal(a.sum(1),[r['n'] for r in rows]);assert np.array_equal(a.diagonal(),[r[key] for r in rows])
        er=json.loads((OUT/'05_error_analysis/summary.json').read_text());es=list(csv.DictReader((OUT/'05_error_analysis/all_easy_errors.csv').open()))
        assert len(es)==er['easy_wrong_n']==129
        assert sum(r['full_pred']==r['y'] for r in es)==er['full_would_recover_easy_errors']==58
        assert all(float(r['margin'])>=er['threshold'] and r['early_pred']!=r['y'] for r in es)
        pairs=list(csv.DictReader((OUT/'05_error_analysis/easy_error_pairs.csv').open()));assert sum(int(r['count']) for r in pairs)==129
        assert len({r['sample_id'] for r in es})==129
        info['P1']={'wm_class_confusion_totals_match':True,'wm_mode_totals_match':True,'easy_error_labels_and_recovery_match':True,'easy_error_pair_total_match':True}
    dump(OUT/'provenance'/'validation.json',info);print('Independent checks PASS',flush=True)
if __name__=='__main__':main()
