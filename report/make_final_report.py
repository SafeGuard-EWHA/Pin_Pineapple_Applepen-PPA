"""결과보고서(Word) 생성 - results.json 의 측정값으로 본문 수치를 채운다.

    python make_final_report.py            -> 결과보고서_PPA.docx
"""
import json
import os
import csv
from experiment_sections import load_results

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
R = json.load(open(os.path.join(HERE, "results.json"), encoding="utf-8"))
CONTROL = json.load(open(os.path.join(HERE, '..', 'results_hs', 'assertions', 'summary.json'), encoding='utf-8'))
WM_TRANSACTIONS = list(csv.DictReader(open(os.path.join(HERE, '..', 'results_hs', 'assertions', 'WM_transactions.csv'), encoding='utf-8')))
WM_OBS_AVG_CYC = sum(int(r['cycles']) for r in WM_TRANSACTIONS) / len(WM_TRANSACTIONS)

SWEEP, ROBUST, LEVELS = load_results(os.path.dirname(HERE))
TB_CHECK = json.load(open(os.path.join(HERE, '..', 'results_hs', 'corrected_tb', 'validation.json'), encoding='utf-8'))
TB_RUNS = {r['case']: r for r in TB_CHECK['runs']}
NETSIM = json.load(open(os.path.join(HERE, '..', 'evidence', 'vivado_netlist', 'summary.json'), encoding='utf-8'))
NETRUN = {r['key']: r for r in NETSIM['runs']}
import re as _re0
def _seq_area(path):
    t = open(os.path.join(HERE, '..', path), encoding='utf-8').read()
    return float(_re0.search(r'used for sequential elements: ([0-9.]+)', t).group(1))
SEQ_AREA = {"refchip": _seq_area('orfs/reports_postlayout/refchip_pl/synth_stat.txt'),
            "baseline_A": _seq_area('orfs/reports_final/baseline_A_synth_stat.txt'),
            "adapath_A": _seq_area('orfs/reports_final/adapath_A_synth_stat.txt')}
assert TB_CHECK['protected_hashes_unchanged'] and TB_CHECK['random_vs_sequential_same_index_matches'] == 1000
for _run in TB_RUNS.values():
    assert _run['observer'] == {'outputs':1000,'x_outputs':0,'invalid_reads':0,'unknown_reads':0,'reads':784000}


FONT = "맑은 고딕"
fig_no = [0]
tab_no = [0]

# ---- 그림 및 표 번호: 이 파일의 figure()/table() 호출 순서로 미리 계산하여 본문 참조(@키@, %(키)s)에 사용
import re as _re
_SRC = open(os.path.abspath(__file__), encoding="utf-8").read()
FIGN = {n: i + 1 for i, n in enumerate(_re.findall(r'figure\(doc, os\.path\.join\(OUT, (?:"archA", )?"([^"]+)"', _SRC))}
_TABS = _re.findall(r'\btable\(doc, "([^"]+)"', _SRC)


def _tn(prefix):
    return [i + 1 for i, t in enumerate(_TABS) if t.startswith(prefix)][0]


LBL = {
    "f_flow": FIGN["fig_flow.png"], "f_top2": FIGN["fig_top2.png"], "f_metrics": FIGN["sh2_fig_metric_comparison.png"],
    "f_twofold": FIGN["sh2_fig_twofold.png"], "f_wrapper": FIGN["fig_wrapper.png"], "f_sweep": FIGN["hs_fig_sweep_A.png"],
    "f_block": FIGN["fig_block_energy.png"], "f_breakeven": FIGN["fig_energy_breakeven.png"],
    "f_wmclass": FIGN["sh2_fig_wm_class_modes.png"], "f_rmodes": FIGN["hs_fig_robustness_modes.png"],
    "f_racc": FIGN["hs_fig_robustness_acc.png"], "f_wm_medium": FIGN["fig_vivado_wm_medium.png"], "f_pareto": FIGN["hs_fig_pareto.png"],
    "f_wmpaths": FIGN["fig_vivado_wm_paths.png"],
    "t_icg": _tn("전용 ICG 적용 전후"), "t_pl": _tn("배치 및 전역 배선 후 비교"), "t_area": _tn("면적 구성과 단계별 증가분"), "t_control": _tn("제어 조건의 동적 검사"), "t_netsim": _tn("합성 넷리스트의 Vivado 기능 검증"),
    "t_wmppa": _tn("WM-811K 적용 전후 비교"), "t_wmpaired": _tn("WM 동일 입력의 구간별 전력 및 에너지"),
    "t_map": _tn("비교 설계 대응표"), "t_train": _tn("학습 설정"), "t_acc": _tn("모델별 정확도"),
    "t_twofold": _tn("임계값 선정 및 평가 분리"), "t_stats": _tn("기존 동작점의 AdaPath vs Full"),
    "t_wmclass": _tn("WM-811K 클래스별"), "t_wmrtl": _tn("WM-811K RTL 검증 결과"), "t_verify": _tn("기능 검증 결과"),
}


def lbl(text):
    """본문의 @키@ 를 그림 및 표 번호로 치환."""
    return _re.sub(r"@(\w+)@", lambda m: str(LBL[m.group(1)]), text)


# 문단별 핵심 문장 및 어구: 본문에서 처음 나오는 곳을 굵게+밑줄로 표시한다(렌더링된 문장과 정확히 일치해야 함)
EMPH = [
    "Easy 이미지당 에너지가 22.50 nJ에서 16.68 nJ로 평균 25.9 % 감소하였다",
    # 요약
    "정답 수를 970회로 유지하면서 평균 처리 cycle(36.1 % 감소)과 추정 Fmax 기준 추론 지연(33.0 % 감소)을 함께 줄였다",
    "MAC 감소가 그대로 에너지 감소로 이어지지 않는 원인(후단부 레지스터의 유휴 소모)을 정량화하였다",
    "954장 전부에서 정수 Golden과 판정, 모드, Score Margin이 비트 단위로 일치함(954 / 954)",
    # 1장
    "이들에게 전체 경로를 적용하는 것은 연산, 시간, 에너지의 낭비이다",
    "비교기와 감산기만으로 계산되는 Score Margin을 사용하며",
    "가중치를 입력 포트로 두어 상수 전파 효과를 배제하였다",
    "처리 cycle 증가 없이 판단 회로의 조합 경로를 단축하였다",
    "Reference 대비 전체 구현의 변화와 팀 내부의 적응형 경로 적용 전후를 구분하였다",
    # 2장
    "연산량(MAC) 감소가 아니라 게이트레벨 스위칭 기반의 추론당 에너지로 평가한다",
    # 3.1 ~ 3.4
    "Easy 입력은 Early 점수로 결과를 출력하므로 Conv2와 Light/Full FC의 추론 연산을 생략한다",
    "RTL 시뮬레이션에서는 X 비교의 if/else 처리에 따라 Hard로 진행할 수 있으나",
    "출력 레지스터는 1단 그대로이므로 처리 cycle은 변하지 않는다",
    "Score Margin은 비선형 연산 없이 유리한 정확도–연산량 절충을 보인 지표로 해석한다",
    "'Full 경로 대비 정확도 손실 0.5 %p 이내에서 평균 MAC 최소'인 동작점을 선택하였다",
    "모델 A는 Easy/Hard 두 경로로 동작한다",
    "선정 데이터에서 지킨 정확도 제약이 미사용 데이터에서 보장되지는 않으며",
    "McNemar exact p = 0.63",
    "단일 소스(adapath_top.v)로 작성하였다",
    "주최 측 top_tb.v는 테스트벤치 로직을 수정하지 않았으며",
    # 3.5
    "'Accuracy : 96%'가 출력되었다",
    "Feature Map Buffer 재생, Conv2 채널 enable, Full FC가 활성화되지 않는다",
    "Hard 이미지 1장의 추가 처리 시간은 Easy 대비 171 cycle이다",
    "제출용 모델 A는 TL=TH=63의 고정 임계값을 사용한다",
    "C = 845(1−p_H) + 1016p_H = 845 + 171p_H",
    # 3.6 ~ 3.8
    "클럭 주기를 1.0~2.4 ns로 스윕하여 최악 slack이 0이 되는 주기",
    "판단 회로에 의한 뚜렷한 주파수 저하가 관측되지 않았다",
    "AdaPath_A 통합 합성 면적의 0.65 %에 해당한다",
    "스위칭 파형(VCD)을 추출하고, OpenSTA(read_vcd)로 평균 전력을 계산하였다",
    "최종적으로 Reference 대비 8.9 %의 에너지 감소를 얻었다",
    "면적을 추가로 사용하여 추론 지연과 에너지를 줄인 동작점으로 해석한다",
    "연산 생략 효과는 조합 논리에서 뚜렷하다",
    "Easy에서도 Conv2, Pool2, FC의 레지스터는 연산 없이 클럭만 공급받으며",
    "Easy에서 5.24 nJ(33 %)로 가장 큰 단일 블록이다",
    "클럭 게이팅의 직접적인 대상이다",
    "Top-2 Finder를 포함한 판단 회로는 임계 경로가 아니었다",
    "Easy 4장 구간의 이미지당 에너지는 25.9 %, Easy 3장과 Hard 1장의 혼합 구간은 25.2 %, Hard 4장 구간은 20.7 % 줄었다",
    "처리 cycle이나 MAC 감소만으로 에너지 이득을 보장할 수 없음을 정량적으로 보여준다",
    "Medium이 없는 Early-Exit(2경로)와 AdaPath(3경로)를 임계값 전수 탐색으로 비교하였다",
    "9개 사례 모두 margin, mode, decision이 정수 Golden과 일치하였다",
    # 3.9 ~ 3.11
    "모델 B 구조(4개 클래스 출력)에 같은 AdaPath 기법을 적용하였으며",
    "판정, 모드, Score Margin이 정수 Golden과 954장 모두 비트 단위로 일치하였고",
    "계산 배분은 패턴의 물리적 복잡성보다 현재 전단 분류기의 구분 능력을 따르며",
    "recall이 Full 63.6 %에서 AdaPath 60.5 %로 3.1 %p 낮아졌다",
    "입력이 어려워질 때 AdaPath가 실제로 후단 연산을 더 많이 사용하는지 확인하기 위해",
    "Hard 비율이 4 %에서 72 %로 늘어",
    "강한 가우시안 잡음(σ = 100, 74.9 % vs 83.0 %)에서는 AdaPath의 정확도가 낮았다",
    "큰 Score Margin은 확률로 보정된 신뢰도가 아니므로",
    # 4장
    "Baseline_A보다 최대 8.1 %p 낮았다",
    "SRAM 매크로로 바꾸거나",
    "Reference 대비 평균 에너지 감소가 추정되었다",
    "명확한 패턴은 조기 종료하고 애매한 패턴만 정밀 경로로 보내는 계층적 검사",
    "MNIST 및 WM-811K 4-class 모델에 적용하였다",
]
EMPH_HIT = set()


# ----------------------------------------------------------------- helpers
def set_font(run, size=10.5, bold=False, color=None):
    run.font.name = FONT
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def para(doc, text="", size=10.5, bold=False, align=None, space_after=4, indent=False):
    p = doc.add_paragraph()
    if align == "c":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align != "l":
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.25
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.35)
    add_runs(p, text, size, bold)
    return p


def add_runs(p, text, size, bold=False):
    """**굵게**, ^^굵게+밑줄^^ 표기를 런으로 나눈다. EMPH의 핵심 어구는 자동으로 굵게+밑줄 처리한다."""
    text = lbl(text)
    for k in EMPH:
        if k in text and "^^" + k not in text:
            text = text.replace(k, "^^" + k + "^^", 1)
            EMPH_HIT.add(k)
    b = u = False
    for t in _re.split(r"(\*\*|\^\^)", text):
        if t == "**":
            b = not b
        elif t == "^^":
            u = not u
        elif t:
            r = p.add_run(t)
            set_font(r, size, bold or b or u)
            r.underline = u


def heading(doc, text, level):
    # Word 기본 Heading 스타일을 써서 탐색 창 및 목차에 잡히게 하고, 모양만 본문 서체로 맞춘다
    p = doc.add_paragraph(style="Heading %d" % level)
    p.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    p.paragraph_format.space_after = Pt(6 if level == 1 else 4)
    p.paragraph_format.keep_with_next = True
    set_font(p.add_run(text), {1: 14, 2: 12}.get(level, 11), True, (0, 0, 0))
    return p


def h1(doc, text):
    heading(doc, text, 1)


def h2(doc, text):
    heading(doc, text, 2)


def h3(doc, text):
    heading(doc, text, 3)


def bullet(doc, text, size=10.5):
    p = para(doc, "", size)
    p.paragraph_format.left_indent = Cm(0.5)
    p.paragraph_format.first_line_indent = Cm(-0.35)
    p.paragraph_format.space_after = Pt(2)
    add_runs(p, "• " + text, size)
    return p


def shade(cell, hexcolor):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def row_props(row, header=False):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))
    if header:
        trPr.append(OxmlElement("w:tblHeader"))


def caption(doc, kind, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.keep_together = True
    set_font(p.add_run("[%s] %s" % (kind, text)), 9.5, True)


def table(doc, title, headers, rows, widths=None, hl_rows=(), size=9, note=None):
    tab_no[0] += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    set_font(p.add_run("[표 %d] %s" % (tab_no[0], title)), 9.5, True)
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        c = t.rows[0].cells[j]
        c.text = ""
        set_font(c.paragraphs[0].add_run(str(h)), size, True)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].paragraph_format.keep_with_next = True
        shade(c, "D9E2F3")
    row_props(t.rows[0], header=True)
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            c = t.rows[i + 1].cells[j]
            c.text = ""
            txt = str(v)
            bold = txt.startswith("**") and txt.endswith("**")
            set_font(c.paragraphs[0].add_run(txt.strip("*")), size, bold)
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER if j else WD_ALIGN_PARAGRAPH.LEFT
            if i in hl_rows:
                shade(c, "FFF2CC")
        row_props(t.rows[i + 1])
    if widths:
        for row in t.rows:
            for j, w in enumerate(widths):
                row.cells[j].width = Cm(w)
    # 짧은 표는 한 페이지에 유지하고, 긴 표는 머리글을 반복하여 나눈다.
    if len(rows) <= 9 or title.startswith(('모델 A 임계값 스윕 전체', '모드별 추론당 에너지')):
        for row in t.rows[:-1]:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.keep_with_next = True
    if note:
        for cell in t.rows[-1].cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.keep_with_next = True
        q = para(doc, note, 8.5, space_after=6)
        q.alignment = WD_ALIGN_PARAGRAPH.LEFT
        q.paragraph_format.keep_together = True
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(doc, path, text, width=15.0):
    # Use committed source figures instead of untracked copied aliases.
    sources = {
        'sh2_fig_metric_comparison.png': 'results_sh/v2/02_metrics/fig_metric_comparison.png',
        'sh2_fig_twofold.png': 'results_sh/v2/01_independence/fig_twofold.png',
        'sh2_fig_wm_class_modes.png': 'results_sh/v2/04_wm_classes/fig_wm_class_modes.png',
        'sh2_fig_wm_confusion.png': 'results_sh/v2/04_wm_classes/fig_wm_confusion.png',
        'sh2_fig_error_examples.png': 'results_sh/v2/05_error_analysis/fig_error_examples.png',
        'hs_fig_sweep_A.png': 'out/fig_sweep_A.png',
        'hs_fig_robustness_modes.png': 'out/fig_robustness_modes.png',
        'hs_fig_robustness_acc.png': 'out/fig_robustness_acc.png',
        'sh2_fig_accuracy_ci.png': 'results_sh/v2/03_statistics/fig_accuracy_ci.png',
        'hs_fig_icg_energy.png': 'results_hs/clock_gating/power_results/energy_comparison.png',
        'hs_fig_pareto.png': 'results_hs/accuracy_energy_pareto/accuracy_energy_pareto.png',
    }
    if os.path.basename(path) in sources:
        path = os.path.join(HERE, '..', sources[os.path.basename(path)])
    fig_no[0] += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    pic = p.add_run().add_picture(path, width=Cm(width))
    pic._inline.docPr.set("descr", text)            # 대체 텍스트
    pic._inline.docPr.set("name", "그림 %d" % fig_no[0])
    caption(doc, "그림 %d" % fig_no[0], text)


def f0(x):
    return "{:,.0f}".format(x)


def f1(x):
    return "{:,.1f}".format(x)


def f2(x):
    return "{:,.2f}".format(x)


def pct(new, old):
    return (new / old - 1) * 100


def chg(new, old):
    """감소/증가를 말로 쓰는 변화율 (부호와 '감소'를 중복하지 않음)."""
    v = pct(new, old)
    return "%.1f %% %s" % (abs(v), "감소" if v < 0 else "증가")


# ----------------------------------------------------------------- 값 준비
A, D = R["area"], R["crit"]
SW = R["fmax_sweep"]          # 클럭 주기 스윕으로 구한 통과 주기 (slack = 0 교차점)
PER = {k: SW[k]["io20"]["period_ps"] for k in SW}
FMAX = {k: SW[k]["io20"]["fmax_mhz"] for k in SW}           # 원 SDC 규칙 (입출력 지연 = 주기의 20 %)
FMAX_S = {k: SW[k]["static_w"]["fmax_mhz"] for k in SW}     # 가중치 포트 정적 (false path)
BE = R["block_energy_nJ"]
E = R["energy_nJ"]
MAC = R["mac"]
ACC = R["acc"]
CYC = R["cycles"]
MODE = R["mode_ratio"]


def avg(dct, ratio):
    return sum(ratio[k] * dct[k] for k in ratio)


E_A = avg({"easy": E["A_easy"], "hard": E["A_hard"]}, MODE["A"])
E_B = avg({"easy": E["B_easy"], "med": E["B_med"], "hard": E["B_hard"]}, MODE["B"])
E_REF = E["ref"]
E_ABASE = E["Abase"]
MAC_A = avg({"easy": MAC["A_easy"], "hard": MAC["A_hard"]}, MODE["A"])
CYC_A = avg({"easy": CYC["easy"], "hard": CYC["hard"]}, MODE["A"])
CYC_B = avg({"easy": CYC["easy"], "med": CYC["hard"], "hard": CYC["hard"]}, MODE["B"])


def topsw(mac, e_nj):
    return 2 * mac / (e_nj * 1e-9) / 1e12


LAT = {  # ns / 추론, 각 설계의 pre-layout 추정 Fmax 기준
    "ref": CYC["ref"] / FMAX["refchip"] * 1e3,
    "A": CYC_A / FMAX["adapath_A"] * 1e3,
}

