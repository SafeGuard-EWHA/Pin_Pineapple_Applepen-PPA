# logs/ 의 넷리스트 실행 로그를 RTL 결과와 이미지 인덱스 기준으로 대조하여 summary.json을 만든다.
# RTL 기준: results_hs/corrected_tb/sequential.csv (인덱스 0~999), 인덱스 1000(X→0 치환)은 같은 조건 RTL 결과 decision 5.
import csv, re, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
seq = {int(r['image_index']): r for r in csv.DictReader(open(os.path.join(HERE, '..', '..', 'results_hs', 'corrected_tb', 'sequential.csv'), encoding='utf-8'))}
RUNS = [("default", "기본", "net_seed_default.log"), ("seed2", "2", "net_seed2.log"), ("seed3", "3", "net_seed3.log"),
        ("seed4", "4", "net_seed4.log"), ("seed5", "5", "net_seed5.log")]
out = {"runs": [], "rtl_ref": "results_hs/corrected_tb/sequential.csv"}
grp = json.load(open(os.path.join(HERE, 'content_group.json'), encoding='utf-8'))['group']
idx_all = set()
for key, seed, fn in RUNS:
    txt = open(os.path.join(HERE, 'logs', fn), encoding='utf-8', errors='ignore').read()
    obs = [tuple(map(int, m.groups())) for m in re.finditer(r'OBS n=(\d+) idx=(\d+) dec=(\d+) t=(\d+)', txt)]
    dm = cm = cor = checked = 0; prev = 10175; bad = []; excluded = []
    for n, idx, dec, t in obs:
        gd = 5 if idx == 1000 else int(seq[idx]['decision'])
        gc = None if idx == 1000 else int(seq[idx]['interface_cycles'])
        cyc = (t - 10 - prev) // 10 - 1; prev = t - 10
        dm += dec == gd; cor += (idx % 10) == dec
        if gc is None:
            excluded.append({"n": n, "image_index": idx, "observed_cycles": cyc, "reason": "No cycle reference for X/Z-filled input"})
        else:
            checked += 1
            cm += cyc == gc
        if dec != gd or not (gc is None or cyc == gc): bad.append([n, idx, dec, gd, cyc, gc])
        idx_all.add(idx)
    fin = re.search(r'Accuracy :\s*(\d+)%', txt)
    out["runs"].append({"key": key, "seed": seed, "outputs": len(obs), "decision_match": dm, "cycle_match": cm,
                        "correct": cor, "cycle_checked": checked, "cycle_excluded": excluded, "mismatches": bad, "final_accuracy_line": fin.group(0) if fin else None,
                        "sim_end_ns": max([int(x) for x in re.findall(r'STEP k=\d+ t=(\d+) ns', txt)] or [0])})
out["total_outputs"] = sum(r["outputs"] for r in out["runs"])
out["total_decision_match"] = sum(r["decision_match"] for r in out["runs"])
out["total_cycle_match"] = sum(r["cycle_match"] for r in out["runs"])
out["total_cycle_checked"] = sum(r["cycle_checked"] for r in out["runs"])
out["total_cycle_excluded"] = sum(len(r["cycle_excluded"]) for r in out["runs"])
out["distinct_indices"] = len(idx_all)
out["distinct_contents"] = len({grp[i] if i < 1000 else -1 for i in idx_all})
json.dump(out, open(os.path.join(HERE, 'summary.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "runs"}, ensure_ascii=False), [(r["key"], r["outputs"], r["decision_match"], r["cycle_match"]) for r in out["runs"]])
