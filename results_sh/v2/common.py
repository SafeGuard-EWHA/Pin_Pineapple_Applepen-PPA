"""Shared helpers. No RTL simulation, training, or source-file edits."""
from pathlib import Path
import json,csv,hashlib,sys,platform
import numpy as np
BASE_COMMIT='4990d117fcc571183000605a514ad5d9c7d5c98a'
SEEDS=[2026,2027,2028,2029,2030]
INFERENCE_SEED=2026
OUT=Path(__file__).resolve().parent
COLORS={'Score Margin':'#16845c','Max softmax':'#377eb8','Negative entropy':'#d58b00','Top-1 logit':'#a73f58'}
def dump(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    def cv(x):
        if isinstance(x,np.ndarray):return x.tolist()
        if isinstance(x,np.generic):return x.item()
        if isinstance(x,Path):return str(x)
        raise TypeError(type(x))
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=cv,allow_nan=False)+'\n',encoding='utf8')
def csvwrite(path,rows):
    rows=list(rows);path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def provenance(path):
    b=Path(path).read_bytes()
    return {'sha256':hashlib.sha256(b).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),'bytes':len(b)}
def plotsetup():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    assert 'Malgun Gothic' in {f.name for f in font_manager.fontManager.ttflist},'Malgun Gothic missing'
    plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'svg.fonttype':'path','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.facecolor':'white'})
    return plt
def savefig(fig,folder,name):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    fig.savefig(folder/(name+'.png'),dpi=300,bbox_inches='tight',facecolor='white')
    fig.savefig(folder/(name+'.svg'),bbox_inches='tight',facecolor='white')
def load_cache(folder):
    return {k:{n:d[n] for n in d.files} for k in ['mnist_A','mnist_B','wm811k_B'] for d in [np.load(Path(folder)/(k+'.npz'))]}
def route(d,lo,hi,idx=None,score=None):
    if idx is None:idx=np.arange(len(d['y']))
    s=d['margin'][idx] if score is None else score[idx]
    modes=np.where(s>=hi,0,np.where(s<lo,2,1))
    preds=np.stack([d['pred_early'],d['pred_light'],d['pred_full']],1)[idx,modes]
    return preds,modes
def summarize(d,lo,hi,idx=None,score=None):
    if idx is None:idx=np.arange(len(d['y']))
    pred,mode=route(d,lo,hi,idx,score);n=len(idx);mac=float(np.mean(d['macs'][mode]));full=int(np.sum(d['pred_full'][idx]==d['y'][idx]));correct=int(np.sum(pred==d['y'][idx]));counts=np.bincount(mode,minlength=3)
    return {'t_low':float(lo),'t_high':float(hi),'n':n,'correct':correct,'full_correct':full,'accuracy_pct':100*correct/n,'full_accuracy_pct':100*full/n,'delta_pp':100*(correct-full)/n,'avg_mac':mac,'mac_saving_hard_pct':100*(1-mac/d['macs'][2]),'mac_saving_baseline_pct':100*(1-mac/float(d['baseline_mac'])),'easy_n':int(counts[0]),'medium_n':int(counts[1]),'hard_n':int(counts[2]),'easy_pct':100*counts[0]/n,'medium_pct':100*counts[1]/n,'hard_pct':100*counts[2]/n}
def boundary(d,idx,score=None):
    s=d['margin'][idx] if score is None else score[idx]
    order=np.argsort(s,kind='stable'); vals=s[order].astype('float64'); unique,starts=np.unique(vals,return_index=True)
    bounds=np.r_[starts,len(vals)]
    thresholds=np.r_[unique,np.nextafter(unique[-1],np.inf)]
    y=d['y'][idx][order]
    pref=[np.r_[0,np.cumsum(d[p][idx][order]==y)][bounds] for p in ['pred_early','pred_light','pred_full']]
    return thresholds,bounds,pref
def pick(d,idx,two=False,method='exact',score=None):
    """Exact optimum over all achievable tied-score boundaries, or original 25 quantiles.
    For each upper boundary j, minimal feasible lower i minimizes MAC:
    correct = (F_i-L_i)+(L_j-E_j)+E_N, cost monotone in i.
    Prefix-max search finds that smallest i without enumerating O(N^2) pairs.
    Tie break: MAC, -correct, low, high.
    """
    n=len(idx);full=int(np.sum(d['pred_full'][idx]==d['y'][idx]));target=full-int(np.floor(.005*n+1e-10));mm=d['macs']
    if method=='legacy_grid25':
        s=d['margin'][idx] if score is None else score[idx];th=np.quantile(s,np.linspace(.02,.98,25));rows=[]
        for i,lo in enumerate(th):
            for hi in ([lo] if two else th[i:]):
                q=summarize(d,lo,hi,idx,score)
                if q['correct']>=target:rows.append(q)
        if not rows:
            # Explicit fallback absent from old script; never silently omit failed folds.
            hi=np.nextafter(float(np.max(s)),np.inf);q=summarize(d,hi,hi,idx,score);q['fallback_all_hard']=True;return q
        return min(rows,key=lambda q:q['avg_mac']) # Original script: first point among MAC ties.
    th,k,(ce,cl,cf)=boundary(d,idx,score);j=np.arange(len(k))
    if two:i=j
    else:i=np.searchsorted(np.maximum.accumulate(cf-cl),target-(cl-ce+ce[-1]),side='left')
    valid=i<=j; i=i[valid];j=j[valid]
    c=cf[i]+cl[j]-cl[i]+ce[-1]-ce[j]
    cost=mm[0]*n+(mm[2]-mm[1])*k[i]+(mm[1]-mm[0])*k[j]
    ok=c>=target;i=i[ok];j=j[ok];cost=cost[ok];c=c[ok]
    best=np.lexsort((th[j],th[i],-c,cost))[0]
    q=summarize(d,th[i[best]],th[j[best]],idx,score)
    assert q['correct']==c[best] and abs(q['avg_mac']-cost[best]/n)<1e-8
    return q
def table(rows,cols):
    out=['| '+' | '.join(h for k,h in cols)+' |','|'+'|'.join('---' for _ in cols)+'|']
    for r in rows:
        out.append('| '+' | '.join(f'{r[k]:.4f}' if isinstance(r[k],(float,np.floating)) else str(r.get(k,'')) for k,h in cols)+' |')
    return '\n'.join(out)