# 배치 및 전역 배선 후 결과 (orfs/reports_postlayout, 2,000 ps 제약, 레지스터 간 임계 경로 -> 최소 주기 = 2,000 - slack)
PL = {"refchip": {"area": 32330.1, "slack": 259.86, "skew": 40.37},
      "adapath_A": {"area": 50614.2, "slack": 37.59, "skew": 55.13}}
for _v in PL.values():
    _v["fmax"] = 1e6 / (2000 - _v["slack"])
PL_LAT = {"ref": CYC["ref"] / PL["refchip"]["fmax"] * 1e3, "A": CYC_A / PL["adapath_A"]["fmax"] * 1e3}

# 손익분기 (모드별 에너지 고정 혼합 모델)
P_BE_REF = (E["A_hard"] - E_REF) / (E["A_hard"] - E["A_easy"])
P_BE_BASE = (E["A_hard"] - E_ABASE) / (E["A_hard"] - E["A_easy"])
P_BE_CYC = (CYC["hard"] - CYC["base"]) / (CYC["hard"] - CYC["easy"])

# WM-811K: 10-class AdaPath_B 의 모드별 에너지를 WM 모드 비율로 가중한 대리 추정
WM = R["wm"]
E_WM_BASE = E["B_hard"]
E_WM = avg({"easy": E["B_easy"], "med": E["B_med"], "hard": E["B_hard"]}, WM["mode"])
# WM 동일 입력 비교: 모드별 동일4장을 두 설계에 적용하고 양쪽에 동일 RTL 모드 비율을 가중.
WMP = json.load(open(os.path.join(HERE, "..", "results_hs", "wm_paired_power", "summary.json"), encoding="utf-8"))
assert WMP["validation"] == "PASS" and WMP["unique_selected_pixel_contents"] == 12
E_WM_D = float(WMP["rtl_mode_weighted_estimate"]["adapath_energy_nJ"])
E_WM_BASE_D = float(WMP["rtl_mode_weighted_estimate"]["baseline_energy_nJ"])
WM_PAIRED_ROWS = []
for _g, _name in (("easy", "Easy"), ("med", "Medium"), ("hard", "Hard")):
    _a, _b = WMP["per_run"]["ada_" + _g], WMP["per_run"]["base_" + _g]
    WM_PAIRED_ROWS.append([_name + " (4장)", "%.3f" % float(_b["power_mW"]),
                          "%.3f" % float(_a["power_mW"]), "%.2f" % float(_b["energy_nJ_per_image"]),
                          "%.2f" % float(_a["energy_nJ_per_image"]),
                          "%.2f %%" % float(WMP["pairs"][_g]["energy_reduction_pct"])])
rg = R["region2"]
region2_ratio = rg["area_v2"] / A["adapath_A"] * 100


# ----------------------------------------------------------------- 문서
doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
sec.left_margin = sec.right_margin = Cm(2.0)
sec.top_margin = sec.bottom_margin = Cm(2.0)
st = doc.styles["Normal"]
st.font.name = FONT
st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
for toc_name in ('TOC 1', 'TOC 2'):
    if toc_name not in doc.styles:
        doc.styles.add_style(toc_name, 1, builtin=True)
    toc_style = doc.styles[toc_name]
    toc_style.font.name = FONT
    toc_style._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), FONT)
    toc_style.font.size = Pt(10)
    toc_style.paragraph_format.space_before = Pt(0)
    toc_style.paragraph_format.space_after = Pt(3)
    toc_style.paragraph_format.line_spacing = 1.0
    toc_style.paragraph_format.keep_with_next = False
    toc_style.paragraph_format.keep_together = True

# ---- 표지 ----
for _ in range(5):
    doc.add_paragraph()
para(doc, "결 과 보 고 서", 26, True, "c", 30)
para(doc, "과제명: 반도체 결함 패턴 분류를 위한 Score Margin 기반", 14, False, "c", 2)
para(doc, "난이도 적응형 Tiny NPU Datapath 설계", 14, False, "c", 2)
para(doc, "— OpenROAD(ORFS) 기반 ASAP7 7 nm PPA 비교 분석", 12, False, "c", 60)
para(doc, "팀    명: Pin_Pineapple_Applepen(PPA)", 13, False, "c", 2)
para(doc, "이화여자대학교 전자전기공학과  윤현서, 최서현, 윤홍은", 11, False, "c", 2)
para(doc, "지도교수: 최종윤", 11, False, "c", 120)
para(doc, "경북대학교 IDEC 2026 창의 회로설계 챌린지", 15, True, "c", 0)
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

para(doc, "목차", 18, True, space_after=12)
toc = doc.add_paragraph()
# TOC는 복합 필드로 만들어 Word와 LibreOffice에서 모두 인식되게 한다.
begin = OxmlElement('w:fldChar'); begin.set(qn('w:fldCharType'), 'begin')
begin.set(qn('w:dirty'), 'true')
instruction = OxmlElement('w:instrText')
instruction.set(qn('xml:space'), 'preserve')
instruction.text = ' TOC \\o "1-2" \\h \\z \\u '
separate = OxmlElement('w:fldChar'); separate.set(qn('w:fldCharType'), 'separate')
end = OxmlElement('w:fldChar'); end.set(qn('w:fldCharType'), 'end')
toc.add_run()._r.append(begin)
toc.add_run()._r.append(instruction)
toc.add_run()._r.append(separate)
toc.add_run('목차를 갱신하십시오.')
toc.add_run()._r.append(end)
doc.add_page_break()
sec.different_first_page_header_footer = True
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
for instruction, suffix in [('PAGE', ' / '), ('NUMPAGES', '')]:
    field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), instruction)
    footer._p.append(field)
    if suffix: footer.add_run(suffix)

# ---- 요약 ----
_EZ0 = BE["AdaPath_A Easy"]
_IDLE0 = sum(_EZ0.get(b, 0) for b in ("Conv2", "Pool2", "FC (Full)", "Light FC"))
_E_CG0 = MODE["A"]["easy"] * (E["A_easy"] - _IDLE0) + MODE["A"]["hard"] * E["A_hard"]
h1(doc, "요약")
para(doc, "본 과제는 입력마다 Early Classifier 점수의 Top-1과 Top-2 차이(Score Margin)를 비교기와 감산기만으로 계산하여 "
     "Easy / Medium / Hard 경로를 선택하는 난이도 적응형 NPU Datapath(AdaPath-NPU)를 설계하였다. 지정주제(MNIST)에서는 "
     "주최 측 Reference와 같은 주 경로 신경망(모델 A)을 사용하여, 주최 입력 순차 1,000회 기준 정답 수를 970회로 유지하면서 "
     "평균 처리 cycle(%s)과 추정 Fmax 기준 추론 지연(%s)을 함께 줄였다. ASAP7 pre-layout 게이트레벨 VCD 기반 추론당 에너지는 "
     "%s이며, 면적은 Feature Map Buffer와 Early Classifier 추가로 %s이다. Top-2 Finder를 토너먼트 트리로 변경한 후, "
     "합성 직후 추정 Fmax는 판단 회로가 없는 Baseline_A와 거의 같았다(AdaPath_A %.1f MHz, Baseline_A %.1f MHz). 다만 "
     "Reference의 %.1f MHz보다는 낮았다. 배치와 전역 배선까지 수행한 결과에서는 FSM enable "
     "신호의 배선 지연으로 Fmax 차이가 다시 커졌지만, 추론 지연은 여전히 Reference보다 %.1f %% 짧았다. 또한 블록별 에너지 분해로 MAC 감소가 그대로 에너지 감소로 이어지지 않는 "
     "원인(후단부 레지스터의 유휴 소모)을 정량화하였다. 후단부 클럭 게이팅을 적용하면 추론당 에너지는 상한 추정으로 "
     "Reference 대비 %s에 이르며, 전용 ICG 셀을 실제로 넣은 설계의 배치 전 평가에서도 선정 구간의 에너지가 게이팅 전보다 "
     "20.7~25.9 %% 줄었다." % (chg(CYC_A, CYC["ref"]), chg(LAT["A"], LAT["ref"]), chg(E_A, E_REF),
                              chg(A["adapath_A"], A["refchip"]), FMAX["adapath_A"], FMAX["baseline_A"], FMAX["refchip"],
                              -pct(PL_LAT["A"], PL_LAT["ref"]), chg(_E_CG0, E_REF)), indent=True)
para(doc, "자유주제(WM-811K 웨이퍼맵 4-class)에서는 같은 기법을 3-경로 모델에 적용하여, 주최 측 chip 인터페이스를 유지한 RTL이 "
     "954장 전부에서 정수 Golden과 판정, 모드, Score Margin이 비트 단위로 일치함(954 / 954)을 Vivado로 확인하였고, Easy / Medium / "
     "Hard 세 경로가 모두 사용됨(404 / 167 / 383장)을 보였다. 아울러 2-fold 교차 평가, 정확도 차이의 통계 검정, 입력 열화 실험을 "
     "통해 적응형 경로의 이득이 성립하는 조건과 한계를 함께 제시하였다.", indent=True)
para(doc, "**핵심어:** Early-Exit, Score Margin, 적응형 추론, NPU, ASAP7, OpenROAD, 게이트레벨 전력, WM-811K", indent=True)
doc.add_page_break()

# =================================================================== 1
h1(doc, "1. 과제 개요")
para(doc, "고정 경로 CNN 가속기는 입력 난이도와 관계없이 모든 입력에 동일한 연산 경로를 수행한다. 그러나 실제 입력의 "
     "상당수는 얕은 특징만으로도 분류가 가능하며, 이들에게 전체 경로를 적용하는 것은 연산, 시간, 에너지의 낭비이다. 본 과제는 "
     "전단부(Conv1) 직후 ^^Early Classifier 점수의 Top-1과 Top-2 차이(Score Margin)^^를 난이도 지표로 사용하여, 입력마다 "
     "Easy / Medium / Hard 경로 중 하나를 선택하는 ^^난이도 적응형 NPU Datapath(AdaPath-NPU)^^를 설계하였다.", indent=True)
para(doc, "엔트로피 기반 Early-Exit 기법(BranchyNet 등)은 분기 판단에 확률 분포의 엔트로피를 사용하므로 확률, 로그 계산 또는 그 근사 "
     "회로가 필요하다. 본 설계는 비교기와 감산기만으로 계산되는 Score Margin을 사용하며, 같은 판단 결과로 후단 연산을 "
     "생략(Easy)하거나 일부 채널만 활성화(Medium)한다.", indent=True)
para(doc, "관련 연구로, BranchyNet[1]은 엔트로피 기반 조기 종료와 여러 출구의 공동 학습을 제시하였고, Shallow-Deep "
     "Networks[7]는 최대 클래스 확률에 따른 조기 종료와 과도한 후단 계산의 영향을 분석하였다. CascadeCNN[6]은 확률 벡터의 "
     "Best-vs-Second-Best 계열 지표로 저정밀도 추론과 고정밀도 재계산을 선택하였다(부록 B). 본 설계의 구현 범위는 다음과 같다. ^^본 설계는 정수 로짓 차이를 비교기와 감산기만으로 계산하는 "
     "판단 회로, 공유 전단부와 3단계 경로 선택, 주최 측 인터페이스 통합을 하나의 RTL로 구현^^하고, ASAP7 합성, 배치와 STA, "
     "게이트레벨 VCD 기반 전력 분석까지 연결하여 하드웨어 비용과 이득을 함께 정량화하였다. "
     "주최 측 평가 구조에 맞추어 과제를 다음과 같이 구성하였다.", indent=True)
table(doc, "평가 항목별 과제 구성", ["구분", "대상 모델 / 데이터", "수행 내용"], [
    ["지정주제 (50 %)", "주최 측 MNIST 레퍼런스 가속기와 주 경로 계층 및 채널 구성이 같은 모델 A",
     "같은 주 경로에 AdaPath 적용 → 정확도 유지 조건에서 PPA 비교"],
    ["자유주제 (30 %)", "WM-811K 웨이퍼맵 결함 분류 (4개 클래스, 모델 B)",
     "같은 기법의 적용 전후 (Baseline_WM vs AdaPath_WM) PPA 비교"],
    ["확장 실험", "MNIST, 확장 모델 B (Conv2 8채널)", "후단부가 큰 모델에서 Medium 경로의 기여 분리"],
], [3.0, 5.8, 8.2])
table(doc, "비교 설계 대응표 (모두 동일 RTL 소스 adapath_top.v에서 파라미터로 생성, Reference 제외)",
      ["설계", "VARIANT", "Conv2 / Medium 채널", "클래스", "데이터", "비고"], [
    ["Reference", "-", "3 / -", "10", "MNIST", "주최 측 chip.v, 항상 전체 경로"],
    ["Baseline_A", "0", "3 / -", "10", "MNIST", "본 팀 데이터패스, 항상 Hard, Early Classifier 없음"],
    ["**AdaPath_A**", "2", "3 / 1", "10", "MNIST", "**지정주제 제출 설계**"],
    ["Baseline_B", "0", "8 / -", "10", "MNIST", "확장 모델, 항상 Hard"],
    ["Early-Exit_B", "1", "8 / -", "10", "MNIST", "Medium 없는 2경로 (기여 분리용)"],
    ["AdaPath_B", "2", "8 / 4", "10", "MNIST", "확장 모델 3경로"],
    ["Baseline_WM / AdaPath_WM", "0 / 2", "8 / 4", "4", "WM-811K", "자유주제 (N_CLASS=4, 가중치, 임계값, shift 별도)"],
], [3.6, 1.6, 2.6, 1.3, 2.0, 5.9], hl_rows=(2,),
    note="모델 A는 Reference와 주 경로(Conv1 3채널 → Conv2 3채널 → FC 48→10)의 계층 및 채널 구성이 같다. 다만 가중치는 본 팀이 "
         "학습한 값이고, 정수 규약(가중치 INT8, 활성값 12-bit, bias 16-bit)과 Early Classifier 추가가 다르다. ASIC 합성에서는 "
         "세 설계 모두 가중치를 입력 포트로 두어 상수 전파 효과를 배제하였다.")
para(doc, "본 과제의 기여는 다음 세 가지이다. 첫째, Score Margin으로 입력 난이도를 판정하고 공통 전단부 이후의 연산 경로를 "
     "선택하는 스트리밍 데이터패스를 구현하였다. Easy 입력은 후단 추론을 생략하며, Medium과 Hard 입력은 저장한 특징을 "
     "재생하여 일부 또는 전체 Conv2 채널을 사용한다. 둘째, Top-2 탐색을 직렬 비교 체인에서 이진 토너먼트 트리로 바꾸어, "
     "처리 cycle 증가 없이 판단 회로의 조합 경로를 단축하였다. 셋째, 주최 측 Reference와 항상 Hard 경로를 실행하는 "
     "Baseline_A를 함께 비교하여 Reference 대비 전체 구현의 변화와 팀 내부의 적응형 경로 적용 전후를 구분하였다. 모델 A는 선정 임계값에서 "
     "Easy/Hard 두 경로를 사용하며, Medium 경로의 기여는 확장 모델에서 별도로 평가하였다. Reference와는 가중치와 정수 규약도 "
     "다르므로 전체 개선율을 경로 선택만의 효과로 해석하지 않는다.", indent=True)

# =================================================================== 2
para(doc, "**핵심 결과:** 지정주제에서 Reference와 같은 970 / 1,000 정답을 유지하면서 ^^평균 처리 cycle 36.1 %, 추론 지연 33.0 %, "
     "추론당 에너지 8.9 %를 줄였다^^(배치 전 추정, 면적 55.4 % 증가). 별도 ICG 적용 전후 비교에서는 구간별 에너지가 20.7~25.9 % 줄었고, "
     "같은 기법을 자유주제 WM-811K에 적용하여 3경로 제어를 확인하고 WM 동일 입력 12개에 대한 모드 비율 가중 에너지가 6.7 % 감소하는 것으로 추정하였다. 두 에너지 감소율은 비교 기준이 달라 합산하지 않는다.", indent=True)
h1(doc, "2. 설계 목표")
para(doc, "지정주제의 전제 조건(정확도 유지)에서 PPA 개선을 목표로 하되, 다음 세 가지를 평가 원칙으로 정하였다. ① 연산량"
     "(MAC) 감소가 아니라 게이트레벨 스위칭 기반의 추론당 에너지로 평가한다. ② 판단 회로가 동작 주파수를 낮추지 않아야 "
     "한다. ③ Medium 경로의 기여는 Medium이 없는 2경로 구조와 분리하여 평가한다.", indent=True)
table(doc, "설계 목표 및 결과 (지정주제: Reference 대비 AdaPath_A)", ["항목", "목표", "결과", "판정"], [
    ["분류 정확도", "Reference 이상 유지",
     "970 / 1,000 (Reference 970 / 1,000, 주최 입력 순차 실행)", "달성"],
    ["평균 처리 cycle", "Reference 대비 단축",
     "%s → %s cycle (%s)" % (f0(CYC["ref"]), f0(CYC_A), chg(CYC_A, CYC["ref"])), "달성"],
    ["추론 지연 (pre-layout Fmax 기준)", "Reference 대비 단축",
     "%s → %s ns (%s)" % (f0(LAT["ref"]), f0(LAT["A"]), chg(LAT["A"], LAT["ref"])), "달성"],
    ["추론당 에너지", "Reference 대비 감소",
     "%s → %s nJ (%s, VCD 기반 추정)" % (f1(E_REF), f1(E_A), chg(E_A, E_REF)),
     "달성" if E_A < E_REF else "미달"],
    ["최대 동작 주파수", "판단 회로로 인한 저하 없음",
     "Baseline_A %s / AdaPath_A %s MHz (Reference %s MHz)" % (
         f1(FMAX["baseline_A"]), f1(FMAX["adapath_A"]), f1(FMAX["refchip"])),
     "달성" if FMAX["adapath_A"] >= FMAX["baseline_A"] * 0.99 else "미달"],
    ["판단 및 제어 회로 면적", "전체 면적의 5 % 이내",
     "%s µm² (AdaPath_A의 %.2f %%, 단독 합성 기준 참고치)" % (f1(rg["area_v2"]), region2_ratio), "달성"],
    ["입출력 인터페이스", "Reference와 동일", "동일 포트 래퍼, 주최 측 TB 로직 무수정 실행", "달성"],
    ["자유주제 (WM-811K)", "적용 전후 PPA 개선",
     "MAC %s, 정확도 %.2f %%p 하락, 에너지 %s (WM 게이트레벨 VCD 기반 추정)" % (
         chg(WM["mac_ada"], WM["mac_base"]), WM["acc_base"] - WM["acc_ada"], chg(E_WM_D, E_WM_BASE_D)),
     "달성" if E_WM_D < E_WM_BASE_D else "에너지 미달"],
], [3.3, 3.6, 7.6, 2.0], hl_rows=(1, 2, 3))
para(doc, "면적은 처리 cycle을 줄이기 위한 병렬 데이터패스와 적응형 경로의 추가로 Reference보다 증가한다. 증가분의 대부분은 "
     "병렬 연산기에서 발생하며 판단 회로 자체는 전체의 1 % 미만이다(3.6절). 면적 투자가 지연과 에너지 이득으로 전환되는 "
     "정도를 3.6~3.7절과 4장에서 정량적으로 분석한다. WM 에너지는 WM 넷리스트의 게이트레벨 VCD 기반 추정이다(3.9절).", indent=True)

