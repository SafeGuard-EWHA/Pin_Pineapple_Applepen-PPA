"""결과보고서(Word) 생성 - results.json 의 측정값으로 본문 수치를 채운다.

    python make_final_report.py            -> 결과보고서_PPA.docx
"""
import json
import os
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

SWEEP, ROBUST, LEVELS = load_results(os.path.dirname(HERE))

FONT = "맑은 고딕"
fig_no = [0]
tab_no = [0]

# ---- 그림·표 번호: 이 파일의 figure()/table() 호출 순서로 미리 계산하여 본문 참조(@키@, %(키)s)에 사용
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
    "f_racc": FIGN["hs_fig_robustness_acc.png"],
    "t_map": _tn("비교 설계 대응표"), "t_train": _tn("학습 설정"), "t_acc": _tn("모델별 정확도"),
    "t_twofold": _tn("임계값 선정·평가 분리"), "t_stats": _tn("기존 동작점의 AdaPath vs Full"),
    "t_wmclass": _tn("WM-811K 클래스별"), "t_robust": _tn("입력 열화 조건별"),
}


def lbl(text):
    """본문의 @키@ 를 그림·표 번호로 치환."""
    return _re.sub(r"@(\w+)@", lambda m: str(LBL[m.group(1)]), text)


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
    parts = lbl(text).split("**")
    for i, t in enumerate(parts):
        if t:
            set_font(p.add_run(t), size, bold or (i % 2 == 1))
    return p


def heading(doc, text, level):
    # Word 기본 Heading 스타일을 써서 탐색 창·목차에 잡히게 하고, 모양만 본문 서체로 맞춘다
    p = doc.add_paragraph(style="Heading %d" % level)
    p.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    p.paragraph_format.space_after = Pt(6 if level == 1 else 4)
    p.paragraph_format.keep_with_next = True
    set_font(p.add_run(text), 14 if level == 1 else 12, True, (0, 0, 0))
    return p


def h1(doc, text):
    heading(doc, text, 1)


def h2(doc, text):
    heading(doc, text, 2)


def bullet(doc, text, size=10.5):
    p = para(doc, "", size)
    p.paragraph_format.left_indent = Cm(0.5)
    p.paragraph_format.first_line_indent = Cm(-0.35)
    p.paragraph_format.space_after = Pt(2)
    parts = lbl("· " + text).split("**")
    for i, t in enumerate(parts):
        if t:
            set_font(p.add_run(t), size, i % 2 == 1)
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
    if title.startswith(('모델 A 임계값 스윕 전체', '모드별 추론당 에너지')):
        for row in t.rows[:-1]:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.keep_with_next = True
    if note:
        q = para(doc, note, 8.5, space_after=6)
        q.alignment = WD_ALIGN_PARAGRAPH.LEFT
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

# 손익분기 (모드별 에너지 고정 혼합 모델)
P_BE_REF = (E["A_hard"] - E_REF) / (E["A_hard"] - E["A_easy"])
P_BE_BASE = (E["A_hard"] - E_ABASE) / (E["A_hard"] - E["A_easy"])
P_BE_CYC = (CYC["hard"] - CYC["base"]) / (CYC["hard"] - CYC["easy"])

# WM-811K: 10-class AdaPath_B 의 모드별 에너지를 WM 모드 비율로 가중한 대리 추정
WM = R["wm"]
E_WM_BASE = E["B_hard"]
E_WM = avg({"easy": E["B_easy"], "med": E["B_med"], "hard": E["B_hard"]}, WM["mode"])
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
        doc.styles.add_style(toc_name, 1)
    toc_style = doc.styles[toc_name]
    toc_style.font.name = FONT
    toc_style.font.size = Pt(10)
    toc_style.paragraph_format.space_before = Pt(0)
    toc_style.paragraph_format.space_after = Pt(3)
    toc_style.paragraph_format.line_spacing = 1.0

# ---- 표지 ----
for _ in range(5):
    doc.add_paragraph()
para(doc, "결 과 보 고 서", 26, True, "c", 30)
para(doc, "과제명: 반도체 결함 패턴 분류를 위한 Score-Margin 기반", 14, False, "c", 2)
para(doc, "난이도 적응형 Tiny NPU Datapath 설계", 14, False, "c", 2)
para(doc, "— OpenROAD(ORFS) 기반 ASAP7 7 nm PPA 비교 분석", 12, False, "c", 60)
para(doc, "팀    명: Pin_Pineapple_Applepen(PPA)", 13, False, "c", 2)
para(doc, "이화여자대학교 전자전기공학과  윤현서 · 최서현 · 윤홍은", 11, False, "c", 2)
para(doc, "지도교수: 최종윤", 11, False, "c", 120)
para(doc, "경북대학교 IDEC 2026 창의 회로설계 챌린지", 15, True, "c", 0)
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

para(doc, "목차", 18, True, space_after=12)
toc = doc.add_paragraph()
field = OxmlElement('w:fldSimple')
field.set(qn('w:instr'), 'TOC \\o "1-2" \\h \\z \\u')
toc._p.append(field)
doc.add_page_break()
sec.different_first_page_header_footer = True
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
for instruction, suffix in [('PAGE', ' / '), ('NUMPAGES', '')]:
    field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), instruction)
    footer._p.append(field)
    if suffix: footer.add_run(suffix)

# =================================================================== 1
h1(doc, "1. 과제 개요")
para(doc, "고정 경로 CNN 가속기는 입력 난이도와 관계없이 모든 입력에 동일한 연산 경로를 수행한다. 그러나 실제 입력의 "
     "상당수는 얕은 특징만으로도 분류가 가능하며, 이들에게 전체 경로를 적용하는 것은 연산·시간·에너지의 낭비이다. 본 과제는 "
     "전단부(Conv1) 직후 **Early Classifier 점수의 Top-1과 Top-2 차이(Score Margin)**를 난이도 지표로 사용하여, 입력마다 "
     "Easy / Medium / Hard 경로 중 하나를 선택하는 **난이도 적응형 NPU Datapath(AdaPath-NPU)**를 설계하였다.", indent=True)
para(doc, "엔트로피 기반 Early-Exit 기법(BranchyNet 등)은 분기 판단에 확률 분포의 엔트로피를 사용하므로 확률·로그 계산 또는 그 근사 "
     "회로가 필요하다. 본 설계는 비교기와 감산기만으로 계산되는 Score Margin을 사용하며, 같은 판단 결과로 후단 연산을 "
     "생략(Easy)하거나 일부 채널만 활성화(Medium)한다.", indent=True)
para(doc, "관련 연구로, BranchyNet[1]은 엔트로피 기반 조기 종료와 여러 출구의 공동 학습을 제시하였고, Shallow-Deep "
     "Networks[7]는 최대 클래스 확률에 따른 조기 종료와 과도한 후단 계산의 영향을 분석하였다. CascadeCNN[6]은 확률 벡터의 "
     "Best-vs-Second-Best 계열 지표로 저정밀도 추론과 고정밀도 재계산을 선택하였다(부록 B). 따라서 본 과제는 조기 종료나 "
     "상위 점수 차이의 사용 자체를 새로운 개념으로 주장하지 않는다. 본 설계는 정수 로짓 차이의 비교·감산 회로, 공유 전단부와 "
     "제한된 경로 선택, 주최 측 인터페이스 통합을 하나의 RTL로 구현하고, ASAP7 합성·STA와 게이트레벨 VCD 기반 전력 추정까지 "
     "연결한 데 초점을 둔다. 플랫폼·모델 규모·평가셋이 달라 선행 연구와 절감률이나 면적을 직접 비교하지 않는다. "
     "주최 측 평가 구조에 맞추어 과제를 다음과 같이 구성하였다.", indent=True)
table(doc, "평가 항목별 과제 구성", ["구분", "대상 모델 / 데이터", "수행 내용"], [
    ["지정주제 (50 %)", "주최 측 MNIST 레퍼런스 가속기와 주 경로 계층·채널 구성이 같은 모델 A",
     "같은 주 경로에 AdaPath 적용 → 정확도 유지 조건에서 PPA 비교"],
    ["자유주제 (30 %)", "WM-811K 웨이퍼맵 결함 분류 (4개 클래스, 모델 B)",
     "같은 기법의 적용 전·후 (Baseline_WM vs AdaPath_WM) PPA 비교"],
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
    ["Baseline_WM / AdaPath_WM", "0 / 2", "8 / 4", "4", "WM-811K", "자유주제 (N_CLASS=4, 가중치·임계값·shift 별도)"],
], [3.6, 1.6, 2.6, 1.3, 2.0, 5.9], hl_rows=(2,),
    note="모델 A는 Reference와 주 경로(Conv1 3채널 → Conv2 3채널 → FC 48→10)의 계층·채널 구성이 같다. 다만 가중치는 본 팀이 "
         "학습한 값이고, 정수 규약(가중치 INT8, 활성값 12-bit, bias 16-bit)과 Early Classifier 추가가 다르다. ASIC 합성에서는 "
         "세 설계 모두 가중치를 입력 포트로 두어 상수 전파 효과를 배제하였다.")
