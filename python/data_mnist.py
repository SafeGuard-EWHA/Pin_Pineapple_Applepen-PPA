"""MNIST 10-class 로더 (중간보고서 단계 1차 검증용).

WM-811K 파이프라인(data_wm811k.py)은 다른 공모전에 쓸 예정이라 건드리지 않고,
동일한 스키마의 npz 를 "mnist_" 접두사로 별도 생성한다.

    python data_mnist.py

출력: ../out/mnist_{train,test}.npz  (x: uint8 [N,28,28], y: int64 [N], classes: "0".."9")
"""
import argparse
import os

import numpy as np


def build(out_dir, seed):
    from torchvision.datasets import MNIST

    os.makedirs(out_dir, exist_ok=True)
    root = out_dir + "/mnist_raw"

    tr = MNIST(root, train=True, download=True)
    te = MNIST(root, train=False, download=True)

    x_tr = tr.data.numpy().astype(np.uint8)          # [60000,28,28]
    y_tr = tr.targets.numpy().astype(np.int64)
    x_te = te.data.numpy().astype(np.uint8)           # [10000,28,28]
    y_te = te.targets.numpy().astype(np.int64)

    classes = np.array([str(i) for i in range(10)])
    np.savez_compressed(out_dir + "/mnist_train.npz", x=x_tr, y=y_tr, classes=classes)
    np.savez_compressed(out_dir + "/mnist_test.npz", x=x_te, y=y_te, classes=classes)

    print("train %d / test %d  -> %s" % (len(y_tr), len(y_te), out_dir))
    print("클래스별 train 개수:", np.bincount(y_tr))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="../out")
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    build(a.out, a.seed)