# =================================================================== 3
h1(doc, "3. 설계 및 시뮬레이션")
para(doc, "그림 @f_flow@은 학습부터 PPA 비교까지의 전체 설계 및 평가 흐름이다. 기능 검증은 Golden 모델과의 비트 정합으로, 전력은 "
     "게이트레벨 VCD 활동 기반 추정으로, 비교는 동일 모델, 입력, 조건을 명시하여 수행하였다.", indent=True)
figure(doc, os.path.join(OUT, "fig_flow.png"), "AdaPath-NPU 설계 및 평가 흐름", 16.5)

h2(doc, "3.1 전체 구조 및 데이터 흐름")
para(doc, "AdaPath-NPU는 세 영역으로 구성된다. **Region 1(공유 전단부)**은 28×28 입력을 1 pixel/cycle로 스트리밍하여 "
     "Conv1(5×5, 3채널)과 MaxPool을 수행한다. 풀링 출력(12×12×3)은 Feature Map Buffer와 Early Classifier에 동시에 "
     "공급된다. **Region 2(난이도 판단 및 제어)**는 Early Classifier(AvgPool 3×3 → FC 48→10) 점수에서 Score Margin을 "
     "계산하고 두 임계값과 비교해 모드를 결정한다. **Region 3(후단부)**는 Medium 또는 Hard일 때만 버퍼를 재생(replay)하여 "
     "Conv2와 Light/Full FC를 수행한다. Easy 입력은 Early 점수로 결과를 출력하므로 Conv2와 Light/Full FC의 추론 연산을 "
     "생략한다(Early FC는 수행하며, 클럭이 공급되는 레지스터의 전력은 남는다).", indent=True)
figure(doc, os.path.join(OUT, "fig_arch.png"), "AdaPath-NPU의 데이터 및 제어 흐름 (모델 A의 선정 동작점에서는 Medium 미선택)", 16.5)
table(doc, "모드별 활성 경로와 연산량 (MNIST, 10개 클래스)", ["모드", "활성 경로", "MAC (A)", "MAC (B)"], [
    ["Easy", "Conv1 + Early Classifier", f0(MAC["A_easy"]), f0(MAC["B_easy"])],
    ["Medium", "Conv1 + Early Classifier + Conv2 일부 채널 + Light FC", f0(MAC["A_med"]), f0(MAC["B_med"])],
    ["Hard", "Conv1 + Early Classifier + Conv2 전 채널 + Full FC", f0(MAC["A_hard"]), f0(MAC["B_hard"])],
    ["Baseline (항상 Hard)", "Conv1 + Conv2 전 채널 + Full FC (Early Classifier 없음)", f0(MAC["Abase"]), "82,880"],
    ["Reference", "Conv1 + Conv2 + FC (항상)", f0(MAC["ref"]), "-"],
], [3.0, 8.2, 2.6, 2.6], note="A: Conv2 3채널, Medium 1채널. B: Conv2 8채널, Medium 4채널. 모드별 MAC에는 Early FC(480 MAC)가 포함된다.")

h2(doc, "3.2 Score Margin 기반 난이도 판단과 Top-2 Finder 개선")
para(doc, "Score Margin m = s(Top-1) − s(Top-2)는 분류기가 1순위를 얼마나 확신하는지를 나타낸다. m ≥ T_high이면 Easy, "
     "T_low ≤ m < T_high이면 Medium, m < T_low이면 Hard로 판정한다. RTL 시뮬레이션에서는 X 비교의 if/else 처리에 따라 Hard로 진행할 수 있으나, "
     "합성 넷리스트의 X 전파 차단이나 실제 회로의 안전 동작을 보증하지 않는다.", indent=True)
figure(doc, os.path.join(OUT, "fig_plan_flow.png"), "난이도 판단 및 모드 결정 흐름", 12.0)
para(doc, "10개 점수의 Top-2를 구하는 기존 회로는 Top-1 탐색(Pass 1, 9단)과 해당 위치를 제외한 Top-2 탐색(Pass 2, 9단)을 직렬로 "
     "연결하여 최대 18개의 비교 단계가 형성되었고, 이 경로가 설계 전체의 임계 경로가 되었다. 이를 ^^이진 토너먼트 트리^^로 "
     "재설계하였다(그림 @f_top2@). 10개 점수와 6개 패딩 잎을 4개의 병합 레벨로 축약하며, 각 노드는 (1위 값, 1위 index, 2위 값)을 "
     "전달한다. 두 자식 A(낮은 index), B의 병합 규칙은 A.v1 ≥ B.v1이면 1위=A, 2위=max(A.v2, B.v1), 아니면 1위=B, "
     "2위=max(A.v1, B.v2)이다. 동점이면 낮은 index가 이기므로 기존 회로와 출력이 같다. 4레벨은 트리의 구조적 깊이이며 "
     "4 cycle이나 표준셀 4단을 뜻하지 않는다. 출력 레지스터는 1단 그대로이므로 처리 cycle은 변하지 않는다.", indent=True)
figure(doc, os.path.join(OUT, "fig_top2.png"), "Top-2 Finder: 직렬 비교 체인에서 이진 토너먼트 트리로", 16.5)
table(doc, "Top-2 구조 개선에 따른 판단 및 제어 회로 단독 합성 결과 (Top-2, Margin, Decoder, FSM; Early Classifier 제외)",
      ["항목", "기존 (비교기 체인)", "개선 (토너먼트 트리)", "변화"], [
    ["임계 경로", "%s ps" % f0(rg["crit_v1"]), "%s ps" % f0(rg["crit_v2"]), "약 %.2f배 단축" % (rg["crit_v1"] / rg["crit_v2"])],
    ["면적", "%s µm²" % f1(rg["area_v1"]), "%s µm²" % f1(rg["area_v2"]), chg(rg["area_v2"], rg["area_v1"])],
    ["기능 동일성", "-", "테스트한 400,000 벡터에서 출력 비트 동일", "-"],
], [3.0, 3.8, 6.2, 3.0], note="400,000 벡터는 무작위, 동점 다수, 경계값(최소/최대), 전부 동일 값을 포함한 테스트 결과이며, "
                              "전체 입력 공간에 대한 형식적 동등성 증명은 아니다.")
para(doc, "**난이도 지표 비교:** Score Margin을 선택한 근거를 확인하기 위해, 같은 Early Classifier 로짓으로 Score Margin, 최대 "
     "softmax 확률, 엔트로피, Top-1 로짓을 비교하였다(모델 A, MNIST 10,000장, Python float 분석, 그림 @f_metrics@). Full 대비 정확도 손실 "
     "0.5 %p 제약에서 Score Margin은 네 지표 중 가장 작은 평균 MAC(44,079)을 보였으나 다른 지표와의 차이는 0.06~1.0 %로 작았고, "
     "Early 정답 여부를 구분하는 AUROC는 최대 softmax 확률(0.953)이 Score Margin(0.950)보다 약간 높았다. Score Margin은 확률 "
     "정규화와 exp, log 같은 비선형 연산 없이 비교와 감산으로 구현된다는 이점이 있지만, Top-1 로짓보다 연산이 적은 것은 아니므로 "
     "'네 지표 중 최소 회로 비용'이라고 결론짓지 않는다. 즉 Score Margin은 비선형 연산 없이 유리한 정확도–연산량 절충을 보인 "
     "지표로 해석한다(지표별 면적 및 지연은 측정하지 않음).", indent=True)
table(doc, "난이도 지표 비교 (모델 A, Full 대비 정확도 손실 0.5 %p 제약, 동일셋 탐색)",
      ["지표", "필요 연산 (직접 계산 기준)", "AUROC", "정확도", "평균 MAC", "Hard 대비 MAC 절감"], [
    ["**Score Margin**", "비교 트리 + 감산 1 (exp/log/나눗셈 없음)", "0.950", "97.03 %", "44,079", "24.73 %"],
    ["최대 softmax 확률", "exp 10, 덧셈 9, 정규화(나눗셈) + 최대값", "0.953", "97.03 %", "44,106", "24.68 %"],
    ["엔트로피", "softmax + log 10, 곱셈 10, 덧셈 9", "0.950", "97.03 %", "44,256", "24.43 %"],
    ["Top-1 로짓", "비교 9 (최대값만)", "0.893", "97.03 %", "44,530", "23.96 %"],
], [3.0, 5.6, 1.6, 2.0, 2.2, 2.6], hl_rows=(0,),
    note="연산 수는 직접 수식 기준이며 합성 후 셀 수, 면적, 지연이 아니다. 판정만 필요하면 최대값 정규화 등으로 비선형 연산을 "
         "줄일 수 있다. 같은 테스트셋에서 탐색한 결과로 낙관 편향이 있을 수 있으며, 2-fold 교차 평가 평균 정확도는 Margin "
         "97.02 %, 최대 softmax 96.99 %, 엔트로피 96.98 %, Top-1 97.00 %였다.")
figure(doc, os.path.join(OUT, "sh2_fig_metric_comparison.png"),
       "모델 A의 네 난이도 지표에 대한 동일셋 정확도–MAC Pareto와 Early 정답 예측 AUROC", 16.0)

h2(doc, "3.3 소프트웨어 모델링, 임계값 탐색, 정수 양자화")
para(doc, "세 출력(Early / Light / Full)을 가진 3-head 모델을 MNIST 학습셋 60,000장으로 공동 학습하였다(표 @t_train@). 이후 "
     "테스트셋에서 (T_low, T_high)를 탐색하여 'Full 경로 대비 정확도 손실 0.5 %p 이내에서 평균 MAC 최소'인 동작점을 선택하였다. "
     "0.5 %p는 주최 측 기준이 아니라 본 팀이 정한 내부 선정 규칙이다. 이 동작점은 테스트셋 기반 탐색 결과이므로, 임계값 선정과 "
     "평가를 분리한 교차 평가를 아래에 함께 제시한다. 정수 규약은 가중치 INT8, 활성값과 점수 인터페이스 signed 12-bit(포화), bias 누산기 도메인 16-bit, "
     "재양자화 반올림 시프트이며, 이 규약으로 RTL과 비트 단위로 일치하는 Golden 모델을 생성하였다.", indent=True)
table(doc, "학습 설정 (모델 A와 B, MNIST / WM-811K 공통)", ["항목", "설정", "항목", "설정"], [
    ["Optimizer", "Adam, lr 2×10⁻³", "Scheduler", "Cosine annealing"],
    ["Epoch / Batch", "30 / 128", "손실", "CE(Full) + 0.5×CE(Early) + 0.5×CE(Light)"],
    ["입력", "28×28, [0,1] 정규화", "Random seed", "seed 미고정; 반복 재학습 변동성 미평가"],
], [3.0, 4.6, 2.6, 6.8])
sw = R["sw"]
table(doc, "모델별 정확도와 선정 동작점 (MNIST 테스트셋 10,000장)", ["항목", "모델 A (지정주제)", "모델 B (확장)"], [
    ["Full / Light / Early 정확도 (float)", "%s / %s / %s %%" % (sw["A_full"], sw["A_light"], sw["A_early"]),
     "%s / %s / %s %%" % (sw["B_full"], sw["B_light"], sw["B_early"])],
    ["선정 동작점 모드 비율 (Easy / Medium / Hard)", sw["A_modes"], sw["B_modes"]],
    ["AdaPath 정확도 / 평균 MAC 절감", "%s %% / %s %%" % (sw["A_acc"], sw["A_macsave"]),
     "%s %% / %s %%" % (sw["B_acc"], sw["B_macsave"])],
    ["정수 Hard 경로 정확도 (같은 표본의 float 대비)", sw["A_int8"], "97.80 % (float 97.95 %, n=2,000)"],
], [6.6, 5.2, 5.2])
para(doc, "모델 A는 Conv2가 3채널뿐이어서 1채널 Light 경로의 정확도(%s %%)가 낮다. 임계값 탐색은 Medium 구간을 두지 않는 "
     "동작점(T_low = T_high)을 평가한 후보 중에서 선택하였고, 그 결과 모델 A는 Easy/Hard 두 경로로 동작한다. 반면 후단부가 큰 모델 B와 "
     "WM-811K에서는 Medium이 선택된다(3.8절)." % sw["A_light"], indent=True)
figure(doc, os.path.join(OUT, "archA", "fig_margin_hist_mnist.png"), "모델 A의 Score Margin 분포와 선정 임계값", 12.0)
figure(doc, os.path.join(OUT, "archA", "fig_tradeoff_mnist.png"),
       "모델 A의 임계값 조합별 정확도와 평균 MAC (MNIST 테스트셋, Python float). 점은 탐색한 (T_low, T_high) 조합, 별은 항상 Hard인 Baseline이다.", 14.0)
h3(doc, "3.3.1 임계값 선정과 평가의 분리 (2-fold 교차 평가)")
para(doc, "임계값 선정과 평가에 같은 데이터를 쓰는 문제를 줄이기 위해, 고정 "
     "가중치 모델에 대해 테스트셋을 무작위로 반분하여 한쪽에서 동작점을 선정하고 다른 쪽에서 평가하는 2-fold 교차 평가를 "
     "5개 분할 seed로 반복하였다(표 %(t_twofold)s, 그림 %(f_twofold)s). 기존 보고점과 같은 25개 분위수 후보로 선정하면 모델 A는 "
     "두 평가 절반을 합친 반복별 결과에서 정확도 97.41 ± 0.18 %%, MAC 절감 23.99 ± 0.23 %%로 5회 모두 0.5 %%p 손실 예산을 지켰다. 반면 더 촘촘한 "
     "경계 전수 탐색에서는 모델 A도 5회 중 3회 예산을 넘었고(손실 0.51 ± 0.04 %%p), 모델 B와 WM-811K는 두 탐색법 모두 5회 전부 "
     "예산을 넘었다(WM 손실 2.26 ± 1.48 %%p). 즉 **선정 데이터에서 지킨 정확도 제약이 미사용 데이터에서 보장되지는 않으며**, "
     "특히 표본이 작고 클래스가 어려운 WM-811K에서 차이가 컸다. 이 분석은 이미 관찰된 테스트셋을 사후 분할한 것으로, 새로운 "
     "외부 테스트셋 검증은 아니다(표준편차는 분할 seed에 따른 변동)." % LBL, indent=True)
table(doc, "임계값 선정 및 평가 분리 결과 (2-fold × 5 분할 seed, 평가 절반 기준, Python float)",
      ["모델", "탐색", "정확도 (%)", "Full 대비 손실 (%p)", "Hard 대비 MAC 절감 (%)", "Easy / Medium / Hard (%)", "예산 초과"], [
    ["MNIST A", "기존 보고점 (동일셋)", "97.47", "0.06", "23.89", "94.0 / 0 / 6.0", "-"],
    ["MNIST A", "25분위수 후보", "97.41 ± 0.18", "0.12", "23.99 ± 0.23", "94.4 / 0 / 5.6", "0 / 5"],
    ["MNIST A", "경계 전수 탐색", "97.02 ± 0.04", "0.51", "24.68 ± 0.02", "97.1 / 0 / 2.9", "3 / 5"],
    ["MNIST B", "기존 보고점 (동일셋)", "98.12", "0.39", "40.94", "82.0 / 8.0 / 10.0", "-"],
    ["MNIST B", "경계 전수 탐색", "97.79 ± 0.05", "0.72", "43.06 ± 0.12", "85.9 / 9.2 / 4.9", "5 / 5"],
    ["WM-811K", "기존 보고점 (동일셋)", "81.24", "0.31", "23.64", "42.0 / 15.9 / 42.0", "-"],
    ["WM-811K", "경계 전수 탐색", "79.29 ± 1.48", "2.26", "28.38 ± 1.30", "55.5 / 9.1 / 35.4", "5 / 5"],
], [1.9, 3.0, 2.3, 2.0, 2.6, 3.0, 1.6], hl_rows=(1,),
    note="선정 규칙: 선정 절반에서 Full 대비 정확도 손실 0.5 %p 이내의 최소 MAC. 평가 절반에서는 제약을 강제하지 않는다. "
         "각 반복의 두 평가 절반을 합친 OOF 결과를 요약하였으며, MAC 절감의 분모는 Hard 경로(Early FC 포함)이다.")
figure(doc, os.path.join(OUT, "sh2_fig_twofold.png"),
       "임계값 선정 및 평가를 분리한 2-fold 결과 (5개 분할 seed의 평균 ± 표준편차, × = 기존 동일셋 동작점)", 16.0)
h3(doc, "3.3.2 통계적 비교")
para(doc, "기존 동작점에서 AdaPath와 같은 체크포인트의 Full 경로를 같은 이미지 쌍으로 비교하였다(표 %(t_stats)s). "
     "모델 A는 97.47 %% vs 97.53 %% (Wilson 95 %% 구간 97.14–97.76 %% vs 97.21–97.82 %%)이고, 불일치 쌍은 Full만 정답 58장, "
     "AdaPath만 정답 52장으로 McNemar exact p = 0.63이었다. 모델 B는 Full만 정답인 쌍이 54장 대 15장으로 유의한 정확도 하락"
     "(p = 2.6×10⁻⁶)이 있었으며, 이는 B의 동작점이 0.39 %%p 손실을 수용한 결과와 일치한다. 즉 "
     "^^모델 A와 WM-811K에서는 이 검정으로 정확도 차이를 검출하지 못하였다^^. 이는 정확도 동등성이나 비열등성의 증명이 아니다." % LBL, indent=True)
