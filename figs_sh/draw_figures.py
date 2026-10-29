"""Rebuild publication figures: python draw_figures.py (matplotlib, Malgun Gothic)."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib import font_manager

OUT=Path(__file__).resolve().parent
FONT=font_manager.FontProperties(fname='C:/Windows/Fonts/malgun.ttf').get_name()
plt.rcParams.update({'font.family':FONT,'svg.fonttype':'path','axes.unicode_minus':False})
INK='#202831'; GRAY='#65717d'; LINE='#bac2c9'; COMMON='#f0f2f4'
E='#278353'; EF='#e8f4ec'; M='#a67b00'; MF='#fff4c9'; H='#ba4545'; HF='#fbeaea'
def canvas(w,h,title,sub):
    fig,ax=plt.subplots(figsize=(w,h)); fig.patch.set_facecolor('white')
    ax.set(xlim=(0,w),ylim=(h,0)); ax.axis('off');fig.subplots_adjust(0,0,1,1)
    txt(ax,.35,.40,title,18,'left',weight='bold')
    txt(ax,.35,.85,sub,10,'left',color=GRAY)
    return fig,ax
def txt(ax,x,y,s,sz=11,ha='center',color=INK,weight='normal'):
    return ax.text(x,y,s.replace('−','-'),fontsize=sz,ha=ha,va='center',color=color,weight=weight,linespacing=1.5)
def box(ax,x,y,w,h,title,sub='',fill=COMMON,edge=LINE,sz=11):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.015,rounding_size=0.06',facecolor=fill,edgecolor=edge,lw=1.2))
    txt(ax,x+w/2,y+h*(.36 if sub else .5),title,sz,weight='bold')
    if sub:txt(ax,x+w/2,y+h*.72,sub,sz-1,color=GRAY)
def route(ax,pts,c=GRAY,dash=False,lw=1.5):
    for a,b in zip(pts[:-2],pts[1:-1]):ax.plot([a[0],b[0]],[a[1],b[1]],color=c,lw=lw,ls='--' if dash else '-')
    ax.add_patch(FancyArrowPatch(pts[-2],pts[-1],arrowstyle='-|>',mutation_scale=12,lw=lw,color=c,linestyle='--' if dash else '-'))
def region(ax,x,y,w,h,label):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=0.1',facecolor='white',edgecolor=LINE,lw=1))
    txt(ax,x+.18,y+.25,label,11,'left',weight='bold')
def save(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=300,facecolor='white')
    fig.savefig(OUT/(name+'.svg'),facecolor='white')
    plt.close(fig)

def architecture():
    f,a=canvas(16,10.4,'AdaPath-NPU Architecture','입력 난이도에 따라 후단부 연산을 선택하는 스트리밍 데이터패스 · MNIST 10-class 기준')
    region(a,.35,1.25,15.3,1.85,'Region 1  |  공유 전단부')
    box(a,.65,1.95,2.1,.8,'Input Stream','28×28 · 1 px/cycle')
    box(a,3.4,1.95,2.8,.8,'Conv1 5×5','1→3 ch · 75 MAC 병렬')
    box(a,6.85,1.95,3,.8,'MaxPool 2×2 + ReLU','24×24×3 → 12×12×3')
    box(a,11,1.95,4.2,.8,'Feature Map Buffer','12×12×3×12 bit = 5,184 bit')
    for x,z in [(2.75,3.4),(6.2,6.85),(9.85,11)]:route(a,[(x,2.35),(z,2.35)])
    region(a,.35,3.65,15.3,2.2,'Region 2  |  난이도 판단 및 제어')
    box(a,.65,4.35,3.3,.95,'Early Classifier','AvgPool 3×3 → FC 48→10')
    box(a,4.5,4.35,2.25,.95,'Top-2 Finder','토너먼트 트리')
    box(a,7.3,4.35,2.25,.95,'Score Margin','Top1 − Top2 · 감산기 1개')
    box(a,10.1,4.35,2.55,.95,'Difficulty Decoder','T_low, T_high')
    box(a,13.2,4.35,2.15,.95,'Mode Control FSM','모드별 enable 생성',sz=10)
    for x,z in [(3.95,4.5),(6.75,7.3),(9.55,10.1),(12.65,13.2)]:route(a,[(x,4.825),(z,4.825)])
    route(a,[(10.25,2.35),(10.25,3.35),(3.7,3.35),(3.7,4.35)])
    txt(a,6.7,3.17,'풀링 출력을 Early Classifier와 버퍼에 동시 공급',9,color=GRAY)
    region(a,.35,6.4,11.95,2.45,'Region 3  |  Medium / Hard에서만 실행')
    box(a,.65,7.25,2,.8,'Buffer Replay','저장 특징 재생')
    box(a,3.2,7.25,2.8,.8,'Conv2 5×5','ch_en: 일부 / 전체 채널')
    box(a,6.55,7.25,1.75,.8,'MaxPool','2×2 + ReLU',sz=10)
    box(a,9,6.95,2.9,.65,'Light FC','Medium',fill=MF,edge=M,sz=10)
    box(a,9,7.95,2.9,.65,'Full FC','Hard',fill=HF,edge=H,sz=10)
    for y,c in [(7.52,M),(7.78,H)]:
        route(a,[(2.65,y),(3.2,y)],c);route(a,[(6,y),(6.55,y)],c)
    route(a,[(8.3,7.52),(8.65,7.52),(8.65,7.275),(9,7.275)],M)
    route(a,[(8.3,7.78),(8.65,7.78),(8.65,8.275),(9,8.275)],H)
    route(a,[(13.1,2.75),(15.8,2.75),(15.8,6.1),(.15,6.1),(.15,7.65),(.65,7.65)])
    route(a,[(14.27,5.3),(14.27,6.15),(4.6,6.15),(4.6,7.25)],GRAY,True)
    txt(a,9.5,5.98,'제어: replay / ch_en / FC enable',9,color=GRAY)
    box(a,12.85,7.1,2.5,1.4,'Result MUX','Easy / Medium / Hard',sz=10)
    route(a,[(1.2,5.3),(1.2,5.58),(12.55,5.58),(12.55,7.35),(12.85,7.35)],E,lw=2)
    txt(a,6,5.76,'Easy: Early 점수로 조기 종료',10,color=E)
    route(a,[(11.9,7.275),(12.4,7.275),(12.4,7.8),(12.85,7.8)],M)
    route(a,[(11.9,8.275),(12.85,8.275)],H)
    box(a,12.85,9,1.1,.65,'argmax',sz=10);box(a,14.35,9,1,.65,'decision',sz=9)
    route(a,[(14.1,8.5),(14.1,8.75),(13.4,8.75),(13.4,9)])
    route(a,[(13.95,9.325),(14.35,9.325)])
    txt(a,.45,9.27,'Easy: m ≥ T_high     Medium: T_low ≤ m < T_high     Hard: m < T_low',11,'left')
    txt(a,.45,9.85,'공통 블록: 회색   |   모델 A: T_low = T_high → Easy/Hard만 선택   |   점선: 제어 신호',10,'left',GRAY)
    save(f,'fig_arch')

def top2():
    f,a=canvas(16,9.4,'Top-2 Finder: Chain to Tournament Tree','조합 논리 구조 개선 · 출력 레지스터 1단 유지 · 추론 cycle 지연은 동일')
    region(a,.35,1.25,6.5,5.15,'Before  |  2-pass Comparator Chain')
    region(a,7.15,1.25,8.5,5.15,'After  |  Binary Tournament Tree')
    txt(a,3.6,2,'10 scores → Pass 1',12,weight='bold')
    for row,y in enumerate([2.55,4.55]):
        for i in range(9):
            x=.65+i*.66;box(a,x,y,.48,.42,'C'+str(i+1),sz=8)
            if i<8:route(a,[(x+.48,y+.21),(x+.66,y+.21)])
    box(a,1.6,3.35,4,.65,'Top-1 Index Mask','최댓값 위치 제외',sz=10)
    route(a,[(6.4,2.76),(6.6,2.76),(6.6,3.675),(5.6,3.675)])
    route(a,[(1.6,3.675),(.5,3.675),(.5,4.76),(.65,4.76)])
    txt(a,3.6,5.5,'Pass 1: 9단  +  Pass 2: 9단 = 직렬 18단',12,weight='bold')
    txt(a,3.6,5.95,'순차 비교 = 조합 체인의 직렬 비교 (18 cycle 아님)',9,color=GRAY)
    xs=[7.65+i*.48 for i in range(16)]
    for i,x in enumerate(xs):box(a,x-.19,2,.38,.42,str(i) if i<10 else 'P',fill=COMMON if i<10 else '#ffffff',sz=8)
    txt(a,11.45,1.78,'점수 10개 + 패딩 6개 (P = signed MINVAL)',9,color=GRAY)
    cur=xs;yprev=2.42
    for level in range(4):
        y=2.85+level*.7;nxt=[]
        for i in range(0,len(cur),2):
            x=(cur[i]+cur[i+1])/2;nxt.append(x)
            for child in cur[i:i+2]:route(a,[(child,yprev),(x,y)])
            box(a,x-.22,y,.44,.35,'M',fill=EF,edge=E,sz=8)
        cur=nxt;yprev=y+.35
        txt(a,15.18,y+.17,'L'+str(level+1),9,color=E)
    txt(a,11.4,6,'각 노드 전달: (v1, index1, v2) · 병합 레벨 4단',10,weight='bold')
    box(a,.35,6.75,15.3,1.2,'',fill=COMMON)
    txt(a,8,6.96,'Merge Rule',11,weight='bold')
    txt(a,8,7.3,'A.v1 ≥ B.v1:  1위 = A,  2위 = max(A.v2, B.v1)     |     그 외:  1위 = B,  2위 = max(A.v1, B.v2)',11)
    txt(a,8,7.72,'A는 낮은 index 쪽 자식 · 동점은 낮은 index 우선 · 4단은 병합 레벨 수이며 실제 셀 깊이와 구분',9,color=GRAY)
    for x,w,t,s in [(0.35,5,'4,293 → 1,071 ps','임계 경로 · 약 4.01배 단축'),(5.65,4.8,'384.5 → 325.1 µm²','면적 · 15.4% 감소'),(10.75,4.9,'400,000 vectors','출력 비트 단위 동일')]:box(a,x,8.25,w,.85,t,s,fill=EF,edge=E,sz=13)
    txt(a,8,9.22,'PPA 수치는 Top-2 모듈 단독이 아닌 Region 2 단독 합성 기준 · 제공 수치, 원시 로그 대조 필요',8,color=GRAY)
    save(f,'fig_top2')

def wrapper():
    f,a=canvas(14,8.4,'Host-Compatible Interface Wrapper','주최 측 포트와 코어 인터페이스를 연결하는 chip 래퍼')
    region(a,2.8,1.4,8.1,5.85,'chip  |  레퍼런스와 동일 포트')
    for y,t in [(2.25,'clk'),(3,'rst_n'),(4.7,'data_in[7:0]')]:
        txt(a,.5,y,t,12,'left',weight='bold');route(a,[(1.85,y),(3.15,y)])
    box(a,3.15,2.7,2.7,.8,'Reset Edge Detector','rst_n 상승 에지 → start',sz=10)
    box(a,6.5,2.05,3.7,3.2,'adapath_top','코어: Conv1 → 난이도 판단\n→ 선택적 후단 연산 → 결과',sz=12)
    route(a,[(3.15,2.25),(6.5,2.25)])
    route(a,[(5.85,3.1),(6.5,3.1)]);txt(a,6.15,2.82,'start',9,color=GRAY)
    route(a,[(3.15,4.7),(6.5,4.7)])
    route(a,[(3.0,3),(3.0,3.9),(6.5,3.9)]);txt(a,4.5,3.75,'rst_n → core reset',9,color=GRAY)
    for y,t in [(2.7,'decision[3:0]'),(4.15,'valid_out_6')]:
        route(a,[(10.2,y),(11.6,y)]);txt(a,11.7,y,t,11,'left',weight='bold')
    box(a,6.3,5.85,4.1,.9,'Weight Constants','adapath_weights.vh',sz=11)
    route(a,[(8.35,5.85),(8.35,5.25)])
    txt(a,4.5,6.1,'학습 가중치\n내부 상수로 고정',10,color=GRAY)
    txt(a,.5,5.9,'w_11…w_fc\nb_1, b_2, b_fc',11,'left')
    route(a,[(1.95,6.1),(2.8,6.1)])
    txt(a,3.25,6.65,'미사용',10,color=H,weight='bold')
    a.plot([2.95,3.12],[6.0,6.2],color=H);a.plot([2.95,3.12],[6.2,6.0],color=H)
    txt(a,7,7.65,'주최 측 top_tb.v 무수정 실행 (Vivado 2023.1)',14,weight='bold')
    txt(a,7,8.08,'가중치 입력 포트는 호환용으로 유지하며 코어의 학습 가중치와 연결하지 않음 · 데이터 경로 설정은 별도',10,color=GRAY)
    save(f,'fig_wrapper')

def flow():
    f,a=canvas(16,6.8,'AdaPath-NPU Design & Evaluation Flow','학습부터 기능 정합과 PPA 비교까지 연결한 재현 가능한 설계 흐름')
    stages=[('PyTorch Training','3-head 공동 학습\nMNIST / WM-811K'),('Threshold Search','임계값 전수 탐색\n정확도–연산량 절충'),('INT8 + Golden','양자화 및 기준 출력 생성\n가중치 8-bit · 활성값 12-bit'),('Parameterized RTL','모델 A/B · 클래스 수\n채널 수 · 경로 선택'),('Functional Verification','Icarus / Vivado\n주최 측 TB · Golden 대조'),('Yosys / OpenROAD','ASAP7 합성 + STA\n동일 제약 · pre-layout'),('Gate-Level Simulation','합성 넷리스트 + 셀 모델\n모드별 VCD 생성'),('OpenSTA Power','VCD 기반 전력 추정\n평균 전력 → 추론당 에너지'),('PPA Comparison','Reference / Baseline / AdaPath\n정확도 · 지연 · 에너지 · 면적')]
    coords=[(.4,1.8),(3.55,1.8),(6.7,1.8),(9.85,1.8),(13,1.8),(.4,4.25),(4.3,4.25),(8.2,4.25),(12.1,4.25)]
    widths=[2.6]*5+[3.4]*4
    for i,((t,s),(x,y),w) in enumerate(zip(stages,coords,widths)):
        txt(a,x+.02,y-.27,f'{i+1:02}',11,'left',GRAY,weight='bold');box(a,x,y,w,1.3,t,s,sz=10)
        if i not in [4,8]:route(a,[(x+w,y+.65),(coords[i+1][0],y+.65)])
    route(a,[(14.3,3.1),(14.3,3.6),(.2,3.6),(.2,4.9),(.4,4.9)])
    txt(a,8,6.13,'기능 검증: Golden과 비트 정합    |    전력: VCD 활동 기반 추정    |    비교: 동일 모델·입력·조건 명시',11)
    txt(a,8,6.55,'임계값 선정용 데이터와 최종 평가 데이터 분리는 보완 권고 사항이며, 현재 수행 완료를 의미하지 않음',9,color=GRAY)
    save(f,'fig_flow')

if __name__=='__main__':
    architecture();top2();wrapper();flow()
    print('Saved four PNG (300 dpi) and SVG pairs to',OUT)
