#!/usr/bin/env bash
# 실험 2: 입력 열화(난이도)에 따른 모드 분포·정확도 (모델 A, AdaPath vs Baseline)
#
#   cd python && python make_noisy_inputs.py      # rtl/noisy/input_1000_<kind>_<level>.txt
#   cd rtl    && bash run_robustness.sh [JOBS]    # -> robustness_A.csv  (JOBS: 병렬 수, 기본 4)
#   cd python && python plot_robustness.py        # -> out/fig_robustness_*.png
set -e
cd "$(dirname "$0")"
[ -d /c/iverilog/bin ] && export PATH="/c/iverilog/bin:$PATH"
JOBS=${1:-4}
CORE="mac_tree.v conv1_engine.v conv2_engine.v maxpool_relu_n.v fmap_buffer.v early_classifier.v \
      fc_engine.v top2_finder.v score_margin_calc.v difficulty_decoder.v mode_control_fsm.v \
      adapath_top.v ref/conv1_buf.v ref/conv2_buf.v"
DATA='"../out/rtl_data_mnist_A/"'
iverilog -g2012 -I. -DMODEL_A -DDATA="$DATA"            -o rob_ada.vvp  $CORE tb_threshold_sweep.v
iverilog -g2012 -I. -DMODEL_A -DDATA="$DATA" -DBASELINE -o rob_base.vvp $CORE tb_threshold_sweep.v
mkdir -p rob_tmp && rm -f rob_tmp/*
one() {  # file design
  local b; b=$(basename "$1" .txt | sed 's/^input_1000_//')       # <kind>_<level>
  local r; r=$(vvp rob_$2.vvp +TL=63 +TH=63 +IMG=$1 | grep '^SWEEP' | cut -d, -f4-)
  echo "${b%_*},${b##*_},$2,$r" > rob_tmp/${b}_$2.csv
  echo "${b%_*} ${b##*_} $2 : $r"
}
export -f one
ls noisy/input_1000_*.txt | while read f; do for d in ada base; do echo "$f $d"; done; done \
  | xargs -P "$JOBS" -n 2 bash -c 'one "$0" "$1"'
OUT=robustness_A.csv
echo "kind,level,design,correct,avg_cycles,easy,med,hard" > $OUT
cat rob_tmp/*.csv | sort -t, -k1,1 -k2,2g -k3,3 >> $OUT
echo "-> $OUT"
