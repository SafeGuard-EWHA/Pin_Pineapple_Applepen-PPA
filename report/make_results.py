"""WSL 로그(reports_final/) -> results.json + fig_final_compare.png

    python make_results.py <reports_final 경로>
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
REP = sys.argv[1]
GL = r"C:\Users\yhe44\idec_glsim"


def read(p):
    return open(p, encoding="utf-8", errors="ignore").read()


def area(design):
    for p in (os.path.join(REP, design + "_synth_stat.txt"),):
        if os.path.exists(p):
            m = re.search(r"Chip area for module .*?: ([0-9.]+)", read(p))
            if m:
                return float(m.group(1))
    return R_MANUAL_AREA[design]


def crit(design):
    m = re.search(r"wns\s+(-?[0-9.]+)", read(os.path.join(REP, design + "_sta.txt")))
    return 1000.0 - float(m.group(1))


def power(tag):
    """report_power 의 그룹별 total (W)."""
    t = read(os.path.join(REP, "power_%s.log" % tag))
    g = {}
    for name in ("Sequential", "Combinational", "Clock", "Macro", "Pad", "Total"):
        m = re.search(r"^%s\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)" % name, t, re.M)
        if m:
            g[name] = float(m.group(4))
    return g


def vcd_seconds(vcd):
    """VCD 의 timescale 과 마지막 timestamp 로 총 시뮬레이션 시간(s)."""
    with open(vcd, "rb") as f:
        head = f.read(4000).decode("ascii", "ignore")
        f.seek(-4000, 2)
        tail = f.read().decode("ascii", "ignore")
    ts = re.search(r"\$timescale\s+([0-9]+)\s*([munpf]?s)", head)
    unit = {"s": 1, "ms": 1e-3, "us": 1e-6, "ns": 1e-9, "ps": 1e-12, "fs": 1e-15}[ts.group(2)] * int(ts.group(1))
    last = [int(x) for x in re.findall(r"^#([0-9]+)", tail, re.M)][-1]
    return last * unit


def run_energy_nJ(tag, vcd):
    return power(tag)["Total"] * vcd_seconds(os.path.join(GL, vcd)) * 1e9


# reports_v2 / reports_v3 합성 결과 (synth_stat 'Chip area')
R_MANUAL_AREA = {"refchip": 32084.864640, "baseline": 74533.689000, "adapath": 98708.247540,
                 "baseline_wm": 75765.174120, "adapath_wm": 92891.877300}

# ---------------- 런별 에너지 -> 모드별 분리 ----------------
Eb = {m: run_energy_nJ("B_" + m, "gl_ad_%s.vcd" % m) for m in ("easy", "med", "hard")}
B_easy = Eb["easy"] / 4                       # 1-4 : E E E E
B_med = (Eb["med"] - 2 * B_easy) / 2          # 15-18 : M E E M
B_hard = Eb["hard"] - 3 * B_easy              # 5-8 : H E E E
Ea = {"easy": run_energy_nJ("A_easy", "gl_adA_easy.vcd"), "hard": run_energy_nJ("A_hard", "gl_adA_hard.vcd")}
A_easy = Ea["easy"] / 4                       # 1-4 : 모델 A 에서 전부 Easy
A_hard = Ea["hard"] - 3 * A_easy              # 5-8 : H E E E
A_base = run_energy_nJ("Abase", "gl_baA.vcd") / 4
E_ref = sum(run_energy_nJ("ref_" + k, "gl_ref_%s.vcd" % k) for k in "abc") / 12

pA = power("A_easy")
seq_pct = (pA.get("Sequential", 0) + pA.get("Clock", 0)) / pA["Total"] * 100

designs = ["refchip", "baseline_A", "adapath_A", "baseline", "adapath", "baseline_wm", "adapath_wm"]
res = {
    "area": {d: area(d) for d in designs},
    "crit": {d: crit(d) for d in designs},
    "energy_nJ": {"ref": E_ref, "Abase": A_base, "A_easy": A_easy, "A_hard": A_hard,
                  "B_easy": B_easy, "B_med": B_med, "B_hard": B_hard},
    "runs_nJ": {"B": Eb, "A": Ea},
    "power_split": {"A_easy_seq_pct": seq_pct,
                    "groups": {t: power(t) for t in ("A_easy", "A_hard", "Abase", "ref_a", "B_easy")}},
    "mac": {"ref": 58080, "Abase": 58080, "A_easy": 43680, "A_med": 48640, "A_hard": 58560,
            "B_easy": 43680, "B_med": 63520, "B_hard": 83360},
    "acc": {"ref_seq": 97.0, "A_seq": 97.0, "Abase_seq": 97.0, "B_seq": 100.0,
            "ref_org": 96.7, "A_org": 96.6, "B_org": 99.9},
    "cycles": {"ref": 1334, "ref_org": 1336, "base": 985, "easy": 845, "hard": 1016,
               "A_org": 854.8, "B_org": 870.3},
    "mode_ratio": {"A": {"easy": 0.96, "hard": 0.04}, "B": {"easy": 0.87, "med": 0.06, "hard": 0.07}},
    "modes_seq": {"A": "960 / 0 / 40", "B": "870 / 60 / 70"},
    "region2": {"area_v1": 384.5, "area_v2": 325.1, "crit_v1": 4293, "crit_v2": 1071},
    "verify": {"org_ref": "96.7 %", "org_A": "96.6 %", "org_B": "99.9 %"},
    "sw": {"A_full": "97.53", "A_light": "91.14", "A_early": "96.21", "A_modes": "94.0 / 0 / 6.0 %",
           "A_acc": "97.47", "A_macsave": "23.9", "A_int8": "97.10 % (float 96.80 %, n=1,000)",
           "B_full": "98.51", "B_light": "97.76", "B_early": "95.18", "B_modes": "82 / 8 / 10 %",
           "B_acc": "98.12", "B_macsave": "40.9", "B_int8": "97.80 % (float 97.95 %)"},
    "iso": {"mn_gain": "0 ~ 2.2 %", "wm_gain": "2 ~ 3 %",
            "mn_acc": "최대 +0.19 %p", "wm_acc": "최대 +1.68 %p"},
    # WM-811K 테스트 954장 실측 개수: Easy 401 / Medium 152 / Hard 401
    # Baseline_WM(VARIANT 0)은 Early FC 가 없으므로 43,200 + 38,400 + 512 = 82,112 MAC
    "wm": {"n_test": 954, "acc_base": 81.55, "acc_ada": 81.24, "mac_base": 82112, "mac_ada": 62848,
           "counts": {"easy": 401, "med": 152, "hard": 401},
           "mode": {"easy": 401 / 954, "med": 152 / 954, "hard": 401 / 954}, "mode_str": "401 / 152 / 401 (42.0 / 15.9 / 42.0 %)",
           "cyc_ada": (401 * 845 + 553 * 1016) / 954},
}
json.dump(res, open(os.path.join(HERE, "results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("area", "crit", "energy_nJ", "power_split")}, indent=1, ensure_ascii=False))

# ---------------- 그림: Reference = 1.0 정규화 ----------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
fmax = {d: 1e6 / v for d, v in res["crit"].items()}
_sw = os.path.join(GL, "reports_extra")
if os.path.isdir(_sw):              # 클럭 주기 스윕 결과(SDC 규칙)가 있으면 그것을 사용
    for d in list(fmax):
        f = os.path.join(_sw, "sweep_%s.txt" % d)
        if os.path.exists(f):
            xs = sorted((float(l.split()[1]), float(l.split()[2])) for l in open(f) if l.startswith("io20"))
            for (p0, w0), (p1, w1) in zip(xs, xs[1:]):
                if w0 < 0 <= w1:
                    fmax[d] = 1e6 / (p0 - w0 * (p1 - p0) / (w1 - w0))
                    break
mr = res["mode_ratio"]["A"]
cyc_A = mr["easy"] * 845 + mr["hard"] * 1016
mac_A = mr["easy"] * 43680 + mr["hard"] * 58560
E_A = mr["easy"] * A_easy + mr["hard"] * A_hard
metrics = ["평균 cycle", "지연 @Fmax", "추론당 에너지", "평균 MAC", "면적"]
ref = [1334, 1334 / fmax["refchip"], E_ref, 58080, res["area"]["refchip"]]
base = [985, 985 / fmax["baseline_A"], A_base, 58080, res["area"]["baseline_A"]]
ada = [cyc_A, cyc_A / fmax["adapath_A"], E_A, mac_A, res["area"]["adapath_A"]]
nb = [b / r for b, r in zip(base, ref)]
na = [a / r for a, r in zip(ada, ref)]

INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#e4e3dd"
fig, ax = plt.subplots(figsize=(8.2, 3.9))
x = range(len(metrics))
w = 0.36
for xs, vals, col, lab in (([i - w / 2 - 0.01 for i in x], nb, "#2a78d6", "Baseline_A (본 팀 데이터패스, 항상 Hard)"),
                           ([i + w / 2 + 0.01 for i in x], na, "#eb6834", "AdaPath_A (제안)")):
    bars = ax.bar(xs, vals, w, color=col, label=lab, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v - 0.04, "%.2f" % v, ha="center", va="top",
                fontsize=9, color="white", fontweight="bold", zorder=4)
ax.axhline(1.0, ls="--", lw=1.2, color=MUTED, zorder=2)
ax.text(-0.62, 1.02, "Reference = 1.0", ha="left", va="bottom", fontsize=8.5, color=MUTED)
ax.set_xticks(list(x))
ax.set_xticklabels(metrics, fontsize=9.5, color=INK)
ax.set_ylabel("Reference 대비 비율 (낮을수록 좋음)", fontsize=8.5, color=MUTED)
ax.set_ylim(0, max(max(nb), max(na)) * 1.18)
ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(GRID)
ax.tick_params(colors=MUTED)
ax.legend(fontsize=8.5, frameon=False, loc="upper left")
ax.set_title("정확도 동일(970/1,000) 조건에서 Reference 대비 비용 지표", fontsize=10.5, color=INK)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_final_compare.png"), dpi=200)
print("figure saved")
