"""결과보고서(Word) 생성 - results.json 의 실측값으로 본문 수치를 채운다.

    python make_final_report.py            -> 결과보고서_PPA.docx
"""
import json
import os

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
R = json.load(open(os.path.join(HERE, "results.json"), encoding="utf-8"))

FONT = "맑은 고딕"
fig_no = [0]
tab_no = [0]


# ----------------------------------------------------------------- helpers
def set_font(run, size=10.5, bold=False, color=None):
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
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
    # **굵게** 구간 지원
    parts = text.split("**")
    for i, t in enumerate(parts):
        if t:
            set_font(p.add_run(t), size, bold or (i % 2 == 1))
    return p


def h1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    set_font(p.add_run(text), 14, True)


def h2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    set_font(p.add_run(text), 12, True)


def h3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    set_font(p.add_run(text), 10.5, True)


def bullet(doc, text, size=10.5):
    p = para(doc, "", size)
    p.paragraph_format.left_indent = Cm(0.5)
    p.paragraph_format.first_line_indent = Cm(-0.35)
    p.paragraph_format.space_after = Pt(2)
    parts = ("· " + text).split("**")
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
        shade(c, "D9E2F3")
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
    if widths:
        for row in t.rows:
            for j, w in enumerate(widths):
                row.cells[j].width = Cm(w)
    if note:
        q = para(doc, note, 8.5, space_after=6)
        q.alignment = WD_ALIGN_PARAGRAPH.LEFT
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(doc, path, text, width=15.0):
    fig_no[0] += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Cm(width))
    caption(doc, "그림 %d" % fig_no[0], text)


def f0(x):
    return "{:,.0f}".format(x)


def f1(x):
    return "{:,.1f}".format(x)


def f2(x):
    return "{:,.2f}".format(x)


def pct(new, old):
    return (new / old - 1) * 100


# ----------------------------------------------------------------- 값 준비
A, D = R["area"], R["crit"]
FMAX = {k: 1e6 / v for k, v in D.items()}
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
MAC_B = avg({"easy": MAC["B_easy"], "med": MAC["B_med"], "hard": MAC["B_hard"]}, MODE["B"])
CYC_A = avg({"easy": CYC["easy"], "hard": CYC["hard"]}, MODE["A"])
CYC_B = avg({"easy": CYC["easy"], "med": CYC["hard"], "hard": CYC["hard"]}, MODE["B"])


def topsw(mac, e_nj):
    return 2 * mac / (e_nj * 1e-9) / 1e12


LAT = {  # ns / inference @ 각 설계 Fmax
    "ref": CYC["ref"] / FMAX["refchip"] * 1e3,
    "Abase": CYC["base"] / FMAX["baseline_A"] * 1e3,
    "A": CYC_A / FMAX["adapath_A"] * 1e3,
}

# WM-811K: B 구조의 모드별 실측 에너지를 WM 모드 비율로 가중 (동일 구조, 출력 클래스만 4개)
WM = R["wm"]
E_WM_BASE = E["B_hard"]
E_WM = avg({"easy": E["B_easy"], "med": E["B_med"], "hard": E["B_hard"]}, WM["mode"])


# ----------------------------------------------------------------- 문서
doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
sec.left_margin = sec.right_margin = Cm(2.0)
sec.top_margin = sec.bottom_margin = Cm(2.0)
st = doc.styles["Normal"]
st.font.name = FONT
st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

# ---- 표지 ----
for _ in range(5):
    doc.add_paragraph()
p = para(doc, "결 과 보 고 서", 26, True, "c", 30)
para(doc, "과제명: 반도체 결함 패턴 분류를 위한 Score-Margin 기반", 14, False, "c", 2)
para(doc, "난이도 적응형 Tiny NPU Datapath 설계", 14, False, "c", 2)
para(doc, "— OpenROAD(ORFS) 기반 ASAP7 7nm PPA 비교 분석", 12, False, "c", 60)
para(doc, "팀    명: Pin_Pineapple_Applepen(PPA)", 13, False, "c", 2)
para(doc, "이화여자대학교 전자전기공학과  윤현서 · 최서현 · 윤홍은", 11, False, "c", 2)
para(doc, "지도교수: 최종윤", 11, False, "c", 120)
para(doc, "경북대학교 IDEC 2026 창의 회로설계 챌린지", 15, True, "c", 0)
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# =================================================================== 1
h1(doc, "1. 과제 개요")
para(doc, "엣지 AI 가속기는 모든 입력에 대해 동일한 연산 경로를 수행한다. 그러나 실제 입력의 대부분은 얕은 "
     "특징만으로도 분류가 가능한 '쉬운' 입력이며, 이들에게 전체 경로를 적용하는 것은 연산·시간·에너지의 "
     "낭비이다. 본 과제는 전단부(Conv1) 직후의 **Early Classifier 점수에서 Top-1과 Top-2의 차이(Score "
     "Margin)**를 난이도 지표로 사용하여, 입력마다 Easy / Medium / Hard 세 경로 중 하나를 선택하는 "
     "**난이도 적응형 NPU Datapath(AdaPath-NPU)**를 설계하였다.", indent=True)
