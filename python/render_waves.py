# -*- coding: utf-8 -*-
"""tb_adapath.vcd -> 보고서용 파형 그림 4컷 (그림 6~9).

GTKWave/Vivado 없이 VCD 를 직접 파싱해 matplotlib 로 그린다.
시뮬레이션이 9장(easy 3 / hard 3 / med 3)을 연속으로 돌리므로,
각 모드의 대표 윈도우 하나씩 + 전체 개요 1장을 만든다.

    python render_waves.py            # ../rtl/tb_adapath.vcd 사용

출력: ../out/fig_wave_{easy,medium,hard,overview}.png
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

CLK_PS = 10000            # tb: 10 ns 주기, timescale 1ps

# (스코프 경로 끝, 신호명) -> 우리가 쓸 key
WANTED = {
    ("tb_adapath", "start"): "start",
    ("tb_adapath", "valid_out"): "valid_out",
    ("dut", "front_done"): "front_done",
    ("dut", "mode_v"): "mode_v",
    ("dut", "mode"): "mode",
    ("dut", "margin"): "margin",
    ("dut", "fm_ov"): "fm_ov",
    ("dut", "p2_v"): "p2_v",
    ("dut", "result_sel"): "result_sel",
    ("u_fsm", "state"): "state",
    ("u_fsm", "conv2_en"): "conv2_en",
    ("u_fsm", "ch_en"): "ch_en",
    ("u_fsm", "fc_light_en"): "fc_light_en",
    ("u_fsm", "fc_full_en"): "fc_full_en",
    ("u_fsm", "done"): "done",
}

MODE_NAME = {0: "EASY", 1: "MED", 2: "HARD"}
STATE_NAME = {0: "IDLE", 1: "FRONT", 2: "DECIDE", 3: "BACK", 4: "DONE"}
SEL_NAME = {0: "EARLY", 1: "LIGHT", 2: "FULL"}

INK, INK2, INK3, LINE = "#161B22", "#3D4754", "#77828F", "#D4DAE1"
# EDA 파형 뷰어 다크 테마 (GTKWave/Vivado 풍)
BG    = "#0B0F0B"          # 파형 영역 배경
GRID  = "#20301F"          # 세로 그리드
GREEN = "#00E640"          # 1-bit 트레이스
BUSC  = "#38E060"          # 버스 외곽
BUST  = "#CFFFDC"          # 버스 값 텍스트
AMBER = "#FFD24A"
REDC  = "#FF7A66"
TEALC = "#45E0D8"


def parse_vcd(path):
    """id -> [(t, value_str)], key 매핑과 함께 반환."""
    id2key = {}
    changes = {}          # key -> [(t, raw)]
    scope = []
    t = 0
    with open(path, encoding="ascii", errors="ignore") as f:
        in_header = True
        for line in f:
            line = line.strip()
            if not line:
                continue
            if in_header:
                if line.startswith("$scope"):
                    scope.append(line.split()[2])
                elif line.startswith("$upscope"):
                    scope.pop()
                elif line.startswith("$var"):
                    parts = line.split()
                    vid, name = parts[3], parts[4]
                    for (sc, nm), key in WANTED.items():
                        if nm == name and scope and scope[-1] == sc and key not in [
                                k for k in id2key.values()]:
                            id2key[vid] = key
                            changes[key] = []
                elif line.startswith("$enddefinitions"):
                    in_header = False
                continue
            if line[0] == "#":
                t = int(line[1:])
            elif line[0] in "01xz":
                vid = line[1:]
                if vid in id2key:
                    changes[id2key[vid]].append((t, line[0]))
            elif line[0] in "bB":
                val, vid = line[1:].split()
                if vid in id2key:
                    changes[id2key[vid]].append((t, val))
    return changes


def to_int(raw):
    try:
        return int(raw, 2)
    except ValueError:
        return None       # x/z 포함


def sample_series(chs, t0, t1):
    """구간 [t0,t1] 의 (cycle, value) 계단 시퀀스 (직전 값 포함)."""
    out = []
    last = None
    for t, v in chs:
        if t < t0:
            last = v
        elif t <= t1:
            if not out and last is not None:
                out.append((t0, last))
            out.append((t, v))
        else:
            break
    if not out and last is not None:
        out.append((t0, last))
    return out


def draw(ax, y, series, t0, t1, kind, color, namemap=None):
    """kind: 'bit' | 'bus'"""
    c0 = 0
    span = (t1 - t0) / CLK_PS

    def cyc(t):
        return (t - t0) / CLK_PS

    if kind == "bit":
        xs, ys = [], []
        prev_v = 0
        prev_t = t0
        for t, v in series:
            iv = 1 if v == "1" else 0
            xs += [cyc(prev_t), cyc(t)]
            ys += [prev_v, prev_v]
            prev_v, prev_t = iv, t
        xs += [cyc(prev_t), span]
        ys += [prev_v, prev_v]
        yy = [y + 0.10 + 0.62 * v for v in ys]
        ax.plot(xs, yy, color=color, lw=1.4, solid_capstyle="butt", zorder=5)
        ax.fill_between(xs, y + 0.10, yy, color=color, alpha=0.12, zorder=3)
    else:
        segs = []
        prev = None
        prev_t = t0
        for t, v in series:
            if prev is not None:
                segs.append((prev_t, t, prev))
            prev, prev_t = v, t
        segs.append((prev_t, t1, prev))
        h0, h1 = y + 0.08, y + 0.74
        for a, b, v in segs:
            if v is None:
                continue
            xa, xb = cyc(a), cyc(b)
            iv = to_int(v)
            dx = min((xb - xa) * 0.25, span * 0.006)
            ax.plot([xa + dx, xb - dx], [h1, h1], color=color, lw=1.3, zorder=5)
            ax.plot([xa + dx, xb - dx], [h0, h0], color=color, lw=1.3, zorder=5)
            ax.plot([xa, xa + dx], [(h0 + h1) / 2, h1], color=color, lw=1.3, zorder=5)
            ax.plot([xa, xa + dx], [(h0 + h1) / 2, h0], color=color, lw=1.3, zorder=5)
            ax.plot([xb - dx, xb], [h1, (h0 + h1) / 2], color=color, lw=1.3, zorder=5)
            ax.plot([xb - dx, xb], [h0, (h0 + h1) / 2], color=color, lw=1.3, zorder=5)
            label = "x" if iv is None else (
                namemap[iv] if namemap and iv in namemap else "%02X" % iv)
            if xb - xa > span * 0.02:
                ax.text((xa + xb) / 2, y + 0.41, label, fontsize=7.8, color=BUST,
                        ha="center", va="center", weight="bold", zorder=6)


ROWS = [   # (key, 라벨, kind, color, namemap)
    ("front_done",  "front_done",   "bit", GREEN, None),
    ("mode_v",      "mode_valid",   "bit", GREEN, None),
    ("mode",        "mode[1:0]",    "bus", AMBER, MODE_NAME),
    ("state",       "state[2:0]",   "bus", TEALC, STATE_NAME),
    ("conv2_en",    "conv2_en",     "bit", REDC, None),
    ("ch_en",       "ch_en[7:0]",   "bus", REDC, None),
    ("fm_ov",       "fmap_replay",  "bit", GREEN, None),
    ("fc_light_en", "fc_light_en",  "bit", GREEN, None),
    ("fc_full_en",  "fc_full_en",   "bit", GREEN, None),
    ("result_sel",  "result_sel",   "bus", BUSC, SEL_NAME),
    ("done",        "done",         "bit", GREEN, None),
    ("valid_out",   "valid_out",    "bit", GREEN, None),
]


def render_window(ch, t0, t1, title, sub, out_png):
    fig, ax = plt.subplots(figsize=(11, 6.2))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(BG)
    span = (t1 - t0) / CLK_PS
    n = len(ROWS)
    step = 10 if span < 300 else 50
    for gx in range(0, int(span) + 1, step):
        ax.axvline(gx, color=GRID, lw=0.7, zorder=1)
    for i, (key, label, kind, color, nm) in enumerate(ROWS):
        y = (n - 1 - i) * 1.05
        ax.text(-span * 0.012, y + 0.40, label, fontsize=8.5, color=INK,
                ha="right", va="center")
        draw(ax, y, sample_series(ch[key], t0, t1), t0, t1, kind, color, nm)
    ax.set_xlim(0, span)
    ax.set_ylim(-0.35, n * 1.05 + 0.25)
    ax.set_yticks([])
    ax.set_xlabel("cycle (표시 구간 시작 기준)", fontsize=9, color=INK2)
    ax.set_title(title + "\n" + sub, fontsize=11.5, color=INK, loc="left", pad=10)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.tick_params(colors=INK3, labelsize=8)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    print("saved", out_png)


def main(a):
    ch = parse_vcd(a.vcd)
    starts = [t for t, v in ch["start"] if v == "1"]
    valids = [t for t, v in ch["valid_out"] if v == "1"]
    print("images:", len(starts), "valid_out:", len(valids))

    # tb_list 순서: easy 0,1,2 / hard 18,33,62 / med 22,61,78
    windows = {"easy": 0, "hard": 3, "medium": 6}
    for name, k in windows.items():
        t_start, t_end = starts[k], valids[k]
        # 판정 직전(front_done)부터 결과까지 확대
        fd = [t for t, v in ch["front_done"] if v == "1" and t_start <= t <= t_end]
        t0 = (fd[0] if fd else t_start) - 15 * CLK_PS
        t1 = t_end + 8 * CLK_PS
        mg = [to_int(v) for t, v in ch["margin"] if t <= t_end]
        title = {"easy": "그림 6 · Easy 모드 파형 — 후단 전면 비활성 (replay 없음)",
                 "hard": "그림 8 · Hard 모드 파형 — ch_en=FF, Full FC 활성",
                 "medium": "그림 7 · Medium 모드 파형 — ch_en=0F, Light FC 활성"}[name]
        sub = "margin=%s → mode=%s   (AdaPath VARIANT=2, 실제 MNIST 이미지, iverilog 시뮬레이션)" % (
            mg[-1] if mg else "?", name.upper())
        render_window(ch, t0, t1, title, sub,
                      os.path.join(a.out, "fig_wave_%s.png" % name))

    # ---- 개요: 9장 전체 — 판정된 모드 밴드 / FSM / conv2_en / valid_out ----
    fig, ax = plt.subplots(figsize=(11, 3.8))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(BG)
    t_all0, t_all1 = starts[0] - 20 * CLK_PS, valids[-1] + 40 * CLK_PS

    def cyc_all(t):
        return (t - t_all0) / CLK_PS

    # 판정된 모드: valid_out 시점의 mode 값을 이미지 구간 밴드로 표시
    mode_color = {0: "#00E640", 1: "#FFD24A", 2: "#FF7A66"}
    y_mode = 3 * 1.05
    ax.text(-(t_all1 - t_all0) / CLK_PS * 0.015, y_mode + 0.42, "판정 mode",
            fontsize=8.5, color=INK2, ha="right", va="center")
    for k, (ts, tv) in enumerate(zip(starts, valids)):
        mv = [to_int(v) for t, v in ch["mode"] if t <= tv]
        m = mv[-1] if mv else None
        te = starts[k + 1] if k + 1 < len(starts) else t_all1
        if m is not None:
            ax.fill_between([cyc_all(ts), cyc_all(te)], y_mode + 0.10,
                            y_mode + 0.74, color=mode_color[m], alpha=.22)
            ax.text((cyc_all(ts) + cyc_all(te)) / 2, y_mode + 0.42, MODE_NAME[m],
                    fontsize=8, color=mode_color[m], ha="center", va="center",
                    weight="bold")

    rows = [("state", "FSM state", "bus", TEALC, STATE_NAME),
            ("conv2_en", "conv2_en", "bit", REDC, None),
            ("valid_out", "valid_out", "bit", GREEN, None)]
    for i, (key, label, kind, color, nm) in enumerate(rows):
        y = (len(rows) - 1 - i) * 1.05
        ax.text(-(t_all1 - t_all0) / CLK_PS * 0.015, y + 0.42, label, fontsize=8.5,
                color=INK2, ha="right", va="center")
        draw(ax, y, sample_series(ch[key], t_all0, t_all1), t_all0, t_all1,
             kind, color, nm)
    seq = ["E", "E", "E", "H", "H", "H", "M", "M", "M"]
    for k, t in enumerate(starts):
        x = cyc_all(t)
        ax.axvline(x, color="#3A4A3A", lw=0.8, ls=":")
        ax.text(x + 30, 4 * 1.05 + 0.15, "img%d(%s)" % (k, seq[k]),
                fontsize=7.5, color=INK3)
    ax.set_xlim(0, (t_all1 - t_all0) / CLK_PS)
    ax.set_ylim(-0.5, 4 * 1.05 + 0.8)
    ax.set_yticks([])
    ax.set_xlabel("cycle", fontsize=9, color=INK2)
    ax.set_title("그림 9 · 9장 연속 추론 개요 — 이미지마다 mode 판정과 FSM 천이 (E=Easy, H=Hard, M=Medium)",
                 fontsize=11.5, color=INK, loc="left", pad=8)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.tick_params(colors=INK3, labelsize=8)
    fig.tight_layout()
    p = os.path.join(a.out, "fig_wave_overview.png")
    fig.savefig(p, dpi=150)
    plt.close(fig)
    print("saved", p)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--vcd", default="../rtl/tb_adapath.vcd")
    ap.add_argument("--out", default="../out")
    main(ap.parse_args())
