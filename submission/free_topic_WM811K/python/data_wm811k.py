"""WM-811K 웨이퍼 맵 로드 / 클래스 축소 / 균형화 / 28x28 리사이즈.

준비물: Kaggle 'WM-811K wafer map' 의 LSWMD.pkl
  https://www.kaggle.com/datasets/qingyi/wm811k-wafer-map
  받은 파일을  ../data/LSWMD.pkl  에 두면 된다.

출력: ../out/wm811k_{train,test}.npz  (x: uint8 [N,28,28], y: int64 [N])
"""
import argparse
import os

import numpy as np

CLASSES_4 = ["none", "Center", "Edge-Ring", "Scratch"]
CLASSES_6 = ["none", "Center", "Edge-Ring", "Scratch", "Random", "Near-full"]

# 웨이퍼 맵 원본 값: 0=웨이퍼 밖, 1=정상 die, 2=불량 die
PIX = np.array([0, 85, 255], dtype=np.uint8)


def _label_str(v):
    """failureType 필드는 스칼라 / 1x1 ndarray / 빈 배열이 섞여 있다."""
    a = np.asarray(v).ravel()
    return str(a[0]) if a.size else ""


def load_raw(pkl_path):
    import pandas as pd
    df = pd.read_pickle(pkl_path)
    df["label"] = df["failureType"].map(_label_str)
    return df[["waferMap", "label"]]


def resize28(wmap, size=28):
    from PIL import Image
    m = np.clip(np.asarray(wmap, dtype=np.int64), 0, 2)
    img = Image.fromarray(PIX[m])
    return np.asarray(img.resize((size, size), Image.BILINEAR), dtype=np.uint8)


def build(pkl_path, classes, per_class, size, seed, out_dir, test_ratio=0.2):
    rng = np.random.default_rng(seed)
    df = load_raw(pkl_path)

    # 1단계: 클래스별 사용 가능한 표본(20x20 이상)을 먼저 전부 세어,
    # "표본 수를 동일하게 맞춘 균형 데이터셋"이 실제로 성립하도록
    # 가장 적은 클래스 하나에 전체 n 을 맞춘다.
    keep_by_class = {}
    for cname in classes:
        sub = df[df["label"] == cname]
        keep = [i for i in sub.index
                if min(np.asarray(sub.at[i, "waferMap"]).shape[:2]) >= 20]
        if not keep:
            raise SystemExit("[!] 클래스 " + cname + " 샘플이 없습니다. 라벨명을 확인하세요.")
        keep_by_class[cname] = keep
        print("  (가용) %-12s %6d 장" % (cname, len(keep)))

    n = min(per_class, min(len(v) for v in keep_by_class.values()))
    if n < per_class:
        bottleneck = min(keep_by_class, key=lambda c: len(keep_by_class[c]))
        print("[!] 가장 적은 클래스(%s = %d장)에 맞춰 클래스당 %d장으로 균형화합니다."
              % (bottleneck, len(keep_by_class[bottleneck]), n))

    xs, ys = [], []
    for ci, cname in enumerate(classes):
        for i in rng.choice(keep_by_class[cname], size=n, replace=False):
            xs.append(resize28(df.at[i, "waferMap"], size))
            ys.append(ci)
        print("  (사용) %-12s %6d 장" % (cname, n))

    x = np.stack(xs).astype(np.uint8)
    y = np.asarray(ys, dtype=np.int64)

    idx = rng.permutation(len(y))
    x, y = x[idx], y[idx]
    n_test = int(len(y) * test_ratio)

    os.makedirs(out_dir, exist_ok=True)
    np.savez_compressed(os.path.join(out_dir, "wm811k_test.npz"),
                        x=x[:n_test], y=y[:n_test], classes=np.array(classes))
    np.savez_compressed(os.path.join(out_dir, "wm811k_train.npz"),
                        x=x[n_test:], y=y[n_test:], classes=np.array(classes))
    print("\n train %d / test %d  -> %s" % (len(y) - n_test, n_test, out_dir))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--pkl", default="../data/LSWMD.pkl")
    p.add_argument("--n_class", type=int, default=4, choices=[4, 6])
    p.add_argument("--per_class", type=int, default=1500)
    p.add_argument("--size", type=int, default=28)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default="../out")
    a = p.parse_args()
    build(a.pkl, CLASSES_4 if a.n_class == 4 else CLASSES_6,
          a.per_class, a.size, a.seed, a.out)
