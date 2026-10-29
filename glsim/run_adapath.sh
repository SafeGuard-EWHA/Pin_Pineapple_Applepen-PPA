#!/bin/bash
cd /c/Users/yhe44/idec_glsim
export PATH="/c/iverilog/bin:$PATH"
echo "compile $(date +%T)"
iverilog -g2012 -I. -o gl_adapath_v2.vvp adapath_v2_net.v std_cell_fn/*.v tb_gl_adapath.v 2>&1 | grep -v -i "warning" | head -5
echo "compiled $(date +%T)"
for m in "easy 1" "med 15" "hard 5"; do set -- $m
  vvp gl_adapath_v2.vvp +START=$2 +VCD=gl_ad_$1.vcd 2>&1 | grep -E "img|gate-level"
  echo "  done $1 $(date +%T)"
done
