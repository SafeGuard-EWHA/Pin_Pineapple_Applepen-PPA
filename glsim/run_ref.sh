#!/bin/bash
cd /c/Users/yhe44/idec_glsim
export PATH="/c/iverilog/bin:$PATH"
echo "compile $(date +%T)"
iverilog -g2012 -DN_IMG=4 -o gl_ref.vvp ref_net.v std_cell_fn/*.v tb_gl_ref.v 2>&1 | grep -v -i warning | head -5
echo "compiled $(date +%T)"
for m in "a 1" "b 15" "c 5"; do set -- $m
  vvp gl_ref.vvp +START=$2 +VCD=gl_ref_$1.vcd 2>&1 | grep -E "img|gate-level"
  echo "  done $1 $(date +%T)"
done
