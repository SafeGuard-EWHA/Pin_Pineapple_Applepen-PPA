#!/usr/bin/env bash
# 실험 2: 입력 난이도(노이즈) 에 따른 모드 분포·정확도 (모델 A, AdaPath vs Baseline)
#
#   cd python && python make_noisy_inputs.py      # rtl/noisy/input_1000_s*.txt 생성
#   cd rtl    && bash run_robustness.sh           # -> robustness_A.csv
#   cd python && python plot_robustness.py        # -> fig_robustness_*.png
set -e
cd "$(dirname "$0")"
[ -d /c/iverilog/bin ] && export PATH="/c/iverilog/bin:$PATH"
CORE="mac_tree.v conv1_engine.v conv2_engine.v maxpool_relu_n.v fmap_buffer.v early_classifier.v \
      fc_engine.v top2_finder.v score_margin_calc.v difficulty_decoder.v mode_control_fsm.v \
      adapath_top.v ref/conv1_buf.v ref/conv2_buf.v"
DATA='"../out/rtl_data_mnist_A/"'
iverilog -g2012 -I. -DMODEL_A -DDATA="$DATA"            -o rob_ada.vvp  $CORE tb_threshold_sweep.v
iverilog -g2012 -I. -DMODEL_A -DDATA="$DATA" -DBASELINE -o rob_base.vvp $CORE tb_threshold_sweep.v
OUT=robustness_A.csv
echo "sigma,design,correct,avg_cycles,easy,med,hard" > $OUT
for f in $(ls noisy/input_1000_s*.txt | sort -t s -k3 -n); do
  s=$(basename $f .txt | sed 's/.*_s//')
  for d in ada base; do
    r=$(vvp rob_$d.vvp +TL=63 +TH=63 +IMG=$f | grep '^SWEEP' | cut -d, -f4-)
    echo "$s,$d,$r" | tee -a $OUT
  done
done
echo "-> $OUT"
