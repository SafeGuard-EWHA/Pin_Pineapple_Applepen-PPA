"""주최측 input_1000.txt 를 열화시킨 입력 파일 생성 (실험 2: 난이도 비례 연산 배분).

    python make_noisy_inputs.py --src ../verilog_ref/data/input_1000.txt --out ../rtl/noisy

열화 종류 (실제 센서 환경에 대응):
  contrast : 저조도 / 노출 부족   (픽셀 x c,  c = 1.0, 0.7, 0.5, 0.4, 0.3, 0.2)
  blur     : 초점 흐림            (3x3 평균 필터 n회, n = 0..4)
  gauss    : 센서 잡음            (가우시안 σ = 0, 20, 40, 60, 80, 100)

출력: <out>/input_1000_<kind>_<level>.txt  (원본과 같은 형식: 한 줄 28개 hex, 행 사이 빈 줄)
seed 고정이라 누가 실행해도 같은 파일이 만들어진다.
※ 주최측 input_1000.txt 는 서로 다른 100장이 10번 반복된 구성이라, 결정적 열화(contrast,
  blur)의 결과는 10장 단위로 움직인다.
"""
import argparse
import os

import numpy as np

LEVELS = {
    "contrast": [1.0, 0.7, 0.5, 0.4, 0.3, 0.2],
    "blur": [0, 1, 2, 3, 4],
    "gauss": [0, 20, 40, 60, 80, 100],
}


def read_pixels(path):
    tok = open(path, encoding="ascii").read().split()
    px = np.array([int(t, 16) for t in tok], dtype=np.float64)
    assert px.size % 784 == 0, px.size
    return px.reshape(-1, 28, 28)


def write_pixels(path, img):
    px = np.clip(np.rint(img), 0, 255).astype(np.int32).reshape(-1, 28)
    with open(path, "w", encoding="ascii", newline="\n") as f:
        for r in px:
            f.write(" ".join("%02x" % v for v in r) + "\n\n")


def blur3(img):
    p = np.pad(img, ((0, 0), (1, 1), (1, 1)))
    return sum(p[:, i:i + 28, j:j + 28] for i in range(3) for j in range(3)) / 9.0


def degrade(img, kind, lv, rng):
    if kind == "contrast":
        return img * lv
    if kind == "blur":
        for _ in range(int(lv)):
            img = blur3(img)
        return img
    if kind == "gauss":
        return img + (rng.normal(0, lv, img.shape) if lv > 0 else 0)
    raise ValueError(kind)


def main(a):
    img = read_pixels(a.src)
    os.makedirs(a.out, exist_ok=True)
    for kind in a.kind:
        rng = np.random.default_rng(a.seed)
        for lv in LEVELS[kind]:
            out = os.path.join(a.out, "input_1000_%s_%s.txt" % (kind, ("%g" % lv)))
            write_pixels(out, degrade(img.copy(), kind, lv, rng))
            print("%-8s %-5g -> %s" % (kind, lv, out))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--src", default="../verilog_ref/data/input_1000.txt")
    p.add_argument("--out", default="../rtl/noisy")
    p.add_argument("--kind", nargs="+", default=["contrast", "blur", "gauss"], choices=list(LEVELS))
    p.add_argument("--seed", type=int, default=2026)
    main(p.parse_args())