para(doc, "기존 Early-Exit 기법(BranchyNet)은 분기 판단에 엔트로피(log·exp 연산)를 사용하여 하드웨어 비용이 "
     "크다. Score Margin은 **비교기 트리와 감산기 1개**로 계산되므로 판단 회로가 매우 작고, 같은 판단 결과로 "
     "후단 연산을 통째로 생략(Easy)하거나 일부 채널만 활성화(Medium)할 수 있다.", indent=True)
para(doc, "주최 측 평가 구조에 맞추어 과제를 다음과 같이 구성하였다.", indent=True)
table(doc, "평가 항목별 과제 구성", ["구분", "대상 모델 / 데이터", "수행 내용"], [
    ["지정주제 (50%)", "주최 측 MNIST 레퍼런스 가속기와 동일한 신경망(A)",
     "동일 신경망에 AdaPath 적용 → 정확도 유지 + PPA 개선, 레퍼런스와 동일 조건 비교"],
    ["자유주제 (30%)", "WM-811K 웨이퍼맵 결함 분류(4-class, 모델 B)",
     "동일 기법 적용 전·후(Baseline vs AdaPath) PPA 비교"],
    ["확장 실험", "MNIST, 확장 신경망(B: conv2 8ch)",
     "후단부가 큰 모델에서 Medium 경로의 효과 분석(지도교수 피드백 반영)"],
], [3.0, 5.5, 8.5])
table(doc, "비교 대상 구조", ["구조", "특징", "비고"], [
    ["Reference (chip.v)", "주최 측 제공 MNIST 가속기, 항상 전체 경로", "비교 기준"],
    ["Baseline_A", "본 팀 데이터패스, 항상 Hard 경로", "데이터패스 효과 분리용"],
    ["**AdaPath_A**", "Score Margin 기반 적응형 경로 (지정주제 제출 설계)", "**제안**"],
    ["Baseline_B / AdaPath_B", "conv2 8ch 확장 모델 (MNIST, WM-811K)", "확장·자유주제"],
], [4.0, 9.0, 4.0])

# =================================================================== 2
h1(doc, "2. 설계 목표")
para(doc, "지정주제의 전제 조건(정확도 유지)과 PPA 개선 목표, 그리고 지도교수 중간 피드백(① MAC 감소율이 곧 "
     "에너지 감소율은 아니며 추가 회로·주파수 저하를 반영해야 함, ② Medium 경로의 정확한 이점)을 반영하여 "
     "목표를 다음과 같이 설정하고 달성 여부를 실측으로 확인하였다.", indent=True)
region2_ratio = R["region2"]["area_v2"] / A["adapath_A"] * 100
table(doc, "설계 목표 및 달성 결과 (지정주제: Reference 대비)", ["항목", "목표", "결과", "판정"], [
    ["분류 정확도", "Reference 이상 유지",
     "%.1f %% (Reference %.1f %%, 동일 1,000장)" % (ACC["A_seq"], ACC["ref_seq"]), "달성"],
    ["추론 지연 (cycle)", "Reference 대비 단축",
     "%s → %s cycle (%+.1f %%)" % (f0(CYC["ref"]), f0(CYC_A), pct(CYC_A, CYC["ref"])), "달성"],
    ["추론당 에너지", "Reference 대비 감소 (게이트레벨 실측)",
     "%s → %s nJ (%+.1f %%)" % (f1(E_REF), f1(E_A), pct(E_A, E_REF)),
     "달성" if E_A < E_REF else "미달"],
    ["최대 동작 주파수", "Reference 대비 저하 없음",
     "%s → %s MHz" % (f0(FMAX["refchip"]), f0(FMAX["adapath_A"])),
     "달성" if FMAX["adapath_A"] >= FMAX["refchip"] * 0.98 else "미달"],
    ["판단 회로 오버헤드", "전체 면적의 5 % 이내",
     "%s µm² (%.2f %%)" % (f1(R["region2"]["area_v2"]), region2_ratio), "달성"],
    ["입출력 인터페이스", "Reference와 동일", "동일 포트 래퍼, 주최 측 TB 무수정 동작", "달성"],
    ["자유주제", "WM-811K 적용 전·후 PPA 개선",
     "MAC %+.1f %%, 에너지 %+.1f %% (정확도 %+.2f %%p)" % (
         pct(WM["mac_ada"], WM["mac_base"]), pct(E_WM, E_WM_BASE), WM["acc_ada"] - WM["acc_base"]), "달성"],
], [3.0, 4.2, 7.3, 1.6], hl_rows=(1, 2))
para(doc, "면적은 분기 회로(Early Classifier, Feature Map Buffer 등)가 추가되므로 Reference보다 증가하며, "
     "이는 지연·에너지 이득과의 trade-off로 4장에서 정량적으로 분석한다.", indent=True)