para(doc, "본 과제의 기여는 다음 세 가지이다. 첫째, Score Margin으로 입력 난이도를 판정하고 공통 전단부 이후의 연산 경로를 "
     "선택하는 스트리밍 데이터패스를 구현하였다. Easy 입력은 후단 추론을 생략하며, Medium과 Hard 입력은 저장한 특징을 "
     "재생하여 일부 또는 전체 Conv2 채널을 사용한다. 둘째, Top-2 탐색을 직렬 비교 체인에서 이진 토너먼트 트리로 바꾸어, "
     "처리 cycle 증가 없이 판단 회로의 조합 경로를 단축하였다. 셋째, 주최 측 Reference와 항상 Hard 경로를 실행하는 "
     "Baseline_A를 함께 비교하여 데이터패스 변경 효과와 적응형 경로 선택 효과를 분리하였다. 모델 A는 선정 임계값에서 "
     "Easy/Hard 두 경로를 사용하며, Medium 경로의 기여는 확장 모델에서 별도로 평가하였다.", indent=True)

# =================================================================== 2
para(doc, "핵심 결과: 무열화 순차 입력에서 Reference와 같은 970/1,000 정답을 유지하면서 평균 cycle을 "
     "36.1%, VCD 기반 추정 에너지를 8.9% 줄였고 셀 면적은 55.4% 증가하였다. 모델 A의 지정 동작점은 "
     "Easy/Hard 두 경로이며, 강한 잡음에서는 정확도가 Baseline_A보다 8.1%p 낮아졌다. 이 성과와 비용을 "
     "동일 조건의 결과로 함께 해석하였다.", indent=True)
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
    ["판단·제어 회로 면적", "전체 면적의 5 % 이내",
     "%s µm² (AdaPath_A의 %.2f %%, 단독 합성 기준 참고치)" % (f1(rg["area_v2"]), region2_ratio), "달성"],
    ["입출력 인터페이스", "Reference와 동일", "동일 포트 래퍼, 주최 측 TB 로직 무수정 실행", "달성"],
    ["자유주제 (WM-811K)", "적용 전·후 PPA 개선",
     "MAC %s, 정확도 %.2f %%p 하락, 에너지 %s (대리 추정)" % (
         chg(WM["mac_ada"], WM["mac_base"]), WM["acc_base"] - WM["acc_ada"], chg(E_WM, E_WM_BASE)),
     "추정 기준 달성"],
], [3.3, 3.6, 7.6, 2.0], hl_rows=(1, 2, 3))
para(doc, "면적은 Early Classifier, Feature Map Buffer, 판단·제어 회로가 추가되므로 Reference보다 증가한다. 이는 지연·에너지 "
     "이득과의 trade-off로 3.6~3.7절과 4장에서 정량적으로 분석한다.", indent=True)

# =================================================================== 3
h1(doc, "3. 설계 및 시뮬레이션")
para(doc, "그림 @f_flow@은 학습부터 PPA 비교까지의 전체 설계·평가 흐름이다. 기능 검증은 Golden 모델과의 비트 정합으로, 전력은 "
     "게이트레벨 VCD 활동 기반 추정으로, 비교는 동일 모델·입력·조건을 명시하여 수행하였다.", indent=True)
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
     "T_low ≤ m < T_high이면 Medium, m < T_low이면 Hard로 판정한다. 판정이 미정(X)인 경우에도 안전하게 Hard로 진행하도록 "
     "FSM과 디코더를 if/else 우선순위 구조로 작성하였다.", indent=True)
figure(doc, os.path.join(OUT, "fig_plan_flow.png"), "난이도 판단 및 모드 결정 흐름", 12.0)
para(doc, "10개 점수의 Top-2를 구하는 기존 회로는 Top-1 탐색(Pass 1, 9단)과 해당 위치를 제외한 Top-2 탐색(Pass 2, 9단)을 직렬로 "
     "연결하여 최대 18개의 비교 단계가 형성되었고, 이 경로가 설계 전체의 임계 경로가 되었다. 이를 **이진 토너먼트 트리**로 "
     "재설계하였다(그림 @f_top2@). 10개 점수와 6개 패딩 잎을 4개의 병합 레벨로 축약하며, 각 노드는 (1위 값, 1위 index, 2위 값)을 "
     "전달한다. 두 자식 A(낮은 index), B의 병합 규칙은 A.v1 ≥ B.v1이면 1위=A, 2위=max(A.v2, B.v1), 아니면 1위=B, "
     "2위=max(A.v1, B.v2)이다. 동점이면 낮은 index가 이기므로 기존 회로와 출력이 같다. 4레벨은 트리의 구조적 깊이이며 "
     "4 cycle이나 표준셀 4단을 뜻하지 않는다. 출력 레지스터는 1단 그대로이므로 처리 cycle은 변하지 않는다.", indent=True)
figure(doc, os.path.join(OUT, "fig_top2.png"), "Top-2 Finder: 직렬 비교 체인에서 이진 토너먼트 트리로", 16.5)
table(doc, "Top-2 구조 개선에 따른 판단·제어 회로 단독 합성 결과 (Top-2, Margin, Decoder, FSM; Early Classifier 제외)",
      ["항목", "기존 (비교기 체인)", "개선 (토너먼트 트리)", "변화"], [
    ["임계 경로", "%s ps" % f0(rg["crit_v1"]), "%s ps" % f0(rg["crit_v2"]), "약 %.2f배 단축" % (rg["crit_v1"] / rg["crit_v2"])],
    ["면적", "%s µm²" % f1(rg["area_v1"]), "%s µm²" % f1(rg["area_v2"]), chg(rg["area_v2"], rg["area_v1"])],
    ["기능 동일성", "-", "테스트한 400,000 벡터에서 출력 비트 동일", "-"],
], [3.0, 3.8, 6.2, 3.0], note="400,000 벡터는 무작위·동점 다수·경계값(최소/최대)·전부 동일 값을 포함한 테스트 결과이며, "
                              "전체 입력 공간에 대한 형식적 동등성 증명은 아니다.")
para(doc, "**난이도 지표 비교.** Score Margin을 선택한 근거를 확인하기 위해, 같은 Early Classifier 로짓으로 Score Margin, 최대 "
     "softmax 확률, 엔트로피, Top-1 로짓을 비교하였다(모델 A, MNIST 10,000장, Python float 분석, 그림 @f_metrics@). Full 대비 정확도 손실 "
     "0.5 %p 제약에서 Score Margin은 네 지표 중 가장 작은 평균 MAC(44,079)을 보였으나 다른 지표와의 차이는 0.06~1.0 %로 작았고, "
     "Early 정답 여부를 구분하는 AUROC는 최대 softmax 확률(0.953)이 Score Margin(0.950)보다 약간 높았다. Score Margin은 확률 "
     "정규화와 exp·log 같은 비선형 연산 없이 비교·감산으로 구현된다는 이점이 있지만, Top-1 로짓보다 연산이 적은 것은 아니므로 "
     "'네 지표 중 최소 회로 비용'이라고 결론짓지 않는다. 즉 Score Margin은 비선형 연산 없이 유리한 정확도–연산량 절충을 보인 "
     "지표로 해석한다(지표별 면적·지연은 측정하지 않음).", indent=True)