table(doc, "기존 동작점의 AdaPath vs Full 통계 비교 (같은 체크포인트, 이미지 단위)",
      ["모델", "n", "AdaPath (95 % CI)", "Full (95 % CI)", "b / c", "McNemar p (Holm)"], [
    ["MNIST A", "10,000", "97.47 % (97.14–97.76)", "97.53 % (97.21–97.82)", "58 / 52", "0.634 (1.0)"],
    ["MNIST B", "10,000", "98.12 % (97.83–98.37)", "98.51 % (98.25–98.73)", "54 / 15", "2.6×10⁻⁶ (7.8×10⁻⁶)"],
    ["WM-811K", "954", "81.24 % (78.64–83.59)", "81.55 % (78.97–83.88)", "19 / 16", "0.736 (1.0)"],
], [2.0, 1.6, 4.0, 4.0, 1.8, 3.2],
    note="b = Full만 정답, c = AdaPath만 정답. 양측 exact 검정, 세 비교에 Holm 보정.")
figure(doc, os.path.join(OUT, "sh2_fig_accuracy_ci.png"),
       "기존 동작점에서 같은 이미지 쌍의 Full과 AdaPath 정확도 (Wilson 95 % 구간, 패널별 y축 범위가 다름)", 15.0)

h2(doc, "3.4 RTL 설계와 주최 측 인터페이스 호환")
para(doc, "RTL은 채널 수 및 클래스 수를 파라미터화한 단일 소스(adapath_top.v)로 작성하였다. VARIANT(0: Baseline, 1: Early-Exit, "
     "2: AdaPath)와 C2/C2_MED(모델 A와 B), N_CLASS(MNIST 10, WM-811K 4) 및 각 모델의 가중치, 임계값, shift 설정만 바꿔 표 @t_map@의 "
     "비교 설계를 생성하였다. 주요 블록은 conv1_engine(75 MAC 병렬), fmap_buffer(144×36 bit), early_classifier, "
     "top2_finder, score_margin_calc, difficulty_decoder, mode_control_fsm, conv2_engine(채널 enable), "
     "fc_engine(Light/Full)이다.", indent=True)
para(doc, "주최 측 평가는 제출 프로젝트의 테스트벤치에서 입력 파일만 교체하는 방식이므로, 레퍼런스 chip과 ^^포트 목록 및 폭이 "
     "같은 래퍼(chip_adapath.v)^^를 제작하였다(그림 @f_wrapper@). 레퍼런스 가중치 포트는 호환용으로 입력만 받고 사용하지 않으며, "
     "^^본 팀이 학습한 가중치는 래퍼 내부 상수(adapath_weights.vh)로 고정^^하였다. 레퍼런스는 rst_n 해제 직후부터 픽셀을 "
     "받으므로, clk로 샘플링한 rst_n의 상승을 검출하여 코어의 start 펄스를 생성한다(reset low 구간이 최소 1 clk 이상 "
     "관측되어야 함). 주최 측 top_tb.v는 테스트벤치 로직을 수정하지 않았으며, 데이터 파일 경로만 프로젝트 내부 파일명으로 "
     "지정하였다. 시뮬레이션 top은 top_tb_1000, 도구는 Vivado 2023.1이다.", indent=True)
figure(doc, os.path.join(OUT, "fig_wrapper.png"), "주최 측 chip 인터페이스를 유지하는 래퍼", 16.0)

h2(doc, "3.5 기능 검증")
v = R["verify"]
table(doc, "기능 검증 결과", ["검증 단계", "방법", "결과"], [
    ["판단 및 제어 회로 단위", "Python Golden 200 벡터", "200 / 200 일치"],
    ["Top-2 Finder 개선", "기존 회로와 400,000 벡터 비교 (무작위, 동점, 경계값)", "테스트 벡터 전부 출력 동일"],
    ["End-to-end", "3종 구조 × 9장, 모드별 대표 이미지", "27 / 27 Golden 일치"],
    ["1,000장 회귀 (모델 B)", "MNIST 1,000장 Golden (margin / mode / decision)", "1,000 / 1,000 일치"],
    ["게이트레벨 (A, B, Reference)", "합성 넷리스트 + ASAP7 셀 모델 시뮬레이션", "RTL과 판정, 모드, cycle 동일"],
    ["**주최 측 TB (Vivado 2023.1)**", "top_tb_1000, 테스트벤치 로직 무수정",
     "Reference %s / A %s / B %s" % (v["org_ref"], v["org_A"], v["org_B"])],
    ["**WM-811K (Vivado 2023.1)**", "chip 래퍼(4개 클래스) + tb_wm, 테스트 954장",
     "Golden 판정, 모드, Margin 954 / 954 일치"],
    ["**합성 넷리스트 (Vivado 2023.1)**", "ORFS 넷리스트 + ASAP7 셀 + 원본 TB + xfill, 5개 시드 부분 실행",
     "판정 %s/%s, cycle %s/%s 일치" % (f"{NETSIM['total_decision_match']:,}", f"{NETSIM['total_outputs']:,}",
                                          f"{NETSIM['total_cycle_match']:,}", f"{NETSIM['total_cycle_checked']:,}")],
], [3.8, 7.0, 6.2], hl_rows=(5, 6, 7))
table(doc, "주최 측 입력(input_1000.txt) 기준 정확도와 처리 cycle",
      ["설계", "정답 (순차 입력)", "정답률 (주최 TB)", "평균 cycle (주최 TB)", "평균 cycle (순차 입력)", "모드 분포 (순차)"], [
    ["Reference", "970 / 1,000", "%.1f %%" % ACC["ref_org"], f0(CYC["ref_org"]), f0(CYC["ref"]), "-"],
    ["Baseline_A", "970 / 1,000", "-", "-", f0(CYC["base"]), "0 / 0 / 1,000"],
    ["**AdaPath_A**", "**970 / 1,000**", "%.1f %%" % ACC["A_org"], f1(CYC["A_org"]), "**%s**" % f1(CYC_A),
     R["modes_seq"]["A"]],
    ["AdaPath_B", "1,000 / 1,000", "%.1f %%" % ACC["B_org"], f1(CYC["B_org"]), f1(CYC_B), R["modes_seq"]["B"]],
], [2.6, 2.6, 2.4, 2.8, 3.0, 3.0], hl_rows=(2,),
    note="input_1000.txt는 고유 100장이 10회 반복된 1,000회 입력이다. '순차 입력'은 1,000회를 순서대로 처리한 결과이고, "
         "'주최 TB'는 원본 TB의 무작위 추출 실행 결과이다. cycle은 start(rst_n 해제)부터 valid_out까지이다.")
h3(doc, "3.5.1 주최 측 TB의 입력 경계")
para(doc, "원본 TB는 $urandom_range(0,1000)으로 이미지 인덱스를 뽑으므로 인덱스 1000이 선택되면 범위 밖 X 픽셀을 읽고"
     "(Vivado 2024.1의 Reference 실행에서 3회), 첫 출력 1회는 state가 X인 비채점 출력이다. 관측된 3회가 정답 수에 미칠 수 있는 영향은 최대 0.3 %p이며, 이 입력 경계 영향을 배제하기 위해 "
     "정확도와 cycle 비교의 주 근거는 1,000회 순차 실행(970 / 1,000)으로 하였다.", indent=True)
h3(doc, "3.5.2 별도 수정 TB 재검증")
para(doc, "입력 경계를 보완한 별도 TB(top_tb_1000_corrected.v)로 같은 chip 래퍼를 재검증하였다. 상태와 입력을 초기화하고 "
     "인덱스를 0~999로 제한하여 순차 1,000회와 무작위(seed 2026) 1,000회를 실행하였다.", indent=True)
_tb_seq=TB_RUNS['sequential'];_tb_rnd=TB_RUNS['random_seed2026']
_tb_rows=[]
for title,key in [('유효 출력 수','outputs'),('정답 수','correct')]:
    _tb_rows.append([title,str(_tb_seq['summary'][key]),str(_tb_rnd['summary'][key])])
_tb_rows.append(['Easy / Medium / Hard']+[' / '.join(str(x['summary'][k]) for k in ['easy','medium','hard']) for x in [_tb_seq,_tb_rnd]])
for title,key in [('범위 밖 읽기','invalid_reads'),('X 데이터 읽기','unknown_reads'),('X 출력','x_outputs'),('픽셀 읽기 수','reads')]:
    _tb_rows.append([title,str(_tb_seq['observer'][key]),str(_tb_rnd['observer'][key])])
table(doc, "별도 수정 TB의 입력 및 출력 무결성 재검증 (모델 A)",
      ['검사 항목','순차 1,000회','무작위 1,000회'], _tb_rows, [6.5,5.0,5.0], size=9)
para(doc, "두 실행 모두 범위 밖 읽기와 X 출력 없이 1,000개 출력을 4,000 cycle 이내에 완료하였고, ^^무작위 실행의 판정과 모드는 "
     "같은 인덱스의 순차 실행 결과와 1,000 / 1,000 일치^^하였다.", indent=True)
h3(doc, "3.5.3 Vivado 실행 화면과 파형")
figure(doc, os.path.join(OUT, "fig_vivado_console.png"),
       "Vivado 2023.1 실행 화면 — 주최 측 top_tb_1000 실행 결과 (AdaPath_A)", 15.0)
para(doc, "제출 프로젝트(.xpr)를 Vivado 2023.1에서 그대로 실행한 화면이다. 원본 테스트벤치의 cnt가 1,000에 도달한 뒤 $stop(391행)에서 "
     "정지하였고, Tcl 콘솔에 'Accuracy : 96%'가 출력되었다. Objects 창의 accuracy = 0x3C6(966), cnt = 0x3E8(1,000)이다.",
     indent=True)
figure(doc, os.path.join(OUT, "fig_vivado_ref_vs_ada.png"),
       "같은 41,500 cycle(0~415 ns, 논리 시뮬레이션) 동안 완료한 이미지 수: Reference 30장 vs AdaPath_A 47장 (각 설계의 파형을 0~207 ns와 207~415 ns 두 줄로 표시)", 16.0)
para(doc, "같은 테스트벤치에서 같은 41,500 cycle 동안 Reference는 30장(정답 30), ^^AdaPath_A는 47장(정답 46)을 완료하여 57 %% 많은 "
     "이미지를 처리^^하였다. 이미지당 평균 처리 cycle이 1,336에서 855로 줄어든 효과가 파형에 그대로 나타난다." % LBL, indent=True)
para(doc, "파형의 시간축은 원본 TB의 10 ps 클럭에 따른 기능 시뮬레이션 시간이며, 물리적 동작 주파수는 3.6절의 STA 결과를 따른다.", indent=True)
figure(doc, os.path.join(OUT, "fig_vivado_detail_easy_hard.png"),
       "Vivado 파형 (376~415 ns, 논리 시뮬레이션): 실행 순번 42~45번째(Easy)와 46번째(Hard) 이미지의 내부 동작 비교", 17.0)
para(doc, "실행 순번 42~45번째 Easy 이미지는 Early Classifier가 끝난 직후 FSM이 FRONT(1)에서 바로 출력으로 넘어가므로, Feature Map Buffer "
     "재생, Conv2 채널 enable, Full FC가 활성화되지 않는다. 46번째 이미지만 Score Margin이 57로 임계값 63보다 작아 Hard로 "
     "판정되며 후단부가 동작한다. mode 및 margin 레지스터는 이미지마다 리셋되고 Easy 판정은 출력 직전 수 cycle 동안만 "
     "유지되므로, 이 배율에서는 리셋값(Hard=2)이 주로 보인다.", indent=True)
figure(doc, os.path.join(OUT, "fig_vivado_detail_hard.png"),
       "Vivado 파형 확대 (399~404 ns, 논리 시뮬레이션): 46번째(Hard 판정) 이미지의 내부 처리 순서", 15.5)
para(doc, "Hard 판정 시 내부 동작은 ① Early Classifier 완료 → ② Score Margin 57 산출 및 판정 유효 → ③ FSM BACK(3) 전환 → "
     "④ Feature Map Buffer 재생 시작 및 재생 데이터 유효 구간 → ⑤ Conv2 전 채널 enable(111)과 Full FC 동작 → ⑥ valid_out_6 "
     "출력과 누적 정답 수 증가(44 → 45) 순서로 진행된다. Hard 이미지 1장의 추가 처리 시간은 Easy 대비 171 cycle이다.",
     indent=True)
h3(doc, "3.5.4 제출 패키지의 독립 PC 재현 (Vivado 2024.1)")
para(doc, "제출 패키지의 이식성을 확인하기 위해 작성자와 다른 PC의 Vivado 2024.1에서 A, B, WM 프로젝트 ZIP을 새 경로에 풀어 "
     "실행하였다. 패키지 파일의 SHA-256이 원본과 일치하였고, ^^A 966 / 1,000, B 999 / 1,000, WM 774 / 954(81.13 %%)와 Golden "
     "954 / 954 일치를 그대로 재현^^하였다. WM의 Easy / Medium / Hard 사용 횟수도 404 / 167 / 383으로 같았다." % LBL, indent=True)
figure(doc, os.path.join(OUT, "fig_vivado_submit3.png"),
       "독립 PC의 Vivado 2024.1에서 제출 ZIP 3종을 실행한 Tcl 콘솔 (콘솔의 백분율은 원본 TB의 정수 나눗셈 표시)", 15.0)
h3(doc, "3.5.5 제어 조건 검사")
para(doc, "Vivado 2024.1에서 RTL과 TB를 변경하지 않고 읽기 전용 관측 모듈을 시뮬레이션 최상위에 추가하여, 4개 제어 조건을 "
     "매 cycle 검사하였다(표 @t_control@).", indent=True)
table(doc, "제어 조건의 동적 검사 (Vivado 2024.1, 검사 횟수 / 위반 건수)",
      ["검사 조건 및 단위", "모델 A", "WM-811K"], [
          ["Easy 결정 후 valid까지 Conv2 비활성 (cycle)",
           f"{CONTROL['A']['easy_checks']:,} / {CONTROL['A']['easy_errors']}",
           f"{CONTROL['WM']['easy_checks']:,} / {CONTROL['WM']['easy_errors']}"],
          ["Medium 후단 활성 중 채널 mask, Light/Full FC 선택 (cycle)", "0 / 해당 없음",
           f"{CONTROL['WM']['medium_checks']:,} / {CONTROL['WM']['medium_errors']}"],
          ["start→valid 4,000 cycle 이내 응답 (완료 거래)",
           f"{CONTROL['A']['deadline_checks']:,} / {CONTROL['A']['deadline_errors']}",
           f"{CONTROL['WM']['deadline_checks']:,} / {CONTROL['WM']['deadline_errors']}"],
          ["S_BACK과 S_DONE에서 선택 모드와 Result MUX 일치 (cycle)",
           f"{CONTROL['A']['mux_checks']:,} / {CONTROL['A']['mux_errors']}",
           f"{CONTROL['WM']['mux_checks']:,} / {CONTROL['WM']['mux_errors']}"],
      ], [8.0, 3.5, 3.5], size=9,
      note="모델 A는 선정 동작점에서 Medium을 사용하지 않는다. WM은 Medium 167장의 후단 활성 27,555 cycle을 검사하였다.")
para(doc, "^^실제로 검사한 조건에서 위반은 0건^^이었고, 검사한 제어 신호에서 X는 관측되지 않았다. 관측 모듈은 4종 위반을 인위로 주입한 "
     "자가 시험에서 각 위반을 검출함을 확인하였다. A의 채점 로그 1,000개는 기존 ZIP 실행과 줄 단위로 같았다(정답 966).", indent=True)
para(doc, "A의 완료 1,001회에는 초기 비채점 출력 1회가 포함되며, 종료 시 남은 start 1회는 응답 기한 전에 시뮬레이션이 "
     "끝나 완료 여부를 평가하지 못하였다. 활성 구간의 입력 X는 A 2,096 cycle, WM 221 cycle에서, decision X는 A의 초기 "
     "비채점 출력 1회에서 관측되었다. 제어 조건의 통과를 입력 X의 부재나 전체 입력 공간에 대한 형식 증명으로 해석하지 않는다.", indent=True)
h3(doc, "3.5.6 실험용 RTL의 임계값 스윕")
para(doc, "실험용 RTL에서 difficulty_decoder의 임계값 입력 모드(USE_REG_TH=1)를 최상위 포트로 연결하고, "
     "주최 측 입력 1,000회에 대해 TL = TH를 0~400으로 바꿔 가며 16개 동작점을 RTL로 측정하였다(그림 %(f_sweep)s). TH = 63에서 "
     "기존 결과(정답 970, 평균 851.84 cycle, Easy/Hard 960/40)가 재현되었다. TH를 높이면 Hard 수가 0(TH = 0)에서 730"
     "(TH = 400)까지 늘고 평균 cycle은 845.0에서 969.8로 증가하였다. 이 구성에서 임계값 변화에 따른 정확도와 처리 cycle을 "
     "확인하였다. 이 입력 집합에서는 TH = 0, 10, 20, 30(전부 Easy)이 정답 980개로 가장 높았으나, MNIST 테스트셋 "
     "10,000장에서는 Early 경로 단독 정확도(96.21 %%)가 Full 경로(97.53 %%)보다 낮다. 최적 임계값은 입력 분포에 따라 달라진다. "
     "임계값 가변 기능은 실험용 RTL에 해당하며, 제출용 모델 A는 TL=TH=63의 고정 임계값을 사용한다." % LBL,
     indent=True)
para(doc, "Hard 비율을 p_H라 하면 평균 cycle은 C = 845(1−p_H) + 1016p_H = 845 + 171p_H이다. "
     "16개 조건 모두 이 관계와 일치하여, 평균 처리 cycle을 Hard 비율로 정확히 예측할 수 있다.", indent=True)
figure(doc, os.path.join(OUT, "hs_fig_sweep_A.png"),
       "모델 A 임계값 스윕 (실험용 RTL, 주최 측 입력 1,000회): 정확도–평균 처리 cycle", 14.0)
h3(doc, "3.5.7 합성 넷리스트의 Vivado 기능 검증")
_nd = NETRUN["default"]
_nok = min(NETSIM["total_decision_match"], NETSIM["total_cycle_match"])
para(doc, "설명회 Sample Flow의 기능 검증 단계에 따라, 제출 chip(AdaPath_A, 가중치 상수)을 ORFS로 합성한 넷리스트와 주최 측 "
     "ASAP7 표준셀 Verilog를 원본 top_tb_1000과 함께 Vivado 2023.1 시뮬레이터에서 실행하고 RTL 결과와 비교하였다. "
     "셀 모델은 지연이 0인 기능 모델이므로 이 실행은 타이밍이 아닌 기능 일치를 확인한다.", indent=True)