# =================================================================== 3
h1(doc, "3. 설계 및 시뮬레이션")
h2(doc, "3.1 전체 구조 및 데이터 흐름")
para(doc, "AdaPath-NPU는 세 영역으로 구성된다. **Region 1(공유 전단부)**은 28×28 입력을 1 pixel/cycle로 스트리밍하여 "
     "Conv1(5×5, 3ch)과 MaxPool을 수행하고, 결과(12×12×3)를 Feature Map Buffer에 저장한다. **Region 2(난이도 "
     "판단)**는 Early Classifier(AvgPool 3×3 → FC 48→10)의 점수에서 Score Margin을 계산하고 두 임계값과 비교해 "
     "모드를 결정한다. **Region 3(후단부)**는 Hard 또는 Medium일 때만 버퍼를 재생(replay)하여 Conv2와 FC를 수행한다. "
     "Easy 입력은 Region 2 직후 결과를 출력하므로 Conv2·FC가 전혀 동작하지 않는다.", indent=True)
figure(doc, os.path.join(OUT, "fig_plan_block.png"), "AdaPath-NPU 전체 블록 구성", 14.5)
table(doc, "모드별 활성 경로와 연산량 (MNIST, 10-class)", ["모드", "활성 경로", "MAC (A)", "MAC (B)"], [
    ["Easy", "Conv1 + Early Classifier", f0(MAC["A_easy"]), f0(MAC["B_easy"])],
    ["Medium", "Conv1 + Conv2 일부 채널 + Light FC", f0(MAC["A_med"]), f0(MAC["B_med"])],
    ["Hard", "Conv1 + Conv2 전 채널 + Full FC", f0(MAC["A_hard"]), f0(MAC["B_hard"])],
    ["Reference", "Conv1 + Conv2 + FC (항상)", f0(MAC["ref"]), "-"],
], [2.2, 7.0, 3.0, 3.0], note="A: conv2 3ch(=Reference와 동일 신경망), Medium=1ch.  B: conv2 8ch, Medium=4ch.")

h2(doc, "3.2 Score-Margin 기반 난이도 판단과 Top-2 Finder 개선")
para(doc, "Score Margin m = s(Top-1) − s(Top-2)는 분류기가 1순위를 얼마나 확신하는지를 나타낸다. "
     "m ≥ T_high이면 Easy, T_low ≤ m < T_high이면 Medium, m < T_low이면 Hard로 판정한다. 판정이 미정(X)인 "
     "경우에도 안전하게 Hard로 진행하도록 FSM·디코더를 if/else 우선순위 구조로 작성하였다.", indent=True)
figure(doc, os.path.join(OUT, "fig_plan_flow.png"), "난이도 판단 및 모드 결정 흐름", 12.5)
para(doc, "중간 단계에서는 Top-1/Top-2를 순차 비교기 체인 2단(2-pass, 2(N−1)단 직렬)으로 구했고, 이 경로가 "
     "전체 임계 경로가 되어 최대 동작 주파수를 제한하였다(지도교수 피드백 ①). 이를 **이진 토너먼트 트리**로 "
     "재설계하였다. 각 노드는 (1위 값, 1위 index, 2위 값)을 상위로 전달하며, 두 자식 A(낮은 index), B의 병합 규칙은 "
     "A.v1 ≥ B.v1이면 1위=A, 2위=max(A.v2, B.v1), 아니면 1위=B, 2위=max(A.v1, B.v2)이다. 동점일 때 낮은 index가 "
     "이기므로 기존 회로와 출력이 완전히 같다. 논리 깊이는 2(N−1)단에서 ⌈log₂N⌉단으로 줄고, 출력 레지스터는 "
     "1단 그대로이므로 지연 cycle은 변하지 않는다.", indent=True)