table(doc, "난이도 지표 비교 (모델 A, Full 대비 정확도 손실 0.5 %p 제약, 동일셋 탐색)",
      ["지표", "필요 연산 (직접 계산 기준)", "AUROC", "정확도", "평균 MAC", "Hard 대비 MAC 절감"], [
    ["**Score Margin**", "비교 트리 + 감산 1 (exp/log/나눗셈 없음)", "0.950", "97.03 %", "44,079", "24.73 %"],
    ["최대 softmax 확률", "exp 10, 덧셈 9, 정규화(나눗셈) + 최대값", "0.953", "97.03 %", "44,106", "24.68 %"],
    ["엔트로피", "softmax + log 10, 곱셈 10, 덧셈 9", "0.950", "97.03 %", "44,256", "24.43 %"],
    ["Top-1 로짓", "비교 9 (최대값만)", "0.893", "97.03 %", "44,530", "23.96 %"],
], [3.0, 5.6, 1.6, 2.0, 2.2, 2.6], hl_rows=(0,),
    note="연산 수는 직접 수식 기준이며 합성 후 셀 수·면적·지연이 아니다. 판정만 필요하면 최대값 정규화 등으로 비선형 연산을 "
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
table(doc, "학습 설정 (모델 A·B, MNIST / WM-811K 공통)", ["항목", "설정", "항목", "설정"], [
    ["Optimizer", "Adam, lr 2×10⁻³", "Scheduler", "Cosine annealing"],
    ["Epoch / Batch", "30 / 128", "손실", "CE(Full) + 0.5·CE(Early) + 0.5·CE(Light)"],
    ["입력", "28×28, [0,1] 정규화", "Random seed", "seed 미고정; 반복 재학습 변동성 미평가"],
], [3.0, 4.6, 2.6, 6.8])
sw = R["sw"]
table(doc, "모델별 정확도와 선정 동작점 (MNIST 테스트셋 10,000장)", ["항목", "모델 A (지정주제)", "모델 B (확장)"], [
    ["Full / Light / Early 정확도 (float)", "%s / %s / %s %%" % (sw["A_full"], sw["A_light"], sw["A_early"]),
     "%s / %s / %s %%" % (sw["B_full"], sw["B_light"], sw["B_early"])],
    ["선정 동작점 모드 비율 (Easy / Medium / Hard)", sw["A_modes"], sw["B_modes"]],
    ["AdaPath 정확도 / 평균 MAC 절감", "%s %% / %s %%" % (sw["A_acc"], sw["A_macsave"]),
     "%s %% / %s %%" % (sw["B_acc"], sw["B_macsave"])],
    ["정수 Hard 경로 정확도 (1,000장, 같은 표본의 float 대비)", sw["A_int8"], "97.80 % (float 97.95 %)"],
], [6.6, 5.2, 5.2])
para(doc, "모델 A는 Conv2가 3채널뿐이어서 1채널 Light 경로의 정확도(%s %%)가 낮다. 임계값 탐색은 Medium 구간을 두지 않는 "
     "동작점(T_low = T_high)을 평가한 후보 중에서 선택하였고, 그 결과 모델 A는 Easy/Hard 두 경로로 동작한다. 반면 후단부가 큰 모델 B와 "
     "WM-811K에서는 Medium이 선택된다(3.8절)." % sw["A_light"], indent=True)
figure(doc, os.path.join(OUT, "archA", "fig_margin_hist_mnist.png"), "모델 A의 Score Margin 분포와 선정 임계값", 12.0)
para(doc, "**임계값 선정과 평가의 분리 (2-fold 교차 평가).** 임계값 선정과 평가에 같은 데이터를 쓰는 문제를 줄이기 위해, 고정 "
     "가중치 모델에 대해 테스트셋을 무작위로 반분하여 한쪽에서 동작점을 선정하고 다른 쪽에서 평가하는 2-fold 교차 평가를 "
     "5개 분할 seed로 반복하였다(표 %(t_twofold)s, 그림 %(f_twofold)s). 기존 보고점과 같은 25개 분위수 후보로 선정하면 모델 A는 "
     "평가 절반에서도 정확도 97.41 ± 0.18 %%, MAC 절감 23.99 ± 0.23 %%로 5회 모두 0.5 %%p 손실 예산을 지켰다. 반면 더 촘촘한 "
     "경계 전수 탐색에서는 모델 A도 5회 중 3회 예산을 넘었고(손실 0.51 ± 0.04 %%p), 모델 B와 WM-811K는 두 탐색법 모두 5회 전부 "
     "예산을 넘었다(WM 손실 2.26 ± 1.48 %%p). 즉 **선정 데이터에서 지킨 정확도 제약이 미사용 데이터에서 보장되지는 않으며**, "
     "특히 표본이 작고 클래스가 어려운 WM-811K에서 차이가 컸다. 이 분석은 이미 관찰된 테스트셋을 사후 분할한 것으로, 새로운 "
     "외부 테스트셋 검증은 아니다(표준편차는 분할 seed에 따른 변동)." % LBL, indent=True)
table(doc, "임계값 선정·평가 분리 결과 (2-fold × 5 분할 seed, 평가 절반 기준, Python float)",
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
         "MAC 절감의 분모는 Hard 경로(Early FC 포함)이다.")
figure(doc, os.path.join(OUT, "sh2_fig_twofold.png"),
       "임계값 선정·평가를 분리한 2-fold 결과 (5개 분할 seed의 평균 ± 표준편차, × = 기존 동일셋 동작점)", 16.0)
para(doc, "**통계적 비교.** 기존 동작점에서 AdaPath와 같은 체크포인트의 Full 경로를 같은 이미지 쌍으로 비교하였다(표 %(t_stats)s). "
     "모델 A는 97.47 %% vs 97.53 %%(Wilson 95 %% 구간 97.14–97.76 %% vs 97.21–97.82 %%)이고, 불일치 쌍은 Full만 정답 58장, "
     "AdaPath만 정답 52장으로 McNemar exact p = 0.63이었다. 모델 B는 Full만 정답인 쌍이 54장 대 15장으로 유의한 정확도 하락"
     "(p = 2.6×10⁻⁶)이 있었으며, 이는 B의 동작점이 0.39 %%p 손실을 수용한 결과와 일치한다. 유의하지 않다는 결과(A, WM)는 "
     "동등성이나 비열등성의 증명이 아니며, 같은 테스트셋으로 임계값을 선정한 사후 비교라는 한계가 있다. 주최 측 input_1000.txt는 "
     "고유 100장의 10회 반복이므로 통계 검정에서 제외하였다." % LBL, indent=True)
table(doc, "기존 동작점의 AdaPath vs Full 통계 비교 (같은 체크포인트, 이미지 단위)",
      ["모델", "n", "AdaPath (95 % CI)", "Full (95 % CI)", "b / c", "McNemar p (Holm)"], [
    ["MNIST A", "10,000", "97.47 % (97.14–97.76)", "97.53 % (97.21–97.82)", "58 / 52", "0.634 (1.0)"],
    ["MNIST B", "10,000", "98.12 % (97.83–98.37)", "98.51 % (98.25–98.73)", "54 / 15", "2.6×10⁻⁶ (7.8×10⁻⁶)"],
    ["WM-811K", "954", "81.24 % (78.64–83.59)", "81.55 % (78.97–83.88)", "19 / 16", "0.736 (1.0)"],
], [2.0, 1.6, 4.0, 4.0, 1.8, 3.2],
    note="b = Full만 정답, c = AdaPath만 정답. 양측 exact 검정, 세 비교에 Holm 보정.")

h2(doc, "3.4 RTL 설계와 주최 측 인터페이스 호환")
para(doc, "RTL은 채널 수·클래스 수를 파라미터화한 단일 소스(adapath_top.v)로 작성하였다. VARIANT(0: Baseline, 1: Early-Exit, "
     "2: AdaPath)와 C2/C2_MED(모델 A·B), N_CLASS(MNIST 10, WM-811K 4) 및 각 모델의 가중치·임계값·shift 설정만 바꿔 표 @t_map@의 "
     "비교 설계를 생성하였다. 주요 블록은 conv1_engine(75 MAC 병렬), fmap_buffer(144×36 bit), early_classifier, "
     "top2_finder, score_margin_calc, difficulty_decoder, mode_control_fsm, conv2_engine(채널 enable), "
     "fc_engine(Light/Full)이다.", indent=True)
para(doc, "주최 측 평가는 제출 프로젝트의 테스트벤치에서 입력 파일만 교체하는 방식이므로, 레퍼런스 chip과 **포트 목록·폭이 "
     "같은 래퍼(chip_adapath.v)**를 제작하였다(그림 @f_wrapper@). 레퍼런스 가중치 포트는 호환용으로 입력만 받고 사용하지 않으며, "
     "**본 팀이 학습한 가중치는 래퍼 내부 상수(adapath_weights.vh)로 고정**하였다. 레퍼런스는 rst_n 해제 직후부터 픽셀을 "
     "받으므로, clk로 샘플링한 rst_n의 상승을 검출하여 코어의 start 펄스를 생성한다(reset low 구간이 최소 1 clk 이상 "
     "관측되어야 함). 주최 측 top_tb.v는 테스트벤치 로직을 수정하지 않았으며, 데이터 파일 경로만 프로젝트 내부 파일명으로 "
     "지정하였다. 시뮬레이션 top은 top_tb_1000, 도구는 Vivado 2023.1이다.", indent=True)
figure(doc, os.path.join(OUT, "fig_wrapper.png"), "주최 측 chip 인터페이스를 유지하는 래퍼", 14.0)

h2(doc, "3.5 기능 검증")
v = R["verify"]
table(doc, "기능 검증 결과", ["검증 단계", "방법", "결과"], [
    ["판단·제어 회로 단위", "Python Golden 200 벡터", "200 / 200 일치"],
    ["Top-2 Finder 개선", "기존 회로와 400,000 벡터 비교 (무작위·동점·경계값)", "테스트 벡터 전부 출력 동일"],
    ["End-to-end", "3종 구조 × 9장, 모드별 대표 이미지", "27 / 27 Golden 일치"],
    ["1,000장 회귀 (모델 B)", "MNIST 1,000장 Golden (margin / mode / decision)", "1,000 / 1,000 일치"],
    ["게이트레벨 (A, B, Reference)", "합성 넷리스트 + ASAP7 셀 모델 시뮬레이션", "RTL과 판정·모드·cycle 동일"],
    ["**주최 측 TB (Vivado 2023.1)**", "top_tb_1000, 테스트벤치 로직 무수정",
     "Reference %s / A %s / B %s" % (v["org_ref"], v["org_A"], v["org_B"])],
], [3.8, 7.0, 6.2], hl_rows=(5,))
table(doc, "주최 측 입력(input_1000.txt) 기준 정확도와 처리 cycle",
      ["설계", "정답 (순차 입력)", "정답률 (주최 TB)", "평균 cycle (주최 TB)", "평균 cycle (순차 입력)", "모드 분포 (순차)"], [
    ["Reference", "970 / 1,000", "%.1f %%" % ACC["ref_org"], f0(CYC["ref_org"]), f0(CYC["ref"]), "-"],
    ["Baseline_A", "970 / 1,000", "-", "-", f0(CYC["base"]), "0 / 0 / 1,000"],
    ["**AdaPath_A**", "**970 / 1,000**", "%.1f %%" % ACC["A_org"], f1(CYC["A_org"]), "**%s**" % f1(CYC_A),
     R["modes_seq"]["A"]],
    ["AdaPath_B", "1,000 / 1,000", "%.1f %%" % ACC["B_org"], f1(CYC["B_org"]), f1(CYC_B), R["modes_seq"]["B"]],
], [2.6, 2.6, 2.4, 2.8, 3.0, 3.0], hl_rows=(2,),
    note="input_1000.txt는 서로 다른 100장이 10번 반복된 1,000회 입력이므로 1,000개의 독립 표본이 아니다. '순차 입력'은 "
         "1,000회를 순서대로 1회씩 처리한 결과이고, cycle은 start(rst_n 해제)부터 valid_out까지이다. '주최 TB'는 "
         "$urandom_range로 복원 무작위 추출하므로 설계마다 추출된 표본 구성이 달라질 수 있다. cycle은 연속한 "
         "valid_out 사이 간격(리셋 포함)의 평균이다.")
para(doc, "주최 TB의 경계 검사를 위해 제출 ZIP의 설계와 TB를 수정하지 않고 별도 관찰 모듈을 연결하여 "
     "Icarus Verilog 12.0에서 재실행하였다. $urandom_range(0,1000)의 상한을 포함하는 추출로 이미지 인덱스 "
     "1000이 2회 선택되었으며, cnt<1000의 읽기 구간에서 배열 범위를 벗어난 읽기와 X 데이터 읽기가 각각 "
     "1,570회 관측되었다. 전체 종료 전 valid_out 관측은 1,001회, X를 포함한 decision은 1회였다. 따라서 "
     "원본 TB의 종료·계수 조건과 입력 범위를 정상적인 독립 1,000회 검증으로 간주하지 않는다.", indent=True)
para(doc, "이 실행의 accuracy 카운터는 960이었다. 이는 Icarus 기본 난수열의 새 진단 실행이며, 기존 "
     "Vivado 로그의 966을 재현하거나 대체한 값이 아니다. 원본 TB 로직은 보존하였고, Vivado의 과거 실행에서 "
     "같은 문제가 발생했는지는 당시 인덱스 추적 로그가 없어 확정할 수 없다. 정확도·cycle 비교의 주 근거는 "
     "입력 범위와 출력 수를 확인한 별도 순차 실행(970/1,000)으로 한정한다. 관찰 모듈과 원본 로그는 "
     "results_hs/pre_submit_checks/에 보존하였다.", indent=True)
figure(doc, os.path.join(OUT, "fig_vivado_console.png"),
       "Vivado 2023.1 실행 화면 — 주최 측 top_tb_1000 실행 결과 (AdaPath_A)", 16.0)
para(doc, "제출 프로젝트(.xpr)를 Vivado 2023.1에서 그대로 실행한 화면이다. 주최 측 테스트벤치가 1,000회 처리 후 $stop(391행)에서 "
     "정지하였고, Tcl 콘솔에 'Accuracy : 96%'가 출력되었다. Objects 창의 accuracy = 0x3C6(966), cnt = 0x3E8(1,000)이다.",
     indent=True)
figure(doc, os.path.join(OUT, "fig_vivado_ref_vs_ada.png"),
       "같은 0~415 ns 동안의 처리량 (Vivado, 주최 측 TB): Reference 30장 vs AdaPath_A 46장", 17.0)
para(doc, "같은 테스트벤치·같은 클럭에서 415 ns 동안 Reference는 30장, AdaPath_A는 46장을 분류하였다(두 설계 모두 해당 "
     "구간 전부 정답). 이미지당 평균 처리 cycle이 1,336에서 855로 줄어든 효과가 파형에 그대로 나타난다.", indent=True)
para(doc, "위 시간축은 timescale 1ps/1ps 및 always #5 클럭에 따른 10 ps 주기의 기능 시뮬레이션 "
     "표시이다. 물리적 동작 주파수나 실제 추론 지연으로 해석하지 않으며, STA의 Fmax 및 100 MHz 전력 평가 조건과 "
     "구분한다.", indent=True)
figure(doc, os.path.join(OUT, "fig_vivado_detail_easy_hard.png"),
       "Vivado 파형 (376~415 ns): Easy 이미지 42~45와 Hard 이미지 46의 내부 동작 비교", 17.0)
para(doc, "Easy 이미지(42~45)는 Early Classifier가 끝난 직후 FSM이 FRONT(1)에서 바로 출력으로 넘어가므로, Feature Map Buffer "
     "재생·Conv2 채널 enable·Full FC가 활성화되지 않는다. 이미지 46만 Score Margin이 57로 임계값 63보다 작아 Hard로 "
     "판정되며 후단부가 동작한다. mode·margin 레지스터는 이미지마다 리셋되고 Easy 판정은 출력 직전 수 cycle 동안만 "
     "유지되므로, 이 배율에서는 리셋값(Hard=2)이 주로 보인다.", indent=True)
figure(doc, os.path.join(OUT, "fig_vivado_detail_hard.png"),
       "Vivado 파형 확대 (399~408 ns): Hard 판정 이미지 46의 내부 처리 순서", 17.0)
para(doc, "Hard 판정 시 내부 동작은 ① Early Classifier 완료 → ② Score Margin 57 산출 및 판정 유효 → ③ FSM BACK(3) 전환 → "
     "④ Feature Map Buffer 재생 시작 및 재생 데이터 유효 구간 → ⑤ Conv2 전 채널 enable(111)과 Full FC 동작 → ⑥ valid_out_6 "
     "출력과 누적 정답 수 증가(44 → 45) 순서로 진행된다. Hard 이미지 1장의 추가 처리 시간은 Easy 대비 171 cycle이다.",
     indent=True)
para(doc, "**런타임 임계값 스윕 (RTL 실측).** difficulty_decoder의 레지스터 임계값 모드(USE_REG_TH)를 최상위 포트로 연결하고, "
     "주최 측 입력 1,000회에 대해 TL = TH를 0~400으로 바꿔 가며 16개 동작점을 RTL로 측정하였다(그림 %(f_sweep)s). TH = 63에서 "
     "기존 결과(정답 970, 평균 851.84 cycle, Easy/Hard 960/40)가 재현되었다. TH를 높이면 Hard 수가 0(TH = 0)에서 730"
     "(TH = 400)까지 늘고 평균 cycle은 845.0에서 969.8로 증가하여, 칩을 다시 합성하지 않고 런타임에 정확도–연산 시간 동작점을 "
     "바꿀 수 있음을 확인하였다. 한편 이 입력 집합에서는 평가한 TH = 0, 10, 20, 30(전부 Easy)이 정답 980개로 오히려 높아 TH = 63을 지배하였다. "
     "이는 고유 100장으로 구성된 입력의 특성으로, MNIST 테스트셋 10,000장에서는 Early 경로 단독 정확도(96.21 %%)가 Full 경로"
     "(97.53 %%)보다 낮다. 따라서 이 스윕은 런타임 조정 기능의 검증이며, 이 입력에서의 최적 임계값을 일반화하지 않는다." % LBL,
     indent=True)
table(doc, "모델 A 임계값 스윕 전체 결과 (RTL, TL=TH)",
      ["TL=TH", "정답 / 1,000", "정확도 (%)", "평균 cycle", "Easy", "Hard"],
      [[r['TH'], r['correct'], f"{r['correct']/10:.1f}", f"{r['avg_cycles']:.2f}", r['easy'], r['hard']] for r in SWEEP],
      [1.8, 2.8, 2.7, 3.1, 2.5, 2.5], hl_rows=(6,), size=9,
      note="모든 조건에서 정상 출력 1,000개, Medium=0이다. 표는 rtl/sweep_A.csv에서 직접 생성하였다.")
para(doc, "Hard 비율을 p_H라 하면 평균 cycle은 C = 845(1−p_H) + 1016p_H = 845 + 171p_H이다. "
     "16개 조건은 CSV 표시 정밀도 범위에서 이 관계와 일치하였다. TH=63보다 낮은 네 조건은 이 입력에서 "
     "정확도가 1.0 %p 높고 평균 cycle이 6.84 작았다. 그러나 이 결과만으로 기존 동작점을 변경하거나 다른 입력에서도 "
     "우세하다고 결론짓지 않았다. TL=TH이므로 Medium 경로의 기여도 검증하지 않는다.", indent=True)
figure(doc, os.path.join(OUT, "hs_fig_sweep_A.png"),
       "모델 A 런타임 임계값 스윕 (RTL 실측, 주최 측 입력 1,000회): 정확도–평균 처리 cycle", 14.0)

h2(doc, "3.6 논리 합성 및 타이밍 (OpenROAD-flow-scripts, ASAP7)")
para(doc, "모든 설계를 동일한 흐름(Yosys + ABC area 스크립트, 동일 SDC 규칙: 입출력 지연 = 클럭 주기의 20 %)으로 합성하고 "
     "OpenROAD로 pre-layout STA를 수행하였다. 가중치는 모든 설계에서 입력 포트로 두었다. 입력 지연이 주기에 비례하므로, "
     "단일 주기의 WNS로 Fmax를 역산하지 않고 클럭 주기를 1.0~2.4 ns로 스윕하여 최악 slack이 0이 되는 주기(인접 두 점의 "
     "선형 보간)를 추정하였다. 이 값은 보간 주기에서 직접 STA 통과를 확인한 값과 구분한다. 또한 추론 중 값이 바뀌지 않는 가중치 포트를 false path로 둔 조건(레지스터 간·"
     "픽셀 입력 경로 기준)의 Fmax를 함께 제시한다.", indent=True)
rows = []
for key, name in (("refchip", "Reference"), ("baseline_A", "Baseline_A"), ("adapath_A", "**AdaPath_A**"),
                  ("baseline", "Baseline_B"), ("adapath", "AdaPath_B")):
    rows.append([name, f0(A[key]), "%+.1f %%" % pct(A[key], A["refchip"]), f0(PER[key]), f1(FMAX[key]), f1(FMAX_S[key])])
table(doc, "합성 결과 (pre-layout, 클럭 주기 스윕)",
      ["설계", "Cell Area (µm²)", "Reference 대비", "슬랙 0 추정 주기 (ps)", "Fmax (MHz, SDC 규칙)", "Fmax (MHz, 가중치 정적)"],
      rows, [2.8, 2.8, 2.6, 2.6, 3.1, 3.1], hl_rows=(2,),
      note="추정 주기·Fmax(SDC 규칙)는 입출력 지연 20 % 조건에서 최악 slack = 0인 교차점을 선형 보간한 값이다. 이 조건의 임계 경로는 세 설계 "
           "모두 가중치 입력 포트에서 시작한다. '가중치 정적'은 가중치 포트를 false path로 둔 결과이다.")
sweep_evidence = []
for key, name in [('refchip', 'Reference'), ('baseline_A', 'Baseline_A'), ('adapath_A', 'AdaPath_A')]:
    lines = open(os.path.join(HERE, '..', 'orfs/reports_extra/sweep_'+key+'.txt'), encoding='utf-8').read().splitlines()
    points = [(float(x.split()[1]), float(x.split()[2])) for x in lines if x.startswith('io20 ')]
    fail = max((x for x in points if x[1] < 0), key=lambda x:x[0])
    passed = min((x for x in points if x[1] >= 0), key=lambda x:x[0])
    sweep_evidence.append([name, f'{fail[0]:.0f}', f'{fail[1]:+.2f}', f'{passed[0]:.0f}', f'{passed[1]:+.2f}', f'{1e6/passed[0]:.1f}'])
table(doc, "STA 스윕의 실제 실패·통과점 (입출력 지연 20% 조건)",
      ['설계','실패 주기 (ps)','실패 slack (ps)','통과 주기 (ps)','통과 slack (ps)','통과점 주파수 (MHz)'],
      sweep_evidence,[2.7,2.4,2.8,2.4,2.8,3.0],size=8.5,
      note="orfs/reports_extra/sweep_*.txt에서 직접 추출하였다. 통과점 주파수는 스윕한 점에서 확인한 값이며, "
           "위 표의 슬랙 0 보간 추정 Fmax와 구분한다. 실리콘 동작 주파수 또는 post-layout 결과가 아니다.")
para(doc, "Top-2 Finder 개선 후 AdaPath_A의 Fmax는 판단 회로가 없는 Baseline_A와 두 조건 모두에서 거의 같다(SDC 규칙 %s vs %s MHz, "
     "가중치 정적 %s vs %s MHz). 따라서 측정한 조건에서는 판단 회로에 의한 뚜렷한 주파수 저하가 관측되지 않았다. Reference 대비 SDC 규칙 기준 %.1f %%, 가중치 "
     "정적 기준 %.1f %% 낮은데, 이는 판단 회로가 아니라 본 팀 데이터패스(Conv2 가중치 입력 경로, FC·FSM 제어 경로)에서 "
     "결정된다. 면적 증가는 Feature Map Buffer(5,184 bit), Early Classifier FC, 제어 회로에서 발생한다. 판단·제어 회로(Top-2, "
     "Margin, Decoder, FSM) 단독 합성 면적은 %s µm²로, AdaPath_A 통합 합성 면적의 %.2f %%에 해당한다(단독 합성과 통합 "
     "합성의 최적화 차이가 있어 참고치)."
     % (f1(FMAX["adapath_A"]), f1(FMAX["baseline_A"]), f1(FMAX_S["adapath_A"]), f1(FMAX_S["baseline_A"]),
        -pct(FMAX["adapath_A"], FMAX["refchip"]), -pct(FMAX_S["adapath_A"], FMAX_S["refchip"]),
        f1(rg["area_v2"]), region2_ratio), indent=True)

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
       "정확도 동일(970/1,000) 조건에서 Reference 대비 처리 cycle·지연·에너지·MAC·면적 (Reference = 1.0)", 15.0)
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
     "Conv2·Pool2·FC의 레지스터는 연산 없이 클럭만 공급받으며 **%.2f nJ(Easy 에너지의 %.0f %%)**를 소모한다. ③ Feature Map "
     "Buffer(5,184 bit 레지스터)는 Easy에서 %.2f nJ(%.0f %%)로 가장 큰 단일 블록이다. 이 분석은 CTS 이전이라 클럭망 전력이 "
     "포함되지 않았으며(Easy 런에서 순차 소자 비중 %.0f %%), 배치·배선 이후 다시 평가해야 한다."
     % (EZ["조합 논리 (블록 미분류)"], BS["조합 논리 (블록 미분류)"], IDLE, IDLE / E["A_easy"] * 100,
        EZ["Feature Map Buffer"], EZ["Feature Map Buffer"] / E["A_easy"] * 100, pw["A_easy_seq_pct"]), indent=True)
