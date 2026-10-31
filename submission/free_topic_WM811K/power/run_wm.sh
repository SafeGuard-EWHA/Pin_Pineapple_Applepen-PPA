#!/bin/bash
# WM-811K 게이트레벨 시뮬레이션 + VCD (Icarus Verilog). glsim/wm 폴더에서 실행.
# NET_DIR: 넷리스트(.v)가 있는 폴더 (없으면 이 폴더의 .v.gz를 풀어서 사용), VCD도 여기에 저장
cd "$(dirname "$0")"
NET_DIR=${NET_DIR:-.}
export PATH="/c/iverilog/bin:$PATH"
for d in adapath_wm baseline_wm; do
  [ -f $NET_DIR/${d}_net.v ] || gunzip -c ${d}_net.v.gz > $NET_DIR/${d}_net.v
done
echo "compile $(date +%T)"
iverilog -g2012 -o $NET_DIR/gl_wm_ada.vvp  $NET_DIR/adapath_wm_net.v  std_cell_fn/*.v tb_gl_wm.v 2>&1 | grep -iv warning | head -5
iverilog -g2012 -DTOP_BASELINE -o $NET_DIR/gl_wm_base.vvp $NET_DIR/baseline_wm_net.v std_cell_fn/*.v tb_gl_wm.v 2>&1 | grep -iv warning | head -5
echo "compiled $(date +%T)"
# 이미지 인덱스 (wm_expect.txt에서 정답이고 모드가 같은 앞쪽 4장): Easy 8,10,18,22 / Medium 2,3,5,24 / Hard 0,1,4,9
run() { vvp $NET_DIR/$1 +I0=$3 +I1=$4 +I2=$5 +I3=$6 +VCD=$NET_DIR/$2.vcd > $NET_DIR/$2.log 2>&1; echo "done $2 $(date +%T)"; }
run gl_wm_ada.vvp  wm_ada_easy 8 10 18 22 &
run gl_wm_ada.vvp  wm_ada_med  2 3 5 24 &
run gl_wm_ada.vvp  wm_ada_hard 0 1 4 9 &
run gl_wm_base.vvp wm_base     0 1 2 3 &
wait
grep -h "img\|done" $NET_DIR/wm_*.log
echo "ALL_SIM_DONE $(date +%T)"