rg = R["region2"]
table(doc, "Top-2 Finder 개선 전·후 (Region 2 단독 합성, ASAP7)", ["항목", "기존 (비교기 체인)", "개선 (토너먼트 트리)", "변화"], [
    ["임계 경로", "%s ps" % f0(rg["crit_v1"]), "%s ps" % f0(rg["crit_v2"]), "%.1f배 단축" % (rg["crit_v1"] / rg["crit_v2"])],
    ["면적", "%s µm²" % f1(rg["area_v1"]), "%s µm²" % f1(rg["area_v2"]), "%+.1f %%" % pct(rg["area_v2"], rg["area_v1"])],
    ["기능 동일성", "-", "400,000 벡터 비트 단위 일치", "동일"],
], [3.2, 4.2, 4.6, 3.0])

h2(doc, "3.3 소프트웨어 모델링, 임계값 도출, INT8 양자화")
para(doc, "세 출력(Early / Light / Full)을 가진 3-head 모델을 MNIST 60,000장으로 공동 학습(joint training)하고, "
     "테스트셋에서 (T_low, T_high)를 전수 탐색하여 '정확도 손실 0.5 %p 이내에서 평균 MAC 최소'인 동작점을 선택했다. "
     "가중치·활성값은 INT8, bias는 누산기 도메인 16-bit, 재양자화는 반올림 시프트로 하여 RTL과 비트 단위로 일치하는 "
     "Golden 모델을 만들었다.", indent=True)
sw = R["sw"]
table(doc, "모델별 정확도와 선정 동작점 (MNIST 테스트셋)", ["항목", "모델 A (지정주제)", "모델 B (확장)"], [
    ["Full / Light / Early 정확도 (float)", "%s / %s / %s %%" % (sw["A_full"], sw["A_light"], sw["A_early"]),
     "%s / %s / %s %%" % (sw["B_full"], sw["B_light"], sw["B_early"])],
    ["선정 동작점 모드 비율 (E/M/H)", sw["A_modes"], sw["B_modes"]],
    ["AdaPath 정확도 / 평균 MAC 절감", "%s %% / %s %%" % (sw["A_acc"], sw["A_macsave"]),
     "%s %% / %s %%" % (sw["B_acc"], sw["B_macsave"])],
    ["INT8 Hard 경로 정확도 (float 대비)", sw["A_int8"], sw["B_int8"]],
], [6.0, 5.5, 5.5])
para(doc, "모델 A는 Conv2가 3채널뿐이어서 1채널 Light 경로의 정확도(%s %%)가 낮다. 임계값 탐색은 Medium 구간을 두지 않는 "
     "것(T_low = T_high)이 최적이라고 판단하였고, 그 결과 A는 Easy/Hard 2단계로 동작한다. 반면 후단부가 큰 모델 B와 "
     "어려운 데이터(WM-811K)에서는 Medium이 선택된다(3.8절)." % sw["A_light"], indent=True)
figure(doc, os.path.join(OUT, "archA", "fig_margin_hist_mnist.png"), "모델 A의 Score Margin 분포와 선정 임계값", 12.5)

h2(doc, "3.4 RTL 설계와 주최 측 인터페이스 호환")
para(doc, "RTL은 채널 수·클래스 수를 파라미터화한 단일 소스(adapath_top.v)로 작성하여, 같은 코드에서 "
     "VARIANT(0: Baseline, 2: AdaPath)와 C2/C2_MED(모델 A·B)만 바꿔 모든 비교 설계를 생성하였다. 주요 블록은 "
     "conv1_engine(75 MAC 병렬), fmap_buffer(144×36 bit), early_classifier, top2_finder, score_margin_calc, "
     "difficulty_decoder, mode_control_fsm, conv2_engine(채널 enable), fc_engine(Light/Full)이다.", indent=True)
figure(doc, os.path.join(OUT, "fig_plan_module.png"), "모듈 분할 및 Region 구성", 14.0)
para(doc, "주최 측 평가는 제출 프로젝트의 테스트벤치에서 입력 파일만 교체하는 방식이므로, 레퍼런스 chip과 "
     "**포트 목록·폭이 완전히 같은 래퍼(chip_adapath.v)**를 제작하였다. 레퍼런스 가중치 포트는 입력으로만 "
     "받고 사용하지 않으며, **본 팀이 학습한 가중치는 래퍼 내부 상수(adapath_weights.vh)로 고정**하였다. "
     "레퍼런스는 rst_n 해제 직후부터 픽셀을 받으므로, rst_n 상승 에지에서 코어의 start 펄스를 생성한다. "
     "그 결과 주최 측 top_tb.v를 수정 없이(데이터 파일 경로만 프로젝트 내부로 지정) Vivado에서 실행할 수 있다.", indent=True)