figure(doc, os.path.join(OUT, "fig_block_energy.png"),
       "블록별 추론당 에너지 (게이트레벨 VCD 기반 추정, 100 MHz; Reference는 이미지 1~4 런, Hard는 런 차감 추정)", 16.5)
para(doc, "②의 유휴 에너지는 Easy 판정 시 후단부 레지스터의 클럭을 차단하는 클럭 게이팅의 직접적인 대상이다. 이 에너지를 모두 "
     "제거할 수 있다고 가정한 상한 추정에서 Easy 에너지는 %.1f nJ, 가중 평균은 %.1f nJ로 Reference 대비 %s이 된다. ICG 셀과 "
     "게이팅 제어의 오버헤드는 반영하지 않은 값이므로 실제 이득은 이보다 작으며, 구현과 재측정으로 확인해야 한다(4.2절)."
     % (E_EZ_CG, E_A_CG, chg(E_A_CG, E_REF)), indent=True)
table(doc, "효율 지표", ["설계", "실행 MAC", "에너지 (nJ)", "실효 TOPS/W", "등가 TOPS/W"], [
    ["Reference", f0(MAC["ref"]), f1(E_REF), f2(topsw(MAC["ref"], E_REF)), f2(topsw(MAC["ref"], E_REF))],
    ["Baseline_A", f0(MAC["Abase"]), f1(E_ABASE), f2(topsw(MAC["Abase"], E_ABASE)), f2(topsw(MAC["ref"], E_ABASE))],
    ["**AdaPath_A**", f0(MAC_A), f1(E_A), f2(topsw(MAC_A, E_A)), "**%s**" % f2(topsw(MAC["ref"], E_A))],
], [3.4, 3.2, 3.0, 3.2, 3.2], hl_rows=(2,),
    note="1 MAC = 2 operations. 실효 TOPS/W = 2 × 실행 MAC / 추론당 에너지. 등가 TOPS/W = 2 × Reference MAC(%s) / 추론당 "
         "에너지로, 같은 분류 작업을 완료하는 효율이다. 본 측정에서는 실행 MAC 감소율이 에너지 감소율보다 커서 AdaPath_A의 "
         "실효 지표가 낮아졌으므로, 두 지표를 평균 에너지·정확도와 함께 제시한다." % f0(MAC["ref"]))
