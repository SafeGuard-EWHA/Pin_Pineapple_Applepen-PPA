"""robustness_A.csv -> 그림 (실험 2).

    python plot_robustness.py --csv ../rtl/robustness_A.csv --out ../out

fig_robustness_modes.png : 열화 강도 vs Hard 비율 / 평균 cycle (열화 종류별 열)
fig_robustness_acc.png   : 열화 강도 vs 정확도 (AdaPath_A vs Baseline_A)
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
XLABEL = {"contrast": "대비 배율 (낮을수록 어두움)", "blur": "3×3 블러 적용 횟수", "gauss": "가우시안 잡음 σ"}
TITLE = {"contrast": "저조도 (대비 감소)", "blur": "초점 흐림 (블러)", "gauss": "센서 잡음 (가우시안)"}


def style(ax):
    ax.grid(color=GRID, lw=0.8, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED)


def main(a):
    rows = list(csv.DictReader(open(a.csv, encoding="utf-8")))
    kinds = [k for k in ("contrast", "blur", "gauss") if any(r["kind"] == k for r in rows)]
    n = 1000.0

    def series(kind, design, key):
        rs = sorted((r for r in rows if r["kind"] == kind and r["design"] == design), key=lambda r: float(r["level"]))
        return [float(r["level"]) for r in rs], [float(r[key]) for r in rs]

    def xfix(ax, kind):
        if kind == "contrast":
            ax.invert_xaxis()          # 왼쪽 = 원본(1.0), 오른쪽으로 갈수록 어려움
        ax.set_xlabel(XLABEL[kind], fontsize=9)

    fig, ax = plt.subplots(2, len(kinds), figsize=(max(4.2 * len(kinds), 9.5), 6.4), squeeze=False)
    for j, k in enumerate(kinds):
        x, h = series(k, "ada", "hard")
        ax[0][j].plot(x, [v / n * 100 for v in h], "-o", color=ORANGE, lw=2, ms=6, label="AdaPath_A")
        ax[0][j].set_ylabel("Hard 경로 비율 (%)")
        ax[0][j].set_title(TITLE[k], fontsize=10.5, color=INK)
        x, cb = series(k, "base", "avg_cycles")
        ax[1][j].plot(x, cb, "-o", color=BLUE, lw=2, ms=6, label="Baseline_A (항상 Hard)")
        x, ca = series(k, "ada", "avg_cycles")
        ax[1][j].plot(x, ca, "-o", color=ORANGE, lw=2, ms=6, label="AdaPath_A")
        ax[1][j].set_ylabel("평균 cycle / 이미지")
        for i in (0, 1):
            xfix(ax[i][j], k)
            style(ax[i][j])
    ax[1][0].legend(fontsize=8.5, frameon=False)
    fig.suptitle("입력이 어려워질수록 AdaPath는 Hard 경로(연산)를 자동으로 늘린다", fontsize=11.5, color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(a.out, "fig_robustness_modes.png"), dpi=200)

    fig, ax = plt.subplots(1, len(kinds), figsize=(max(4.2 * len(kinds), 9.5), 3.4), squeeze=False)
    for j, k in enumerate(kinds):
        x, cb = series(k, "base", "correct")
        ax[0][j].plot(x, [v / n * 100 for v in cb], "-o", color=BLUE, lw=2, ms=6, label="Baseline_A (항상 Hard)")
        x, ca = series(k, "ada", "correct")
        ax[0][j].plot(x, [v / n * 100 for v in ca], "-o", color=ORANGE, lw=2, ms=6, label="AdaPath_A")
        ax[0][j].set_ylabel("정확도 (%)")
        ax[0][j].set_title(TITLE[k], fontsize=10.5, color=INK)
        xfix(ax[0][j], k)
        style(ax[0][j])
    ax[0][0].legend(fontsize=8.5, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(a.out, "fig_robustness_acc.png"), dpi=200)
    print("saved fig_robustness_modes.png, fig_robustness_acc.png ->", a.out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default="../rtl/robustness_A.csv")
    p.add_argument("--out", default="../out")
    main(p.parse_args())
