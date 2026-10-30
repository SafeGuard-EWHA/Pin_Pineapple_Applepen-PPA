"""Read-only checks of report artifacts and frozen evidence; no experiments run.

Run from the repository root: python results_sh/final_review/validate_report.py
Add --pdf after exporting the current DOCX to PDF.
"""
from pathlib import Path
import argparse, csv, hashlib, json, math, re
from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE_COMMIT = 'e4b7a3cfd5c89cd5d33b3a90cdf7c84a497b288a'
CONTROL_COMMIT = '7364903c0ec1f4352448bcc64ae6c9e193811a37'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf', action='store_true')
    args = ap.parse_args()
    p = ROOT / 'report/결과보고서_PPA.docx'
    d = Document(p)
    texts = [x.text for x in d.paragraphs]
    texts += [c.text for t in d.tables for row in t.rows for c in row.cells]
    text = '\n'.join(texts)
    assert not any(s in text for s in ('@', '%%', '%(', '^^', '**'))
    assert '수상작' not in text
    fnums = [int(x) for x in re.findall(r'\[그림 (\d+)\]', text)]
    tnums = [int(x) for x in re.findall(r'\[표 (\d+)\]', text)]
    assert fnums == list(range(1, len(d.inline_shapes) + 1)), fnums
    assert tnums == list(range(1, len(d.tables) + 1)), tnums
    assert all(t.rows[0]._tr.trPr.find(qn('w:tblHeader')) is not None for t in d.tables)
    assert all(row._tr.trPr.find(qn('w:cantSplit')) is not None for t in d.tables for row in t.rows)
    assert all(s._inline.docPr.get('descr') for s in d.inline_shapes)
    # Required interpretation and newly corrected passages must survive generation.
    for s in ('순 정확도 차이는 6장(0.06 %p)', '정상(none)의 83.3 %가 Hard',
              '자유주제 WM-811K에 그대로 적용할 수 없다', 'pre-layout', '대리 추정',
              '고유 100장', '주최 측 기준이 아니라', '비열등성의 증명이 아니며'):
        assert s in text, s
    R = json.loads((ROOT/'report/results.json').read_text(encoding='utf-8'))
    E = R['energy_nJ']; F = R['fmax_sweep']; M = R['mode_ratio']['A']
    ea = M['easy']*E['A_easy'] + M['hard']*E['A_hard']
    ca = M['easy']*R['cycles']['easy'] + M['hard']*R['cycles']['hard']
    lref = R['cycles']['ref']/F['refchip']['io20']['fmax_mhz']*1000
    la = ca/F['adapath_A']['io20']['fmax_mhz']*1000
    wm = R['wm']['mode']
    ew = sum(wm[k]*E[v] for k,v in [('easy','B_easy'),('med','B_med'),('hard','B_hard')])
    pbe = (E['A_hard']-E['ref'])/(E['A_hard']-E['A_easy'])
    numbers = dict(a_energy_nj=ea, a_cycles=ca, reference_latency_ns=lref, a_latency_ns=la,
                   energy_saving_pct=(1-ea/E['ref'])*100,
                   cycle_saving_pct=(1-ca/R['cycles']['ref'])*100,
                   latency_saving_pct=(1-la/lref)*100,
                   area_increase_pct=(R['area']['adapath_A']/R['area']['refchip']-1)*100,
                   easy_energy_breakeven_pct=pbe*100, wm_float_proxy_energy_nj=ew)
    for key in ('energy_saving_pct','cycle_saving_pct','latency_saving_pct','area_increase_pct'):
        assert f'{numbers[key]:.1f} %' in text, (key,numbers[key])
    assert math.isclose(sum(wm.values()),1)
    stats = list(csv.DictReader((ROOT/'results_sh/v2/03_statistics/statistics.csv').open(encoding='utf-8-sig')))
    for r in stats:
        assert int(r['full_correct'])-int(r['ada_correct']) == int(r['b_full_correct_ada_wrong'])-int(r['c_full_wrong_ada_correct'])
        assert f"{float(r['ada_accuracy_pct']):.2f} %" in text
    # Round-to-two-decimals accuracy and MAC values from committed OOF summaries.
    summaries = list(csv.DictReader((ROOT/'results_sh/v2/01_independence/summary.csv').open(encoding='utf-8-sig')))
    for r in summaries:
        if r['method']=='exact' or r['model']=='mnist_A':
            assert f"{float(r['accuracy_pct_mean']):.2f} ± {float(r['accuracy_pct_sd']):.2f}" in text
    # Vivado Windows paths include local-codepage bytes; checked tokens are ASCII.
    log = (ROOT/'evidence/vivado_logs/adapath_WM_tb_wm.log').read_text(encoding='utf-8', errors='replace')
    for token in ('774 / 954', '404 / 167 / 383', '954 / 954'):
        assert token in log, token
    control = json.loads((ROOT/'results_hs/assertions/summary.json').read_text(encoding='utf-8'))
    for model, q in control.items():
        assert all(q[k] == 0 for k in ('easy_errors','medium_errors','mux_errors','deadline_errors','unknown_controls'))
    assert control['A']['n_medium'] == 0 and control['A']['active'] == 1
    assert control['A']['unknown_decisions'] == 1
    assert control['WM']['n_medium'] == 167 and control['WM']['medium_checks'] == 27555
    transactions = list(csv.DictReader((ROOT/'results_hs/assertions/WM_transactions.csv').open(encoding='utf-8')))
    assert len(transactions) == 954
    assert [int(r['mode']) for r in transactions[:7]] == [2,2,1,1,2,1,0]
    assert all(int(r['cycles']) == (839 if r['mode']=='0' else 1004) for r in transactions)
    wm_observed_cycles = sum(int(r['cycles']) for r in transactions)/len(transactions)
    assert f'{wm_observed_cycles:.2f} cycle' in text
    assert '4-class WM RTL의 실측 cycle이 아니다' in text
    for token in ('0 / 해당 없음', '27,555 / 0', '1,001 / 0', '91,704 / 0',
                  '마지막 1회는 종료 시 미평가', 'A 2,096회, WM 221회', '28.605~30.255 µs',
                  '30.265~30.275 µs', 'ch_en = 0x0F', '형식 검증은 아니다'):
        assert token in text, token
    report = dict(source_commit=SOURCE_COMMIT, figures=len(fnums), tables=len(tnums),
                  control_evidence_commit=CONTROL_COMMIT, control_checks=control,
                  docx_checks_passed=True, arithmetic=numbers, experiments_rerun=False,
                  files={str(x.relative_to(ROOT)):sha(x) for x in [p,ROOT/'report/make_final_report.py',ROOT/'report/results.json']},
                  pdf_checked=False)
    if args.pdf:
        import pymupdf
        pp=ROOT/'report/결과보고서_PPA.pdf'; pdf=pymupdf.open(pp)
        pt='\n'.join(page.get_text() for page in pdf)
        compact=re.sub(r'\s+', '', pt)
        for s in ('순 정확도 차이는 6장(0.06 %p)', '자유주제 WM-811K에 그대로 적용할 수 없다',
                  '27,555 / 0', '마지막 1회는 종료 시 미평가', '30.265~30.275 µs'):
            assert re.sub(r'\s+','',s) in compact, 'PDF is stale or missing text: '+s
        assert not any(s in pt for s in ('@','%%','%(','^^','**'))
        assert '목차를 갱신하십시오' not in pt
        assert '3.11 추가 RTL 실험' in pdf[1].get_text(), 'TOC not updated'
        figure_pages = []
        outside = []
        for page_no, page in enumerate(pdf, 1):
            for n in re.findall(r'\[그림\s*(\d+)\]', page.get_text()):
                assert page.get_image_info(), ('Figure caption separated from image',n,page_no)
                figure_pages.append([int(n),page_no])
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines',[]):
                    for span in line.get('spans',[]):
                        x0,y0,x1,y1 = span['bbox']
                        if x0 < -1 or y0 < -1 or x1 > page.rect.width+1 or y1 > page.rect.height+1:
                            outside.append([page_no,span['text']])
        assert not outside, outside
        assert [x[0] for x in figure_pages] == list(range(1,len(fnums)+1))
        report.update(pdf_checked=True,pdf_pages=len(pdf),pdf_sha256=sha(pp),
                      pdf_toc_updated=True,figure_pages=figure_pages,outside_page_text=outside)
    OUT.mkdir(exist_ok=True)
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
