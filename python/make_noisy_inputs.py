"""주최측 input_1000.txt 에 가우시안 노이즈를 더한 입력 파일 생성 (실험 2: 난이도 비례 연산 배분).

    python make_noisy_inputs.py --src ../verilog_ref/data/input_1000.txt --out ../rtl/noisy

출력: <out>/input_1000_s<σ>.txt  (원본과 같은 형식: 한 줄 28개 hex, 행 사이 빈 줄)
같은 seed 를 쓰므로 누가 실행해도 같은 파일이 만들어진다.
"""
import argparse
import os

import numpy as np


def read_pixels(path):
    tok = open(path, encoding="ascii").read().split()
    px = np.array([int(t, 16) for t in tok], dtype=np.int32)
    assert px.size % 784 == 0, px.size
    return px


def write_pixels(path, px):
    with open(path, "w", encoding="ascii", newline="\n") as f:
        for r in px.reshape(-1, 28):
            f.write(" ".join("%02x" % v for v in r) + "\n\n")


def main(a):
    px = read_pixels(a.src)
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    for s in a.sigma:
        noisy = px + (rng.normal(0, s, px.shape) if s > 0 else 0)
        noisy = np.clip(np.rint(noisy), 0, 255).astype(np.int32)
        out = os.path.join(a.out, "input_1000_s%d.txt" % s)
        write_pixels(out, noisy)
        print("σ=%-3d -> %s   (평균 |변화| %.1f)" % (s, out, np.abs(noisy - px).mean()))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--src", default="../verilog_ref/data/input_1000.txt")
    p.add_argument("--out", default="../rtl/noisy")
    p.add_argument("--sigma", type=int, nargs="+", default=[0, 10, 20, 30, 40, 60])
    p.add_argument("--seed", type=int, default=2026)
    main(p.parse_args())
