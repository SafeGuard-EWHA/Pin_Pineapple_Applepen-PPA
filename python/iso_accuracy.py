"""Early-Exit(2단계) vs AdaPath(3단계) 동일 정확도(iso-accuracy) 비교.

    python iso_accuracy.py --prefix mnist

두 구조 모두 같은 Early Classifier, 같은 Score Margin 으로 난이도를 판정한다.
 - Early-Exit : margin >= T 이면 Easy, 아니면 Hard (Medium 없음)
 - AdaPath    : margin >= T_high Easy / T_low <= margin < T_high Medium / 그 외 Hard
각 구조에서 임계값을 전수 스윕해 얻은 (정확도, 평균 MAC) 점들 중, 같은 정확도 이상을
만족하는 최소 평균 MAC 을 비교한다.
"""
import argparse
import csv

import numpy as np

from analyze_margin import ARCHS, collect, cycles
import torch


def load(a):
    arch = ARCHS[a.arch]
    path = a.out + "/adapath_" + a.prefix + "_" + a.arch + ".pt"
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    for k, v in ckpt["arch"].items():
        setattr(arch, k, v)
    return arch, collect(arch, ckpt, a.out, a.prefix)


def point(r, mm, easy, hard):
    med = ~easy & ~hard
    pred = np.where(easy, r["pred_early"], np.where(med, r["pred_light"], r["pred_full"]))
    mac = np.where(easy, mm["Easy"], np.where(med, mm["Medium"], mm["Hard"]))
    return {"acc": (pred == r["y"]).mean(), "mac": mac.mean(),
            "r_easy": easy.mean(), "r_med": med.mean(), "r_hard": hard.mean()}


