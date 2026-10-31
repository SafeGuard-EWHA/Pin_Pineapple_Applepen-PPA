"""Score-Margin 분포 분석 + T_high / T_low 최적화 + 모드 비율 / MAC 절감 산출.

중간보고서 3장에 들어갈 그림·표를 전부 여기서 생성한다.

    python analyze_margin.py --arch B

산출물 (../out/):
    fig_margin_hist.png     [그림] Score Margin 분포 (정답/오답 분리)
    fig_tradeoff.png        [그림] 정확도-연산량 Trade-off 및 동작점
    table_modes.md          [표]   선정 임계값에서의 모드 비율 / 정확도 / MAC
    sweep.csv               전체 스윕 원본 데이터
"""
import argparse

import numpy as np
import torch

from arch import CANDIDATES
from model import AdaPathNet, margin

ARCHS = {c.name[0]: c for c in CANDIDATES}


def cycles(a, mode):
    """대략적 처리 사이클 모델 (레퍼런스의 1 pixel/cycle 스트리밍 기준).

    conv1 은 입력 픽셀 수, conv2 는 conv1 pool 출력 픽셀 수에 비례하며,
    FC 는 출력 클래스당 1 사이클로 근사한다. 상대 비교용이다.
    """
    front = a.img ** 2 + a.n_class                       # conv1 스트리밍 + early FC
    if mode == 0:
        return front
    back = a.h_pool1 ** 2 + a.n_class                     # conv2 스트리밍 + FC
    return front + back                                   # Medium/Hard 는 사이클 동일, 전력이 다름


@torch.no_grad()
def collect(arch, ckpt, out_dir, prefix):
    d = np.load(out_dir + "/" + prefix + "_test.npz", allow_pickle=True)
    x = torch.from_numpy(d["x"]).float().div_(255.).unsqueeze(1)
    y = torch.from_numpy(d["y"]).long()

    model = AdaPathNet(arch)
    model.load_state_dict(ckpt["state"])
    model.eval()

    e, l, f = model(x)
    return {
        "y": y.numpy(),
        "margin": margin(e).numpy(),
        "pred_early": e.argmax(1).numpy(),
        "pred_light": l.argmax(1).numpy(),
        "pred_full": f.argmax(1).numpy(),
        "classes": d["classes"],
    }


def eval_point(r, a, t_low, t_high):
    """(T_low, T_high) 한 점에서의 모드 배분 / 정확도 / 평균 MAC."""
    m = r["margin"]
    easy = m >= t_high
    hard = m < t_low
    med = ~easy & ~hard

    pred = np.where(easy, r["pred_early"],
                    np.where(med, r["pred_light"], r["pred_full"]))
    mm = a.mode_macs()
    mac = np.where(easy, mm["Easy"], np.where(med, mm["Medium"], mm["Hard"]))
    cyc = np.where(easy, cycles(a, 0), cycles(a, 1))

    return {
        "t_low": t_low, "t_high": t_high,
        "r_easy": easy.mean(), "r_med": med.mean(), "r_hard": hard.mean(),
        "acc": (pred == r["y"]).mean(),
        "avg_mac": mac.mean(), "avg_cyc": cyc.mean(),
    }