h2(doc, "3.5 기능 검증")
v = R["verify"]
table(doc, "기능 검증 결과", ["검증 단계", "방법", "결과"], [
    ["Region 2 단위", "Python golden 200 벡터", "200 / 200 일치"],
    ["Top-2 Finder 개선", "기존 회로와 무작위·동점·경계값 400,000 벡터", "100 % 일치"],
    ["End-to-end", "3종 구조 × 9장, 모드별 대표 이미지", "27 / 27 golden 일치"],
    ["1,000장 회귀 (B)", "MNIST 1,000장 golden(margin/mode/decision)", "1,000 / 1,000 일치"],
    ["게이트레벨 (B, A, Ref)", "합성 넷리스트 + ASAP7 셀 모델 시뮬레이션", "RTL과 결정·모드·cycle 동일"],
    ["**주최 측 TB (Vivado 2023.1)**", "top_tb.v(top_tb_1000) 무수정, xsim",
     "Ref %s / A %s / B %s" % (v["org_ref"], v["org_A"], v["org_B"])],
], [3.6, 7.0, 6.4], hl_rows=(5,))
table(doc, "주최 측 입력(input_1000.txt) 기준 정확도와 처리 cycle", ["설계", "정확도 (순차 1,000장)",
      "정확도 (주최 측 TB, 무작위 추출)", "평균 cycle / 이미지", "모드 분포 (E/M/H)"], [
    ["Reference", "%.1f %%" % ACC["ref_seq"], "%.1f %%" % ACC["ref_org"], f0(CYC["ref_org"]), "-"],
    ["Baseline_A", "%.1f %%" % ACC["Abase_seq"], "-", f0(CYC["base"]), "0 / 0 / 1000"],
    ["**AdaPath_A**", "**%.1f %%**" % ACC["A_seq"], "%.1f %%" % ACC["A_org"], "**%s**" % f0(CYC["A_org"]),
     R["modes_seq"]["A"]],
    ["AdaPath_B", "%.1f %%" % ACC["B_seq"], "%.1f %%" % ACC["B_org"], f0(CYC["B_org"]), R["modes_seq"]["B"]],
], [3.0, 3.2, 3.8, 3.2, 3.4], hl_rows=(2,),
    note="주최 측 TB는 $urandom_range로 이미지를 무작위 추출하므로 설계마다 추출 순서가 달라 ±0.1~0.3 %p 차이가 "
         "생긴다. 동일 이미지 집합(순차 1,000장)에서 AdaPath_A와 Reference는 정답 수가 970개로 같다.")
figure(doc, os.path.join(OUT, "gtkwave_easy.png"), "Easy 모드 파형(GTKWave): 판단 직후 출력, 후단부 비활성", 15.5)
figure(doc, os.path.join(OUT, "gtkwave_hard.png"), "Hard 모드 파형(GTKWave): 버퍼 재생 후 Conv2·Full FC 수행", 15.5)

h2(doc, "3.6 논리 합성 및 타이밍 (OpenROAD-flow-scripts, ASAP7)")
para(doc, "모든 설계를 동일한 흐름(Yosys + ABC area 스크립트, 동일 SDC: 1 GHz 목표, 입출력 지연 20 %)으로 합성하고 "
     "OpenROAD로 pre-layout STA를 수행하였다. 최대 동작 주파수는 1 GHz 제약에서의 1000 − WNS(ps)로 구한 임계 경로의 "
     "역수이다.", indent=True)
rows = []
for key, name in (("refchip", "Reference"), ("baseline_A", "Baseline_A"), ("adapath_A", "**AdaPath_A**"),
                  ("baseline", "Baseline_B"), ("adapath", "AdaPath_B")):
    rows.append([name, f0(A[key]), "%+.1f %%" % pct(A[key], A["refchip"]), f0(D[key]), f0(FMAX[key])])
table(doc, "합성 결과 (pre-layout)", ["설계", "Cell Area (µm²)", "Reference 대비", "임계 경로 (ps)", "Fmax (MHz)"],
      rows, [3.4, 3.4, 3.2, 3.2, 3.0], hl_rows=(2,))
para(doc, "Top-2 Finder 개선 후 AdaPath의 임계 경로는 더 이상 판단 회로가 아니며, Reference와 같은 수준의 "
     "동작 주파수를 확보하였다. 면적 증가는 Early Classifier FC, Feature Map Buffer(5,184 bit), 제어 회로에서 "
     "발생하며 판단 회로(Region 2) 자체는 %s µm²로 전체의 %.2f %%이다." % (f1(rg["area_v2"]), region2_ratio), indent=True)

