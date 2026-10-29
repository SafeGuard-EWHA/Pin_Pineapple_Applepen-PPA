"""블록별 에너지 분해 + 클럭 주기 스윕 Fmax -> results.json 에 추가하고 그림 생성.

    python make_extra.py <reports_extra 경로>
    python make_extra.py --plot      (results.json 의 저장값으로 그림만 다시 그림)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
REP = sys.argv[1]
PLOT_ONLY = REP == "--plot"
GL = r"C:\Users\yhe44\idec_glsim"
RES = os.path.join(HERE, "results.json")
R = json.load(open(RES, encoding="utf-8"))

LABEL = {  # 그룹명 -> 블록
    "u_conv1": "Conv1", "conv1_layer": "Conv1",
    "u_pool1": "Pool1", "maxpool_relu_1": "Pool1",
    "u_fmap": "Feature Map Buffer",
    "u_early": "Early Classifier",
    "u_top2": "판단·제어", "u_margin": "판단·제어", "u_dec": "판단·제어", "u_fsm": "판단·제어",
    "conv2_en_d": "판단·제어", "replay_req": "판단·제어",
    "u_conv2": "Conv2", "conv2_layer": "Conv2",
    "u_pool2": "Pool2", "maxpool_relu_2": "Pool2",
    "u_fcf": "FC (Full)", "fully_connected": "FC (Full)",
    "u_fcl": "Light FC",
    "u_argmax": "출력 (argmax)", "comparator": "출력 (argmax)",
    "_comb": "조합 논리 (블록 미분류)",
}
ORDER = ["Conv1", "Pool1", "Feature Map Buffer", "Early Classifier", "판단·제어", "Conv2", "Pool2",
         "FC (Full)", "Light FC", "출력 (argmax)", "기타", "조합 논리 (블록 미분류)"]


def vcd_seconds(vcd):
    with open(vcd, "rb") as f:
        head = f.read(4000).decode("ascii", "ignore")
        f.seek(-4000, 2)
        tail = f.read().decode("ascii", "ignore")
    ts = re.search(r"\$timescale\s+([0-9]+)\s*([munpf]?s)", head)
    unit = {"s": 1, "ms": 1e-3, "us": 1e-6, "ns": 1e-9, "ps": 1e-12, "fs": 1e-15}[ts.group(2)] * int(ts.group(1))
    return [int(x) for x in re.findall(r"^#([0-9]+)", tail, re.M)][-1] * unit


def block_energy(tag, vcd, n_img):
    """그룹 전력(W) x 런 시간 / 이미지 수 -> 블록별 nJ/이미지."""
    T = vcd_seconds(os.path.join(GL, vcd))
    e = {}
    for line in open(os.path.join(REP, "block_%s.txt" % tag), encoding="utf-8", errors="ignore"):
        g, n, pi, ps, pl, pt = line.split()
        b = LABEL.get(g, "기타")
        e[b] = e.get(b, 0.0) + float(pt) * T * 1e9 / n_img
    return e


if PLOT_ONLY:
    blocks = R["block_energy_nJ"]
else:
    ref = block_energy("ref_a", "gl_ref_a.vcd", 4)
    base = block_energy("Abase", "gl_baA.vcd", 4)
    easy = block_energy("A_easy", "gl_adA_easy.vcd", 4)
    run_h = block_energy("A_hard", "gl_adA_hard.vcd", 4)
    hard = {b: run_h.get(b, 0) * 4 - 3 * easy.get(b, 0) for b in set(run_h) | set(easy)}
    mr = R["mode_ratio"]["A"]
    avgA = {b: mr["easy"] * easy.get(b, 0) + mr["hard"] * hard.get(b, 0) for b in set(easy) | set(hard)}
    blocks = {"Reference": ref, "Baseline_A": base, "AdaPath_A Easy": easy, "AdaPath_A Hard": hard,
              "AdaPath_A 평균": avgA}
    for k, v in blocks.items():
        print("%-16s total %.2f nJ  " % (k, sum(v.values())) +
              "  ".join("%s %.2f" % (b, v[b]) for b in ORDER if b in v and abs(v[b]) > 0.005))


    # ---------------- 주기 스윕 -> Fmax ----------------
    def fmax_from_sweep(design):
        pts = {"io20": [], "static_w": []}
        for line in open(os.path.join(REP, "sweep_%s.txt" % design), encoding="utf-8"):
            mode, P, w = line.split()[:3]
            pts[mode].append((float(P), float(w)))
        out = {}
        for mode, xs in pts.items():
            xs.sort()
            pmin = None
            for (p0, w0), (p1, w1) in zip(xs, xs[1:]):
                if w0 < 0 <= w1:                   # slack 은 주기에 선형 -> 0 교차점 보간
                    pmin = p0 + (0 - w0) * (p1 - p0) / (w1 - w0)
                    break
            if pmin is None and xs and xs[0][1] >= 0:
                pmin = xs[0][0]
            out[mode] = {"period_ps": pmin, "fmax_mhz": 1e6 / pmin if pmin else None}
        return out


    SW = {}
    for d in ("refchip", "baseline_A", "adapath_A", "baseline", "adapath", "baseline_wm", "adapath_wm"):
        if os.path.exists(os.path.join(REP, "sweep_%s.txt" % d)):
            SW[d] = fmax_from_sweep(d)
            print("%-12s io20 %.0f ps (%.1f MHz)   static_w %.0f ps (%.1f MHz)" % (
                d, SW[d]["io20"]["period_ps"], SW[d]["io20"]["fmax_mhz"],
                SW[d]["static_w"]["period_ps"], SW[d]["static_w"]["fmax_mhz"]))

    R["block_energy_nJ"] = blocks
    R["fmax_sweep"] = SW
    json.dump(R, open(RES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------------- 그림: 블록별 에너지 누적 막대 ----------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#e4e3dd"
# 블록 색: 공통(회색 계열) / 적응 경로 추가 블록(주황 계열) / 후단부(파랑 계열)
COL = {"Conv1": "#8f8e86", "Pool1": "#b9b8b0", "Feature Map Buffer": "#eb6834", "Early Classifier": "#f3a37f",
       "판단·제어": "#c94a1a", "Conv2": "#1c5cab", "Pool2": "#86b6ef", "FC (Full)": "#2a78d6",
       "Light FC": "#b7d3f6", "출력 (argmax)": "#5c5b55", "기타": "#d9d8d0", "조합 논리 (블록 미분류)": "#e9e8e2"}
names = ["Reference", "Baseline_A", "AdaPath_A Easy", "AdaPath_A Hard", "AdaPath_A 평균"]
fig, ax = plt.subplots(figsize=(9.6, 4.6))
bottom = [0.0] * len(names)
for b in ORDER:
    vals = [max(blocks[n].get(b, 0.0), 0.0) for n in names]
    if max(vals) < 0.01:
        continue
    ax.bar(range(len(names)), vals, 0.62, bottom=bottom, color=COL[b], label=b.replace("·", " 및 "), edgecolor="white", linewidth=1.2, zorder=3)
    bottom = [x + y for x, y in zip(bottom, vals)]
for i, t in enumerate(bottom):
    ax.text(i, t + 0.3, "%.1f nJ" % t, ha="center", va="bottom", fontsize=9.5, color=INK, fontweight="bold")
ax.set_xticks(range(len(names)))
ax.set_xticklabels(["Reference", "Baseline_A", "AdaPath_A\nEasy", "AdaPath_A\nHard", "AdaPath_A\n평균 (96/4 %)"],
                   fontsize=9.5, color=INK)
ax.set_ylabel("추론당 에너지 (nJ)", fontsize=9.5, color=MUTED)
ax.set_ylim(0, max(bottom) * 1.15)
ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(GRID)
ax.tick_params(colors=MUTED)
ax.legend(fontsize=8, frameon=False, loc="center left", bbox_to_anchor=(1.0, 0.5))
ax.set_title("블록별 추론당 에너지 (게이트레벨 VCD 기반 추정, 100 MHz)", fontsize=10.5, color=INK)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_block_energy.png"), dpi=250)
print("saved fig_block_energy.png")
