# 넷리스트 OBS 기록을 RTL 결과와 이미지 인덱스 기준으로 대조한다.
# RTL 기준: results_hs/corrected_tb/sequential.csv (모델 A RTL, 인덱스 0~999의 decision, mode, interface_cycles)
#           인덱스 1000(X→0 치환)은 같은 조건의 RTL 실행 결과(decision 5)를 사용한다.
import csv, re, sys, json
seq = {int(r['image_index']): r for r in csv.DictReader(open(sys.argv[2], encoding='utf-8'))}
obs = [tuple(map(int, m.groups())) for m in re.finditer(r'OBS n=(\d+) idx=(\d+) dec=(\d+) t=(\d+)', open(sys.argv[1], encoding='utf-8', errors='ignore').read())]
ok_dec = ok_cyc = correct = checked = 0; bad = []; excluded = []
prev_t = 10175  # 첫 비채점 출력 시각 (RTL과 동일, 아래에서 확인)
for n, idx, dec, t in obs:
    gd = 5 if idx == 1000 else int(seq[idx]['decision'])
    gc = None if idx == 1000 else int(seq[idx]['interface_cycles'])
    cyc = (t - 10 - prev_t) // 10 - 1
    prev_t = t - 10
    ok_dec += dec == gd
    if gc is None:
        excluded.append({"n": n, "image_index": idx, "observed_cycles": cyc, "reason": "No cycle reference for X/Z-filled input"})
    else:
        checked += 1
        if cyc == gc: ok_cyc += 1
        else: bad.append(("cyc", n, idx, cyc, gc))
    if dec != gd: bad.append(('dec', n, idx, dec, gd))
    correct += (idx % 10) == dec
print(json.dumps({"images": len(obs), "decision_match": ok_dec, "cycle_match": ok_cyc, "cycle_checked": checked, "cycle_excluded": excluded, "correct": correct, "mismatches": bad[:20]}, ensure_ascii=False))
