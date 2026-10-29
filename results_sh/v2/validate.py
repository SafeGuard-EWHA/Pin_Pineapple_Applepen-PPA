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
    dump(OUT/'provenance'/'validation.json',info);print('P0 independent checks PASS',flush=True)
if __name__=='__main__':main()
