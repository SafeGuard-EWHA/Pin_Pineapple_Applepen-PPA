#!/bin/bash
cd /c/Users/yhe44/idec_glsim
export PATH="/c/iverilog/bin:$PATH"
iverilog -g2012 -I. -o gl_adA.vvp adapath_A_net.v std_cell_fn/*.v tb_gl_A.v 2>&1 | grep -v -i warning | head -3
iverilog -g2012 -I. -DTOP_BASELINE -o gl_baA.vvp baseline_A_net.v std_cell_fn/*.v tb_gl_A.v 2>&1 | grep -v -i warning | head -3
echo "compiled $(date +%T)"
vvp gl_adA.vvp +START=1 +VCD=gl_adA_easy.vcd | grep -E "img|gate"
vvp gl_adA.vvp +START=5 +VCD=gl_adA_hard.vcd | grep -E "img|gate"
vvp gl_baA.vvp +START=1 +VCD=gl_baA.vcd | grep -E "img|gate"
echo "A_GL_DONE $(date +%T)"