para(doc, "모드별 에너지를 고정한 혼합 모델로 입력 분포에 따른 에너지 이득 조건을 분석하였다(그림 @f_breakeven@). Easy 비율을 p라 하면 "
     "모델 A의 평균 에너지는 E_A(p) = %.2f − %.2f·p nJ이다. 이 모델에서 Reference 대비 에너지 이득은 Easy 비율이 약 "
     "**%.1f %%를 넘을 때** 발생하고, Baseline_A 대비 손익분기점은 약 %.1f %%이다. 반면 Baseline_A 대비 처리 cycle의 "
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
figure(doc, os.path.join(OUT, "fig_iso_accuracy_wm811k.png"), "Pareto front 비교: Early-Exit vs AdaPath (WM-811K)", 13.0)
para(doc, "Medium 경로는 ① 후단부 연산이 크고 ② 입력 난이도 분포가 넓어 Early와 Full 사이의 중간 확신 구간이 많을 때 효과가 "
     "있다. MNIST처럼 대부분이 쉬운 데이터에서는 이득이 작고, 모델 A에서는 임계값 탐색이 Medium을 자동으로 제외한다. 따라서 "
     "데이터에 맞춰 임계값을 결정하는 본 설계 흐름이 2경로와 3경로 중 유리한 구성까지 선택하는 구조라는 점이 의미가 있다. "
     "다만 모델 A의 성과를 3경로 전체의 성과로 해석하지 않는다.", indent=True)

para(doc, "Medium 경로의 하드웨어 동작을 추가 확인하기 위해 현재 RTL과 모델 B 가중치로 기존 "
     "tb_adapath를 다시 실행하였다. Easy/Hard/Medium 각 3개 입력을 포함하는 9개 사례 모두 margin·mode·decision이 "
     "정수 Golden과 일치하였다. Medium BACK 구간 총 513 cycle에서 ch_en=0x0F, fc_light_en=1, fc_full_en=0의 "
     "관찰 위반은 0회였다. 이는 대표 사례의 동작 검증이며 전체 입력 공간에 대한 형식 검증은 아니다.", indent=True)
figure(doc, os.path.join(OUT, "fig_medium_verified.png"),
       "모델 B Medium 경로의 실제 VCD 파형. 현재 RTL의 Icarus 재실행에서 추출한 신호를 시각화하였으며 EDA 도구 화면 캡처는 아니다.", 17.0)
h2(doc, "3.9 자유주제: WM-811K 웨이퍼맵 결함 분류 적용")
para(doc, "반도체 제조 공정의 웨이퍼맵 결함 패턴(WM-811K, 811,457장 중 라벨 172,950장)에서 정상(none), Center, Edge-Ring, "
     "Scratch 4개 클래스를 클래스당 같은 개수(가장 적은 Scratch 기준 약 1,190장)로 균형 추출하고, 웨이퍼 맵(웨이퍼 밖 / 정상 "
     "die / 불량 die)을 28×28로 리사이즈한 뒤 8:2로 학습·테스트를 나누었다. 모델 B 구조(4개 클래스 출력)에 같은 AdaPath "
     "기법을 적용하였으며, 데이터 준비·학습·정수화·RTL 생성은 MNIST와 동일한 코드로 수행하였다. 선정 동작점은 정확도 "
     "0.31 %p 하락을 수용하고 연산량을 줄인 지점이다.", indent=True)
table(doc, "WM-811K 적용 전·후 비교 (Baseline_WM = 항상 Hard)", ["항목", "Baseline_WM", "AdaPath_WM", "변화"], [
    ["정확도 (테스트 %d장, float)" % WM["n_test"], "%.2f %%" % WM["acc_base"], "%.2f %%" % WM["acc_ada"],
     "%.2f %%p 하락" % (WM["acc_base"] - WM["acc_ada"])],
    ["모드 개수 (Easy / Medium / Hard)", "0 / 0 / %d" % WM["n_test"], WM["mode_str"], "-"],
    ["평균 MAC / 이미지", f0(WM["mac_base"]), f0(WM["mac_ada"]), chg(WM["mac_ada"], WM["mac_base"])],
    ["Cell Area (µm²)", f0(A["baseline_wm"]), f0(A["adapath_wm"]), chg(A["adapath_wm"], A["baseline_wm"])],
    ["추정 Fmax (MHz)", f1(FMAX["baseline_wm"]), f1(FMAX["adapath_wm"]), "-"],
    ["평균 처리 cycle / 이미지", f0(CYC["base"]), f0(WM["cyc_ada"]), chg(WM["cyc_ada"], CYC["base"])],
    ["추론당 에너지 (nJ, 대리 추정)", f1(E_WM_BASE), f1(E_WM), chg(E_WM, E_WM_BASE)],
], [5.0, 3.4, 4.6, 3.0], hl_rows=(6,),
    note="WM 에너지는 10개 클래스 AdaPath_B의 모드별 VCD 기반 에너지에 WM-811K 모드 비율을 가중한 대리 추정이다. "
         "Baseline_WM 값으로 AdaPath_B Hard 에너지를 사용하였으나 Baseline_WM에는 Early 경로가 없으므로, 4개 클래스 설계의 "
         "직접 전력 측정 결과와 구분한다.")
para(doc, "**클래스별 분석.** 전체 평균만으로는 결함 종류별 영향을 알 수 없으므로 클래스별 경로 배분과 정확도를 분석하였다(표 "
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
       "WM-811K 클래스별 경로 배분(Easy/Medium/Hard)과 Full·AdaPath recall", 16.0)

h2(doc, "3.10 입력 열화에 따른 적응적 연산 배분 (RTL 실측)")
para(doc, "입력이 어려워질 때 AdaPath가 실제로 후단 연산을 더 많이 사용하는지 확인하기 위해, 주최 측 입력 1,000회에 실제 센서 "
     "환경을 모사한 열화(대비 감소 6단계, 3×3 블러 5단계, 가우시안 잡음 6단계, seed 고정)를 적용하고 모델 A의 AdaPath_A와 "
     "같은 가중치의 항상-Hard 설계(Baseline_A)를 RTL로 각각 실행하였다(총 34회, 표 %(t_robust)s, 그림 %(f_rmodes)s·%(f_racc)s). 원본과 "
     "대비 0.3 조건의 기준값을 먼저 재현한 뒤 전체를 실행하였다." % LBL, indent=True)
table(doc, "입력 열화 생성 조건", ["종류", "수준", "변환 및 처리"], [
    ["대비 축소", "1.0, 0.7, 0.5, 0.4, 0.3, 0.2", "픽셀값에 계수 c를 곱함"],
    ["평균 블러", "0, 1, 2, 3, 4회", "영 패딩 3×3 평균 필터를 반복 적용"],
    ["가우시안 잡음", "σ=0, 20, 40, 60, 80, 100", "픽셀 단위 N(0, σ²) 가산, seed=2026"],
], [2.5, 6.4, 7.1], size=9,
    note="변환 후 np.rint로 반올림하고 [0,255]로 포화시켰다. σ는 8-bit 픽셀값 단위이다. "
         "종류별 수준을 나열된 순서로 생성하며 난수 생성기의 상태를 이어 사용하였다.")
robust_rows = []
for kind, levels in LEVELS.items():
    for level in levels:
        a, b = ROBUST[kind, level, 'ada'], ROBUST[kind, level, 'base']
        name = {'contrast': '대비', 'blur': '블러', 'gauss': '잡음 σ'}[kind]
        robust_rows.append([f'{name} {level:g}', f"{a['correct']/10:.1f}", f"{b['correct']/10:.1f}",
                           f"{(a['correct']-b['correct'])/10:+.1f}", f"{a['hard']/10:.1f}",
                           f"{a['avg_cycles']:.2f}", f"{(985-a['avg_cycles'])/985*100:.2f}"])
table(doc, "입력 열화 조건별 결과 (모델 A, RTL, TL = TH = 63, 주최 측 입력 1,000회)",
      ["조건", "AdaPath\n정확도 (%)", "Baseline\n정확도 (%)", "차이\n(%p)", "Hard\n(%)", "AdaPath\n평균 cycle", "cycle\n감소 (%)"],
      robust_rows, [2.2, 2.5, 2.5, 1.5, 1.5, 3.0, 2.8], hl_rows=(0, 4, 10, 16), size=8.5,
      note="차이는 AdaPath−Baseline이다. Baseline_A는 모든 조건에서 985.00 cycle이며 감소율은 (985−C_AdaPath)/985×100이다. "
           "모든 AdaPath 조건에서 Medium=0, Easy 비율은 100−Hard(%)이다. cycle 감소율은 MAC·전력·에너지 감소율이 아니다. "
           "17조건×2설계에서 정상 출력과 모드 합은 모두 1,000개이며, 세 종류의 무열화 기준점은 중복 포함된다.")
figure(doc, os.path.join(OUT, "hs_fig_robustness_modes.png"),
       "입력 열화 강도에 따른 AdaPath_A의 Hard 경로 비율(위)과 평균 처리 cycle(아래) (RTL 실측)", 16.5)
figure(doc, os.path.join(OUT, "hs_fig_robustness_acc.png"),
       "입력 열화 강도에 따른 정확도: AdaPath_A vs Baseline_A (RTL 실측)", 16.5)
para(doc, "세 열화 모두에서 열화가 강해질수록 Hard 비율과 평균 cycle이 증가하였다. 특히 대비를 1.0에서 0.2로 낮추면 Hard 비율이 "
     "4 %%에서 72 %%로 늘어, **평가한 열화 수준에 따라 연산을 더 배분하는 동작**이 RTL에서 확인되었다. 대비 감소에서는 정확도가 "
     "Baseline_A와 같거나 높았다(0.2에서 80.0 %% vs 76.0 %%). 반면 강한 블러(4회, 87.0 %% vs 90.0 %%)와 강한 가우시안 잡음(σ = 100, "
     "74.9 %% vs 83.0 %%)에서는 AdaPath의 정확도가 낮았다. 이 조건에서는 Hard 비율이 36~38 %%에 머물러, 일부 입력이 높은 Score "
     "Margin으로 Easy에서 종료되었을 가능성이 있다. 다만 집계 결과만으로 개별 오류의 원인을 입증하지는 않았다(MNIST 테스트셋의 "
     "높은 Margin 오분류 분석은 4.2절). 정확도가 열화 강도에 대해 항상 단조 감소하지 않은 점(대비 0.5에서 99.0 %%)도 고유 100장 "
     "입력의 특성으로 해석한다." % LBL, indent=True)

para(doc, "대비 0.3에서는 AdaPath_A와 Baseline_A의 정확도가 93.0%로 같고 cycle은 7.62% 감소하였다. "
     "반면 σ=100에서는 7.96%의 cycle 감소와 8.1%p의 정확도 손실이 함께 나타났다. 큰 Score Margin은 "
     "확률로 보정된 신뢰도가 아니므로 ‘Early Classifier가 확신을 갖고 틀리는 경우’가 가능하다. 다만 잡음 "
     "실험의 집계 CSV만으로 오류가 발생한 경로나 원인을 확정하지 않았다. 4.2절과 부록 C의 무열화 "
     "소프트웨어 오류 사례는 별도 입력·수치 조건의 분석이며, 잡음 입력의 직접 원인 검증으로 대체할 수 없다.", indent=True)
h2(doc, "3.11 추가 RTL 실험의 재현성과 해석 범위")
para(doc, "실험 1·2는 기존 RTL과 out/rtl_data_mnist_A/ 가중치를 고정하여 수행하였다. Python 3.12.14와 "
     "Icarus Verilog 12.0(devel)을 사용하였으며 기존 설계 .v 파일은 수정하지 않았다. 실험 1은 run_sweep.sh A와 "
     "같은 테스트벤치·컴파일 인수·16개 임계값을 Windows 실행기로 구동하였고, 실험 2는 make_noisy_inputs.py의 "
     "변환과 같은 RTL 비교 조건을 사용하였다. 소스 기준은 5b9d9d2ce36e86ef7d3a3dfd46eac903435a209f이며, "
     "입력·소스·가중치 해시와 실행별 로그는 results_hs/exp1_artifacts/ 및 results_hs/exp2_artifacts/에 보존하였다. "
     "전체 결과 표는 rtl/sweep_A.csv와 rtl/robustness_A.csv에서 직접 생성하였다.", indent=True)
para(doc, "원본 입력은 고유 100장의 10회 반복이다. 대비·블러는 결정적 변환이므로 반복을 독립 표본으로 "
     "간주할 수 없다. 잡음은 반복마다 서로 다른 실현값을 가하지만 원본 이미지의 다양성을 늘리지는 않으며, "
     "단일 seed로 잡음 실현 간 변동성도 평가하지 못하였다. 따라서 이 RTL 결과에는 독립 1,000표본을 전제한 "
     "신뢰구간이나 유의성 검정을 적용하지 않았다. 이는 3.3절의 이미지 단위 소프트웨어 통계 검정과 구분한다.", indent=True)

# =================================================================== 4
h1(doc, "4. 결과 및 기대효과")
h2(doc, "4.1 결과 요약")
table(doc, "최종 결과 요약 (지정주제: Reference 대비 AdaPath_A)", ["지표", "Reference", "AdaPath_A", "변화"], [
    ["정답 (주최 입력 순차 1,000회)", "970", "970", "유지"],
    ["평균 처리 cycle (순차 입력)", f0(CYC["ref"]), f1(CYC_A), chg(CYC_A, CYC["ref"])],
    ["추정 Fmax (MHz, pre-layout)", f1(FMAX["refchip"]), f1(FMAX["adapath_A"]), chg(FMAX["adapath_A"], FMAX["refchip"])],
    ["추론 지연 @추정 Fmax (ns)", f0(LAT["ref"]), f0(LAT["A"]), chg(LAT["A"], LAT["ref"])],
    ["평균 실행 MAC / 추론", f0(MAC["ref"]), f0(MAC_A), chg(MAC_A, MAC["ref"])],
    ["추론당 에너지 (nJ, VCD 기반 추정)", f1(E_REF), f1(E_A), chg(E_A, E_REF)],
    ["Cell Area (µm²)", f0(A["refchip"]), f0(A["adapath_A"]), chg(A["adapath_A"], A["refchip"])],
], [5.4, 3.4, 3.4, 3.8], hl_rows=(1, 3, 5))
para(doc, "위 성능은 무열화 입력과 사전 지정 TH=63의 조건부 결과이다. 평가한 TH=0, 10, 20, 30은 "
     "같은 입력에서 98.0%와 845.00 cycle을 보여 TH=63보다 유리하므로 TH=63의 보편적 최적성을 주장하지 않는다. "
     "강한 잡음에서는 8.1%p의 정확도 손실이 발생하였다. 적응형 경로의 이득은 입력 분포와 허용 오류에 따라 달라지며, "
     "동작점 변경에는 별도 검증이 필요하다.", indent=True)
h2(doc, "4.2 평가 범위, 한계 및 향후 개선")
bullet(doc, "**정확도 표본:** 주최 입력은 고유 100장이 10회 반복된 1,000회 입력이므로 1,000개의 독립 이미지에 대한 일반화 "
       "평가와 구분한다. MNIST 테스트셋 10,000장 결과(표 @t_acc@)는 임계값 탐색에도 사용된 동일셋 결과이며, 사후 분할 교차 평가와 외부 미사용 테스트셋 검증을 구분한다.")
bullet(doc, "**임계값 선정의 일반화:** 2-fold 교차 평가(3.3절)에서 선정 데이터의 0.5 %p 제약이 평가 데이터에서는 보장되지 "
       "않았다(특히 WM-811K). 학습 단계부터 분리된 검증셋으로 임계값을 정하고, 미사용 외부 테스트셋으로 평가하는 절차가 필요하다.")
bullet(doc, "**높은 Score Margin의 오분류:** 모델 A에서 Easy로 판정된 9,400장 중 129장(전체의 1.29 %, Easy 내부 1.37 %)이 "
       "오분류되었고, 이 중 58장은 Full 경로였다면 정답이었다(주요 혼동: 7→2, 2→8). 높은 Margin이 정답을 보증하지 않으며, "
       "조기 종료의 정확도 비용이 이 58장에 해당한다(부록 C 사례 그림).")
bullet(doc, "**강한 블러·잡음:** 강한 블러와 가우시안 잡음에서 AdaPath 정확도가 Baseline_A보다 최대 8.1 %p 낮았다(3.10절). 열화 "
       "입력을 포함한 학습(데이터 증강)이나 Early Classifier 보정이 필요하다.")
bullet(doc, "**통계 해석:** AdaPath와 Full의 정확도 차이가 유의하지 않다는 결과(모델 A, WM-811K)는 동등성의 증명이 아니며, "
       "모델 B는 유의한 하락이 있었다(3.3절).")
bullet(doc, "**전력 추정:** 전력은 소수 대표 입력의 게이트레벨 VCD에 기반한 pre-layout 추정이며 실리콘 계측이 아니다. 배치·"
       "배선, 클럭망, 실제 입력 분포를 반영한 후속 검증이 필요하다. WM-811K 에너지는 대리 추정이다.")
bullet(doc, "**클럭 게이팅:** Easy에서도 후단부 레지스터가 %.2f nJ를 소모한다(그림 @f_block@). 모드 신호로 후단부 클럭을 차단하는 "
       "클럭 게이팅(ICG 셀)을 적용하면, 오버헤드를 제외한 상한 추정으로 평균 에너지를 %.1f nJ(Reference 대비 %s)까지 줄일 수 "
       "있다." % (IDLE, E_A_CG, chg(E_A_CG, E_REF)))
bullet(doc, "**Feature Map Buffer:** 5,184 bit 레지스터 버퍼가 면적과 Easy 에너지(%.0f %%)의 가장 큰 단일 항목이다. SRAM 매크로로 "
       "바꾸거나, Early Classifier를 Full FC와 시분할 공유하면 면적·에너지 오버헤드를 줄일 수 있다."
       % (EZ["Feature Map Buffer"] / E["A_easy"] * 100))
bullet(doc, "**런타임 동작점 조정:** difficulty_decoder는 레지스터 임계값 모드(USE_REG_TH)를 지원하므로, 런타임에 정확도–연산량 "
       "동작점을 조정하는 운용으로 확장할 수 있다(전압·주파수를 바꾸는 DVFS와는 구분).")
h2(doc, "4.3 기대효과")
bullet(doc, "**엣지 AI 저전력화:** Early Classifier·특징 버퍼·판단 및 제어 회로를 추가하여 쉬운 입력의 후단 연산을 생략함으로써, "
       "배터리 기반 엣지 기기의 추론당 에너지와 지연을 함께 줄일 수 있다. 쉬운 입력의 비율이 손익분기점(약 %.0f %%)보다 "
       "높은 응용에서 효과가 크다." % (P_BE_REF * 100))
bullet(doc, "**반도체 공정 검사 적용:** 웨이퍼맵 검사에서 Edge-Ring·Center처럼 명확한 패턴은 조기 종료하고 애매한 패턴만 정밀 "
       "경로로 보내는 계층적 검사에 활용할 수 있다. 다만 Scratch recall 감소(3.9절)처럼 결함 누락 비용이 큰 클래스는 별도 "
       "recall 제약과 함께 운용해야 한다.")
bullet(doc, "**설계 방법론:** 임계값 탐색 → 정수 Golden → 파라미터화 RTL → ORFS 합성 → 게이트레벨 VCD 전력까지 하나의 흐름으로 "
       "연결하여, 다른 모델·데이터셋에도 같은 절차로 적용할 수 있음을 보였다.")

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
    ["OpenROAD / OpenSTA", "26Q3-1305-gf552262465 (ORFS 6101364b2, 2026-08-18)", "STA·전력 리포트 배너"],
    ["표준셀 라이브러리", "ASAP7 7.5-track RVT, TT corner (NLDM)", "STA·전력 Tcl의 Liberty 지정"],
    ["Icarus Verilog", "12.0 (devel) s20150603-1539-g2693dd32b", "iverilog -V"],
    ["Vivado", "2023.1 (SW Build 3865809)", "Vivado 실행 로그"],
    ["Python / PyTorch", "3.13.2 / 2.10.0+cpu (학습 PC 환경)", "학습 PC에서 확인, 학습 당시 로그는 별도 보존하지 않음"],
    ["게이트레벨 시뮬레이션", "100 MHz(10 ns), 이미지마다 리셋 12 cycle, ASAP7 셀 모델(지연 0 기능 모델)", "glsim TB"],
], [3.6, 7.6, 5.8])
table(doc, "주요 실행 단계와 데이터", ["단계", "명령 / 스크립트", "데이터·조건"], [
    ["학습", "python/train.py --arch A --n_class 10 --prefix mnist", "MNIST 학습 60,000장, 30 epoch, seed 미고정"],
    ["임계값 탐색", "python/analyze_margin.py --arch A --prefix mnist", "MNIST 테스트 10,000장 (동일셋 선정)"],
    ["정수화", "python/export_int8.py --arch A --prefix mnist --t_low 1.161 --t_high 1.161", "RTL 임계값 A 63/63, B 71/119, WM 13/41"],
    ["RTL 검증", "rtl/run_sim.sh, tb_batch1000.v, tb_official1000.v", "Golden 대조, 주최 측 입력 1,000회"],
    ["합성·STA", "ORFS make synth, flow_scripts/sta_one.sh, sta_sweep.tcl", "동일 SDC 규칙, 주기 1.0~2.4 ns 스윕"],
    ["전력", "glsim/run_*.sh → flow_scripts/vcd_power_odb.tcl, blockpower.tcl", "VCD 런 구성: evidence/README.md"],
    ["Vivado 제출", "vivado/submit/make_submit.tcl", "top_tb_1000, 프로젝트 내부 상대 경로"],
    ["추가 분석", "results_sh/v2/ (Python), results_hs/ (RTL 스윕·열화)", "분할 seed 2026–2030, 열화 seed 2026"],
], [2.6, 8.2, 6.2], note="전체 스크립트·원시 결과·실행 로그는 팀 저장소(SafeGuard-EWHA/Pin_Pineapple_Applepen-PPA)에 보존하였다.")

