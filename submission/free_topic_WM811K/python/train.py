"""AdaPathNet 학습 (3-head joint training).

    python train.py --arch B --epochs 30
"""
import argparse

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from arch import CANDIDATES
from model import AdaPathNet

ARCHS = {c.name[0]: c for c in CANDIDATES}          # "A" / "B" / "C"


def load(split, out_dir, prefix):
    d = np.load(out_dir + "/" + prefix + "_" + split + ".npz", allow_pickle=True)
    x = torch.from_numpy(d["x"]).float().div_(255.).unsqueeze(1)    # [N,1,28,28]
    y = torch.from_numpy(d["y"]).long()
    return TensorDataset(x, y)


@torch.no_grad()
def evaluate(model, loader, dev):
    model.eval()
    n, hit = 0, torch.zeros(3)
    for x, y in loader:
        x, y = x.to(dev), y.to(dev)
        for i, o in enumerate(model(x)):
            hit[i] += (o.argmax(1) == y).sum().item()
        n += len(y)
    return (hit / n).tolist()                       # [early, light, full]


def main(a):
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    arch = ARCHS[a.arch]
    arch.n_class = a.n_class
    print("[arch " + arch.name + "] " + arch.shapes())
    print("[device] " + dev)

    tr = DataLoader(load("train", a.out, a.prefix), batch_size=a.bs, shuffle=True)
    te = DataLoader(load("test", a.out, a.prefix), batch_size=512)

    model = AdaPathNet(arch).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=a.lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, a.epochs)

    for ep in range(1, a.epochs + 1):
        model.train()
        tot = 0.0
        for x, y in tr:
            x, y = x.to(dev), y.to(dev)
            e, l, f = model(x)
            # full 을 주 목적, early / light 를 보조 목적으로 동시 학습
            loss = (F.cross_entropy(f, y)
                    + a.w_early * F.cross_entropy(e, y)
                    + a.w_light * F.cross_entropy(l, y))
            opt.zero_grad()
            loss.backward()
            opt.step()
            tot += loss.item() * len(y)
        sched.step()
        acc = evaluate(model, te, dev)
        print("ep%3d  loss %.4f  acc early %.4f | light %.4f | full %.4f"
              % (ep, tot / len(tr.dataset), acc[0], acc[1], acc[2]))

    ckpt_path = a.out + "/adapath_" + a.prefix + "_" + a.arch + ".pt"
    torch.save({"state": model.state_dict(), "arch": arch.__dict__}, ckpt_path)
    print("\n saved -> " + ckpt_path)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--arch", default="B", choices=list(ARCHS))
    p.add_argument("--n_class", type=int, default=4)
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--bs", type=int, default=128)
    p.add_argument("--lr", type=float, default=2e-3)
    p.add_argument("--w_early", type=float, default=0.5)
    p.add_argument("--w_light", type=float, default=0.5)
    p.add_argument("--out", default="../out")
    p.add_argument("--prefix", default="wm811k",
                   help="데이터셋 이름 (npz/체크포인트 파일명 접두사)")
    main(p.parse_args())
