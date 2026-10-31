"""power_results/power_*.rpt의 Total 평균 전력과 VCD 관측 시간으로 추론당 에너지를 계산한다.
E_run[nJ] = P_avg[mW] x T[us], 이미지당 = E_run / 4 (이미지마다 리셋 12 cycle 포함, 지정주제와 같은 방법).
AdaPath_WM 평균 = Vivado RTL 모드 비율(Easy 404 / Medium 167 / Hard 383, 954장) 가중."""
import re, os, sys, json
here = os.path.dirname(os.path.abspath(__file__)); vdir = sys.argv[1] if len(sys.argv) > 1 else here
res = {}
for tag in ("wm_ada_easy", "wm_ada_med", "wm_ada_hard", "wm_base"):
    rpt = open(os.path.join(here, "power_results", f"power_{tag}.rpt"), encoding="utf-8", errors="ignore").read()
    tot = re.search(r"^Total\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)", rpt, re.M)
    p_w = float(tot.group(4))                      # W
    with open(os.path.join(vdir, f"{tag}.vcd"), "rb") as f:
        f.seek(max(0, os.path.getsize(f.name) - 4000)); tail = f.read().decode(errors="ignore")
    t_end = max(int(x) for x in re.findall(r"^#(\d+)", tail, re.M))   # timescale 1ps
    t_us = t_end * 1e-6
    res[tag] = {"P_mW": p_w * 1e3, "T_us": t_us, "E_per_img_nJ": p_w * 1e3 * t_us / 4}
m = {"easy": 404, "med": 167, "hard": 383}; n = sum(m.values())
e_ada = sum(m[k] * res[f"wm_ada_{k}"]["E_per_img_nJ"] for k in m) / n
e_base = res["wm_base"]["E_per_img_nJ"]
res["summary"] = {"E_AdaPath_WM_nJ": e_ada, "E_Baseline_WM_nJ": e_base, "change_pct": (e_ada - e_base) / e_base * 100,
                  "mode_counts": m}
json.dump(res, open(os.path.join(here, "power_results", "energy_wm.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
