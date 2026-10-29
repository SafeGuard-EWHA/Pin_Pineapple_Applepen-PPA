"""rtl_data_<prefix>/ 의 가중치 hex 파일을 chip 래퍼용 상수(adapath_weights.vh)로 변환.

    python gen_chip_weights.py --prefix mnist

비트 배치는 tb_adapath / tb_official1000 의 로드 로직과 동일하다
(원소 k 가 [k*W +: W] 에 위치).
"""
import argparse
import os
import re


def read_hex(path):
    vals = []
    for line in open(path, encoding="utf-8"):
        line = re.sub(r"//.*", "", line)
        vals += [int(t, 16) for t in line.split()]
    return vals


def pack(vals, width):
    v = 0
    for k, x in enumerate(vals):
        v |= (x & ((1 << width) - 1)) << (k * width)
    n = len(vals) * width
    return "%d'h%0*x" % (n, (n + 3) // 4, v)


def main(a):
    d = a.data
    C1, C2, CM, N = 3, a.c2, a.c2_med, a.n_class
    conv1 = sum((read_hex(os.path.join(d, "conv1_weight_%d.txt" % (c + 1))) for c in range(C1)), [])
    conv2 = sum((read_hex(os.path.join(d, "conv2_weight_%d%d.txt" % (o + 1, c + 1)))
                 for o in range(C2) for c in range(C1)), [])
    items = [
        ("W_CONV1", conv1, 8, C1 * 25),
        ("B_CONV1", read_hex(os.path.join(d, "conv1_bias.txt")), 16, C1),
        ("W_CONV2", conv2, 8, C2 * C1 * 25),
        ("B_CONV2", read_hex(os.path.join(d, "conv2_bias.txt")), 16, C2),
        ("W_FCE", read_hex(os.path.join(d, "early_fc_weight.txt")), 8, N * C1 * 16),
        ("B_FCE", read_hex(os.path.join(d, "early_fc_bias.txt")), 16, N),
        ("W_FCL", read_hex(os.path.join(d, "light_fc_weight.txt")), 8, N * CM * 16),
        ("B_FCL", read_hex(os.path.join(d, "light_fc_bias.txt")), 16, N),
        ("W_FCF", read_hex(os.path.join(d, "fc_weight.txt")), 8, N * C2 * 16),
        ("B_FCF", read_hex(os.path.join(d, "fc_bias.txt")), 16, N),
    ]
    lines = ["// AdaPath-NPU 학습 가중치 상수 (gen_chip_weights.py 자동 생성, %s)" % a.prefix,
             "// chip 래퍼가 레퍼런스 가중치 포트 대신 사용한다.",
             "localparam CHIP_C2 = %d;" % C2,
             "localparam CHIP_C2_MED = %d;" % CM,
             "localparam CHIP_N_CLASS = %d;" % N]
    for name, vals, w, n in items:
        assert len(vals) == n, (name, len(vals), n)
        lines.append("localparam [%d:0] %s = %s;" % (n * w - 1, name, pack(vals, w)))
    open(a.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("written", a.out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--prefix", default="mnist")
    p.add_argument("--data", default=None)
    p.add_argument("--out", default="../rtl/adapath_weights.vh")
    p.add_argument("--c2", type=int, default=8)
    p.add_argument("--c2_med", type=int, default=4)
    p.add_argument("--n_class", type=int, default=10)
    a = p.parse_args()
    a.data = a.data or "../out/rtl_data_" + a.prefix
    main(a)