h1(doc, "부록 B. 관련 연구 비교")
table(doc, "조기 종료·동적 추론 선행 연구와 본 설계의 비교", ["연구", "판단 지표", "경로 / 출구 수", "구현", "평가"], [
    ["BranchyNet [1]", "softmax 엔트로피", "LeNet 2, AlexNet/ResNet 3", "CPU/GPU (전용 RTL 없음)", "MNIST/CIFAR-10 정확도·추론 시간"],
    ["CascadeCNN [6]", "확률의 generalized Best-vs-Second-Best", "2 (저정밀 종료 / 고정밀 재계산)",
     "FPGA CNN + ARM CPU (softmax·판단)", "ImageNet, FPGA 실측 처리량"],
    ["Shallow-Deep Networks [7]", "최대 클래스 확률", "7 (내부 6 + 최종 1)", "소프트웨어 (전용 RTL 없음)",
     "CIFAR-10/100, Tiny ImageNet 정확도–FLOPs"],
    ["**AdaPath-NPU (본 설계)**", "정수 로짓 Top-1 − Top-2", "A: 2, B: 3", "Verilog RTL, ASAP7 합성·STA",
     "MNIST/WM-811K, 게이트레벨 VCD 에너지"],
], [3.4, 3.6, 3.2, 3.6, 3.6], hl_rows=(3,),
    note="플랫폼·모델 규모·평가셋이 달라 수치를 직접 순위화하지 않는다.")

