"""robustness_A.csv -> 그림 2개 (실험 2).

    python plot_robustness.py --csv ../rtl/robustness_A.csv --out ../out
"""
import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#e4e3dd"
BLUE, ORANGE = "#2a78d6", "#eb6834"      # 고정 순서: Baseline_A, AdaPath_A


def style(ax):
    ax.grid(color=GRID, lw=0.8, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED)


def main(a):
    rows = list(csv.DictReader(open(a.csv, encoding="utf-8")))
    sig = sorted({int(r["sigma"]) for r in rows})
    get = lambda d, k: [float(next(r[k] for r in rows if int(r["sigma"]) == s and r["design"] == d)) for s in sig]
    n = 1000.0

    # (1) 노이즈 vs Hard 비율 / 평균 cycle
    fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.6))
    ax[0].plot(sig, [h / n * 100 for h in get("ada", "hard")], "-o", color=ORANGE, lw=2, ms=7, label="AdaPath_A")
    ax[0].set_xlabel("노이즈 σ")
    ax[0].set_ylabel("Hard 경로 비율 (%)")
    ax[0].set_title("입력이 어려워지면 Hard 경로가 늘어난다", fontsize=10, color=INK)
    ax[1].plot(sig, get("base", "avg_cycles"), "-o", color=BLUE, lw=2, ms=7, label="Baseline_A (항상 Hard)")
    ax[1].plot(sig, get("ada", "avg_cycles"), "-o", color=ORANGE, lw=2, ms=7, label="AdaPath_A")
    ax[1].set_xlabel("노이즈 σ")
    ax[1].set_ylabel("평균 cycle / 이미지")
    ax[1].set_title("연산(시간)이 난이도에 비례해 배분된다", fontsize=10, color=INK)
    ax[1].legend(fontsize=8.5, frameon=False)
    for x in ax:
        style(x)
    fig.tight_layout()
    fig.savefig(os.path.join(a.out, "fig_robustness_modes.png"), dpi=200)

    # (2) 노이즈 vs 정확도
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.plot(sig, [c / n * 100 for c in get("base", "correct")], "-o", color=BLUE, lw=2, ms=7, label="Baseline_A (항상 Hard)")
    ax.plot(sig, [c / n * 100 for c in get("ada", "correct")], "-o", color=ORANGE, lw=2, ms=7, label="AdaPath_A")
    ax.set_xlabel("노이즈 σ")
    ax.set_ylabel("정확도 (%)")
    ax.set_title("노이즈에 따른 정확도", fontsize=10, color=INK)
    ax.legend(fontsize=8.5, frameon=False)
    style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(a.out, "fig_robustness_acc.png"), dpi=200)
    print("saved fig_robustness_modes.png, fig_robustness_acc.png ->", a.out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default="../rtl/robustness_A.csv")
    p.add_argument("--out", default="../out")
    main(p.parse_args())
