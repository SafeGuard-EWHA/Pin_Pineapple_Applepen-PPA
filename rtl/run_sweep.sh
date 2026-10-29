#!/usr/bin/env bash
# 런타임 임계값 스윕 (실험 1: 하드웨어 실측 동작 곡선)
#
#   bash run_sweep.sh A        # 모델 A (지정주제), T_low = T_high 스윕
#   bash run_sweep.sh B        # 모델 B, T_low 고정(71) + T_high 스윕
#
# 필요: ../verilog_ref/data/input_1000.txt (주최측 배포 데이터)
# 결과: sweep_<model>.csv  (TL,TH,correct,avg_cycles,easy,med,hard)
set -e
cd "$(dirname "$0")"
[ -d /c/iverilog/bin ] && export PATH="/c/iverilog/bin:$PATH"
M=${1:-A}
CORE="mac_tree.v conv1_engine.v conv2_engine.v maxpool_relu_n.v fmap_buffer.v early_classifier.v \
      fc_engine.v top2_finder.v score_margin_calc.v difficulty_decoder.v mode_control_fsm.v \
      adapath_top.v ref/conv1_buf.v ref/conv2_buf.v"
if [ "$M" = A ]; then
  iverilog -g2012 -I. -DMODEL_A -DDATA='"../out/rtl_data_mnist_A/"' -o sweep_A.vvp $CORE tb_threshold_sweep.v
else
  cp ../out/rtl_data_mnist/shifts.vh ../out/rtl_data_mnist/thresholds.vh .
  iverilog -g2012 -I. -o sweep_B.vvp $CORE tb_threshold_sweep.v
fi
OUT=sweep_$M.csv
echo "TL,TH,correct,avg_cycles,easy,med,hard" > $OUT
for TH in 0 10 20 30 40 50 63 80 100 119 140 170 200 250 300 400; do
  if [ "$M" = A ]; then TL=$TH; else TL=$(( TH < 71 ? TH : 71 )); fi
  vvp sweep_$M.vvp +TL=$TL +TH=$TH | grep '^SWEEP' | cut -d, -f2- | tee -a $OUT
done
echo "-> $OUT"