h1(doc, "부록 C. 추가 그림")
figure(doc, os.path.join(OUT, "sh2_fig_wm_confusion.png"),
       "WM-811K 4개 클래스 혼동 행렬 (Full vs AdaPath, 칸마다 표본 수와 행 정규화 비율)", 15.0)
figure(doc, os.path.join(OUT, "sh2_fig_error_examples.png"),
       "모델 A 오류 사례: 위 = Easy 오답 중 Margin 상위 6개, 아래 = Hard 입력의 Margin 분위별 사례 (정답·Early/Full 예측·Margin 표기)",
       16.0)

doc.add_page_break()
h1(doc, "부록 D. 전력 원시 근거와 에너지 환산")
para(doc, "아래 값은 orfs/reports_final/power_*.rpt의 Total 행에서 읽은 평균 전력이다. "
     "Internal은 셀 내부 전력, Switching은 부하 충방전 전력, Leakage는 누설 전력이며 Total은 그 합계이다. "
     "표의 합산은 리포트의 표시 정밀도에 따른 반올림 차이를 포함한다.", indent=True)
power_rows = []
for tag in ['ref_a','ref_b','ref_c','Abase','A_easy','A_hard']:
    raw = open(os.path.join(HERE,'..','orfs/reports_final/power_'+tag+'.rpt'), encoding='utf-8').read()
    m = _re.search(r'^Total\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)',raw,_re.M)
    values = [float(v) for v in m.groups()]
    power_rows.append([tag]+[f'{v*1000:.6f}' for v in values])