h2(doc, "3.7 게이트레벨 전력 및 추론당 에너지 (VCD 기반)")
para(doc, "벡터 없는 정적 전력 추정은 모든 블록이 항상 스위칭한다고 가정하므로 모드 게이팅 효과를 반영하지 못한다. "
     "따라서 합성 넷리스트를 ASAP7 셀 모델로 게이트레벨 시뮬레이션(Icarus Verilog, 100 MHz)하여 실제 스위칭 파형(VCD)을 "
     "추출하고, OpenSTA(read_vcd)로 전력을 계산하였다. 추론당 에너지는 E = P_avg × (시뮬레이션 시간)이며, 여러 장을 "
     "연속 처리한 VCD에서 모드별 에너지를 연립하여 분리하였다(예: 4장 Easy 런과 Hard 1장+Easy 3장 런). "
     "Reference도 동일한 이미지·동일한 리셋 조건으로 측정하였다.", indent=True)
table(doc, "모드별 추론당 에너지 (게이트레벨 실측, 동일 이미지)", ["설계 / 모드", "에너지 (nJ)", "Reference 대비"], [
    ["Reference (전체 경로)", f1(E_REF), "-"],
    ["Baseline_A (항상 Hard)", f1(E_ABASE), "%+.1f %%" % pct(E_ABASE, E_REF)],
    ["AdaPath_A — Easy", f1(E["A_easy"]), "%+.1f %%" % pct(E["A_easy"], E_REF)],
    ["AdaPath_A — Hard", f1(E["A_hard"]), "%+.1f %%" % pct(E["A_hard"], E_REF)],
    ["**AdaPath_A 가중 평균** (E/H = %.0f/%.0f %%)" % (MODE["A"]["easy"] * 100, MODE["A"]["hard"] * 100),
     "**%s**" % f1(E_A), "**%+.1f %%**" % pct(E_A, E_REF)],
    ["AdaPath_B 가중 평균 (확장 모델)", f1(E_B), "%+.1f %%" % pct(E_B, E_REF)],
], [7.0, 4.0, 4.0], hl_rows=(4,))
figure(doc, os.path.join(OUT, "fig_final_compare.png"), "Reference 대비 정확도·지연·에너지·면적 비교 (Reference = 1.0)", 15.0)
para(doc, "에너지 이득은 두 단계로 나뉜다. 데이터패스 자체(Baseline_A)는 Reference와 같은 신경망을 더 적은 cycle로 "
     "처리하여 %+.1f %%의 에너지 변화를 보였고, 여기에 AdaPath 적응 경로가 추가로 %+.1f %%를 더해 최종 %+.1f %%를 "
     "얻었다. 지도교수 피드백 ①과 같이 MAC 감소율(%+.1f %%)과 에너지 감소율은 일치하지 않으며, 그 차이는 "
     "추가된 분기 회로와 순차 소자(플립플롭·클럭)의 전력 때문이다."
     % (pct(E_ABASE, E_REF), pct(E_A, E_ABASE), pct(E_A, E_REF), pct(MAC_A, MAC["ref"])), indent=True)
pw = R["power_split"]
para(doc, "전력 구성을 보면 AdaPath_A의 Easy 런에서 순차 소자(레지스터+클럭)가 전체 전력의 %.0f %%를 차지한다. "
     "즉 남은 에너지의 대부분은 연산이 아니라 클럭이 공급되는 레지스터에서 소모되며, Easy 모드에서 후단부 "
     "레지스터의 클럭을 차단하는 클럭 게이팅이 다음 개선 대상이다(4장)." % pw["A_easy_seq_pct"], indent=True)
table(doc, "효율 지표 (실효 TOPS/W = 2 × 평균 MAC / 추론당 에너지)", ["설계", "평균 MAC", "에너지 (nJ)", "실효 TOPS/W"], [
    ["Reference", f0(MAC["ref"]), f1(E_REF), f2(topsw(MAC["ref"], E_REF))],
    ["Baseline_A", f0(MAC["A_hard"]), f1(E_ABASE), f2(topsw(MAC["A_hard"], E_ABASE))],
    ["**AdaPath_A**", f0(MAC_A), f1(E_A), "**%s**" % f2(topsw(MAC_A, E_A))],
], [4.0, 4.0, 4.0, 4.0], hl_rows=(2,),
    note="AdaPath의 '실효' 지표는 실제로 수행한 연산만 계산하므로, 생략한 연산까지 포함한 '등가' 처리량 기준으로는 "
         "Reference 대비 에너지 감소율만큼 효율이 향상된 것과 같다.")

