"""AdaPath-NPU 아키텍처 정의 및 MAC 예산 계산.

의존성 없음(표준 라이브러리만). 데이터셋 없이 바로 실행 가능:
    python arch.py
"""
from dataclasses import dataclass, field


@dataclass
class Arch:
    """레퍼런스(chip.v) 토폴로지를 일반화한 파라미터."""
    name: str
    img: int = 28          # 입력 한 변 (정사각)
    k1: int = 5            # conv1 kernel
    c1: int = 3            # conv1 출력 채널 (= 공유 전단부 폭)
    k2: int = 5            # conv2 kernel
    c2: int = 3            # conv2 출력 채널 (Hard 모드에서 전부 활성)
    c2_med: int = 1        # Medium 모드에서 활성화할 conv2 채널 수
    n_class: int = 4       # WM-811K 축소 클래스 수
    early_pool: int = 3    # Early Classifier 앞단 AvgPool 크기 (12x12 -> 4x4 이면 3)

    # ---- 파생 형상 ----
    @property
    def h_conv1(self) -> int:      # conv1 valid 출력
        return self.img - self.k1 + 1

    @property
    def h_pool1(self) -> int:      # 2x2 maxpool 후 (= 공유 feature map)
        return self.h_conv1 // 2

    @property
    def h_early(self) -> int:      # Early Classifier AvgPool 후
        return self.h_pool1 // self.early_pool

    @property
    def h_conv2(self) -> int:
        return self.h_pool1 - self.k2 + 1

    @property
    def h_pool2(self) -> int:
        return self.h_conv2 // 2

    @property
    def n_early_feat(self) -> int:
        return self.h_early ** 2 * self.c1

    @property
    def n_fc_full(self) -> int:
        return self.h_pool2 ** 2 * self.c2

    @property
    def n_fc_light(self) -> int:
        return self.h_pool2 ** 2 * self.c2_med

    # ---- MAC 예산 ----
    def macs(self) -> dict:
        m = {}
        m["conv1"] = self.h_conv1 ** 2 * self.c1 * self.k1 ** 2
        m["early_fc"] = self.n_early_feat * self.n_class
        m["conv2_full"] = self.h_conv2 ** 2 * self.c2 * self.c1 * self.k2 ** 2
        m["conv2_med"] = self.h_conv2 ** 2 * self.c2_med * self.c1 * self.k2 ** 2
        m["fc_full"] = self.n_fc_full * self.n_class
        m["fc_light"] = self.n_fc_light * self.n_class
        return m

    def mode_macs(self) -> dict:
        m = self.macs()
        front = m["conv1"] + m["early_fc"]
        return {
            "Easy":   front,
            "Medium": front + m["conv2_med"] + m["fc_light"],
            "Hard":   front + m["conv2_full"] + m["fc_full"],
        }

    def shapes(self) -> str:
        return (f"{self.img}x{self.img}x1 "
                f"-> conv1({self.k1}x{self.k1},{self.c1}) {self.h_conv1}^2 "
                f"-> pool {self.h_pool1}^2x{self.c1} "
                f"-> conv2({self.k2}x{self.k2},{self.c2}) {self.h_conv2}^2 "
                f"-> pool {self.h_pool2}^2x{self.c2} "
                f"-> FC({self.n_fc_full}->{self.n_class})   "
                f"[Early: avgpool{self.early_pool} -> {self.h_early}^2x{self.c1} "
                f"= FC({self.n_early_feat}->{self.n_class})]")


# ---------------------------------------------------------------- 후보 3종
CANDIDATES = [
    Arch("A_레퍼런스그대로", img=28, k1=5, c1=3, k2=5, c2=3, c2_med=1),
    Arch("B_conv2확장(권장)", img=28, k1=5, c1=3, k2=5, c2=8, c2_med=4),
    Arch("C_계획서원안",      img=32, k1=3, c1=4, k2=3, c2=8, c2_med=4, early_pool=3),
]


def report(archs=CANDIDATES, ratios=(0.40, 0.35, 0.25)):
    """ratios = (Easy, Medium, Hard) 비율 가정. 실측 전 임시값."""
    for a in archs:
        m, mm = a.macs(), a.mode_macs()
        hard = mm["Hard"]
        print("=" * 78)
        print(f"[{a.name}]")
        print("  " + a.shapes())
        print("  --- 블록별 MAC ---")
        for k in ("conv1", "early_fc", "conv2_full", "fc_full"):
            print(f"    {k:<12} {m[k]:>10,}   ({m[k]/hard*100:5.1f} % of Hard)")
        print("  --- 모드별 MAC ---")
        for k, v in mm.items():
            print(f"    {k:<8} {v:>10,}   Hard 대비 {(1-v/hard)*100:5.1f} % 절감")
        avg = sum(r * mm[k] for r, k in zip(ratios, ("Easy", "Medium", "Hard")))
        print(f"  --- 가정 비율 E/M/H = {ratios} ---")
        print(f"    평균 MAC/이미지 {avg:>10,.0f}   Baseline(Hard 고정) 대비 "
              f"{(1-avg/hard)*100:5.1f} % 절감")
    print("=" * 78)
    print("※ E/M/H 비율은 analyze_margin.py 실측값으로 교체할 것.")
    print("※ 후단부(conv2+fc) 비중이 클수록 Early-Exit 절감 상한이 커진다.")


if __name__ == "__main__":
    report()