def main(a):
    arch = ARCHS[a.arch]
    path = a.out + "/adapath_" + a.prefix + "_" + a.arch + ".pt"
    try:
        ckpt = torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:                              # torch < 2.0 은 weights_only 미지원
        ckpt = torch.load(path, map_location="cpu")
    for k, v in ckpt["arch"].items():
        setattr(arch, k, v)

    r = collect(arch, ckpt, a.out, a.prefix)
    m = r["margin"]
    acc_full = (r["pred_full"] == r["y"]).mean()
    mm = arch.mode_macs()

    print("[arch " + arch.name + "] " + arch.shapes())
    print("Hard(=baseline) 정확도 %.4f, MAC %d" % (acc_full, mm["Hard"]))
    print("margin  min %.3f  median %.3f  max %.3f" % (m.min(), np.median(m), m.max()))

    # ---------- 임계값 스윕 ----------
    qs = np.linspace(0.02, 0.98, a.grid)
    cand = np.quantile(m, qs)
    rows = []
    for i, tl in enumerate(cand):
        for th in cand[i:]:                       # T_low <= T_high 만
            rows.append(eval_point(r, arch, tl, th))

    import csv
    with open(a.out + "/sweep.csv", "w", newline="", encoding="utf-8") as fp:
        w = csv.DictWriter(fp, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # ---------- 동작점 선정: 정확도 손실 허용치 내에서 MAC 최소 ----------
    picks = {}
    for tol in (0.005, 0.010, 0.020):             # 0.5 %p / 1 %p / 2 %p
        ok = [q for q in rows if q["acc"] >= acc_full - tol]
        picks[tol] = min(ok, key=lambda q: q["avg_mac"]) if ok else None

    lines = ["# Score-Margin 동작점 분석 결과", "",
             "* 아키텍처: `" + arch.name + "`  " + arch.shapes(),
             "* 테스트 샘플 %d 장, 클래스 %d 개" % (len(m), arch.n_class),
             "* Baseline(항상 Hard 경로) 정확도 **%.2f %%**, MAC/이미지 **%d**"
             % (acc_full * 100, mm["Hard"]), "",
             "| 정확도 손실 허용 | T_low | T_high | Easy | Medium | Hard | 정확도 | 평균 MAC | MAC 절감 |",
             "|---|---|---|---|---|---|---|---|---|"]
    for tol, q in picks.items():
        if q is None:
            lines.append("| %.1f %%p | (해당 동작점 없음) | | | | | | | |" % (tol * 100))
            continue
        lines.append("| %.1f %%p | %.3f | %.3f | %.1f %% | %.1f %% | %.1f %% | %.2f %% | %.0f | **%.1f %%** |"
                     % (tol * 100, q["t_low"], q["t_high"],
                        q["r_easy"] * 100, q["r_med"] * 100, q["r_hard"] * 100,
                        q["acc"] * 100, q["avg_mac"],
                        (1 - q["avg_mac"] / mm["Hard"]) * 100))
    lines += ["", "| 모드 | 활성 경로 | MAC/이미지 | Hard 대비 |", "|---|---|---|---|"]
    for k, v in mm.items():
        path = {"Easy": "Conv1 + Early Classifier",
                "Medium": "Conv1 + Conv2(%dch) + Light FC" % arch.c2_med,
                "Hard": "Conv1 + Conv2(%dch) + Full FC" % arch.c2}[k]
        lines.append("| %s | %s | %d | %.1f %% 절감 |"
                     % (k, path, v, (1 - v / mm["Hard"]) * 100))

    txt = "\n".join(lines)
    open(a.out + "/table_modes_" + a.prefix + ".md", "w", encoding="utf-8").write(txt)
    print("\n" + txt)

    # ---------- 그림 ----------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams["font.family"] = "Malgun Gothic"
        plt.rcParams["axes.unicode_minus"] = False

        correct = r["pred_early"] == r["y"]
        # 3단계 구조(Easy/Medium/Hard)가 실제로 보이는 지점을 우선 선택한다.
        # 허용치가 커질수록 스윕이 T_low == T_high 로 수렴(=Medium 소멸)할 수 있어
        # 그런 경우는 건너뛴다.
        best = None
        for tol in (0.005, 0.010, 0.020):
            q = picks[tol]
            if q and q["t_low"] < q["t_high"]:
                best = q
                break
        best = best or picks[0.010] or picks[0.020]

        xcap = float(np.percentile(m, 97))
        xcap = max(xcap, (best["t_high"] if best else 0) * 1.3, 1e-6)
        bins = np.linspace(0, xcap, 60)
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(m[correct], bins=bins, alpha=.65, label="Early Classifier correct")
        ax.hist(m[~correct], bins=bins, alpha=.65, label="Early Classifier wrong")
        if best:
            ax.axvline(best["t_low"], ls="--", c="k", lw=1)
            top = ax.get_ylim()[1]
            ax.text(best["t_low"], top * .96, " T_low", fontsize=9, va="top")
            if best["t_high"] > best["t_low"]:
                ax.axvline(best["t_high"], ls="--", c="k", lw=1)
                ax.text(best["t_high"], top * .88, " T_high", fontsize=9, va="top")
        ax.set_xlim(0, xcap)
        ax.set_xlabel("Score Margin (Top-1 - Top-2)  ·  상위 3% 특이값은 축 밖으로 잘림")
        ax.set_ylabel("count")
        ax.set_title("Score Margin distribution")
        ax.legend()
        fig.tight_layout()
        fig.savefig(a.out + "/fig_margin_hist_" + a.prefix + ".png", dpi=150)

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.scatter([q["avg_mac"] for q in rows], [q["acc"] * 100 for q in rows],
                   s=4, alpha=.25, label="threshold sweep")
        ax.axhline(acc_full * 100, ls=":", c="r", label="Baseline accuracy")
        ax.scatter([mm["Hard"]], [acc_full * 100], marker="*", s=180, c="r",
                   label="Baseline (always Hard)")
        for tol, q in picks.items():
            if q:
                ax.scatter([q["avg_mac"]], [q["acc"] * 100], marker="D", s=60,
                           label="AdaPath (-%.1f %%p)" % (tol * 100))
        ax.set_xlabel("average MAC / image")
        ax.set_ylabel("accuracy (%)")
        ax.set_title("Accuracy - Computation trade-off")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(a.out + "/fig_tradeoff_" + a.prefix + ".png", dpi=150)
        print("\n 그림 저장 -> " + a.out + "/fig_margin_hist_" + a.prefix + ".png, "
              "fig_tradeoff_" + a.prefix + ".png")
    except ImportError:
        print("\n[!] matplotlib 미설치 - 그림 생략")

    print("\n※ 선정된 T_low / T_high 는 export_int8.py 에서 정수 스케일로 변환해야")
    print("   RTL difficulty_decoder.v 의 threshold 레지스터 값이 된다.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--arch", default="B", choices=list(ARCHS))
    p.add_argument("--grid", type=int, default=25)
    p.add_argument("--out", default="../out")
    p.add_argument("--prefix", default="wm811k")
    main(p.parse_args())