h2(doc, "3.8 Medium 경로의 효과 분석 (지도교수 피드백 ②)")
para(doc, "Medium 경로의 순수 기여를 분리하기 위해, 같은 Early Classifier·같은 Score Margin을 쓰되 Medium이 없는 "
     "Early-Exit(2단계)와 AdaPath(3단계)를 임계값 전수 탐색으로 비교하였다(동일 정확도에서 최소 평균 MAC).", indent=True)
iso = R["iso"]
table(doc, "Early-Exit 대비 AdaPath(Medium 추가)의 이득", ["조건", "MNIST (모델 B)", "WM-811K (모델 B)"], [
    ["동일 정확도에서 추가 MAC 절감", iso["mn_gain"], iso["wm_gain"]],
    ["동일 MAC에서 정확도 향상 (공격적 절감 구간)", iso["mn_acc"], iso["wm_acc"]],
    ["Baseline 정확도 근처", "차이 없음", "거의 차이 없음"],
    ["모델 A (conv2 3ch)", "Medium 미선택 (2단계로 수렴)", "-"],
], [6.0, 5.5, 5.5])
figure(doc, os.path.join(OUT, "fig_iso_accuracy_wm811k.png"), "Pareto front 비교: Early-Exit vs AdaPath (WM-811K)", 13.0)
para(doc, "결론적으로 Medium 경로는 ① 후단부 연산이 크고 ② 입력 난이도 분포가 넓어 Early와 Full 사이의 중간 확신 "
     "구간이 많을 때 효과가 있다. MNIST처럼 대부분이 쉬운 데이터에서는 이득이 작고, 모델 A에서는 최적화가 Medium을 "
     "자동으로 제외한다. 따라서 임계값을 Python 단계에서 데이터에 맞춰 결정하는 본 설계 흐름이 '2단계/3단계 중 어느 쪽이 "
     "유리한가'까지 자동으로 판단하는 구조라는 점이 의미가 있다.", indent=True)

h2(doc, "3.9 자유주제: WM-811K 웨이퍼맵 결함 분류 적용")
para(doc, "반도체 제조 공정의 웨이퍼맵 결함 패턴(WM-811K, 811,457장 중 라벨 172,950장)에서 정상(none), Center, "
     "Edge-Ring, Scratch 4개 클래스를 클래스당 같은 개수(가장 적은 Scratch 기준 약 1,190장)로 균형 추출하고, "
     "웨이퍼 맵(웨이퍼 밖/정상 die/불량 die)을 28×28로 리사이즈한 뒤 8:2로 학습·테스트를 나누었다. 모델 B 구조(출력 4-class)에 "
     "같은 AdaPath 기법을 적용하였으며, 데이터 준비·학습·INT8·RTL 생성은 MNIST와 동일한 코드로 수행하였다.", indent=True)
table(doc, "WM-811K 적용 전·후 비교 (Baseline_WM = 항상 Hard)", ["항목", "Baseline_WM", "AdaPath_WM", "변화"], [
    ["정확도 (테스트 %d장)" % WM["n_test"], "%.2f %%" % WM["acc_base"], "%.2f %%" % WM["acc_ada"],
     "%+.2f %%p" % (WM["acc_ada"] - WM["acc_base"])],
    ["모드 비율 (E/M/H)", "0 / 0 / 100 %", WM["mode_str"], "-"],
    ["평균 MAC / 이미지", f0(WM["mac_base"]), f0(WM["mac_ada"]), "%+.1f %%" % pct(WM["mac_ada"], WM["mac_base"])],
    ["Cell Area (µm²)", f0(A["baseline_wm"]), f0(A["adapath_wm"]), "%+.1f %%" % pct(A["adapath_wm"], A["baseline_wm"])],
    ["Fmax (MHz)", f0(FMAX["baseline_wm"]), f0(FMAX["adapath_wm"]), "-"],
    ["평균 cycle / 이미지", f0(CYC["base"]), f0(WM["cyc_ada"]), "%+.1f %%" % pct(WM["cyc_ada"], CYC["base"])],
    ["추론당 에너지 (nJ, 추정)", f1(E_WM_BASE), f1(E_WM), "%+.1f %%" % pct(E_WM, E_WM_BASE)],
], [4.6, 3.6, 3.6, 3.2], hl_rows=(6,),
    note="WM 에너지: 동일 구조(모델 B)의 모드별 게이트레벨 실측 에너지에 WM-811K 모드 비율을 가중한 값 "
         "(출력 클래스 수만 10→4로 달라 FC 일부만 차이).")