para(doc, "원본 TB는 첫 valid_out 전까지 state가 X이므로 첫 비채점 이미지의 픽셀을 X로 입력하고, 인덱스 1000이 선택될 때도 "
     "X 픽셀을 읽는다(3.5.1절). RTL에서는 X가 있어도 제어가 진행되지만, 넷리스트에서는 X가 Score Margin과 모드 판정을 거쳐 "
     "FSM 상태 레지스터까지 전파되어 ^^valid_out이 1이 되지 않고 시뮬레이션이 시작 직후 정지^^하였다. 입력에 따라 경로를 바꾸는 "
     "제어가 게이트레벨 시뮬레이션의 X 전파에 노출된 결과이며, 실제 회로의 정상 동작 또는 고장을 단정하지 않는다. 따라서 TB "
     "파일은 수정하지 않고, ^^TB가 내보내는 입력 바이트에 X 또는 Z가 포함된 경우에만 DUT 입력을 0으로 바꾸는 시뮬레이션 전용 모듈^^을 추가하였다. 이 모듈은 "
     "각 채점 출력의 이미지 인덱스와 판정도 기록하며 DUT의 다른 입력은 구동하지 않는다. 같은 모듈을 적용한 RTL 실행은 기존 "
     "Vivado 로그와 1,000개 채점 출력 시각이 모두 같았고, 판정은 인덱스 1000 이미지(879번째, 원래도 오답) 1건만 10에서 5로 "
     "바뀌어 정답 수 966은 변하지 않았다.", indent=True)
para(doc, "넷리스트 시뮬레이션은 RTL보다 수백 배 느려 1,000장 실행에 수 시간이 걸리므로, 기본 시드 실행과 함께 같은 TB를 xsim의 "
     "-sv_seed " + ", ".join(r["seed"] for r in NETSIM["runs"] if r["key"] != "default" and r["outputs"]) +
     "로 병렬 실행하였다. 출력 순서의 입력 이미지가 시드마다 다르므로, 각 출력을 같은 이미지 인덱스의 RTL 결과"
     "와 대조하였다(표 @t_netsim@). ^^합계 %s개 채점 출력의 판정이 RTL과 일치^^하였다. "
     f"처리 cycle은 기준값이 있는 {NETSIM['total_cycle_checked']:,}개 출력에서 모두 일치하였으며, 인덱스 1000의 치환 출력 1건은 제외하였다. 정답 수는 넷리스트와 RTL 모두 "
     f"{sum(r['correct'] for r in NETSIM['runs']):,}개였다. 출력에 포함된 입력 인덱스는 %s개이나, input_1000.txt는 고유 이미지 "
     "100장이 반복된 파일이므로 픽셀 내용 기준으로는 %s종(X 치환 이미지 포함)이다. " % (f"{NETSIM['total_outputs']:,}", f"{NETSIM['distinct_indices']:,}",
                                    f"{NETSIM['distinct_contents']:,}"),
     indent=True)
table(doc, "합성 넷리스트의 Vivado 기능 검증 결과 (Vivado 2023.1, 같은 이미지 인덱스의 RTL 결과와 대조)",
      ["실행", "채점 출력 수", "판정 일치", "cycle 일치/대조", "정답 수 (넷리스트 = RTL)"],
      [["기본 시드" if r["key"] == "default" else "-sv_seed " + r["seed"], f"{r['outputs']:,}", f"{r['decision_match']:,}",
        f"{r['cycle_match']:,}/{r['cycle_checked']:,}", f"{r['correct']:,}"] for r in NETSIM["runs"] if r["outputs"]] +
      [["**합계**", f"**{NETSIM['total_outputs']:,}**", f"**{NETSIM['total_decision_match']:,}**",
        f"**{NETSIM['total_cycle_match']:,}/{NETSIM['total_cycle_checked']:,}**", f"{sum(r['correct'] for r in NETSIM['runs']):,}"]],
      [3.4, 3.0, 3.0, 3.2, 4.4], size=9,
      note=("기본 시드는 원본 TB 1,000장 실행 전체를 완료하였다(%s)." % _nd["final_accuracy_line"]) if _nd["final_accuracy_line"] else
           ("기본 시드는 %s회 출력(시뮬레이션 %s ns)까지 확인하였다. 5개 시드의 부분 실행 합계이며, 원본 TB 한 번의 1,000회 실행 완료는 아니다."
            % (f"{_nd['outputs']:,}", f"{_nd['sim_end_ns']:,}")))
figure(doc, os.path.join(OUT, "fig_vivado_netlist.png"),
       "Vivado 2023.1 시뮬레이터에서 합성 넷리스트(1_synth.v + 주최 측 ASAP7 셀 Verilog)로 원본 top_tb_1000을 실행한 화면. "
       "위는 처음 45 ns의 파형, 아래 콘솔의 집계는 교정 전 값이다(cycle 대조 1건 제외, 표 %(t_netsim)s)." % LBL, 17.0)
para(doc, "그림은 같은 넷리스트 스냅샷을 GUI 모드로 다시 실행하여 캡처한 것이다. 첫 비채점 이미지 구간의 data_in은 X로 표시되며(0~10 ns), "
     "그 뒤 이미지마다 rst_n 펄스와 valid_out이 반복되고 cnt와 accuracy가 함께 증가한다. 콘솔의 OBS 줄은 시뮬레이션 전용 모듈이 "
     "기록한 이미지 인덱스와 판정이고, 마지막 줄은 교정 전 집계이다. 인덱스 1000은 cycle 기준값 없이 일치로 집계되었으므로 표 @t_netsim@에서 제외하였다.", indent=True)
para(doc, "처리 cycle은 연속한 채점 출력 사이 간격에서 리셋 1 cycle을 뺀 값으로, RTL 결과의 처리 cycle과 같은 정의이다.", indent=True)

h2(doc, "3.6 논리 합성 및 타이밍 (OpenROAD-flow-scripts, ASAP7)")
para(doc, "모든 설계를 동일한 흐름(Yosys + ABC area 스크립트, 동일 SDC 규칙: 입출력 지연 = 클럭 주기의 20 %)으로 합성하고 "
     "OpenROAD로 pre-layout STA를 수행하였다. 가중치는 모든 설계에서 입력 포트로 두었다. 입력 지연이 주기에 비례하므로, "
     "단일 주기의 WNS로 Fmax를 역산하지 않고 클럭 주기를 1.0~2.4 ns로 스윕하여 최악 slack이 0이 되는 주기(인접 두 점의 "
     "선형 보간)를 추정하였다. 또한 추론 중 값이 바뀌지 않는 가중치 포트를 false path로 둔 조건(레지스터 간, "
     "픽셀 입력 경로 기준)의 Fmax를 함께 제시한다.", indent=True)
rows = []
for key, name in (("refchip", "Reference"), ("baseline_A", "Baseline_A"), ("adapath_A", "**AdaPath_A**"),
                  ("baseline", "Baseline_B"), ("adapath", "AdaPath_B")):
    rows.append([name, f0(A[key]), "%+.1f %%" % pct(A[key], A["refchip"]), f0(PER[key]), f1(FMAX[key]), f1(FMAX_S[key])])
table(doc, "합성 결과 (pre-layout, 클럭 주기 스윕)",
      ["설계", "Cell Area (µm²)", "Reference 대비", "슬랙 0 추정 주기 (ps)", "Fmax (MHz, SDC 규칙)", "Fmax (MHz, 가중치 정적)"],
      rows, [2.8, 2.8, 2.6, 2.6, 3.1, 3.1], hl_rows=(2,),
      note="추정 주기 및 Fmax(SDC 규칙)는 입출력 지연 20 % 조건에서 최악 slack = 0인 교차점을 선형 보간한 값이다. 이 조건의 임계 경로는 세 설계 "
           "모두 가중치 입력 포트에서 시작한다. '가중치 정적'은 가중치 포트를 false path로 둔 결과이다.")
sweep_evidence = []
for key, name in [('refchip', 'Reference'), ('baseline_A', 'Baseline_A'), ('adapath_A', 'AdaPath_A')]:
    lines = open(os.path.join(HERE, '..', 'orfs/reports_extra/sweep_'+key+'.txt'), encoding='utf-8').read().splitlines()
    points = [(float(x.split()[1]), float(x.split()[2])) for x in lines if x.startswith('io20 ')]
    fail = max((x for x in points if x[1] < 0), key=lambda x:x[0])
    passed = min((x for x in points if x[1] >= 0), key=lambda x:x[0])
    sweep_evidence.append([name, f'{fail[0]:.0f}', f'{fail[1]:+.2f}', f'{passed[0]:.0f}', f'{passed[1]:+.2f}', f'{1e6/passed[0]:.1f}'])
table(doc, "STA 스윕의 실제 실패 및 통과점 (입출력 지연 20% 조건)",
      ['설계','실패 주기 (ps)','실패 slack (ps)','통과 주기 (ps)','통과 slack (ps)','통과점 주파수 (MHz)'],
      sweep_evidence,[2.7,2.4,2.8,2.4,2.8,3.0],size=8.5,
      note="통과점 주파수는 스윕한 주기 중 STA를 통과한 값이다.")
para(doc, "Top-2 Finder 개선 후 AdaPath_A의 Fmax는 판단 회로가 없는 Baseline_A와 두 조건 모두에서 거의 같다(SDC 규칙 %s vs %s MHz, "
     "가중치 정적 %s vs %s MHz). 따라서 측정한 조건에서는 판단 회로에 의한 뚜렷한 주파수 저하가 관측되지 않았다. Reference 대비 SDC 규칙 기준 %.1f %%, 가중치 "
     "정적 기준 %.1f %% 낮은데, 이는 판단 회로가 아니라 본 팀 데이터패스(Conv2 가중치 입력 경로, FC 및 FSM 제어 경로)에서 "
     "결정된다. 판단 및 제어 회로(Top-2, "
     "Margin, Decoder, FSM) 단독 합성 면적은 %s µm²로, AdaPath_A 통합 합성 면적의 %.2f %%에 해당한다(단독 합성과 통합 "
     "합성의 최적화 차이가 있어 참고치)."
     % (f1(FMAX["adapath_A"]), f1(FMAX["baseline_A"]), f1(FMAX_S["adapath_A"]), f1(FMAX_S["baseline_A"]),
        -pct(FMAX["adapath_A"], FMAX["refchip"]), -pct(FMAX_S["adapath_A"], FMAX_S["refchip"]),
        f1(rg["area_v2"]), region2_ratio), indent=True)
_dA_base = A["baseline_A"] - A["refchip"]; _dA_ada = A["adapath_A"] - A["baseline_A"]; _dA_tot = A["adapath_A"] - A["refchip"]
_ADP = {k: A[k] * L for k, L in (("refchip", LAT["ref"]), ("adapath_A", LAT["A"]))}
para(doc, "**면적 증가의 구성:** AdaPath_A의 면적 증가(Reference 대비 %s µm², %s)를 단계별로 나누면, ^^%.0f %%는 본 팀 "
     "데이터패스에서, %.0f %%만 적응형 경로 추가에서 발생^^하였다(표 @t_area@). 본 팀 데이터패스는 Conv1의 75개 MAC을 병렬로 "
     "처리하는 스트리밍 구조로, 이 병렬 연산기가 조합 논리 면적 증가의 대부분을 차지하며 그 대가로 Baseline_A의 처리 cycle을 "
     "%.1f %% 줄였다. 적응형 경로(Early Classifier, 판단 및 제어 회로)의 추가분은 %s µm²이고, 그중 판단 회로는 %s µm²(%.2f %%)에 "
     "불과하다. 순차 소자는 세 설계 모두 전체 면적의 5~8 %%로, 면적은 레지스터가 아니라 연산 병렬도가 결정한다. ^^면적과 추론 지연의 "
     "곱은 Reference와 %.1f %% 차이에 그쳐^^, 늘어난 면적이 대부분 처리 속도로 전환되었다."
     % (f0(_dA_tot), chg(A["adapath_A"], A["refchip"]), _dA_base / _dA_tot * 100, _dA_ada / _dA_tot * 100,
        -pct(CYC["base"], CYC["ref"]), f0(_dA_ada), f1(rg["area_v2"]), region2_ratio,
        pct(_ADP["adapath_A"], _ADP["refchip"])), indent=True)
table(doc, "면적 구성과 단계별 증가분 (합성 직후, µm²)", ["구분", "Reference", "Baseline_A", "AdaPath_A"], [
    ["조합 논리", f0(A["refchip"] - SEQ_AREA["refchip"]), f0(A["baseline_A"] - SEQ_AREA["baseline_A"]),
     f0(A["adapath_A"] - SEQ_AREA["adapath_A"])],
    ["순차 소자 (비율)", "%s (%.1f %%)" % (f0(SEQ_AREA["refchip"]), SEQ_AREA["refchip"] / A["refchip"] * 100),
     "%s (%.1f %%)" % (f0(SEQ_AREA["baseline_A"]), SEQ_AREA["baseline_A"] / A["baseline_A"] * 100),
     "%s (%.1f %%)" % (f0(SEQ_AREA["adapath_A"]), SEQ_AREA["adapath_A"] / A["adapath_A"] * 100)],
    ["**합계**", f0(A["refchip"]), f0(A["baseline_A"]), "**%s**" % f0(A["adapath_A"])],
    ["직전 단계 대비 증가", "-", "+%s (병렬 데이터패스)" % f0(_dA_base), "+%s (적응형 경로)" % f0(_dA_ada)],
    ["평균 처리 cycle", f0(CYC["ref"]), f0(CYC["base"]), f1(CYC_A)],
], [4.2, 3.6, 4.6, 4.6], hl_rows=(2,),
    note="순차 소자 면적은 각 설계의 Yosys 합성 통계(synth_stat)에서 읽은 값이다.")
para(doc, "**배치와 전역 배선 이후 결과:** 위 값은 합성 직후의 추정이므로, Reference와 AdaPath_A를 같은 SDC 규칙과 2 ns 클럭 "
     "제약으로 ORFS 전체 흐름에 넣어 배치, 클럭 트리 합성(CTS), 전역 배선까지 수행하였다(표 %s). 상세 배선은 작업 PC의 "
     "메모리 한도(10 GB)로 두 설계 모두 끝내지 못했으므로, 값은 전역 배선 기반 기생 성분과 실제 클럭 트리를 반영한 결과이다. "
     "면적은 Reference보다 %.1f %% 커서 합성 직후(%.1f %%)와 거의 같았다. 반면 환산 Fmax는 Reference %s MHz, AdaPath_A %s MHz로 차이가 %.1f %%로 "
     "커졌다. AdaPath_A의 임계 경로는 FSM 상태 레지스터에서 Conv2 MAC 레지스터들로 퍼지는 enable 신호로, 신호 하나가 많은 "
     "레지스터를 구동하면서 배선 지연이 커진 것이다. Top-2 Finder를 포함한 판단 회로는 임계 경로가 아니었다. 이 Fmax로 환산한 "
     "추론 지연은 Reference %s ns, AdaPath_A %s ns로 AdaPath_A가 여전히 %.1f %% 짧다. FSM enable 신호를 복제하거나 한 단 파이프라인하면 이 경로를 "
     "줄일 수 있다(4.2절)."
     % (LBL["t_pl"], pct(PL["adapath_A"]["area"], PL["refchip"]["area"]), pct(A["adapath_A"], A["refchip"]),
        f1(PL["refchip"]["fmax"]), f1(PL["adapath_A"]["fmax"]), -pct(PL["adapath_A"]["fmax"], PL["refchip"]["fmax"]),
        f0(PL_LAT["ref"]), f0(PL_LAT["A"]), -pct(PL_LAT["A"], PL_LAT["ref"])), indent=True)
table(doc, "배치 및 전역 배선 후 비교 (ORFS, ASAP7, 2,000 ps 제약, 상세 배선 전)",
      ["항목", "Reference", "AdaPath_A", "변화"], [
    ["표준셀 면적 (µm²)", f0(PL["refchip"]["area"]), f0(PL["adapath_A"]["area"]), chg(PL["adapath_A"]["area"], PL["refchip"]["area"])],
    ["2,000 ps에서 최악 setup slack (ps)", "+%.1f" % PL["refchip"]["slack"], "+%.1f" % PL["adapath_A"]["slack"], "-"],
    ["클럭 skew (ps)", "%.1f" % PL["refchip"]["skew"], "%.1f" % PL["adapath_A"]["skew"], "-"],
    ["환산 Fmax (MHz)", f1(PL["refchip"]["fmax"]), f1(PL["adapath_A"]["fmax"]), chg(PL["adapath_A"]["fmax"], PL["refchip"]["fmax"])],
    ["추론 지연 @환산 Fmax (ns)", f0(PL_LAT["ref"]), f0(PL_LAT["A"]), chg(PL_LAT["A"], PL_LAT["ref"])],
], [5.6, 3.3, 3.3, 3.6], hl_rows=(4,),
    note="두 설계의 임계 경로가 모두 레지스터 간 경로이므로 최소 주기 = 2,000 ps − slack으로 환산하였다. 2 ns 목표로 최적화한 "
         "배치 결과의 환산값이며, hold 위반은 없었다. 원시 리포트는 orfs/reports_postlayout/에 있다.")

h2(doc, "3.7 게이트레벨 VCD 기반 전력 및 추론당 에너지")
para(doc, "벡터 없는(vectorless) 전력 추정은 기본 또는 지정 활동률을 적용하므로 입력별 모드 활성 패턴을 충분히 반영하지 "
     "못한다. 따라서 합성 넷리스트를 ASAP7 셀 모델로 게이트레벨 시뮬레이션(Icarus Verilog, 100 MHz)하여 스위칭 파형(VCD)을 "
     "추출하고, OpenSTA(read_vcd)로 평균 전력을 계산하였다. 한 런의 에너지는 E_run = P_avg × (t_end − t_start), 추론당 평균 "
     "에너지는 E_inf = E_run / N이며, 측정 창에는 이미지마다 12 cycle의 리셋 구간이 포함된다. 모드별 에너지는 Easy 4장 런"
     "(이미지 1~4)과 Hard 1장+Easy 3장 런(이미지 5~8)의 차감으로 분리하였다(모델 B의 Medium은 이미지 15~18 런 사용). "
     "Reference는 같은 이미지 12장, Baseline_A는 4장의 평균이다. 따라서 모드별 값은 소수 대표 런 기반 추정이며, 서로 다른 "
     "Easy 이미지의 에너지가 같다는 근사를 포함한다.", indent=True)
