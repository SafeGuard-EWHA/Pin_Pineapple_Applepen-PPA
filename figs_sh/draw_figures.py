"""Rebuild publication figures: python draw_figures.py (matplotlib, Malgun Gothic).

보고서 본문 폭(16.5 cm)에 넣었을 때 글씨가 약 7~8 pt가 되도록, 캔버스 폭 12.5 in 기준으로 글꼴 크기를 정했다.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager

OUT=Path(__file__).resolve().parent
FONT=font_manager.FontProperties(fname='C:/Windows/Fonts/malgun.ttf').get_name()
plt.rcParams.update({'font.family':FONT,'svg.fonttype':'path','axes.unicode_minus':False})
INK='#202831'; GRAY='#65717d'; LINE='#bac2c9'; COMMON='#f0f2f4'
E='#278353'; EF='#e8f4ec'; M='#a67b00'; MF='#fff4c9'; H='#ba4545'; HF='#fbeaea'
T=14; S=12.5; N=13   # 박스 제목 / 박스 부제 / 주석
def canvas(w,h):
    fig,ax=plt.subplots(figsize=(w,h)); fig.patch.set_facecolor('white')
    ax.set(xlim=(0,w),ylim=(h,0)); ax.axis('off');fig.subplots_adjust(0,0,1,1)
    return fig,ax
def txt(ax,x,y,s,sz=S,ha='center',color=INK,weight='normal',bg=False):
    return ax.text(x,y,s.replace('−','-'),fontsize=sz,ha=ha,va='center',color=color,weight=weight,linespacing=1.4,
                   bbox=dict(facecolor='white',edgecolor='none',pad=1.5) if bg else None,zorder=5)
def box(ax,x,y,w,h,title,sub='',fill=COMMON,edge=LINE,sz=T,ty=None):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.012,rounding_size=0.06',facecolor=fill,edgecolor=edge,lw=1.4,zorder=2))
    if ty is None: ty=.33 if sub else .5
    txt(ax,x+w/2,y+h*ty,title,sz,weight='bold')
    if sub: txt(ax,x+w/2,y+h*(ty+1)/2+h*.05,sub,sz-1.5,color=GRAY)
def route(ax,pts,c=GRAY,dash=False,lw=1.8):
    ls='--' if dash else '-'
    for a,b in zip(pts[:-2],pts[1:-1]):ax.plot([a[0],b[0]],[a[1],b[1]],color=c,lw=lw,ls=ls,zorder=1)
    ax.add_patch(FancyArrowPatch(pts[-2],pts[-1],arrowstyle='-|>',mutation_scale=16,lw=lw,color=c,linestyle=ls,zorder=3))
def region(ax,x,y,w,h,label):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.015,rounding_size=0.1',facecolor='white',edgecolor=LINE,lw=1.2,zorder=0))
    txt(ax,x+.18,y+.24,label,13,'left',weight='bold')
def save(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=300,facecolor='white')
    fig.savefig(OUT/(name+'.svg'),facecolor='white')
    plt.close(fig)

def architecture():
    f,a=canvas(12.5,7.35)
    region(a,.15,.12,12.1,1.38,'① 공유 전단부')
    box(a,.4,.58,2.1,.78,'Input Stream','28×28, 1 px/cycle')
    box(a,2.9,.58,2.1,.78,'Conv1 5×5','1→3 ch')
    box(a,5.4,.58,2.5,.78,'MaxPool + ReLU','24×24×3 → 12×12×3')
    box(a,8.4,.58,3.6,.78,'Feature Map Buffer','12×12×3, 5,184 bit')
    for x,z in [(2.5,2.9),(5.0,5.4),(7.9,8.4)]:route(a,[(x,.97),(z,.97)])
    region(a,.15,2.0,12.1,1.45,'② 난이도 판단 및 제어')
    for x,w,t,s in [(.4,2.4,'Early Classifier','AvgPool → FC 48→10'),(3.15,1.85,'Top-2 Finder','토너먼트 트리'),
                    (5.35,1.95,'Score Margin','Top1 − Top2'),(7.65,2.25,'Difficulty Decoder','T_low, T_high'),
                    (10.25,1.75,'Mode FSM','enable 생성')]:
        box(a,x,2.45,w,.85,t,s)
    for x,z in [(2.8,3.15),(5.0,5.35),(7.3,7.65),(9.9,10.25)]:route(a,[(x,2.875),(z,2.875)])
    route(a,[(6.65,1.36),(6.65,1.75),(2.6,1.75),(2.6,2.45)])           # 풀링 출력 → Early Classifier
    route(a,[(12.0,.97),(12.36,.97),(12.36,4.15),(.12,4.15),(.12,5.35),(.4,5.35)])   # 버퍼 → Replay
    txt(a,7.2,4.15,'저장 특징',N,color=GRAY,bg=True)
    route(a,[(11.12,3.3),(11.12,3.65),(3.95,3.65),(3.95,4.95)],GRAY,True)  # 제어 신호
    txt(a,9.05,3.65,'제어: replay, ch_en, FC enable',N,color=GRAY,bg=True)
    route(a,[(1.0,3.3),(1.0,3.9),(11.43,3.9),(11.43,4.75)],E,lw=2.4)    # Easy 조기 종료
    txt(a,5.3,3.9,'Easy: Early 점수로 조기 종료',N,color=E,weight='bold',bg=True)
    region(a,.15,4.35,10.15,1.85,'③ Medium / Hard에서만 실행')
    box(a,.4,4.95,1.9,.8,'Buffer Replay','저장 특징 재생')
    box(a,2.65,4.95,2.0,.8,'Conv2 5×5','일부 / 전체 채널')
    box(a,5.0,4.95,1.75,.8,'MaxPool','2×2 + ReLU')
    box(a,7.55,4.75,2.5,.6,'Light FC  (Medium)',fill=MF,edge=M,sz=13)
    box(a,7.55,5.42,2.5,.6,'Full FC  (Hard)',fill=HF,edge=H,sz=13)
    for y,c in [(5.22,M),(5.48,H)]:
        route(a,[(2.3,y),(2.65,y)],c);route(a,[(4.65,y),(5.0,y)],c)
    route(a,[(6.75,5.22),(7.15,5.22),(7.15,5.05),(7.55,5.05)],M)
    route(a,[(6.75,5.48),(7.15,5.48),(7.15,5.72),(7.55,5.72)],H)
    box(a,10.55,4.75,1.75,1.25,'Result MUX','모드별 결과 선택',sz=13)
    route(a,[(10.05,5.05),(10.55,5.05)],M);route(a,[(10.05,5.72),(10.55,5.72)],H)
    box(a,10.0,6.35,1.05,.5,'argmax',sz=13);box(a,11.25,6.35,1.05,.5,'decision',sz=13)
    route(a,[(11.43,6.0),(11.43,6.18),(10.52,6.18),(10.52,6.35)])
    route(a,[(11.05,6.6),(11.25,6.6)])
    txt(a,.3,6.62,'Easy: m ≥ T_high     Medium: T_low ≤ m < T_high     Hard: m < T_low',13.5,'left',weight='bold')
    txt(a,.3,7.07,'회색: 공통 블록     점선: 제어 신호     모델 A: T_low = T_high (Easy / Hard만 선택)',N,'left',GRAY)
    save(f,'fig_arch')

def top2():
    f,a=canvas(12.5,7.4)
    region(a,.15,.12,5.6,4.5,'기존: 2-pass 비교기 체인')
    region(a,5.95,.12,6.4,4.5,'개선: 이진 토너먼트 트리')
    txt(a,2.95,.82,'점수 10개 → Pass 1',13,weight='bold')
    for y in (1.05,2.85):
        for i in range(9):
            x=.4+i*.57;box(a,x,y,.44,.4,'C'+str(i+1),sz=11)
            if i<8:route(a,[(x+.44,y+.2),(x+.57,y+.2)],lw=1.4)
    box(a,1.2,1.85,3.6,.62,'Top-1 위치 제외 (마스크)',sz=13)
    route(a,[(5.4,1.25),(5.58,1.25),(5.58,2.16),(4.8,2.16)])
    route(a,[(1.2,2.16),(.28,2.16),(.28,3.05),(.4,3.05)])
    txt(a,2.95,3.68,'직렬 비교 18단 (9단 + 9단)',14,weight='bold')
    txt(a,2.95,4.15,'조합 논리 체인의 길이이며 18 cycle이 아님',N,color=GRAY)
    txt(a,9.15,.82,'점수 10개 + 패딩 6개 (P = 최솟값)',N,color=GRAY)
    xs=[6.35+i*.37 for i in range(16)]
    for i,x in enumerate(xs):box(a,x-.16,1.05,.32,.36,str(i) if i<10 else 'P',fill=COMMON if i<10 else '#ffffff',sz=10.5)
    cur=xs;yprev=1.41
    for level in range(4):
        y=1.75+level*.6;nxt=[]
        for i in range(0,len(cur),2):
            x=(cur[i]+cur[i+1])/2;nxt.append(x)
            for child in cur[i:i+2]:route(a,[(child,yprev),(x,y)],lw=1.3)
            box(a,x-.2,y,.4,.32,'M',fill=EF,edge=E,sz=10.5)
        cur=nxt;yprev=y+.32
        txt(a,12.05,y+.16,'L'+str(level+1),N,color=E,weight='bold')
    txt(a,9.15,4.15,'노드마다 (1위 값, 1위 index, 2위 값) 전달, 병합 4단',13,weight='bold')
    box(a,.15,4.85,12.2,1.0,'',fill=COMMON)
    txt(a,6.25,5.1,'병합 규칙 (A = 낮은 index 쪽 자식, 동점은 낮은 index 우선)',13,weight='bold')
    txt(a,6.25,5.55,'A.v1 ≥ B.v1이면  1위 = A, 2위 = max(A.v2, B.v1)       아니면  1위 = B, 2위 = max(A.v1, B.v2)',13)
    for x,t,s in [(.15,'4,293 → 1,071 ps','임계 경로 약 4.0배 단축'),(4.25,'384.5 → 325.1 µm²','면적 15.4 % 감소'),
                  (8.35,'400,000 벡터','출력 비트 단위 동일')]:
        box(a,x,6.05,4.0,.9,t,s,fill=EF,edge=E,sz=15)
    txt(a,6.25,7.17,'타이밍과 면적은 Region 2(판단 회로) 단독 합성 기준',N,color=GRAY)
    save(f,'fig_top2')

def wrapper():
    f,a=canvas(10.7,6.3)
    region(a,2.3,.15,6.3,4.85,'chip (레퍼런스와 같은 포트)')
    for y,t in [(.9,'clk'),(1.78,'rst_n'),(3.3,'data_in[7:0]')]:
        txt(a,.2,y,t,14,'left',weight='bold')
    route(a,[(1.5,.9),(5.5,.9)]);route(a,[(1.5,1.78),(2.6,1.78)]);route(a,[(1.5,3.3),(5.5,3.3)])
    box(a,2.6,1.4,2.45,.76,'Reset Edge Detector','rst_n 상승 → start',sz=13)
    box(a,5.5,.6,2.8,3.1,'adapath_top','코어\nConv1 → 난이도 판단\n→ 선택적 후단 연산',sz=15,ty=.25)
    route(a,[(5.05,1.78),(5.5,1.78)]);txt(a,5.27,1.55,'start',11,color=GRAY)
    route(a,[(2.45,1.78),(2.45,2.6),(5.5,2.6)]);txt(a,3.95,2.42,'rst_n → core reset',11,color=GRAY)
    for y,t in [(1.3,'decision[3:0]'),(2.8,'valid_out_6')]:
        route(a,[(8.3,y),(8.95,y)]);txt(a,9.05,y,t,14,'left',weight='bold')
    box(a,5.3,4.0,3.2,.78,'가중치 상수','adapath_weights.vh',sz=13)
    route(a,[(6.9,4.0),(6.9,3.7)])
    txt(a,.2,4.4,'w_11 … w_fc\nb_1, b_2, b_fc',13,'left')
    route(a,[(1.65,4.4),(2.75,4.4)])
    a.plot([2.85,3.1],[4.25,4.55],color=H,lw=2);a.plot([2.85,3.1],[4.55,4.25],color=H,lw=2)
    txt(a,3.85,4.4,'미사용',13,color=H,weight='bold')
    txt(a,5.35,5.5,'주최 측 top_tb.v를 수정 없이 실행 (Vivado 2023.1)',15,weight='bold')
    txt(a,5.35,5.97,'가중치 입력 포트는 호환용으로만 남기고 코어와 연결하지 않음',N,color=GRAY)
    save(f,'fig_wrapper')

def flow():
    f,a=canvas(12.5,4.8)
    stages=[('PyTorch 학습','3-head 공동 학습\nMNIST, WM-811K'),('임계값 탐색','전수 탐색\n정확도–연산량 절충'),
            ('INT8 + Golden','8-bit 가중치\n12-bit 활성값'),('파라미터화 RTL','모델 A/B, 클래스 수\n채널 수, 경로 선택'),
            ('기능 검증','Icarus, Vivado\n주최 TB, Golden 대조'),('Yosys / OpenROAD','ASAP7 합성 + STA\n동일 제약, pre-layout'),
            ('게이트레벨 시뮬레이션','합성 넷리스트\n모드별 VCD 생성'),('OpenSTA 전력','VCD 기반 전력\n→ 추론당 에너지'),
            ('PPA 비교','Reference, Baseline, AdaPath\n정확도, 지연, 에너지, 면적')]
    coords=[(.3+i*2.47,.5) for i in range(5)]+[(.3+i*3.1,2.65) for i in range(4)]
    widths=[2.05]*5+[2.7]*4
    for i,((t,s),(x,y),w) in enumerate(zip(stages,coords,widths)):
        txt(a,x+.02,y-.2,f'{i+1:02}',12,'left',GRAY,weight='bold');box(a,x,y,w,1.35,t,s,ty=.27)
        if i not in [4,8]:route(a,[(x+w,y+.675),(coords[i+1][0],y+.675)])
    route(a,[(11.2,1.85),(11.2,2.2),(.12,2.2),(.12,3.325),(.3,3.325)])
    txt(a,6.25,4.42,'기능 검증: Golden과 비트 단위 일치      전력: VCD 활동 기반 추정      비교: 같은 모델, 입력, 조건',13)
    save(f,'fig_flow')

if __name__=='__main__':
    architecture();top2();wrapper();flow()
    print('Saved four PNG (300 dpi) and SVG pairs to',OUT)