def main(a):
    arch, r = load(a)
    m, mm = r["margin"], arch.mode_macs()
    acc_full = (r["pred_full"] == r["y"]).mean()
    acc_light = (r["pred_light"] == r["y"]).mean()
    acc_early = (r["pred_early"] == r["y"]).mean()
    cand = np.unique(np.quantile(m, np.linspace(0.0, 1.0, a.grid)))

    ee = []                                  # Early-Exit : 임계값 1개
    for t in cand:
        p = point(r, mm, m >= t, np.zeros_like(m, bool) | (m < t))
        p["t"] = t
        ee.append(p)
    ee.append({**point(r, mm, np.zeros_like(m, bool), np.ones_like(m, bool)), "t": np.inf})

    ap = []                                  # AdaPath : 임계값 2개
    for i, tl in enumerate(cand):
        for th in cand[i:]:
            p = point(r, mm, m >= th, m < tl)
            p["t_low"], p["t_high"] = tl, th
            ap.append(p)

    print("Full %.2f%%  Light %.2f%%  Early %.2f%%   MAC Easy/Med/Hard = %d/%d/%d"
          % (acc_full * 100, acc_light * 100, acc_early * 100,
             mm["Easy"], mm["Medium"], mm["Hard"]))

    def best(rows, tol):
        ok = [q for q in rows if q["acc"] >= acc_full - tol]
        return min(ok, key=lambda q: q["mac"]) if ok else None

    lines = ["| 정확도 손실 허용 | Early-Exit 평균 MAC | AdaPath 평균 MAC | AdaPath 추가 절감 |"
             " Early-Exit 모드(E/H) | AdaPath 모드(E/M/H) | Early-Exit 정확도 | AdaPath 정확도 |",
             "|---|---|---|---|---|---|---|---|"]
    out_rows = []
    for tol in (0.001, 0.002, 0.003, 0.004, 0.005, 0.0075, 0.010, 0.020):
        e, p = best(ee, tol), best(ap, tol)
        if e is None or p is None:
            continue
        gain = (1 - p["mac"] / e["mac"]) * 100
        lines.append("| %.2f %%p | %.0f (-%.1f %%) | %.0f (-%.1f %%) | **%.2f %%** | %.1f/%.1f | %.1f/%.1f/%.1f | %.2f %% | %.2f %% |"
                     % (tol * 100, e["mac"], (1 - e["mac"] / mm["Hard"]) * 100,
                        p["mac"], (1 - p["mac"] / mm["Hard"]) * 100, gain,
                        e["r_easy"] * 100, e["r_hard"] * 100,
                        p["r_easy"] * 100, p["r_med"] * 100, p["r_hard"] * 100,
                        e["acc"] * 100, p["acc"] * 100))
        out_rows.append((tol, e, p))
    print("\n".join(lines))

    # 보고서 동작점(T_low=1.599, T_high=2.593)과 같은 T_high 의 Early-Exit 비교
    th_sel = a.t_high
    pe = point(r, mm, m >= th_sel, m < th_sel)
    pa = point(r, mm, m >= th_sel, m < a.t_low)
    print("\n[보고서 동작점 T_high=%.3f]" % th_sel)
    print("  Early-Exit: acc %.2f%%  MAC %.0f  E/H %.1f/%.1f"
          % (pe["acc"] * 100, pe["mac"], pe["r_easy"] * 100, pe["r_hard"] * 100))
    print("  AdaPath   : acc %.2f%%  MAC %.0f  E/M/H %.1f/%.1f/%.1f (T_low=%.3f)"
          % (pa["acc"] * 100, pa["mac"], pa["r_easy"] * 100, pa["r_med"] * 100,
             pa["r_hard"] * 100, a.t_low))

    # 동일 MAC 에서 정확도
    print("\n[동일 평균 MAC 에서 최대 정확도]")
    for target in (48000, 52000, 56000, 60000, 64000):
        e = max([q for q in ee if q["mac"] <= target], key=lambda q: q["acc"], default=None)
        p = max([q for q in ap if q["mac"] <= target], key=lambda q: q["acc"], default=None)
        if e and p:
            print("  MAC<=%d : Early-Exit %.2f%%  AdaPath %.2f%%  (+%.2f%%p)"
                  % (target, e["acc"] * 100, p["acc"] * 100, (p["acc"] - e["acc"]) * 100))

    with open(a.out + "/iso_accuracy_" + a.prefix + ".md", "w", encoding="utf-8") as fp:
        fp.write("# Early-Exit vs AdaPath : 동일 정확도 비교\n\n" + "\n".join(lines) + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False

    def front(rows):
        rows = sorted(rows, key=lambda q: q["mac"])
        best_acc, pts = -1, []
        for q in rows:
            if q["acc"] > best_acc:
                best_acc = q["acc"]
                pts.append(q)
        return pts

    fe, fa = front(ee), front(ap)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot([q["mac"] / 1e3 for q in fe], [q["acc"] * 100 for q in fe], "-o", ms=3,
            label="Early-Exit (Easy/Hard)")
    ax.plot([q["mac"] / 1e3 for q in fa], [q["acc"] * 100 for q in fa], "-s", ms=3,
            label="AdaPath (Easy/Medium/Hard)")
    ax.axhline(acc_full * 100, ls=":", c="r", lw=1)
    ax.scatter([mm["Hard"] / 1e3], [acc_full * 100], marker="*", s=160, c="r", label="Baseline")
    ax.set_xlim(left=mm["Easy"] / 1e3 - 1, right=mm["Hard"] / 1e3 + 1)
    ax.set_ylim(bottom=acc_full * 100 - 3)
    ax.set_xlabel("평균 MAC / 이미지 (x1000)")
    ax.set_ylabel("정확도 (%)")
    ax.set_title("Pareto front : Early-Exit vs AdaPath")
    ax.legend(fontsize=8)
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(a.out + "/fig_iso_accuracy_" + a.prefix + ".png", dpi=150)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--arch", default="B")
    p.add_argument("--grid", type=int, default=60)
    p.add_argument("--out", default="../out")
    p.add_argument("--prefix", default="mnist")
    p.add_argument("--t_low", type=float, default=1.599)
    p.add_argument("--t_high", type=float, default=2.593)
    main(p.parse_args())
