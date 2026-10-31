"""Recheck committed evidence and report files without running any experiment.

Run from the repository root with python results_hs/final_submission_review/validate.py.
"""
from pathlib import Path
from io import BytesIO
import csv, hashlib, json, math, re, statistics, subprocess, zipfile
from docx import Document
from docx.oxml.ns import qn
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
def load(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
def rows(p): return list(csv.DictReader((ROOT/p).open(encoding='utf-8-sig')))
def compact(s): return re.sub(r'\s+', '', s)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

d=Document(ROOT/'report/결과보고서_PPA.docx')
text='\n'.join([p.text for p in d.paragraphs]+[c.text for t in d.tables for r in t.rows for c in r.cells])
pdf=PdfReader(ROOT/'report/결과보고서_PPA.pdf')
pdftext='\n'.join(p.extract_text() for p in pdf.pages)
assert len(pdf.pages)==43
assert len(d.tables)==32 and len(d.inline_shapes)==32
for body in [text,pdftext]:
    assert not re.search(r'@\w+@|%%|%\(\w+\)s|\^\^|\*\*|·',body)
    assert '수상작' not in body
    assert [int(x) for x in re.findall(r'\[그림\s*(\d+)\]',body)]==list(range(1,33))
    assert [int(x) for x in re.findall(r'\[표\s*(\d+)\]',body)]==list(range(1,33))
    for term in ['정확도 동등성이나 비열등성의 증명이 아니다', '실제로 검사한 조건에서 위반은 0건',
                 'A 2,096 cycle, WM 221 cycle', '완료 여부를 평가하지 못하였다',
                 '두 에너지 감소율은 비교 기준이 달라 합산하지 않는다', '5개 시드의 부분 실행 합계',
                 '1,006/1,006', '9개 구간 평균의 표준편차', '개별 이미지의 편차가 아니다',
                 'WM 자체의 전력 평가는 미완료', '81.13', '8.1 %p', '22.50 nJ에서 16.68 nJ']:
        assert compact(term) in compact(body),term
assert '목차를 갱신하십시오' not in pdftext
assert all(t.rows[0]._tr.trPr.find(qn('w:tblHeader')) is not None for t in d.tables)
assert all(r._tr.trPr.find(qn('w:cantSplit')) is not None for t in d.tables for r in t.rows)
source=(ROOT/'report/make_final_report.py').read_bytes()
assert b'\n' not in source.replace(b'\r\n',b'')

# This final edit changes interpretation only; preserve every table and image.
oldbytes=subprocess.check_output(['git','show','51e13a8:report/결과보고서_PPA.docx'],cwd=ROOT)
old=Document(BytesIO(oldbytes))
def tabletexts(doc): return [[[c.text for c in r.cells] for r in t.rows] for t in doc.tables]
assert tabletexts(old)==tabletexts(d)
def media(data):
    with zipfile.ZipFile(data) as z:
        return sorted(hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/'))
assert media(BytesIO(oldbytes))==media(ROOT/'report/결과보고서_PPA.docx')

R=load('report/results.json'); E=R['energy_nJ']; F=R['fmax_sweep']
e=.96*E['A_easy']+.04*E['A_hard']; c=.96*845+.04*1016
lat_ref=1334/F['refchip']['io20']['fmax_mhz']*1000
lat_a=c/F['adapath_A']['io20']['fmax_mhz']*1000
arithmetic={'average_cycles':c,'average_energy_nJ':e,
 'cycle_reduction_pct':(1-c/1334)*100,'energy_reduction_pct':(1-e/E['ref'])*100,
 'latency_reduction_pct':(1-lat_a/lat_ref)*100,
 'area_increase_pct':(R['area']['adapath_A']/R['area']['refchip']-1)*100,
 'energy_break_even_easy_pct':100*(E['A_hard']-E['ref'])/(E['A_hard']-E['A_easy'])}
assert math.isclose(c,851.84)
for k in ['cycle_reduction_pct','energy_reduction_pct','latency_reduction_pct','area_increase_pct']:
    assert f'{arithmetic[k]:.1f}%' in compact(text)

sweep=rows('rtl/sweep_A.csv')
assert len(sweep)==16
for r in sweep:
    easy,med,hard=(int(r[k]) for k in ('easy','med','hard'))
    assert easy+med+hard==1000 and med==0
    assert math.isclose(float(r['avg_cycles']),(845*easy+1016*hard)/1000,abs_tol=.0051)
assert next(r for r in sweep if r['TH']=='63')['correct']=='970'
robust=rows('rtl/robustness_A.csv')
for kind,level,correct,cycles in [('contrast',1,970,851.84),('contrast',.3,930,909.98),('gauss',100,749,906.56)]:
    r=next(x for x in robust if x['kind']==kind and float(x['level'])==level and x['design']=='ada')
    assert int(r['correct'])==correct and math.isclose(float(r['avg_cycles']),cycles)
assert next(x for x in robust if x['kind']=='gauss' and float(x['level'])==100 and x['design']=='base')['correct']=='830'

stats=rows('results_sh/v2/03_statistics/statistics.csv')
for r in stats:
    assert int(r['full_correct'])-int(r['ada_correct'])==int(r['b_full_correct_ada_wrong'])-int(r['c_full_wrong_ada_correct'])
    assert f"{float(r['ada_accuracy_pct']):.2f}%" in compact(text)
oof=rows('results_sh/v2/01_independence/summary.csv')
for r in oof:
    if r['method']=='exact' or r['model']=='mnist_A':
        assert compact(f"{float(r['accuracy_pct_mean']):.2f} ± {float(r['accuracy_pct_sd']):.2f}") in compact(text)

cg=load('results_hs/clock_gating_sample_expansion/power_results/summary.json')
for variant in ['ungated','gated']:
    a=[v['energy_nJ'] for v in cg['checks'] if v['name'].startswith(variant+'_easy_')]
    assert len(a)==9
    assert math.isclose(statistics.mean(a),cg['variants'][variant]['easy_nJ'])
    assert math.isclose(statistics.stdev(a),cg['variants'][variant]['easy_batch_sd_nJ'])
arithmetic['icg_easy_reduction_pct']=100*(1-cg['variants']['gated']['easy_nJ']/cg['variants']['ungated']['easy_nJ'])
assert math.isclose(arithmetic['icg_easy_reduction_pct'],cg['easy_reduction_percent'])

control=load('results_hs/assertions/summary.json')
for r in control.values():
    assert all(r[k]==0 for k in ['easy_errors','medium_errors','mux_errors','deadline_errors','unknown_controls'])
assert control['A']['active']==1 and control['A']['unknown_decisions']==1
wm=rows('results_hs/assertions/WM_transactions.csv')
assert len(wm)==954
assert [sum(int(x['mode'])==m for x in wm) for m in range(3)]==[404,167,383]
assert f"{statistics.mean(int(x['cycles']) for x in wm):.2f}cycle" in compact(text)

net=load('evidence/vivado_netlist/summary.json')
assert (net['total_outputs'],net['total_decision_match'],net['total_cycle_checked'],net['total_cycle_match'],net['total_cycle_excluded'])==(1007,1007,1006,1006,1)
assert all(r['final_accuracy_line'] is None and not r['mismatches'] for r in net['runs'])
for design in ['refchip','adapath_A']:
    pl=load(f'orfs/reports_postlayout/{design}_pl/5_1_grt.json')
    assert pl['globalroute__timing__drv__hold_violation_count']==0
    assert pl['globalroute__timing__setup__ws']>0

changes=subprocess.check_output(['git','diff','51e13a8','--name-only','--','rtl','vivado/submit','report/results.json'],cwd=ROOT,text=True)
assert not changes.strip()
evidence=['report/results.json','rtl/sweep_A.csv','rtl/robustness_A.csv',
 'results_sh/v2/03_statistics/statistics.csv','results_sh/v2/01_independence/summary.csv',
 'results_hs/clock_gating_sample_expansion/power_results/summary.json',
 'results_hs/assertions/summary.json','results_hs/assertions/WM_transactions.csv','evidence/vivado_netlist/summary.json']
result={'review_base':'51e13a8f1c401ed156233c2356e7ed43e78833cb','main_base':'433736bd3dbd45aac67d1560b668cf95fda59908',
 'new_simulations':False,'pages':len(pdf.pages),'figures':32,'tables':32,'all_existing_tables_and_images_preserved':True,
 'arithmetic':arithmetic,'evidence_sha256':{p:sha(ROOT/p) for p in evidence},
 'artifacts_sha256':{p:sha(ROOT/p) for p in ['report/make_final_report.py','report/결과보고서_PPA.docx','report/결과보고서_PPA.pdf']}}
(OUT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if not k.endswith('sha256')},ensure_ascii=False,indent=2))
