"""WM-811K 테스트셋 -> Vivado/RTL 시뮬레이션 입력 (자유주제 RTL 검증용).

    python make_wm_vivado_data.py --out ../vivado/wm_data

출력
  wm_input_954.txt : 주최 측 input_1000.txt 와 같은 형식 (한 줄 28개 hex, 행 사이 빈 줄)
  wm_expect.txt    : 이미지마다 "label exp_decision exp_mode margin" (정수 Golden, thresholds.vh 기준)
"""
import argparse
import os
import re

import numpy as np


def main(a):
    d = np.load(a.npz, allow_pickle=True)
    x, y = d["x"], d["y"]
    vh = open(os.path.join(a.rtl_data, "thresholds.vh"), encoding="ascii").read()
    t_low = int(re.search(r"T_LOW\s*=\s*12'sd(\d+)", vh).group(1))
    t_high = int(re.search(r"T_HIGH\s*=\s*12'sd(\d+)", vh).group(1))
    gold = {}
    for line in open(os.path.join(a.rtl_data, "golden_reference.txt"), encoding="ascii"):
        if not line.startswith("#"):
            idx, label, margin, pe, pl, pf = map(int, line.split())
            gold[idx] = (label, margin, pe, pl, pf)
    assert len(gold) == len(x), (len(gold), len(x))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "wm_input_954.txt"), "w", encoding="ascii", newline="\n") as f:
        for r in x.reshape(-1, 28):
            f.write(" ".join("%02x" % int(v) for v in r) + "\n\n")
    n_mode = [0, 0, 0]
    with open(os.path.join(a.out, "wm_expect.txt"), "w", encoding="ascii", newline="\n") as f:
        for i in range(len(x)):
            label, margin, pe, pl, pf = gold[i]
            assert label == int(y[i]), (i, label, y[i])
            mode = 0 if margin >= t_high else (1 if margin >= t_low else 2)
            dec = (pe, pl, pf)[mode]
            n_mode[mode] += 1
            f.write("%d %d %d %d\n" % (label, dec, mode, margin))
    exp_acc = sum(1 for i in range(len(x)) if (gold[i][2], gold[i][3], gold[i][4])[
        0 if gold[i][1] >= t_high else (1 if gold[i][1] >= t_low else 2)] == gold[i][0])
    print("images %d  T_LOW %d T_HIGH %d  modes E/M/H %s  integer-golden correct %d (%.2f %%)"
          % (len(x), t_low, t_high, n_mode, exp_acc, exp_acc / len(x) * 100))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--npz", default="../data_test/wm811k_test.npz")
    p.add_argument("--rtl_data", default="../out/rtl_data_wm811k")
    p.add_argument("--out", default="../vivado/wm_data")
    main(p.parse_args())