table(doc, "원본 report_power의 평균 전력 (mW)",
      ['런','Internal','Switching','Leakage','Total'],power_rows,[3.0,3.2,3.2,3.2,3.2],size=9)
para(doc, "원본 A_easy 리포트 발췌: Annotated 1506829 pin activities. Total: Internal 1.612403e-03 W, "
     "Switching 1.754858e-04 W, Leakage 5.182715e-05 W, Total 1.839716e-03 W. "
     "이 annotated 수는 활동 주석 건수이며, 전체 대상 핀 수와 미주석 목록이 없어 100% 주석률로 해석하지 않는다. "
     "리포트의 Clock=0은 CTS 이전 평가에 따른 것으로 실제 클럭망 전력이 0이라는 뜻이 아니다.", indent=True)
table(doc, "측정 창과 추론당 에너지의 환산", ['런','창 길이 (µs)','입력 수','런 에너지 (nJ)','런 평균 (nJ/회)'], [
    ['Reference a','53.836','4','70.486990','17.621748'],
    ['Reference b','53.836','4','70.884731','17.721183'],
    ['Reference c','53.836','4','71.522041','17.880510'],
    ['Baseline_A','39.916','4','83.186501','20.796625'],
    ['AdaPath_A Easy','34.316','4','63.131694','15.782924'],
    ['AdaPath_A 혼합','36.026','4','72.497065','18.124266'],
], [3.7,3.0,2.0,3.7,3.7],size=8.5,
    note="Reference 창은 evidence/gatelevel/sta_and_power_B_ref.txt의 VCD 종료 시각에서 확인하였다. A 창 길이는 "
         "보존된 런 에너지와 Total 전력으로 역산한 값이며 원본 A VCD 끝 시각의 독립 재확인은 아니다. 리셋 12 cycle/이미지 포함.")
para(doc, "E_run[nJ] = P_avg[mW] × Δt[µs], E_avg = E_run/N이다. Reference는 a·b·c 총 12회의 "
     "에너지 평균 17.741147 nJ이다. A 혼합 런은 Hard 1회+Easy 3회이므로 Hard 에너지는 "
     "72.497065−3×15.782924 = 25.148294 nJ이며 혼합 런 평균 18.124266 nJ와 구분한다. "
     "96% Easy+4% Hard의 가중 평균은 약 16.16 nJ이다. 새 전력 측정이 아니라 보존 로그와 기존 에너지 결과의 대조이다.", indent=True)

out = os.path.join(HERE, "결과보고서_PPA.docx")
doc.save(out)
print("written", out, "figs", fig_no[0], "tables", tab_no[0])
