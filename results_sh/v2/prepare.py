"""Run unchanged collect(); capture its original model outputs with a read-only hook.
python results_sh/v2/prepare.py --repo . --cache work/v2_cache
"""
from common import *
import argparse,shutil,copy
def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True,type=Path);p.add_argument('--cache',required=True,type=Path);a=p.parse_args();a.repo=a.repo.resolve();a.cache=a.cache.resolve();a.cache.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(a.repo/'python'))
    import torch
    from analyze_margin import collect,ARCHS
    from model import AdaPathNet
    torch.manual_seed(INFERENCE_SEED);np.random.seed(INFERENCE_SEED);torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
    info={'base_commit':BASE_COMMIT,'inference_seed':INFERENCE_SEED,'split_seeds':SEEDS,'python':platform.python_version(),'platform':platform.platform(),'torch':torch.__version__,'numpy':np.__version__,'device':'CPU','threads':2,'inputs':{},'models':{}}
    for rel in ['README.md','python/analyze_margin.py','python/model.py','python/arch.py','python/train.py','python/data_wm811k.py','rtl/top2_finder.v','report/결과보고서_PPA.pdf','report/results.json']:
        info['inputs'][rel]=provenance(a.repo/rel)
    for key in ['mnist_A','mnist_B','wm811k_B']:
        prefix,archkey=key.split('_'); data=f'data_test/{prefix}_test.npz';ck=f'out/adapath_{key}.pt'
        for rel in [data,ck]:info['inputs'][rel]=provenance(a.repo/rel);shutil.copyfile(a.repo/rel,a.cache/Path(rel).name)
        ckpt=torch.load(a.cache/Path(ck).name,map_location='cpu',weights_only=True)
        arch=copy.deepcopy(ARCHS[archkey])
        for k,v in ckpt['arch'].items():setattr(arch,k,v)
        captured={}
        def hook(mod,inputs,output):
            if isinstance(mod,AdaPathNet):captured['early_logits']=output[0].detach().numpy().copy()
        h=torch.nn.modules.module.register_module_forward_hook(hook)
        try:r=collect(arch,ckpt,str(a.cache),prefix)
        finally:h.remove()
        r['margin']=r['margin'].astype('float64');r.update(captured);r['macs']=np.array(list(arch.mode_macs().values()));r['baseline_mac']=np.array(arch.mode_macs()['Hard']-arch.macs()['early_fc']);r['classes']=r['classes'].astype(str)
        assert np.array_equal(r['early_logits'].argmax(1),r['pred_early'])
        np.savez_compressed(a.cache/(key+'.npz'),**r)
        n=len(r['y']);full=(r['pred_full']==r['y']).sum();info['models'][key]={'n':n,'arch':vars(arch),'classes':r['classes'].tolist(),'macs':arch.mode_macs(),'baseline_mac':int(r['baseline_mac']),'full_correct':int(full),'early_correct':int((r['pred_early']==r['y']).sum()),'light_correct':int((r['pred_light']==r['y']).sum()),'prediction_cache':provenance(a.cache/(key+'.npz'))}
        rows=[]
        for i in range(n):rows.append({'sample_id':i,'y':int(r['y'][i]),'margin':r['margin'][i],**{k:int(r[k][i]) for k in ['pred_early','pred_light','pred_full']},**{f'early_logit_{c}':float(r['early_logits'][i,c]) for c in range(arch.n_class)}})
        csvwrite(OUT/'provenance'/f'{key}_predictions.csv',rows)
        print(key,info['models'][key],flush=True)
    dump(OUT/'provenance'/'manifest.json',info)
if __name__=='__main__':main()
