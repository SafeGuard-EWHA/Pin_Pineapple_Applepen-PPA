"""통합 RTL 테스트벤치(tb_adapath.v)용 이미지 목록 생성.

rtl_data_<prefix>/ 의 img_*.txt 와 golden_reference.txt 를 대조해
    <img_file> <idx> <label> <margin> <mode> <exp_decision> <pred_full>
형식의 tb_list.txt 를 만든다. mode/exp_decision 은 thresholds.vh 기준.

    python gen_tb_list.py --prefix mnist
"""
import argparse
import glob
import os
import re


def main(a):
    rd = a.out + "/rtl_data_" + a.prefix
    vh = open(rd + "/thresholds.vh", encoding="ascii").read()
    t_low = int(re.search(r"T_LOW\s*=\s*12'sd(\d+)", vh).group(1))
    t_high = int(re.search(r"T_HIGH\s*=\s*12'sd(\d+)", vh).group(1))

    gold = {}
    for line in open(rd + "/golden_reference.txt", encoding="ascii"):
        if line.startswith("#"):
            continue
        idx, label, margin, pe, pl, pf = map(int, line.split())
        gold[idx] = (label, margin, pe, pl, pf)

    rows = []
    for f in sorted(glob.glob(rd + "/img_*_*.txt")):
        idx = int(os.path.basename(f).rsplit("_", 1)[1].split(".")[0])
        label, margin, pe, pl, pf = gold[idx]
        mode = 0 if margin >= t_high else (2 if margin < t_low else 1)
        exp = [pe, pl, pf][mode]
        rows.append((os.path.basename(f), idx, label, margin, mode, exp, pf))

    with open(rd + "/tb_list.txt", "w", encoding="ascii") as fp:
        fp.write("%d\n" % len(rows))
        for r in rows:
            fp.write("%s %d %d %d %d %d %d\n" % r)
    print("T_LOW=%d T_HIGH=%d, %d images -> %s/tb_list.txt" % (t_low, t_high, len(rows), rd))
    for r in rows:
        print("  %-18s idx=%-4d label=%d margin=%-4d mode=%d exp=%d full=%d" % r)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--prefix", default="mnist")
    p.add_argument("--out", default="../out")
    main(p.parse_args())
