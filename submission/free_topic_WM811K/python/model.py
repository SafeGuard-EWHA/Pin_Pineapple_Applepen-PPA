"""AdaPath-NPU 의 PyTorch golden model.

레퍼런스 chip.v 의 연산 순서를 그대로 따라간다:
    conv(valid) -> maxpool 2x2 -> ReLU
    (RTL 의 maxpool_relu 는 max 후 relu 순서이며, ReLU 단조성상 relu 후 max 와 동치)

세 개의 head 를 갖는다:
    early : Conv1 직후 AvgPool -> FC          (Easy 모드 출력, Score-Margin 산출원)
    light : Conv2 의 앞 c2_med 채널만 -> FC   (Medium 모드 출력)
    full  : Conv2 전 채널 -> FC               (Hard 모드 출력, baseline 과 동일 경로)
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

from arch import Arch


class AdaPathNet(nn.Module):
    def __init__(self, a: Arch):
        super().__init__()
        self.a = a
        self.conv1 = nn.Conv2d(1, a.c1, a.k1, bias=True)
        self.conv2 = nn.Conv2d(a.c1, a.c2, a.k2, bias=True)
        self.fc_early = nn.Linear(a.n_early_feat, a.n_class)
        self.fc_light = nn.Linear(a.n_fc_light, a.n_class)
        self.fc_full = nn.Linear(a.n_fc_full, a.n_class)

    # ---- Region 1: 모든 모드가 공유하는 전단부 ----
    def front(self, x):
        return F.relu(F.max_pool2d(self.conv1(x), 2))       # [N, c1, h_pool1, h_pool1]

    def early_head(self, h):
        e = F.avg_pool2d(h, self.a.early_pool)              # 12x12 -> 4x4
        return self.fc_early(e.flatten(1))

    # ---- Region 3: 난이도별 후단부 ----
    def back(self, h):
        c = F.relu(F.max_pool2d(self.conv2(h), 2))          # [N, c2, h_pool2, h_pool2]
        full = self.fc_full(c.flatten(1))
        light = self.fc_light(c[:, :self.a.c2_med].flatten(1))
        return light, full

    def forward(self, x):
        h = self.front(x)
        light, full = self.back(h)
        return self.early_head(h), light, full


def margin(logits):
    """Score Margin = Top-1 score - Top-2 score.

    softmax 를 거치지 않은 raw class score 기준이며,
    RTL 의 top2_finder + score_margin_calc 와 동일한 연산이다.
    """
    top2 = torch.topk(logits, 2, dim=1).values
    return top2[:, 0] - top2[:, 1]