table(doc, "모드별 추론당 에너지 (게이트레벨 VCD 기반 추정, 100 MHz)", ["설계 / 모드", "에너지 (nJ)", "Reference 대비"], [
    ["Reference (전체 경로)", f1(E_REF), "-"],
    ["Baseline_A (항상 Hard)", f1(E_ABASE), chg(E_ABASE, E_REF)],
    ["AdaPath_A — Easy", f1(E["A_easy"]), chg(E["A_easy"], E_REF)],
    ["AdaPath_A — Hard", f1(E["A_hard"]), chg(E["A_hard"], E_REF)],
    ["AdaPath_A 가중 평균 (Easy / Hard = %.0f / %.0f %%)" % (MODE["A"]["easy"] * 100, MODE["A"]["hard"] * 100),
     "**%s**" % f1(E_A), "**%s**" % chg(E_A, E_REF)],
    ["AdaPath_B 가중 평균 (확장 모델)", f1(E_B), chg(E_B, E_REF)],
], [7.4, 3.6, 4.0], hl_rows=(4,))
figure(doc, os.path.join(OUT, "fig_final_compare.png"),
       "정확도 동일(970/1,000) 조건에서 Reference 대비 처리 cycle, 지연, 에너지, MAC, 면적 (Reference = 1.0)", 15.0)
para(doc, "에너지 결과는 두 단계로 해석된다. 본 팀 데이터패스(Baseline_A)는 처리 cycle을 %.0f %% 줄였지만 Feature Map Buffer 등 "
     "레지스터가 늘어 추론당 에너지는 Reference보다 %.1f %% 많았다. 여기에 AdaPath 적응 경로가 같은 데이터패스 대비 에너지를 "
     "%.1f %% 줄여, 최종적으로 Reference 대비 %.1f %%의 에너지 감소를 얻었다. 두 감소율은 비교 분모가 다르므로 합산하지 "
     "않는다. 또한 AdaPath_A는 Reference 대비 평균 실행 MAC을 %.1f %% 줄이지만 에너지 감소율은 이보다 작으며, 그 차이는 "
     "특징 저장과 Early Classifier, 제어 회로 및 순차 소자의 전력 때문이다. 셀 면적은 %.1f %% 증가하므로, 본 결과는 면적을 "
     "추가로 사용하여 추론 지연과 에너지를 줄인 동작점으로 해석한다."
     % (-pct(CYC["base"], CYC["ref"]), pct(E_ABASE, E_REF), -pct(E_A, E_ABASE), -pct(E_A, E_REF),
        -pct(MAC_A, MAC["ref"]), pct(A["adapath_A"], A["refchip"])), indent=True)
pw = R["power_split"]
EZ, HD, BS = BE["AdaPath_A Easy"], BE["AdaPath_A Hard"], BE["Baseline_A"]
IDLE = sum(EZ.get(b, 0) for b in ("Conv2", "Pool2", "FC (Full)", "Light FC"))
E_EZ_CG = E["A_easy"] - IDLE
E_A_CG = MODE["A"]["easy"] * E_EZ_CG + MODE["A"]["hard"] * E["A_hard"]
para(doc, "에너지가 어디서 소모되는지 확인하기 위해 셀 단위 전력을 블록별로 합산하였다(그림 @f_block@). 합성 과정에서 이름이 유지되는 "
     "레지스터는 소속 블록으로, 이름이 없는 조합 논리는 하나의 항목으로 집계하였다. 세 가지가 확인된다. ① 연산 생략 효과는 "
     "조합 논리에서 뚜렷하다. Easy에서 조합 논리 에너지는 %.2f nJ로 Baseline_A(%.2f nJ)의 절반 이하이다. ② 반면 Easy에서도 "
     "Conv2, Pool2, FC의 레지스터는 연산 없이 클럭만 공급받으며 ^^%.2f nJ(Easy 에너지의 %.0f %%)^^를 소모한다. ③ Feature Map "
     "Buffer(5,184 bit 레지스터)는 Easy에서 %.2f nJ(%.0f %%)로 가장 큰 단일 블록이다. 이 분석은 CTS 이전이라 클럭망 전력이 "
     "포함되지 않았으며(Easy 런에서 순차 소자 비중 %.0f %%), 배치와 배선 이후 다시 평가해야 한다."
     % (EZ["조합 논리 (블록 미분류)"], BS["조합 논리 (블록 미분류)"], IDLE, IDLE / E["A_easy"] * 100,
        EZ["Feature Map Buffer"], EZ["Feature Map Buffer"] / E["A_easy"] * 100, pw["A_easy_seq_pct"]), indent=True)
figure(doc, os.path.join(OUT, "fig_block_energy.png"),
       "블록별 추론당 에너지 (게이트레벨 VCD 기반 추정, 100 MHz; Reference는 이미지 1~4 런, Hard는 런 차감 추정)", 16.5)
para(doc, "②의 유휴 에너지는 Easy 판정 시 후단부 레지스터의 클럭을 차단하는 클럭 게이팅의 직접적인 대상이다. 이 에너지를 모두 "
     "제거할 수 있다고 가정한 상한 추정에서 Easy 에너지는 %.1f nJ, 가중 평균은 %.1f nJ로 Reference 대비 %s한다. 이는 다른 "
     "에너지 항목을 고정하고 해당 유휴 에너지만 제거한 이상적 계산값이며, ICG와 게이팅 제어의 오버헤드는 포함하지 않았다. 실제 "
     "구현에서는 합성 매핑과 게이팅 범위도 달라질 수 있으므로, 뒤의 구현 평가 결과와 구분한다."
     % (E_EZ_CG, E_A_CG, chg(E_A_CG, E_REF)), indent=True)
para(doc, "**전용 ICG 적용 후 배치 전 전력 평가:** 이 상한 추정을 실제 회로로 확인하기 위해, 모델 A의 후단 Conv2, Pooling, FC "
     "레지스터에 ASAP7 전용 ICG 셀(ICGx1_ASAP7_75t_R)을 넣은 설계를 따로 합성하여 게이팅 전 설계와 비교하였다(표 %(t_icg)s). "
     "두 설계 모두 같은 흐름, ASAP7 RVT TT, 100 MHz에서 합성 넷리스트에 같은 버퍼 셀과 최대 분기 수 4의 클럭 트리를 구성하여 "
     "ICG와 버퍼의 부하 비용을 포함하였다. Easy 4장 구간의 이미지당 에너지는 25.9 %%, Easy 3장과 Hard 1장의 혼합 구간은 "
     "25.2 %%, Hard 4장 구간은 20.7 %% 줄었다. Hard에서도 후단부가 매 cycle 동작하는 것은 아니므로 게이팅 효과가 나타난다. "
     "ICG를 넣은 RTL은 1,000회 순차 입력에서 기존 설계와 판정, 모드, margin, cycle이 모두 같았고(970 / 1,000), 버퍼를 포함한 "
     "최종 넷리스트의 24회 실행 출력도 기존 RTL과 일치하였다. 다만 이 비교는 배치와 배선의 기생 성분을 포함하지 않는 배치 전 "
     "추정이고, 11개 고유 입력으로 구성한 세 구간의 결과이며, 별도 합성에 따른 조합 논리 매핑 차이도 포함한다. 같은 조건의 "
     "Reference 재측정은 하지 않았으므로 이 감소율을 Reference 대비 개선율과 결합하지 않는다." % LBL,
     indent=True)
table(doc, "전용 ICG 적용 전후의 구간별 배치 전 전력과 에너지 (AdaPath_A, ASAP7 RVT TT, 100 MHz)",
      ["측정 구간 (4회 추론)", "게이팅 전 (mW)", "ICG 적용 (mW)", "게이팅 전 (nJ/장)", "ICG 적용 (nJ/장)", "감소율"], [
    ["Easy 4장", "2.616", "1.938", "22.44", "16.63", "25.9 %"],
    ["Easy 3장 + Hard 1장", "2.759", "2.064", "24.85", "18.59", "25.2 %"],
    ["Hard 4장", "2.917", "2.312", "30.01", "23.79", "20.7 %"],
], [4.0, 2.6, 2.6, 2.8, 2.8, 2.0],
    note="두 설계 모두 같은 팬아웃 제한 버퍼 클럭 트리를 넣은 값이라, 버퍼가 없는 3.7절 앞부분의 블록별 에너지와 절대값이 다르다. "
         "에너지는 VCD 구간 평균 전력 × 관측 시간 ÷ 4(reset과 start 포함)이다.")
figure(doc, os.path.join(OUT, "hs_fig_icg_energy.png"),
       "전용 ICG 적용 전후의 구간별 추론당 에너지 (AdaPath_A, ASAP7 RVT TT, 100 MHz, 배치 전 VCD 기반 추정)", 13.0)
expansion_p = para(doc, "같은 조건에서 고유 입력 40개로 평가 범위를 확장하였다. Easy 36장은 4장씩 9개 구간으로 구성하고, "
     "Hard는 기존과 같은 4장 1구간의 결과를 사용하였다. Easy 이미지당 에너지가 22.50 nJ에서 16.68 nJ로 평균 25.9 % 감소하였다. "
     "게이팅 전후 표준편차는 모두 약 0.15 nJ이며, 이는 9개 구간 평균의 표준편차(n = 9)로 개별 이미지의 편차가 아니다. "
     "모델 A에서 Hard 비율은 4 %이며, Hard는 여전히 4장 1구간으로 표본이 적다. 본 결과는 배치 전 활동도 기반 추정이며 "
     "Reference 대비 개선율과 결합하지 않는다.", indent=True)
# Keep the expansion evidence clear of the footer and together on a fresh page.
expansion_p.paragraph_format.page_break_before = True
expansion_p.paragraph_format.keep_together = True
para(doc, "**임계값별 정확도와 에너지의 계산 모델:** 임계값 선택에 따른 정확도와 에너지의 상충 관계를 살펴보기 위해, 3.5.6절 RTL "
     "스윕의 정답 수와 모드 비율에 위의 TH = 63 표본(Easy 36장, Hard 4장)에서 얻은 모드별 에너지를 가중한 모델을 만들었다"
     "(그림 @f_pareto@). 즉 E(TH) = p_Easy(TH) × E_Easy + p_Hard(TH) × E_Hard이며, ^^각 임계값의 전력을 직접 시뮬레이션한 값이 아니다^^. "
     "이 모델에서 TH = 0, 10, 20, 30은 정답 980개와 게이팅 적용 추정 에너지 16.68 nJ/장으로 같은 비지배점에 위치하였고, 선정 "
     "동작점 TH = 63은 정답 970개와 16.97 nJ/장이었다. 따라서 본 평가 입력과 고정 모드 에너지 모델에서는 TH = 63을 최적 임계값으로 "
     "해석할 수 없다. 다만 임계값이 바뀌면 각 모드에 속하는 입력 구성도 바뀌므로(예: TH = 400의 Hard 730장을 TH = 63의 Hard 4장 "
     "평균으로 대표) 이 가정은 직접 검증되지 않았고, 같은 평가 입력으로 사후 선정한 결과는 독립 검증이 아니다. 입력도 고유 100장의 "
     "반복이다. 이 때문에 별도 검증 집합과 임계값별 활동도 분석 없이 설계 동작점을 변경하지 않았다.", indent=True)
figure(doc, os.path.join(OUT, "hs_fig_pareto.png"),
       "모델 A의 임계값별 정확도와 추정 에너지 (정확도는 1,000회 입력의 RTL 스윕, 에너지는 TH = 63의 모드별 VCD 기반 추정에 모드 비율을 가중한 계산값). "
       "별표는 선정값 TH = 63, TH = 0, 10, 20, 30은 서로 겹치는 비지배점이다.", 15.0)
table(doc, "효율 지표", ["설계", "실행 MAC", "에너지 (nJ)", "실효 TOPS/W", "등가 TOPS/W"], [
    ["Reference", f0(MAC["ref"]), f1(E_REF), f2(topsw(MAC["ref"], E_REF)), f2(topsw(MAC["ref"], E_REF))],
    ["Baseline_A", f0(MAC["Abase"]), f1(E_ABASE), f2(topsw(MAC["Abase"], E_ABASE)), f2(topsw(MAC["ref"], E_ABASE))],
    ["**AdaPath_A**", f0(MAC_A), f1(E_A), f2(topsw(MAC_A, E_A)), "**%s**" % f2(topsw(MAC["ref"], E_A))],
], [3.4, 3.2, 3.0, 3.2, 3.2], hl_rows=(2,),
    note="1 MAC = 2 operations. 실효 TOPS/W = 2 × 실행 MAC / 추론당 에너지. 등가 TOPS/W = 2 × Reference MAC(%s) / 추론당 "
         "에너지로, 같은 분류 작업을 완료하는 효율이다. 본 측정에서는 실행 MAC 감소율이 에너지 감소율보다 커서 AdaPath_A의 "
         "실효 지표가 낮아졌으므로, 두 지표를 평균 에너지 및 정확도와 함께 제시한다." % f0(MAC["ref"]))
para(doc, "모드별 에너지를 고정한 혼합 모델로 입력 분포에 따른 에너지 이득 조건을 분석하였다(그림 @f_breakeven@). Easy 비율을 p라 하면 "
     "모델 A의 평균 에너지는 E_A(p) = %.2f − %.2f×p nJ이다. 이 모델에서 Reference 대비 에너지 이득은 Easy 비율이 약 "
     "^^%.1f %%를 넘을 때^^ 발생하고, Baseline_A 대비 손익분기점은 약 %.1f %%이다. 반면 Baseline_A 대비 처리 cycle의 "
     "손익분기점은 약 %.1f %%이므로, Easy 비율 %.0f~%.0f %% 구간에서는 처리 cycle이 줄어도 에너지는 늘어날 수 있다. 즉 "
     "처리 cycle이나 MAC 감소만으로 에너지 이득을 보장할 수 없음을 정량적으로 보여준다. 이 분석은 소수 대표 입력에서 "
     "유도한 모드별 에너지를 사용한 추정이며, 입력 분포가 바뀔 때의 모드별 에너지와 정확도 변화는 별도 검증이 필요하다."
     % (E["A_hard"], E["A_hard"] - E["A_easy"], P_BE_REF * 100, P_BE_BASE * 100, P_BE_CYC * 100,
        P_BE_CYC * 100, P_BE_BASE * 100), indent=True)
figure(doc, os.path.join(OUT, "fig_energy_breakeven.png"),
       "모드별 에너지 고정 가정에서의 AdaPath_A 에너지 손익분기점 (기존 결과를 이용한 계산 모델)", 16.5)

h2(doc, "3.8 Medium 경로의 기여 분리")
para(doc, "Medium 경로의 순수 기여를 분리하기 위해, 같은 Early Classifier와 Score Margin을 쓰되 Medium이 없는 Early-Exit"
     "(2경로)와 AdaPath(3경로)를 임계값 전수 탐색으로 비교하였다(같은 정확도 제약에서의 최소 평균 MAC).", indent=True)
iso = R["iso"]
table(doc, "Early-Exit 대비 AdaPath(Medium 추가)의 이득", ["조건", "MNIST (모델 B)", "WM-811K (모델 B)"], [
    ["같은 정확도 제약에서 추가 MAC 절감", iso["mn_gain"], iso["wm_gain"]],
    ["동일 MAC에서 정확도 향상 (공격적 절감 구간)", iso["mn_acc"], iso["wm_acc"]],
    ["Baseline 정확도 근처", "차이 없음", "거의 차이 없음"],
    ["모델 A (Conv2 3채널)", "Medium 미선택 (2경로로 수렴)", "-"],
], [6.0, 5.5, 5.5])
figure(doc, os.path.join(OUT, "fig_iso_accuracy_mnist.png"), "Pareto front 비교: Early-Exit vs AdaPath (MNIST, 모델 B)", 13.0)
figure(doc, os.path.join(OUT, "fig_iso_accuracy_wm811k.png"), "Pareto front 비교: Early-Exit vs AdaPath (WM-811K)", 13.0)
para(doc, "평가한 조건에서 Medium 경로의 추가 MAC 절감은 MNIST 모델 B에서 0~2.2 %, WM에서 2~3 %였으며, Baseline 정확도 "
     "근처에서는 이득이 작았다. ^^Medium은 공격적으로 연산을 줄이는 동작점에서 효과가 크며^^, 임계값 탐색은 Medium이 "
     "불리한 경우 이를 사용하지 않는 동작점(모델 A)도 선택할 수 있다.", indent=True)

para(doc, "Medium 경로의 하드웨어 동작을 추가 확인하기 위해 현재 RTL과 모델 B 가중치로 기존 "
     "tb_adapath를 다시 실행하였다. Easy/Hard/Medium 각 3개 입력을 포함하는 9개 사례 모두 margin, mode, decision이 "
     "정수 Golden과 일치하였다. Medium BACK 구간 총 513 cycle에서 ch_en=0x0F, fc_light_en=1, fc_full_en=0의 "
     "관찰 위반은 0회였다. 이는 대표 사례의 동작 검증이며 전체 입력 공간에 대한 형식 검증은 아니다.", indent=True)
figure(doc, os.path.join(OUT, "fig_medium_verified.png"),
       "모델 B Medium 경로의 실제 VCD 파형. 현재 RTL의 Icarus 재실행에서 추출한 신호를 시각화하였으며 EDA 도구 화면 캡처는 아니다.", 17.0)
h2(doc, "3.9 자유주제: WM-811K 웨이퍼맵 결함 분류 적용")
para(doc, "반도체 제조 공정의 웨이퍼맵 결함 패턴(WM-811K, 811,457장 중 라벨 172,950장)에서 정상(none), Center, Edge-Ring, "
     "Scratch 4개 클래스를 클래스당 같은 개수(가장 적은 Scratch 기준 약 1,190장)로 균형 추출하고, 웨이퍼 맵(웨이퍼 밖 / 정상 "
     "die / 불량 die)을 28×28로 리사이즈한 뒤 8:2로 학습과 테스트를 나누었다. 모델 B 구조(4개 클래스 출력)에 같은 AdaPath "
     "기법을 적용하였으며, 데이터 준비, 학습, 정수화, RTL 생성은 MNIST와 동일한 코드로 수행하였다. 선정 동작점은 정확도 "
     "0.31 %p 하락을 수용하고 연산량을 줄인 지점이다.", indent=True)
