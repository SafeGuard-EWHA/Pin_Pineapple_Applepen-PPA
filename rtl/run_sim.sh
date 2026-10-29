#!/usr/bin/env bash
# AdaPath-NPU RTL 시뮬레이션 일괄 실행 (Icarus Verilog)
#
#   bash run_sim.sh            # Region2 단위검증 + 3종 아키텍처 end-to-end (MNIST golden)
#   bash run_sim.sh 2          # AdaPath(VARIANT=2) end-to-end 만
#   DATA=../out/rtl_data_wm811k bash run_sim.sh   # 다른 데이터셋 golden 으로
#
# Windows Git Bash: iverilog 가 C:\iverilog\bin 에 설치돼 있으면 자동으로 PATH 추가.
set -e
cd "$(dirname "$0")"
[ -d /c/iverilog/bin ] && export PATH="/c/iverilog/bin:$PATH"
DATA="${DATA:-../out/rtl_data_mnist}"
cp "$DATA/thresholds.vh" "$DATA/shifts.vh" .

CORE="mac_tree.v conv1_engine.v conv2_engine.v maxpool_relu_n.v fmap_buffer.v \
      early_classifier.v fc_engine.v top2_finder.v score_margin_calc.v \
      difficulty_decoder.v mode_control_fsm.v adapath_top.v ref/conv1_buf.v ref/conv2_buf.v"

if [ -z "$1" ]; then
  echo "================ Region 2 단위 검증 (tb_region2) ================"
  cp "$DATA/region2_vectors.txt" . 2>/dev/null || true
  iverilog -g2012 -I. -o tb_region2.vvp top2_finder.v score_margin_calc.v \
           difficulty_decoder.v mode_control_fsm.v tb_region2.v
  vvp tb_region2.vvp | grep -v "VCD info"
  VARIANTS="0 1 2"
else
  VARIANTS="$1"
fi

for V in $VARIANTS; do
  case $V in 0) NAME=Baseline;; 1) NAME=Early-Exit;; 2) NAME=AdaPath;; esac
  echo "================ VARIANT=$V ($NAME) end-to-end ================"
  iverilog -g2012 -I. -DDATA="\"$DATA/\"" -DVARIANT=$V -o tb_v$V.vvp $CORE tb_adapath.v
  vvp tb_v$V.vvp | grep -v "VCD info"
done
echo "파형: tb_region2.vcd / tb_adapath.vcd  (GTKWave 또는 Vivado 로 열기)"
