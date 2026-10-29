"""Region 2 (Top-2 Finder / Score-Margin / Difficulty Decoder) RTL 검증 벡터 생성.

실제 테스트 이미지를 INT8 정수 파이프라인에 통과시켜 Early Classifier 의
4개 class score 와 기대 margin / mode 를 뽑아 $readmemh 포맷으로 저장한다.

    python dump_region2_vectors.py --arch B --n 200

출력: ../out/rtl_data/region2_vectors.txt
    벡터당 6 워드(16-bit hex): s0 s1 s2 s3 margin mode
    mode: 0 = Easy, 1 = Medium, 2 = Hard   (thresholds.vh 의 T_LOW/T_HIGH 기준)
"""
import argparse
import re

import numpy as np
import torch

from arch import CANDIDATES
from export_int8 import IntNet
from model import AdaPathNet

ARCHS = {c.name[0]: c for c in CANDIDATES}


def main(a):
    arch = ARCHS[a.arch]
    try:
        ckpt = torch.load(a.out + "/adapath_" + a.prefix + "_" + a.arch + ".pt",
                          map_location="cpu", weights_only=False)
    except TypeError:
        ckpt = torch.load(a.out + "/adapath_" + a.prefix + "_" + a.arch + ".pt", map_location="cpu")
    for k, v in ckpt["arch"].items():
        setattr(arch, k, v)
    model = AdaPathNet(arch)
    model.load_state_dict(ckpt["state"])
    model.eval()

    d = np.load(a.out + "/" + a.prefix + "_test.npz", allow_pickle=True)
    xs = d["x"]

    net = IntNet(model, arch)
    net.calibrate(xs[:a.n_cal])

    rd = a.out + "/rtl_data_" + a.prefix
    vh = open(rd + "/thresholds.vh", encoding="ascii").read()
    t_low = int(re.search(r"T_LOW\s*=\s*12'sd(\d+)", vh).group(1))
    t_high = int(re.search(r"T_HIGH\s*=\s*12'sd(\d+)", vh).group(1))
    print("thresholds.vh: T_LOW=%d T_HIGH=%d" % (t_low, t_high))

    nc = arch.n_class
    n = min(a.n, len(xs))
    words, modes = [], [0, 0, 0]
    for i in range(n):
        h, _ = net.front(xs[i].astype(np.int32))
        e, _ = net.early(h)                       # signed 12-bit x n_class
        s = np.sort(e)[::-1]
        margin = int(s[0] - s[1])
        mode = 0 if margin >= t_high else (2 if margin < t_low else 1)
        modes[mode] += 1
        words += [int(v) & 0xFFF for v in e] + [margin & 0xFFF, mode]

    path = rd + "/region2_vectors.txt"
    with open(path, "w", encoding="ascii") as f:
        f.write("// s0..s%d margin mode  (16-bit hex words, %d vectors, n_class=%d)\n"
                % (nc - 1, n, nc))
        per_vec = nc + 2
        for i in range(0, len(words), per_vec):
            f.write(" ".join("%04x" % w for w in words[i:i + per_vec]) + "\n")
    print("%d vectors (n_class=%d) -> %s" % (n, nc, path))
    print("mode 분포: Easy %d / Medium %d / Hard %d" % tuple(modes))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--arch", default="B", choices=list(ARCHS))
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--n_cal", type=int, default=64)
    p.add_argument("--out", default="../out")
    p.add_argument("--prefix", default="wm811k")
    main(p.parse_args())