table(doc, "WM-811K 적용 전후 비교 (Baseline_WM = 항상 Hard)", ["항목", "Baseline_WM", "AdaPath_WM", "변화"], [
    ["정확도 (테스트 %d장, float)" % WM["n_test"], "%.2f %%" % WM["acc_base"], "%.2f %%" % WM["acc_ada"],
     "%.2f %%p 하락" % (WM["acc_base"] - WM["acc_ada"])],
    ["모드 개수 (Easy / Medium / Hard)", "0 / 0 / %d" % WM["n_test"], WM["mode_str"], "-"],
    ["평균 MAC / 이미지", f0(WM["mac_base"]), f0(WM["mac_ada"]), chg(WM["mac_ada"], WM["mac_base"])],
    ["Cell Area (µm²)", f0(A["baseline_wm"]), f0(A["adapath_wm"]), chg(A["adapath_wm"], A["baseline_wm"])],
    ["추정 Fmax (MHz)", f1(FMAX["baseline_wm"]), f1(FMAX["adapath_wm"]), "-"],
    ["**추론당 에너지 (nJ, 동일 입력 가중 추정)**", f1(E_WM_BASE_D), "**%s**" % f1(E_WM_D), chg(E_WM_D, E_WM_BASE_D)],
], [5.0, 3.4, 4.6, 3.0], hl_rows=(5,),
    note="WM 에너지는 동일 입력 12개에 대한 배치 전 VCD 기반 추정으로, 모드별 4장 구간 에너지에 "
         "RTL 모드 비율 404 / 167 / 383을 두 설계 모두 동일하게 적용하였다(표 @t_wmpaired@). 954장 전체 전력 측정값이 아니다. 정확도 및 MAC 행의 float 평가와 에너지 행의 정수 RTL 평가는 구분한다.")
table(doc, "WM 동일 입력의 구간별 전력 및 에너지 (100 MHz, 배치 전 추정)",
      ["구간", "Baseline\n전력 (mW)", "AdaPath\n전력 (mW)", "Baseline\n에너지 (nJ/장)",
       "AdaPath\n에너지 (nJ/장)", "에너지 감소율"],
      WM_PAIRED_ROWS + [
          ["12장 균등 평균", "-", "-", "%.2f" % float(WMP["balanced_12_sample"]["baseline_energy_nJ"]),
           "%.2f" % float(WMP["balanced_12_sample"]["adapath_energy_nJ"]),
           "%.2f %%" % float(WMP["balanced_12_sample"]["energy_reduction_pct"])],
          ["RTL 모드 비율 가중", "-", "-", "%.2f" % E_WM_BASE_D, "%.2f" % E_WM_D,
           "%.2f %%" % float(WMP["rtl_mode_weighted_estimate"]["energy_reduction_pct"])],
      ], [3.0, 2.4, 2.4, 3.0, 3.0, 2.2], hl_rows=(4,),
      note="각 모드에서 선택한 동일 4장을 양쪽 설계에 적용하였다. 에너지는 reset과 start를 포함한 4장 관측창의 평균 전력과 "
           "시간으로부터 P×T/4로 계산하였다. 음의 감소율은 증가를 뜻한다. 구간 평균이며 이미지별 표준편차를 나타내지 않는다.")
para(doc, "입력 구성에 따른 활동도 차이를 통제하기 위해 Easy [8, 10, 18, 22], Medium [2, 3, 5, 24], Hard [0, 1, 4, 9]의 "
     "같은 입력을 두 설계에 적용하였다. 픽셀 내용 기준으로도 고유 12종임을 확인하였다. 각 모드에서 AdaPath가 정답을 출력한 앞쪽 "
     "4장을 선택하였으므로 무작위 표본이 아니며 선택 편향이 남는다. Easy 에너지는 29.4 % 감소했으나 Medium은 0.6 %, Hard는 "
     "14.3 % 증가하였다. Medium의 평균 전력은 1.9 % 감소했지만 관측 시간이 길어져 에너지 감소로 이어지지 않았다. "
     "선택 12장의 균등 평균은 4.9 % 감소하였으며, ^^양쪽에 같은 RTL 모드 비율을 적용한 에너지 감소율은 6.7 %이다^^. "
     "이는 모드별 4장에 기초한 추정으로 전체 954장에 대한 전력 측정이나 모집단 일반화를 의미하지 않는다.", indent=True)
para(doc, "두 설계는 공통 10 ns 클럭과 이미지마다 12클럭 reset 조건을 사용하였다. 4장 관측창은 AdaPath Easy 34.076 µs, "
     "Medium/Hard 40.676 µs, Baseline 39.676 µs였으며 reset과 start 오버헤드가 포함된다. 별도로 기록한 이미지당 처리 cycle은 "
     "AdaPath Easy 839, Medium/Hard 1,004, Baseline 979였다. AdaPath 12회의 판정, 모드 및 margin과 "
     "Baseline 12회의 Full 판정은 각각의 정수 Golden과 일치하였다. 기존 8.8 %는 다른 입력인 Baseline 0~3번의 구간 평균을 "
     "공통 기준으로 사용한 결과였으며, 본문에서는 동일 입력 비교로 갱신하였다. 원시 근거는 results_hs/wm_paired_power/에 "
     "보존하였다. 지연 0 기능 모델과 배치 전 분석이므로 배선 기생 성분과 CTS가 포함되지 않으며 setup/hold 및 Fmax 검증을 "
     "대신하지 않는다.", indent=True)
h3(doc, "3.9.1 RTL 검증 (Vivado)")
para(doc, "자유주제 설계도 지정주제와 같은 chip 인터페이스 래퍼(클래스 수만 4로 설정)로 Vivado 프로젝트를 "
     "구성하고, 주최 측 TB와 같은 방식(이미지마다 리셋 후 1 px/cycle 스트리밍)으로 WM-811K 테스트 954장을 처리하였다(표 @t_wmrtl@). "
     "판정, 모드, Score Margin이 정수 Golden과 954장 모두 비트 단위로 일치하였고, 정확도는 774 / 954 = 81.13 %% (정수 Hard 경로 "
     "단독 81.45 %%)였다. 모드는 Easy 404 / Medium 167 / Hard 383장으로, ^^3경로가 모두 하드웨어에서 실제로 사용^^되었다(MNIST "
     "모델 A는 2경로). 정수 임계값(13 / 41) 기준이라 float 분석의 모드 비율(401 / 152 / 401)과 약간 다르며, 이 RTL 모드 비율을 "
     "WM 게이트레벨 에너지 가중에 사용하였다. 제출용 프로젝트(PPA_AdaPath_NPU_WM)는 다른 폴더로 옮겨 실행해도 같은 결과를 "
     "얻었다." % LBL, indent=True)
table(doc, "WM-811K RTL 검증 결과 (Vivado 2023.1, 정수 연산, 테스트 954장)", ["클래스", "n", "AdaPath RTL recall", "정수 Hard 경로 recall"], [
    ["none (정상)", "245", "179 (73.1 %)", "182 (74.3 %)"],
    ["Center", "251", "238 (94.8 %)", "235 (93.6 %)"],
    ["Edge-Ring", "230", "216 (93.9 %)", "215 (93.5 %)"],
    ["Scratch", "228", "141 (61.8 %)", "145 (63.6 %)"],
    ["**전체**", "954", "**774 (81.13 %)**", "777 (81.45 %)"],
], [3.4, 1.6, 4.4, 4.4], hl_rows=(4,),
    note="AdaPath RTL은 Golden 판정과 954 / 954 일치. 모드 Easy / Medium / Hard = 404 / 167 / 383 (정수 임계값 13 / 41).")
h3(doc, "3.9.2 경로별 동작 파형과 제어 조건 검증 (Vivado)")
para(doc, "세 경로가 하드웨어에서 실제로 다르게 동작하는지 같은 Vivado 프로젝트의 파형으로 확인하였다(그림 @f_wmpaths@). "
     "WM-811K 테스트 처음 7장은 Hard, Hard, Medium, Medium, Hard, Medium, Easy 순으로 판정되었다. Hard에서는 Conv2 8채널 전체"
     "(ch_en = 0xFF)와 Full FC가, Medium에서는 하위 4채널(0x0F)과 Light FC가 켜졌다. Easy(Score Margin 68)에서는 Conv2와 "
     "후단 Light/Full FC를 비활성화하고 Early 점수로 출력하였다. 관측기의 start→valid 상승 에지 간격은 Easy 839 cycle, "
     "Medium과 Hard 각각 1,004 cycle이었다(WM_transactions.csv). ^^Medium은 Hard와 같은 응답 cycle 수를 "
     "사용하면서 후단부 활성 채널과 FC 연산량을 줄인다^^.", indent=True)
para(doc, "동일한 관측기 정의로 집계한 WM 954장의 평균은 %.2f cycle이었다((404 × 839 + 550 × 1,004) / 954). "
     "" % WM_OBS_AVG_CYC, indent=True)
figure(doc, os.path.join(OUT, "fig_vivado_wm_paths.png"),
       "Vivado 파형 (WM-811K): 처음 7개 입력의 경로별 후단부 enable과 Easy 출력 구간 확대. "
       "10 ns 클럭의 기능 시뮬레이션이다.", 17.0)
para(doc, "실제 제출용 WM 프로젝트의 세 번째 입력(index 2)을 Vivado 2024.1에서 관측한 결과, 정수 Score Margin은 16으로 "
     "13 ≤ margin < 41을 만족하여 mode = 1(Medium)이 선택되었다(그림 @f_wm_medium@). 후단 활성 구간 "
     "28.605~30.255 µs에서 ch_en = 0x0F, Conv2 및 Light FC 활성, Full FC 비활성이 확인되었다. 이후 "
     "원시 VCD의 30.265~30.275 µs 구간에서 valid_out_6 = 1과 decision = 0이 관측되어 정답 및 Golden과 일치하였다. "
     "출력 이후의 mode = 2는 다음 입력을 위한 리셋 기본값이다.", indent=True)
figure(doc, os.path.join(OUT, "fig_vivado_wm_medium.png"),
       "Vivado 파형 확대 (WM-811K 세 번째 입력, Medium 후단 활성 구간): margin 16, mode 1, ch_en 0x0F, "
       "fc_light_en 1, fc_full_en 0. 유효 출력 펄스는 이 캡처 이후이며 원시 VCD에서 별도로 확인하였다.", width=14.0)
para(doc, "단일 파형 이외의 입력에 대한 제어 조건 검사 결과는 표 @t_control@에 제시하였다. WM Medium 167장의 "
     "27,555개 활성 cycle을 포함하여 검사된 조건의 위반은 0건이었다. 모델 A의 Medium 미실행, 마지막 start 미평가 및 "
     "초기 X 관측을 포함한 검증 범위와 제한사항은 3.5.5절에 명시하였다.", indent=True)
h3(doc, "3.9.3 클래스별 분석")
para(doc, "전체 평균만으로는 결함 종류별 영향을 알 수 없으므로 클래스별 경로 배분과 정확도를 분석하였다(표 "
     "%(t_wmclass)s, 그림 %(f_wmclass)s). Edge-Ring(84.3 %%)과 Center(77.7 %%)는 대부분 Easy로 조기 종료되며 AdaPath 정확도가 Full보다 "
     "오히려 약간 높았다. 반면 정상(none)은 83.3 %%가 Hard로 갔고, Scratch는 Easy가 4.4 %%에 그치며 recall이 Full 63.6 %%에서 "
     "AdaPath 60.5 %%로 3.1 %%p 낮아졌다. 즉 계산 배분은 패턴의 물리적 복잡성보다 현재 전단 분류기의 구분 능력을 따르며, "
     "'정상은 쉽고 결함은 어렵다'고 단순화할 수 없다. 공정 검사에서는 결함을 정상으로 놓치는 비용이 크므로(결함→정상 오분류: "
     "Full 91건, AdaPath 91건으로 동일), 평균 MAC 최적화와 함께 클래스별 recall 제약을 함께 검토해야 한다. 혼동 행렬은 부록 C에 "
     "수록하였다." % LBL, indent=True)
table(doc, "WM-811K 클래스별 경로 배분과 정확도 (기존 동작점, 테스트 954장, Python float)",
      ["클래스", "n", "Easy / Medium / Hard (%)", "Full recall (%)", "AdaPath recall (%)", "차이 (%p)"], [
    ["none (정상)", "245", "0.8 / 15.9 / 83.3", "74.3", "74.3", "0.0"],
    ["Center", "251", "77.7 / 4.8 / 17.5", "94.0", "94.8", "+0.8"],
    ["Edge-Ring", "230", "84.3 / 10.0 / 5.7", "93.5", "94.3", "+0.9"],
    ["Scratch", "228", "4.4 / 34.2 / 61.4", "63.6", "60.5", "−3.1"],
], [2.8, 1.4, 4.2, 2.8, 3.0, 2.2], hl_rows=(3,))
figure(doc, os.path.join(OUT, "sh2_fig_wm_class_modes.png"),
       "WM-811K 클래스별 경로 배분(Easy/Medium/Hard)과 Full 및 AdaPath recall", 16.0)

h2(doc, "3.10 입력 열화에 따른 적응적 연산 배분 (RTL 실측)")
para(doc, "입력이 어려워질 때 AdaPath가 실제로 후단 연산을 더 많이 사용하는지 확인하기 위해, 주최 측 입력 1,000회에 실제 센서 "
     "환경을 모사한 열화(대비 감소 6단계, 3×3 블러 5단계, 가우시안 잡음 6단계, seed 고정)를 적용하고 모델 A의 AdaPath_A와 "
     "같은 가중치의 항상-Hard 설계(Baseline_A)를 RTL로 각각 실행하였다(총 34회, 그림 %(f_rmodes)s 및 %(f_racc)s). 원본과 "
     "대비 0.3 조건의 기준값을 먼저 재현한 뒤 전체를 실행하였다." % LBL, indent=True)
table(doc, "입력 열화 생성 조건", ["종류", "수준", "변환 및 처리"], [
    ["대비 축소", "1.0, 0.7, 0.5, 0.4, 0.3, 0.2", "픽셀값에 계수 c를 곱함"],
    ["평균 블러", "0, 1, 2, 3, 4회", "영 패딩 3×3 평균 필터를 반복 적용"],
    ["가우시안 잡음", "σ=0, 20, 40, 60, 80, 100", "픽셀 단위 N(0, σ²) 가산, seed=2026"],
], [2.5, 6.4, 7.1], size=9,
    note="변환 후 np.rint로 반올림하고 [0,255]로 포화시켰다. σ는 8-bit 픽셀값 단위이다. "
         "종류별 수준을 나열된 순서로 생성하며 난수 생성기의 상태를 이어 사용하였다.")
figure(doc, os.path.join(OUT, "hs_fig_robustness_modes.png"),
       "입력 열화 강도에 따른 AdaPath_A의 Hard 경로 비율(위)과 평균 처리 cycle(아래) (RTL 실측)", 16.5)
figure(doc, os.path.join(OUT, "hs_fig_robustness_acc.png"),
       "입력 열화 강도에 따른 정확도: AdaPath_A vs Baseline_A (RTL 실측)", 16.5)
para(doc, "세 열화 모두에서 열화가 강해질수록 Hard 비율과 평균 cycle이 증가하였다. 특히 대비를 1.0에서 0.2로 낮추면 Hard 비율이 "
     "4 %%에서 72 %%로 늘어, ^^평가한 열화 수준에 따라 연산을 더 배분하는 동작^^이 RTL에서 확인되었다. 대비 감소에서는 정확도가 "
     "Baseline_A와 같거나 높았다(0.2에서 80.0 %% vs 76.0 %%). 반면 강한 블러(4회, 87.0 %% vs 90.0 %%)와 강한 가우시안 잡음(σ = 100, "
     "74.9 %% vs 83.0 %%)에서는 AdaPath의 정확도가 낮았다. 이 조건에서는 Hard 비율이 36~38 %%에 머물러, 일부 입력이 높은 Score "
     "Margin으로 Easy에서 종료된 것으로 보인다. 열화 입력을 포함한 학습이나 Early Classifier 보정으로 개선할 수 있다(4.2절)." % LBL, indent=True)

para(doc, "대비 0.3에서는 AdaPath_A와 Baseline_A의 정확도가 93.0%로 같고 cycle은 7.62% 감소하였다. "
     "반면 σ=100에서는 7.96%의 cycle 감소와 8.1%p의 정확도 손실이 함께 나타났다. 큰 Score Margin은 "
     "확률로 보정된 신뢰도가 아니므로 ‘Early Classifier가 확신을 갖고 틀리는 경우’가 가능하다. 무열화 입력의 오류 사례는 부록 C에 제시하였다.", indent=True)

# =================================================================== 4
h1(doc, "4. 결과 및 기대효과")
h2(doc, "4.1 결과 요약")
table(doc, "최종 결과 요약 (지정주제: Reference 대비 AdaPath_A)", ["지표", "Reference", "AdaPath_A", "변화"], [
    ["정답 (주최 입력 순차 1,000회)", "970", "970", "유지"],
    ["평균 처리 cycle (순차 입력)", f0(CYC["ref"]), f1(CYC_A), chg(CYC_A, CYC["ref"])],
    ["추정 Fmax (MHz, pre-layout)", f1(FMAX["refchip"]), f1(FMAX["adapath_A"]), chg(FMAX["adapath_A"], FMAX["refchip"])],
    ["추정 Fmax에서의 추론 지연 (ns)", f0(LAT["ref"]), f0(LAT["A"]), chg(LAT["A"], LAT["ref"])],
    ["평균 실행 MAC / 추론", f0(MAC["ref"]), f0(MAC_A), chg(MAC_A, MAC["ref"])],
    ["추론당 에너지 (nJ, VCD 기반 추정)", f1(E_REF), f1(E_A), chg(E_A, E_REF)],
    ["Cell Area (µm²)", f0(A["refchip"]), f0(A["adapath_A"]), chg(A["adapath_A"], A["refchip"])],
    ["등가 TOPS/W (같은 분류 작업 기준)", f2(topsw(MAC["ref"], E_REF)), f2(topsw(MAC["ref"], E_A)),
     chg(topsw(MAC["ref"], E_A), topsw(MAC["ref"], E_REF)).replace("감소", "향상").replace("증가", "향상")],
], [5.4, 3.4, 3.4, 3.8], hl_rows=(1, 3, 5))
_LAT_B = CYC["base"] / FMAX["baseline_A"] * 1e3
table(doc, "단계별 설계 개선 (지정주제, 주최 입력 순차 1,000회)",
      ["단계", "설계 변경", "정답", "평균 cycle", "Fmax (MHz)", "추론 지연 (ns)", "에너지 (nJ)", "면적 (µm²)"], [
    ["① Reference", "주최 측 가속기", "970", f0(CYC["ref"]), f1(FMAX["refchip"]), f0(LAT["ref"]), f1(E_REF), f0(A["refchip"])],
    ["② Baseline_A", "스트리밍 데이터패스 (항상 전체 경로)", "970", f0(CYC["base"]), f1(FMAX["baseline_A"]), f0(_LAT_B),
     f1(E_ABASE), f0(A["baseline_A"])],
    ["**③ AdaPath_A**", "Early Classifier, Score Margin 경로 선택, 토너먼트 Top-2", "970", f1(CYC_A), f1(FMAX["adapath_A"]),
     f0(LAT["A"]), f1(E_A), f0(A["adapath_A"])],
    ["④ + 후단부 ICG", "Easy 판정 시 후단부 클럭 차단", "970", f1(CYC_A), "-", "-", "구간별 −20.7~25.9 %", "-"],
    ["**③의 Reference 대비**", "", "유지", chg(CYC_A, CYC["ref"]), chg(FMAX["adapath_A"], FMAX["refchip"]),
     chg(LAT["A"], LAT["ref"]), chg(E_A, E_REF), chg(A["adapath_A"], A["refchip"])],
], [2.4, 4.6, 1.2, 1.7, 1.7, 1.9, 2.4, 1.9], hl_rows=(2, 4), size=8.5,
    note="Fmax와 추론 지연은 합성 직후 추정값이다. ④의 에너지는 클럭 트리를 넣은 같은 조건에서 ICG 적용 전 설계 대비 "
         "구간별 감소율이다(표 %s)." % LBL["t_icg"])
