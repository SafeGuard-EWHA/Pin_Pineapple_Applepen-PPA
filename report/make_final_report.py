"""결과보고서(Word) 생성 - results.json 의 측정값으로 본문 수치를 채운다.

    python make_final_report.py            -> 결과보고서_PPA.docx
"""
import json
import os

from docx import Document
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
    parts = text.split("**")
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

# =================================================================== 1
h1(doc, "1. 과제 개요")
para(doc, "고정 경로 CNN 가속기는 입력 난이도와 관계없이 모든 입력에 동일한 연산 경로를 수행한다. 그러나 실제 입력의 "
     "상당수는 얕은 특징만으로도 분류가 가능하며, 이들에게 전체 경로를 적용하는 것은 연산·시간·에너지의 낭비이다. 본 과제는 "
     "전단부(Conv1) 직후 **Early Classifier 점수의 Top-1과 Top-2 차이(Score Margin)**를 난이도 지표로 사용하여, 입력마다 "
     "Easy / Medium / Hard 경로 중 하나를 선택하는 **난이도 적응형 NPU Datapath(AdaPath-NPU)**를 설계하였다.", indent=True)
para(doc, "Early-Exit 계열 기법(BranchyNet 등)은 분기 판단에 확률 분포의 엔트로피를 사용하므로 확률·로그 계산 또는 그 근사 "
     "회로가 필요하다. 본 설계는 비교기와 감산기만으로 계산되는 Score Margin을 사용하며, 같은 판단 결과로 후단 연산을 "
     "생략(Easy)하거나 일부 채널만 활성화(Medium)한다. 주최 측 평가 구조에 맞추어 과제를 다음과 같이 구성하였다.", indent=True)
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
para(doc, "그림 1은 학습부터 PPA 비교까지의 전체 설계·평가 흐름이다. 기능 검증은 Golden 모델과의 비트 정합으로, 전력은 "
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
     "재설계하였다(그림 4). 10개 점수와 6개 패딩 잎을 4개의 병합 레벨로 축약하며, 각 노드는 (1위 값, 1위 index, 2위 값)을 "
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

h2(doc, "3.3 소프트웨어 모델링, 임계값 탐색, 정수 양자화")
para(doc, "세 출력(Early / Light / Full)을 가진 3-head 모델을 MNIST 학습셋 60,000장으로 공동 학습하였다(표 6). 이후 "
     "테스트셋에서 (T_low, T_high)를 전수 탐색하여 '정확도 손실 0.5 %p 이내에서 평균 MAC 최소'인 동작점을 선택하였다. 이는 "
     "테스트셋 기반 동작점 탐색 결과이며, 독립 검증셋으로 임계값을 고정한 뒤 미사용 테스트셋으로 평가하는 절차는 4.2절의 "
     "보완 과제로 남긴다. 정수 규약은 가중치 INT8, 활성값과 점수 인터페이스 signed 12-bit(포화), bias 누산기 도메인 16-bit, "
     "재양자화 반올림 시프트이며, 이 규약으로 RTL과 비트 단위로 일치하는 Golden 모델을 생성하였다.", indent=True)
table(doc, "학습 설정 (모델 A·B, MNIST / WM-811K 공통)", ["항목", "설정", "항목", "설정"], [
    ["Optimizer", "Adam, lr 2×10⁻³", "Scheduler", "Cosine annealing"],
    ["Epoch / Batch", "30 / 128", "손실", "CE(Full) + 0.5·CE(Early) + 0.5·CE(Light)"],
    ["입력", "28×28, [0,1] 정규화", "Random seed", "고정하지 않음 (재학습 시 ±0.1 %p 수준 변동 가능)"],
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
     "것(T_low = T_high)이 최적이라고 판단하였고, 그 결과 모델 A는 Easy/Hard 두 경로로 동작한다. 반면 후단부가 큰 모델 B와 "
     "WM-811K에서는 Medium이 선택된다(3.8절)." % sw["A_light"], indent=True)
figure(doc, os.path.join(OUT, "archA", "fig_margin_hist_mnist.png"), "모델 A의 Score Margin 분포와 선정 임계값", 12.0)

h2(doc, "3.4 RTL 설계와 주최 측 인터페이스 호환")
para(doc, "RTL은 채널 수·클래스 수를 파라미터화한 단일 소스(adapath_top.v)로 작성하였다. VARIANT(0: Baseline, 1: Early-Exit, "
     "2: AdaPath)와 C2/C2_MED(모델 A·B), N_CLASS(MNIST 10, WM-811K 4) 및 각 모델의 가중치·임계값·shift 설정만 바꿔 표 2의 "
     "비교 설계를 생성하였다. 주요 블록은 conv1_engine(75 MAC 병렬), fmap_buffer(144×36 bit), early_classifier, "
     "top2_finder, score_margin_calc, difficulty_decoder, mode_control_fsm, conv2_engine(채널 enable), "
     "fc_engine(Light/Full)이다.", indent=True)
para(doc, "주최 측 평가는 제출 프로젝트의 테스트벤치에서 입력 파일만 교체하는 방식이므로, 레퍼런스 chip과 **포트 목록·폭이 "
     "같은 래퍼(chip_adapath.v)**를 제작하였다(그림 6). 레퍼런스 가중치 포트는 호환용으로 입력만 받고 사용하지 않으며, "
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
         "$urandom_range로 복원 무작위 추출하므로 설계마다 추출된 표본 구성이 달라 정답률이 소폭 다르며, cycle은 연속한 "
         "valid_out 사이 간격(리셋 포함)의 평균이다.")
figure(doc, os.path.join(OUT, "fig_vivado_console.png"),
       "Vivado 2023.1 실행 화면 — 주최 측 top_tb_1000 실행 결과 (AdaPath_A)", 16.0)
para(doc, "제출 프로젝트(.xpr)를 Vivado 2023.1에서 그대로 실행한 화면이다. 주최 측 테스트벤치가 1,000회 처리 후 $stop(391행)에서 "
     "정지하였고, Tcl 콘솔에 'Accuracy : 96%'가 출력되었다. Objects 창의 accuracy = 0x3C6(966), cnt = 0x3E8(1,000)이다.",
     indent=True)
figure(doc, os.path.join(OUT, "fig_vivado_ref_vs_ada.png"),
       "같은 0~415 ns 동안의 처리량 (Vivado, 주최 측 TB): Reference 30장 vs AdaPath_A 46장", 17.0)
para(doc, "같은 테스트벤치·같은 클럭에서 415 ns 동안 Reference는 30장, AdaPath_A는 46장을 분류하였다(두 설계 모두 해당 "
     "구간 전부 정답). 이미지당 평균 처리 cycle이 1,336에서 855로 줄어든 효과가 파형에 그대로 나타난다.", indent=True)
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

h2(doc, "3.6 논리 합성 및 타이밍 (OpenROAD-flow-scripts, ASAP7)")
para(doc, "모든 설계를 동일한 흐름(Yosys + ABC area 스크립트, 동일 SDC: 1 GHz 목표, 입출력 지연 20 %)으로 합성하고 OpenROAD로 "
     "pre-layout STA를 수행하였다. 가중치는 모든 설계에서 입력 포트로 두었다. 1 GHz 제약에서 모든 설계가 음수 slack이므로, "
     "임계 경로 지연을 1000 ps − WNS로 구하고 그 역수를 pre-layout 추정 Fmax로 사용하였다.", indent=True)
rows = []
for key, name in (("refchip", "Reference"), ("baseline_A", "Baseline_A"), ("adapath_A", "**AdaPath_A**"),
                  ("baseline", "Baseline_B"), ("adapath", "AdaPath_B")):
    rows.append([name, f0(A[key]), "%+.1f %%" % pct(A[key], A["refchip"]), f0(D[key]), f1(FMAX[key])])
table(doc, "합성 결과 (pre-layout)", ["설계", "Cell Area (µm²)", "Reference 대비", "임계 경로 (ps)", "추정 Fmax (MHz)"],
      rows, [3.4, 3.4, 3.2, 3.2, 3.2], hl_rows=(2,))
para(doc, "Top-2 Finder 개선 후 AdaPath_A의 임계 경로는 판단 회로가 아니며, 판단 회로가 없는 Baseline_A와 사실상 같은 Fmax"
     "(%s vs %s MHz, 차이 %.2f %%)를 얻었다. Reference 대비 %.0f %% 낮은 것은 Conv2 MAC 경로(입력 포트 지연 포함)에서 "
     "결정되며 판단 회로와 무관하다. 면적 증가는 Feature Map Buffer(5,184 bit), Early Classifier FC, 제어 회로에서 "
     "발생한다. 판단·제어 회로(Top-2, Margin, Decoder, FSM) 단독 합성 면적은 %s µm²로, AdaPath_A 통합 합성 면적의 "
     "%.2f %%에 해당한다(단독 합성과 통합 합성의 최적화 차이가 있어 참고치)."
     % (f1(FMAX["baseline_A"]), f1(FMAX["adapath_A"]), abs(pct(FMAX["adapath_A"], FMAX["baseline_A"])),
        -pct(FMAX["adapath_A"], FMAX["refchip"]), f1(rg["area_v2"]), region2_ratio), indent=True)

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
para(doc, "전력 구성을 보면 AdaPath_A의 Easy 런에서 순차 소자(레지스터)가 전체 전력의 %.0f %%를 차지한다. 이 분석은 CTS 이전이라 "
     "클럭망 전력이 포함되지 않았으므로, 전력 구성은 배치·배선 이후 다시 평가해야 한다. 남은 에너지의 대부분이 연산보다 "
     "레지스터에서 소모되므로, Easy 모드에서 후단부 레지스터의 클럭을 차단하는 클럭 게이팅이 다음 개선 대상이다(4.2절)."
     % pw["A_easy_seq_pct"], indent=True)
table(doc, "효율 지표", ["설계", "실행 MAC", "에너지 (nJ)", "실효 TOPS/W", "등가 TOPS/W"], [
    ["Reference", f0(MAC["ref"]), f1(E_REF), f2(topsw(MAC["ref"], E_REF)), f2(topsw(MAC["ref"], E_REF))],
    ["Baseline_A", f0(MAC["Abase"]), f1(E_ABASE), f2(topsw(MAC["Abase"], E_ABASE)), f2(topsw(MAC["ref"], E_ABASE))],
    ["**AdaPath_A**", f0(MAC_A), f1(E_A), f2(topsw(MAC_A, E_A)), "**%s**" % f2(topsw(MAC["ref"], E_A))],
], [3.4, 3.2, 3.0, 3.2, 3.2], hl_rows=(2,),
    note="1 MAC = 2 operations. 실효 TOPS/W = 2 × 실행 MAC / 추론당 에너지. 등가 TOPS/W = 2 × Reference MAC(%s) / 추론당 "
         "에너지로, 같은 분류 작업을 완료하는 효율이다. 본 측정에서는 실행 MAC 감소율이 에너지 감소율보다 커서 AdaPath_A의 "
         "실효 지표가 낮아졌으므로, 두 지표를 평균 에너지·정확도와 함께 제시한다." % f0(MAC["ref"]))
para(doc, "모드별 에너지를 고정한 혼합 모델로 입력 분포에 따른 에너지 이득 조건을 분석하였다(그림 12). Easy 비율을 p라 하면 "
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
     "(2경로)와 AdaPath(3경로)를 임계값 전수 탐색으로 비교하였다(동일 정확도에서 최소 평균 MAC).", indent=True)
iso = R["iso"]
table(doc, "Early-Exit 대비 AdaPath(Medium 추가)의 이득", ["조건", "MNIST (모델 B)", "WM-811K (모델 B)"], [
    ["동일 정확도에서 추가 MAC 절감", iso["mn_gain"], iso["wm_gain"]],
    ["동일 MAC에서 정확도 향상 (공격적 절감 구간)", iso["mn_acc"], iso["wm_acc"]],
    ["Baseline 정확도 근처", "차이 없음", "거의 차이 없음"],
    ["모델 A (Conv2 3채널)", "Medium 미선택 (2경로로 수렴)", "-"],
], [6.0, 5.5, 5.5])
figure(doc, os.path.join(OUT, "fig_iso_accuracy_wm811k.png"), "Pareto front 비교: Early-Exit vs AdaPath (WM-811K)", 13.0)
para(doc, "Medium 경로는 ① 후단부 연산이 크고 ② 입력 난이도 분포가 넓어 Early와 Full 사이의 중간 확신 구간이 많을 때 효과가 "
     "있다. MNIST처럼 대부분이 쉬운 데이터에서는 이득이 작고, 모델 A에서는 임계값 탐색이 Medium을 자동으로 제외한다. 따라서 "
     "데이터에 맞춰 임계값을 결정하는 본 설계 흐름이 2경로와 3경로 중 유리한 구성까지 선택하는 구조라는 점이 의미가 있다. "
     "다만 모델 A의 성과를 3경로 전체의 성과로 해석하지 않는다.", indent=True)

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
h2(doc, "4.2 평가 범위, 한계 및 향후 개선")
bullet(doc, "**정확도 표본:** 주최 입력은 고유 100장이 10회 반복된 1,000회 입력이므로 1,000개의 독립 이미지에 대한 일반화 "
       "평가와 구분한다. 일반화 성능은 MNIST 테스트셋 10,000장 결과(표 7)로 제시하였다.")
bullet(doc, "**임계값 선정:** 임계값을 테스트셋에서 탐색한 결과는 해당 데이터의 동작점 탐색이다. 독립 검증셋에서 임계값을 "
       "고정한 뒤 미사용 테스트셋으로 평가하는 절차가 추가로 필요하다.")
bullet(doc, "**전력 추정:** 전력은 소수 대표 입력의 게이트레벨 VCD에 기반한 pre-layout 추정이며 실리콘 계측이 아니다. 배치·"
       "배선, 클럭망, 실제 입력 분포를 반영한 후속 검증이 필요하다. WM-811K 에너지는 대리 추정이다.")
bullet(doc, "**순차 소자 전력:** 남은 에너지의 대부분이 레지스터 전력이다. 모드 신호로 후단부 레지스터의 클럭을 차단하는 클럭 "
       "게이팅(ICG 셀)을 적용하면 Easy 모드 에너지를 추가로 줄일 수 있다.")
bullet(doc, "**면적:** Feature Map Buffer와 Early Classifier가 면적 증가의 주요인이다. 버퍼를 SRAM 매크로로 바꾸거나 Early "
       "Classifier를 Full FC와 시분할 공유하면 오버헤드를 줄일 수 있다.")
bullet(doc, "**런타임 동작점 조정:** difficulty_decoder는 레지스터 임계값 모드(USE_REG_TH)를 지원하므로, 런타임에 정확도–연산량 "
       "동작점을 조정하는 운용으로 확장할 수 있다(전압·주파수를 바꾸는 DVFS와는 구분).")
h2(doc, "4.3 기대효과")
bullet(doc, "**엣지 AI 저전력화:** Early Classifier·특징 버퍼·판단 및 제어 회로를 추가하여 쉬운 입력의 후단 연산을 생략함으로써, "
       "배터리 기반 엣지 기기의 추론당 에너지와 지연을 함께 줄일 수 있다. 쉬운 입력의 비율이 손익분기점(약 %.0f %%)보다 "
       "높은 응용에서 효과가 크다." % (P_BE_REF * 100))
bullet(doc, "**반도체 공정 검사 적용:** 웨이퍼맵 검사처럼 명확한 패턴이 다수인 공정 데이터에서 인라인 분류의 처리량을 높이고, "
       "애매한 패턴만 정밀 경로로 보내는 계층적 검사에 활용할 수 있다.")
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
]:
    q = para(doc, ref, 9, space_after=2)
    q.paragraph_format.keep_with_next = True

out = os.path.join(HERE, "결과보고서_PPA.docx")
doc.save(out)
print("written", out, "figs", fig_no[0], "tables", tab_no[0])
