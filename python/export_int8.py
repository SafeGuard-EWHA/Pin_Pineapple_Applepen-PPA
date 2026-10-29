"""INT8 PTQ + Verilog $readmemh 파일 생성 + 정수 golden reference 덤프.

레퍼런스(chip.v)의 정수 연산 규약을 그대로 재현한다:
    * weight / bias : signed 8-bit
    * activation    : signed 12-bit (saturating)
    * 각 층 누산 후 오른쪽 시프트로 12-bit 재양자화
      (시프트량은 실제 정수 누산기 분포를 측정해 자동 결정 = calibration)

RTL 쪽에서는 이 시프트량이 그대로 `>>` 비트 선택이 되므로,
생성된 shifts.vh 를 Verilog 에 include 하면 bit-accurate 가 성립한다.

    python export_int8.py --arch B --t_low 0.231 --t_high 0.331

산출물 (../out/rtl_data/):
    conv1_weight_*.txt / conv1_bias.txt
    conv2_weight_*.txt / conv2_bias.txt
    fc_weight.txt / fc_bias.txt / early_fc_*.txt / light_fc_*.txt
    img_{easy,med,hard}_*.txt   모드별 대표 테스트 이미지
    golden_reference.txt        이미지별 mode / margin / 각 head 예측 (RTL 대조용)
    shifts.vh, thresholds.vh    RTL 파라미터
"""
import argparse
import os

import numpy as np
import torch

from arch import CANDIDATES
from model import AdaPathNet

ARCHS = {c.name[0]: c for c in CANDIDATES}
I12_MIN, I12_MAX = -2048, 2047


# ----------------------------------------------------------------- 양자화 유틸
def qw(w):
    """대칭 per-tensor INT8 가중치 양자화."""
    s = float(np.abs(w).max()) / 127.0
    s = s if s > 0 else 1e-8
    return np.clip(np.round(w / s), -128, 127).astype(np.int32), s


def sat12(x):
    return np.clip(x, I12_MIN, I12_MAX).astype(np.int32)


def rshift_round(x, k):
    """반올림 우측 시프트: (x + 2^(k-1)) >> k.  HW 구현은 가산기 1개."""
    if k <= 0:
        return np.asarray(x)
    return (np.asarray(x) + (1 << (k - 1))) >> k


def shift_for(vals):
    """누산기 절댓값의 99.9 백분위가 12-bit 에 들어가도록 하는 최소 시프트."""
    p = float(np.percentile(np.abs(np.asarray(vals, dtype=np.float64)), 99.9))
    return max(0, int(np.ceil(np.log2(max(p, 1.0) / I12_MAX))))


def write_hex(path, arr, per_line, bits=8):
    """signed int -> 2의 보수 hex, 공백 구분. 레퍼런스 data/*.txt 와 동일 포맷.

    bits=8  : 가중치 (레퍼런스와 동일, "%02x")
    bits=16 : bias   (누산기 도메인 양자화로 int8 범위를 넘으므로 16-bit, "%04x")
    """
    mask, fmt = (0xFF, "%02x") if bits == 8 else (0xFFFF, "%04x")
    b = np.asarray(arr).ravel().astype(np.int64) & mask
    with open(path, "w", encoding="ascii") as f:
        for i in range(0, len(b), per_line):
            f.write(" ".join(fmt % v for v in b[i:i + per_line]) + "\n")


# ----------------------------------------------------------------- 정수 연산
def conv_raw(x, w, b):
    """x:[Cin,H,W] int, w:[Cout,Cin,k,k] int -> 시프트 전 누산기 [Cout,Ho,Wo] int64."""
    ci, h, wd = x.shape
    co, _, k, _ = w.shape
    ho, wo = h - k + 1, wd - k + 1
    out = np.empty((co, ho, wo), dtype=np.int64)
    xi = x.astype(np.int64)
    for o in range(co):
        acc = np.zeros((ho, wo), dtype=np.int64)
        for c in range(ci):
            for dy in range(k):
                for dx in range(k):
                    acc += int(w[o, c, dy, dx]) * xi[c, dy:dy + ho, dx:dx + wo]
        out[o] = acc + int(b[o])
    return out