para(doc, "TH=63은 MNIST 테스트셋 10,000장에서 Full 대비 정확도 손실 0.5 %p 이내로 연산을 최소화하도록 선정한 동작점이다. "
     "주최 입력에서는 더 낮은 임계값(TH=0~30)도 정답 980개와 평균 845.00 cycle을 보였다. 임계값 가변 기능은 실험용 RTL에서 "
     "확인하였으며(3.5.6절), 제출용 모델 A는 TL=TH=63으로 고정되어 런타임 변경 인터페이스를 제공하지 않는다.", indent=True)
h2(doc, "4.2 한계 및 향후 개선")
bullet(doc, "**평가 데이터와 비교 범위:** 임계값 교차 평가는 이미 관찰한 테스트셋의 사후 분할이며, 새로운 hidden 입력에서의 "
       "정확도 유지나 반복 재학습의 안정성을 보장하지 않는다. Early 단독 모델의 정확도는 확인하였으나, 후단 회로를 제거한 "
       "정적 Early 전용 설계와의 면적 및 에너지 비교는 수행하지 않았다. 따라서 모든 정적 설계보다 우월하다는 결론은 내리지 않는다.")
bullet(doc, "**WM 에너지의 적용 범위:** 동일 입력 비교에서 Easy 구간은 이득을 보였으나 Medium과 Hard 구간은 에너지가 "
       "증가하였다(표 @t_wmpaired@). 모드 비율 가중 6.7 % 감소는 모드별 4장의 선정 표본에 기초한다. 클래스별 오분류 비용과 "
       "실제 운용 입력의 모드 비율을 함께 확인해야 하며, Medium의 MAC 감소를 직접적인 에너지 절감으로 대체 해석하지 않는다.")
bullet(doc, "**배치 및 배선 후 전력:** 전력은 게이트레벨 VCD 기반의 배치 전 추정이다. 상세 배선 후의 기생 성분과 클럭망을 반영한 "
       "전력 평가로 클럭 게이팅 효과(표 @t_icg@)를 다시 확인할 계획이다.")
bullet(doc, "**배치 후 임계 경로:** 배치와 전역 배선 후 임계 경로는 FSM에서 Conv2 MAC 레지스터로 퍼지는 enable 신호였다(표 @t_pl@). "
       "enable 레지스터를 복제하거나 한 단 파이프라인하여 Reference와의 Fmax 차이를 줄일 수 있다.")
bullet(doc, "**열화 입력의 정확도:** 강한 블러와 잡음에서 정확도가 Baseline_A보다 최대 8.1 %p 낮았다(3.10절). 열화 입력을 포함한 "
       "학습과 Early Classifier 보정으로 개선할 수 있다.")
bullet(doc, "**면적:** 면적 증가분의 약 75 %는 병렬 데이터패스에서 발생한다(표 @t_area@). Conv1 병렬도를 응용의 처리량 요구에 맞추면 "
       "면적과 처리 속도 사이에서 동작점을 선택할 수 있으며, 적응형 경로의 추가 면적은 전체의 9 % 수준이다.")
bullet(doc, "**Feature Map Buffer:** 5,184 bit 레지스터 버퍼가 Easy 에너지의 %.0f %%를 차지한다. SRAM 매크로로 바꾸거나 Early "
       "Classifier와 Full FC의 연산기를 공유하여 면적과 에너지를 줄일 수 있다." % (EZ["Feature Map Buffer"] / E["A_easy"] * 100))
h2(doc, "4.3 기대효과")
bullet(doc, "**엣지 AI 저전력화:** Early Classifier, 특징 버퍼, 판단 및 제어 회로를 추가하여 쉬운 입력의 후단 연산을 생략함으로써, "
       "배터리 기반 엣지 기기의 추론당 에너지와 지연을 함께 줄일 수 있다. 모델 A의 모드별 에너지를 고정한 혼합 모델에서는 "
       "Easy 비율이 약 %.1f %%를 넘을 때 Reference 대비 평균 에너지 감소가 추정되었다. 다른 응용에도 같은 손익분기점이 "
       "적용되는지는 확인하지 않았다." % (P_BE_REF * 100))
bullet(doc, "**반도체 공정 검사 적용:** 웨이퍼맵 검사에서 Edge-Ring, Center처럼 명확한 패턴은 조기 종료하고 애매한 패턴만 정밀 "
       "경로로 보내는 계층적 검사에 활용할 수 있다. 다만 Scratch recall 감소(3.9절)처럼 결함 누락 비용이 큰 클래스는 별도 "
       "recall 제약과 함께 운용해야 한다.")
bullet(doc, "**설계 방법론:** 임계값 탐색 → 정수 Golden → 파라미터화 RTL → ORFS 합성 → 게이트레벨 VCD 전력까지 하나의 흐름으로 "
       "연결하고 MNIST 및 WM-811K 4-class 모델에 적용하였다. 다른 모델로의 확장 시에는 임계값 선정, 정수 정확도 및 동일 조건의 PPA를 다시 검증해야 한다.")

h2(doc, "4.4 결론")
para(doc, "본 과제는 고정 경로 가속기가 쉬운 입력에도 전체 연산을 수행하는 낭비를 줄이기 위해, Early Classifier 점수의 Top-1과 "
     "Top-2 차이(Score Margin)를 비교기와 감산기만으로 계산하여 입력마다 Easy, Medium, Hard 경로를 선택하는 AdaPath-NPU를 설계하였다. "
     "알고리즘 탐색, 정수 Golden 모델, 파라미터화 RTL, OpenROAD 합성과 배치, 게이트레벨 전력 분석, Vivado 기능 검증까지 하나의 "
     "흐름으로 연결하여 설계의 효과와 비용을 함께 정량화하였다.", indent=True)
para(doc, "지정주제(MNIST, 모델 A)에서는 주최 측 Reference와 같은 정답 수(970 / 1,000)를 유지하면서 ^^평균 처리 cycle %s, 추론 지연 %s, "
     "추론당 에너지 %s^^를 달성하였다. 추가 면적 %s의 대부분은 처리 cycle을 줄인 병렬 데이터패스에서 발생하였고 판단 회로는 0.65 %%에 불과하며, "
     "Top-2 Finder를 토너먼트 트리로 바꾸어 판단 회로가 임계 경로가 되지 않게 "
     "하였다. 배치와 전역 배선 이후에도 추론 지연은 Reference보다 %.1f %% 짧았다. 블록별 에너지 분해로 Easy 경로에서 후단부 "
     "레지스터의 유휴 전력을 찾아냈고, 전용 ICG 셀로 이를 차단한 설계에서 ^^ICG 적용 전 설계 대비 구간별 에너지를 20.7~25.9 %% 줄였다^^." % (
         chg(CYC_A, CYC["ref"]), chg(LAT["A"], LAT["ref"]), chg(E_A, E_REF), chg(A["adapath_A"], A["refchip"]),
         -pct(PL_LAT["A"], PL_LAT["ref"])), indent=True)
para(doc, "같은 RTL을 파라미터만 바꾸어 확장 모델 B(MNIST, 주최 TB 정답 999 / 1,000)와 자유주제 웨이퍼맵 결함 분류(WM-811K, "
     "4개 클래스)에 적용하였다. WM-811K에서는 Medium 경로가 실제로 선택되어 3경로 제어가 동작함을 확인하였고, Vivado에서 정확도 "
     "81.13 %(774 / 954)와 정수 Golden 대비 판정, 모드, Score Margin 954 / 954 일치를 얻었다. WM 동일 입력 12개의 배치 전 전력 분석에서 RTL 모드 비율 가중 에너지는 Baseline_WM 대비 6.7 % 감소한 것으로 추정되었으나, Medium과 Hard 구간에서는 에너지가 증가하였다. 기능 검증은 단위 회로, 1,000장 회귀, "
     "주최 측 테스트벤치, 제출 패키지의 독립 PC 재현, 합성 넷리스트의 Vivado 시뮬레이션(5개 시드 부분 실행, 판정 1,007회 일치, cycle 1,006/1,006 일치)까지 "
     "단계별로 수행하였다.", indent=True)
para(doc, "또한 본 과제는 ^^연산량(MAC) 감소가 곧 에너지 감소로 이어지지 않는다^^는 점을 블록 단위로 보이고, 적응형 경로가 에너지에서 "
     "유리해지는 Easy 비율(약 %.0f %%)을 손익분기점으로 제시하였다. 이는 적응형 추론 하드웨어를 설계할 때 경로 생략과 함께 유휴 "
     "블록의 클럭 차단과 버퍼 비용을 함께 설계해야 함을 보여준다. 향후에는 배치와 배선 이후의 전력 검증, enable 경로 파이프라인, "
     "Feature Map Buffer의 SRAM화를 통해 면적과 에너지 효율을 더 높일 계획이다." % (P_BE_REF * 100), indent=True)

h1(doc, "※ 참고문헌")
for ref in [
    "[1] S. Teerapittayanon, B. McDanel, H. T. Kung, \"BranchyNet: Fast inference via early exiting from deep "
    "neural networks,\" ICPR, 2016.",
    "[2] M.-J. Wu, J.-S. R. Jang, J.-L. Chen, \"Wafer map failure pattern recognition and similarity ranking for "
    "large-scale data sets,\" IEEE Trans. Semiconductor Manufacturing, 2015. (WM-811K)",
    "[3] Y. LeCun et al., \"Gradient-based learning applied to document recognition,\" Proc. IEEE, 1998. (MNIST)",
    "[4] L. T. Clark et al., \"ASAP7: A 7-nm finFET predictive process design kit,\" Microelectronics Journal, 2016.",
    "[5] T. Ajayi et al., \"Toward an open-source digital flow: First learnings from the OpenROAD project,\" DAC, 2019.",
    "[6] A. Kouris, S. I. Venieris, C.-S. Bouganis, \"CascadeCNN: Pushing the performance limits of quantisation in "
    "convolutional neural networks,\" FPL, 2018.",
    "[7] Y. Kaya, S. Hong, T. Dumitras, \"Shallow-Deep Networks: Understanding and mitigating network overthinking,\" "
    "ICML, PMLR 97, pp. 3301–3310, 2019.",
]:
    q = para(doc, ref, 9, space_after=2)
    q.paragraph_format.keep_with_next = True

# =================================================================== 부록
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
h1(doc, "부록 A. 재현성")
table(doc, "도구 및 실행 환경", ["항목", "버전 / 설정", "근거"], [
    ["Yosys (ABC 포함)", "0.68+ (git a5af9d690)", "합성 로그 배너"],
    ["OpenROAD / OpenSTA", "26Q3-1305-gf552262465 (ORFS 6101364b2, 2026-08-18)", "STA 및 전력 리포트 배너"],
    ["표준셀 라이브러리", "ASAP7 7.5-track RVT, TT corner (NLDM)", "STA 및 전력 Tcl의 Liberty 지정"],
    ["Icarus Verilog", "12.0 (devel) s20150603-1539-g2693dd32b", "iverilog -V"],
    ["Vivado", "2023.1 (SW Build 3865809)", "Vivado 실행 로그"],
    ["Vivado (독립 PC 재검증)", "2024.1", "results_hs/submit_check/logs/"],
    ["Python / PyTorch", "3.13.2 / 2.10.0+cpu (학습 PC 환경)", "학습 PC에서 확인, 학습 당시 로그는 별도 보존하지 않음"],
    ["게이트레벨 시뮬레이션", "100 MHz(10 ns), 이미지마다 리셋 12 cycle, ASAP7 셀 모델(지연 0 기능 모델)", "glsim TB"],
], [3.6, 7.6, 5.8])
para(doc, "위 도구 표의 합성 및 전력 환경은 기존 Reference 비교 분석의 환경이다. "
     "3.7절의 전용 ICG 적용 전후 비교 및 고유 입력 40개 확장 실험은 별도 환경인 "
     "WSL2 Ubuntu 24.04.5 LTS, Yosys 0.58(git 157aabb58), OpenROAD 26Q2-1164-g08f67ee5ec, "
     "ORFS 7bf5a814e47c54ec6c64692b464d398184d99891 및 Icarus Verilog 12.0 stable을 사용하였다. "
     "게이팅 전후 설계는 이 환경에서 동일 조건으로 비교하였으며, 기존 Reference 분석과 도구 버전이 같다는 의미는 아니다. "
     "버전 원문 및 파일 해시는 results_hs/clock_gating/environment.json에 보존하였다.", indent=True)
para(doc, "3.9절의 WM 동일 입력 비교는 Icarus Verilog 12.0 stable, OpenROAD 26Q2-1164-g08f67ee5ec 및 "
     "ORFS 7bf5a814e47c54ec6c64692b464d398184d99891의 ASAP7 RVT TT 환경에서 두 설계를 모두 재계산하였다. "
     "Liberty 시간 단위는 1 ps이며 SDC period 10000은 10 ns이다. 원본 넷리스트 및 TB를 유지하였고, "
     "입력과 라이브러리 해시 및 도구 버전을 results_hs/wm_paired_power/raw/에 기록하였다. 컴파일의 timing-check 미지원과 "
     "Liberty/LEF 경고는 원문 로그에 보존하였으며, 물리 구현 사인오프나 활동도 100 % 커버리지를 주장하지 않는다.", indent=True)
table(doc, "주요 실행 단계와 데이터", ["단계", "명령 / 스크립트", "데이터 및 조건"], [
    ["학습", "python train.py --arch A --n_class 10 --prefix mnist", "python/에서 실행; MNIST 학습 60,000장, 30 epoch, seed 미고정"],
    ["임계값 탐색", "python analyze_margin.py --arch A --prefix mnist", "python/에서 실행; MNIST 테스트 10,000장 (동일셋 선정)"],
    ["정수화", "python export_int8.py --arch A --prefix mnist --t_low 1.161 --t_high 1.161", "python/에서 실행; RTL 임계값 A 63/63, B 71/119, WM 13/41"],
    ["RTL 검증", "rtl/run_sim.sh, tb_batch1000.v, tb_official1000.v", "Golden 대조, 주최 측 입력 1,000회"],
    ["합성 및 STA", "ORFS make synth, flow_scripts/sta_one.sh, sta_sweep.tcl", "동일 SDC 규칙, 주기 1.0~2.4 ns 스윕"],
    ["전력", "glsim/run_*.sh → flow_scripts/vcd_power_odb.tcl, blockpower.tcl", "VCD 런 구성: evidence/README.md"],
    ["Vivado 제출", "vivado/submit/make_submit.tcl", "top_tb_1000, 프로젝트 내부 상대 경로"],
    ["Vivado 자유주제", "vivado/submit/make_submit_wm.tcl", "tb_wm, vivado/wm_data/의 954장, 4개 클래스"],
    ["추가 분석", "results_sh/v2/ (Python), results_hs/ (RTL 스윕 및 열화)", "분할 seed 2026–2030, 열화 seed 2026"],
], [2.6, 8.2, 6.2], note="전체 스크립트, 원시 결과, 실행 로그는 팀 저장소(SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA)에 보존하였다.")

h1(doc, "부록 B. 관련 연구 비교")
table(doc, "조기 종료 및 동적 추론 선행 연구와 본 설계의 비교", ["연구", "판단 지표", "경로 / 출구 수", "구현", "평가"], [
    ["BranchyNet [1]", "softmax 엔트로피", "LeNet 2, AlexNet/ResNet 3", "CPU/GPU (전용 RTL 없음)", "MNIST/CIFAR-10 정확도 및 추론 시간"],
    ["CascadeCNN [6]", "확률의 generalized Best-vs-Second-Best", "2 (저정밀 종료 / 고정밀 재계산)",
     "FPGA CNN + ARM CPU (softmax 및 판단)", "ImageNet, FPGA 실측 처리량"],
    ["Shallow-Deep Networks [7]", "최대 클래스 확률", "7 (내부 6 + 최종 1)", "소프트웨어 (전용 RTL 없음)",
     "CIFAR-10/100, Tiny ImageNet 정확도–FLOPs"],
    ["**AdaPath-NPU (본 설계)**", "정수 로짓 Top-1 − Top-2", "A: 2, B: 3", "Verilog RTL, ASAP7 합성 및 STA",
     "MNIST/WM-811K, 배치 전 VCD 에너지 추정"],
], [3.4, 3.6, 3.2, 3.6, 3.6], hl_rows=(3,),
    note="플랫폼, 모델 규모, 정밀도 및 평가셋이 달라 수치를 직접 순위화하지 않는다. 본 설계의 차별점은 정수 판단 회로와 "
         "공유 전단부의 경로 제어를 통합한 RTL 구현 및 비용 분석이며, 조기 종료나 점수 차이 지표 자체의 최초 제안을 주장하지 않는다.")

h1(doc, "부록 C. 추가 그림")
figure(doc, os.path.join(OUT, "sh2_fig_wm_confusion.png"),
       "WM-811K 4개 클래스 혼동 행렬 (Full vs AdaPath, 칸마다 표본 수와 행 정규화 비율)", 15.0)
figure(doc, os.path.join(OUT, "sh2_fig_error_examples.png"),
       "모델 A 오류 사례: 위 = Easy 오답 중 Margin 상위 6개, 아래 = Hard 입력의 Margin 분위별 사례 (정답, Early/Full 예측, Margin 표기)",
       16.0)

out = os.path.join(HERE, "결과보고서_PPA.docx")
doc.save(out)
print("written", out, "figs", fig_no[0], "tables", tab_no[0])
for k in EMPH:
    if k not in EMPH_HIT:
        print("EMPH miss:", k)