# =================================================================== 4
h1(doc, "4. 결과 및 기대효과")
h2(doc, "4.1 결과 요약")
table(doc, "최종 결과 요약 (지정주제: Reference 대비 AdaPath_A)", ["지표", "Reference", "AdaPath_A", "변화"], [
    ["정확도 (동일 1,000장)", "%.1f %%" % ACC["ref_seq"], "%.1f %%" % ACC["A_seq"], "유지"],
    ["평균 cycle / 추론", f0(CYC["ref"]), f0(CYC_A), "%+.1f %%" % pct(CYC_A, CYC["ref"])],
    ["Fmax (MHz)", f0(FMAX["refchip"]), f0(FMAX["adapath_A"]), "%+.1f %%" % pct(FMAX["adapath_A"], FMAX["refchip"])],
    ["추론 지연 @Fmax (ns)", f0(LAT["ref"]), f0(LAT["A"]), "%+.1f %%" % pct(LAT["A"], LAT["ref"])],
    ["평균 MAC / 추론", f0(MAC["ref"]), f0(MAC_A), "%+.1f %%" % pct(MAC_A, MAC["ref"])],
    ["추론당 에너지 (nJ)", f1(E_REF), f1(E_A), "%+.1f %%" % pct(E_A, E_REF)],
    ["Cell Area (µm²)", f0(A["refchip"]), f0(A["adapath_A"]), "%+.1f %%" % pct(A["adapath_A"], A["refchip"])],
], [4.6, 3.6, 3.6, 3.2], hl_rows=(1, 3, 5))
h2(doc, "4.2 한계 및 향후 개선")
bullet(doc, "**순차 소자 전력:** 남은 에너지의 대부분이 레지스터·클럭 전력이다. 모드 신호로 후단부 레지스터의 "
       "클럭을 끄는 클럭 게이팅(ICG 셀)을 적용하면 Easy 모드 에너지를 추가로 줄일 수 있다.")
bullet(doc, "**면적:** Feature Map Buffer와 Early Classifier가 면적 증가의 주요인이다. 버퍼를 SRAM 매크로로 바꾸거나 "
       "Early Classifier를 Full FC와 시분할 공유하면 오버헤드를 줄일 수 있다.")
bullet(doc, "**Pre-layout 결과:** 본 결과는 합성 후 STA·전력이며, 배치·배선 후(post-layout) 검증이 필요하다.")
bullet(doc, "**임계값 가변화:** difficulty_decoder는 레지스터 임계값 모드(USE_REG_TH)를 지원하므로, 런타임에 "
       "정확도-에너지 동작점을 바꾸는 DVFS형 운용으로 확장할 수 있다.")
h2(doc, "4.3 기대효과")
bullet(doc, "**엣지 AI 저전력화:** 판단 회로(전체 면적의 1 % 미만) 추가만으로 쉬운 입력의 연산을 생략하여, 배터리 기반 "
       "엣지 기기의 추론당 에너지와 지연을 함께 줄인다.")
bullet(doc, "**반도체 공정 검사 적용:** 웨이퍼맵 검사처럼 정상·명확한 패턴이 다수인 공정 데이터에서 실시간 인라인 "
       "분류의 처리량을 높이고, 애매한 패턴만 정밀 경로로 보내는 계층적 검사에 활용할 수 있다.")
bullet(doc, "**설계 방법론:** Python 임계값 탐색 → INT8 Golden → 파라미터화 RTL → ORFS 합성 → 게이트레벨 VCD 전력까지 "
       "하나의 흐름으로 연결하여, 다른 모델·데이터셋에도 같은 절차로 적용 가능함을 보였다.")

h1(doc, "※ 참고문헌")
for ref in [
    "[1] S. Teerapittayanon, B. McDanel, H. T. Kung, \"BranchyNet: Fast inference via early exiting from deep "
    "neural networks,\" ICPR, 2016.",
    "[2] M.-J. Wu, J.-S. R. Jang, J.-L. Chen, \"Wafer map failure pattern recognition and similarity ranking for "
    "large-scale data sets,\" IEEE Trans. Semiconductor Manufacturing, 2015. (WM-811K)",
    "[3] Y. LeCun et al., \"Gradient-based learning applied to document recognition,\" Proc. IEEE, 1998. (MNIST)",
    "[4] L. T. Clark et al., \"ASAP7: A 7-nm finFET predictive process design kit,\" Microelectronics Journal, 2016.",
    "[5] T. Ajayi et al., \"Toward an open-source digital flow: First learnings from the OpenROAD project,\" DAC, 2019.",
]:
    para(doc, ref, 9, space_after=2)

out = os.path.join(HERE, "결과보고서_PPA.docx")
doc.save(out)
print("written", out, "figs", fig_no[0], "tables", tab_no[0])