def pool_relu(x):
    c, h, w = x.shape
    p = x[:, :h // 2 * 2, :w // 2 * 2].reshape(c, h // 2, 2, w // 2, 2).max(axis=(2, 4))
    return np.maximum(p, 0)


def avg_pool(x, k):
    """RTL 에서는 sum >> 3 (9개 합의 ÷8 근사)으로 구현. golden model 도 동일."""
    c, h, w = x.shape
    hh, ww = h // k, w // k
    s = x[:, :hh * k, :ww * k].reshape(c, hh, k, ww, k).sum(axis=(2, 4))
    return sat12(s >> 3)


def fc_raw(x, w, b):
    return (w.astype(np.int64) @ x.astype(np.int64)) + b.astype(np.int64)


class IntNet:
    """레퍼런스 RTL 과 동일한 정수 데이터패스.

    양자화 규약:
      * weight  : per-tensor 대칭 INT8 (스케일 s_w)
      * bias    : 누산기 도메인 정수 = round(b_float / (s_w x s_in)), 16-bit 저장
      * requant : 반올림 우측 시프트 (acc + 2^(k-1)) >> k, 12-bit 포화
    입력 스케일 s_in 을 층마다 추적해 float 모델과의 스케일 정합을 유지한다.
    (avg_pool 은 9합 >>3 근사라 9/8 배율이 생기며, fc_early bias 스케일에 반영)
    """

    KEYS = ("conv1", "conv2", "fc_early", "fc_light", "fc_full")

    def __init__(self, model, arch):
        self.a = arch
        sd = {k: v.detach().numpy() for k, v in model.state_dict().items()}
        self.w1, self.s_w1 = qw(sd["conv1.weight"])
        self.w2, self.s_w2 = qw(sd["conv2.weight"])
        self.we, self.s_we = qw(sd["fc_early.weight"])
        self.wl, self.s_wl = qw(sd["fc_light.weight"])
        self.wf, self.s_wf = qw(sd["fc_full.weight"])
        self.fb = {k: sd[k + ".bias"] for k in
                   ("conv1", "conv2", "fc_early", "fc_light", "fc_full")}
        self.sh = dict.fromkeys(self.KEYS, 0)
        self._rescale_biases()          # 시프트 0 기준 1차 bias; calibrate 중 재정합

    def _rescale_biases(self):
        """현재 시프트 값 기준 각 층의 입력 스케일을 계산해 bias 를 정수화한다."""
        s_in = 1.0 / 255.0                                   # float 모델은 x/255 입력
        a1 = self.s_w1 * s_in                                # conv1 누산기 스케일
        self.b1 = np.round(self.fb["conv1"] / a1).astype(np.int64)
        s1 = a1 * (1 << self.sh["conv1"])                    # conv1 출력(12-bit) 스케일

        s_early_in = s1 * 9.0 / 8.0                          # avg_pool: 9합 >>3 -> x9/8
        self.be = np.round(self.fb["fc_early"] / (self.s_we * s_early_in)).astype(np.int64)

        a2 = self.s_w2 * s1
        self.b2 = np.round(self.fb["conv2"] / a2).astype(np.int64)
        s2 = a2 * (1 << self.sh["conv2"])

        self.bl = np.round(self.fb["fc_light"] / (self.s_wl * s2)).astype(np.int64)
        self.bf = np.round(self.fb["fc_full"] / (self.s_wf * s2)).astype(np.int64)

    # ---- 단계별 ----
    def front(self, img):
        raw = conv_raw(img[None].astype(np.int32), self.w1, self.b1)
        return pool_relu(sat12(rshift_round(raw, self.sh["conv1"]))), raw

    def early(self, h):
        raw = fc_raw(avg_pool(h, self.a.early_pool).ravel(), self.we, self.be)
        return sat12(rshift_round(raw, self.sh["fc_early"])), raw

    def back(self, h):
        raw2 = conv_raw(h, self.w2, self.b2)
        c2 = pool_relu(sat12(rshift_round(raw2, self.sh["conv2"])))
        rl = fc_raw(c2[:self.a.c2_med].ravel(), self.wl, self.bl)
        rf = fc_raw(c2.ravel(), self.wf, self.bf)
        return (sat12(rshift_round(rl, self.sh["fc_light"])),
                sat12(rshift_round(rf, self.sh["fc_full"])), raw2, rl, rf)

    def calibrate(self, imgs):
        """앞 층부터 시프트를 확정하고, 확정될 때마다 bias 를 그 스케일로 재정합한다."""
        self.sh["conv1"] = shift_for(np.concatenate(
            [conv_raw(im[None].astype(np.int32), self.w1, self.b1).ravel() for im in imgs]))
        self._rescale_biases()
        hs = [self.front(im)[0] for im in imgs]

        self.sh["fc_early"] = shift_for(np.concatenate(
            [fc_raw(avg_pool(h, self.a.early_pool).ravel(), self.we, self.be) for h in hs]))
        self.sh["conv2"] = shift_for(np.concatenate(
            [conv_raw(h, self.w2, self.b2).ravel() for h in hs]))
        self._rescale_biases()

        c2s = [pool_relu(sat12(rshift_round(conv_raw(h, self.w2, self.b2),
                                            self.sh["conv2"]))) for h in hs]
        self.sh["fc_light"] = shift_for(np.concatenate(
            [fc_raw(c[:self.a.c2_med].ravel(), self.wl, self.bl) for c in c2s]))
        self.sh["fc_full"] = shift_for(np.concatenate(
            [fc_raw(c.ravel(), self.wf, self.bf) for c in c2s]))
        return self.sh


# ----------------------------------------------------------------- main
def main(a):
    arch = ARCHS[a.arch]
    path = a.out + "/adapath_" + a.prefix + "_" + a.arch + ".pt"
    try:
        ckpt = torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        ckpt = torch.load(path, map_location="cpu")
    for k, v in ckpt["arch"].items():
        setattr(arch, k, v)
    model = AdaPathNet(arch)
    model.load_state_dict(ckpt["state"])
    model.eval()

    d = np.load(a.out + "/" + a.prefix + "_test.npz", allow_pickle=True)
    xs, ys = d["x"], d["y"]

    net = IntNet(model, arch)
    print("[calibration] " + str(net.calibrate(xs[:a.n_cal])))

    rd = a.out + "/rtl_data_" + a.prefix
    os.makedirs(rd, exist_ok=True)

    # ---------- 가중치 파일 (레퍼런스 data/*.txt 와 동일 포맷) ----------
    for o in range(arch.c1):
        write_hex(rd + "/conv1_weight_%d.txt" % (o + 1), net.w1[o, 0], arch.k1)
    write_hex(rd + "/conv1_bias.txt", net.b1, 1, bits=16)
    for o in range(arch.c2):
        for c in range(arch.c1):
            write_hex(rd + "/conv2_weight_%d%d.txt" % (o + 1, c + 1), net.w2[o, c], arch.k2)
    write_hex(rd + "/conv2_bias.txt", net.b2, 1, bits=16)
    write_hex(rd + "/fc_weight.txt", net.wf, arch.n_fc_full)
    write_hex(rd + "/fc_bias.txt", net.bf, 1, bits=16)
    write_hex(rd + "/early_fc_weight.txt", net.we, arch.n_early_feat)
    write_hex(rd + "/early_fc_bias.txt", net.be, 1, bits=16)
    write_hex(rd + "/light_fc_weight.txt", net.wl, arch.n_fc_light)
    write_hex(rd + "/light_fc_bias.txt", net.bl, 1, bits=16)

    with open(rd + "/shifts.vh", "w", encoding="ascii") as fp:
        fp.write("// AdaPath-NPU requantization shifts (auto-calibrated)\n")
        fp.write("// bias files: 16-bit two-complement, accumulator domain\n")
        fp.write("// requant: rounding right-shift (acc + 2^(k-1)) >> k\n")
        for k in IntNet.KEYS:
            fp.write("localparam SHIFT_%s = %d;\n" % (k.upper(), net.sh[k]))

    # ---------- 정수 추론 + golden reference ----------
    n = min(a.n_eval, len(ys))
    xt = torch.from_numpy(xs[:n]).float().div_(255.).unsqueeze(1)
    with torch.no_grad():
        ef, lf, ff = model(xt)

    rows, mg_i, mg_f = [], [], []
    hit = dict(int_early=0, int_light=0, int_full=0, flt_full=0, agree=0)
    for i in range(n):
        h, _ = net.front(xs[i].astype(np.int32))
        e, _ = net.early(h)
        l, f, _, _, _ = net.back(h)
        s = np.sort(e)[::-1]
        mg_i.append(int(s[0] - s[1]))
        sf = torch.sort(ef[i], descending=True).values
        mg_f.append(float(sf[0] - sf[1]))
        rows.append((i, int(ys[i]), mg_i[-1], int(e.argmax()), int(l.argmax()), int(f.argmax())))
        hit["int_early"] += int(e.argmax() == ys[i])
        hit["int_light"] += int(l.argmax() == ys[i])
        hit["int_full"] += int(f.argmax() == ys[i])
        hit["flt_full"] += int(ff[i].argmax().item() == ys[i])
        hit["agree"] += int(f.argmax() == ff[i].argmax().item())

    mg_i = np.array(mg_i)
    print("\n--- INT8 vs float (n=%d) ---" % n)
    print("  Hard   : INT8 %.4f  /  float %.4f   (예측 일치율 %.4f)"
          % (hit["int_full"] / n, hit["flt_full"] / n, hit["agree"] / n))
    print("  Early  : INT8 %.4f" % (hit["int_early"] / n))
    print("  Light  : INT8 %.4f" % (hit["int_light"] / n))
    print("  정수 margin  min %d  median %d  max %d"
          % (mg_i.min(), np.median(mg_i), mg_i.max()))

    with open(rd + "/golden_reference.txt", "w", encoding="ascii") as fp:
        fp.write("# idx label margin pred_early pred_light pred_full\n")
        for r in rows:
            fp.write("%d %d %d %d %d %d\n" % r)

    # ---------- float 임계값 -> 정수 임계값 ----------
    # analyze_margin.py 가 준 float T 를 같은 분위수의 정수 margin 으로 옮긴다.
    mg_f = np.array(mg_f)
    t_low = int(np.quantile(mg_i, (mg_f < a.t_low).mean())) if a.t_low is not None \
        else int(np.quantile(mg_i, a.q_low))
    t_high = int(np.quantile(mg_i, (mg_f < a.t_high).mean())) if a.t_high is not None \
        else int(np.quantile(mg_i, a.q_high))
    with open(rd + "/thresholds.vh", "w", encoding="ascii") as fp:
        fp.write("// AdaPath-NPU difficulty decoder thresholds (integer score domain)\n")
        fp.write("localparam signed [11:0] T_LOW  = 12'sd%d;\n" % t_low)
        fp.write("localparam signed [11:0] T_HIGH = 12'sd%d;\n" % t_high)

    easy, hard = mg_i >= t_high, mg_i < t_low
    med = ~easy & ~hard
    print("\n  T_LOW = %d, T_HIGH = %d" % (t_low, t_high))
    print("  정수 도메인 모드 비율  Easy %.1f %% / Medium %.1f %% / Hard %.1f %%"
          % (easy.mean() * 100, med.mean() * 100, hard.mean() * 100))

    # ---------- 모드별 대표 이미지 (RTL testbench 용) ----------
    for tag, sel in (("easy", easy), ("med", med), ("hard", hard)):
        idx = [int(j) for j in np.flatnonzero(sel)[:3]]
        for j in idx:
            write_hex(rd + "/img_%s_%d.txt" % (tag, j), xs[j], arch.img)
        print("  %-5s 대표 이미지 %s" % (tag, idx))

    print("\n RTL 데이터 -> " + rd)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--arch", default="B", choices=list(ARCHS))
    p.add_argument("--out", default="../out")
    p.add_argument("--prefix", default="wm811k")
    p.add_argument("--n_cal", type=int, default=64, help="시프트 캘리브레이션 샘플 수")
    p.add_argument("--n_eval", type=int, default=1000)
    p.add_argument("--t_low", type=float, default=None,
                   help="analyze_margin.py 가 출력한 float T_low")
    p.add_argument("--t_high", type=float, default=None,
                   help="analyze_margin.py 가 출력한 float T_high")
    p.add_argument("--q_low", type=float, default=0.25, help="t_low 미지정 시 사용할 분위수")
    p.add_argument("--q_high", type=float, default=0.60, help="t_high 미지정 시 사용할 분위수")
    main(p.parse_args())
