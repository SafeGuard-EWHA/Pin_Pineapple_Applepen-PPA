#!/bin/bash
SP=/mnt/c/Users/yhe44/AppData/Local/Temp/claude/C--Users-yhe44-OneDrive----IDEC-----------/6d138761-2b93-4e6f-9ffd-1767ee64f5a6/scratchpad
GL=/mnt/c/Users/yhe44/idec_glsim
ORFS=$HOME/OpenROAD-flow-scripts; F=$HOME/adapath_pkg/reports_extra; mkdir -p $F
export PATH="$ORFS/tools/install/OpenROAD/bin:$PATH"
export PLATFORM_DIR=$ORFS/flow/platforms/asap7
# 1) 블록별 전력
bp() { # design vcd scope tag
  ODB=$ORFS/flow/results/asap7/$1/base/1_synth.odb SDC=$SP/stage/constraint_10ns.sdc VCD=$GL/$2 SCOPE=$3 OUTF=$F/block_$4.txt \
    openroad -exit $SP/blockpower.tcl 2>&1 | grep -v -E "STA-1212|ODB-0" > $F/block_$4.log
  echo "block $4: $(grep -c . $F/block_$4.txt) groups  end=$(tail -c 3000 $GL/$2 | grep '^#' | tail -1)  $(date +%T)"
}
bp refchip gl_ref_a.vcd tb_gl_ref/dut ref_a
bp baseline_A gl_baA.vcd tb_gatelevel/dut Abase
bp adapath_A gl_adA_easy.vcd tb_gatelevel/dut A_easy
bp adapath_A gl_adA_hard.vcd tb_gatelevel/dut A_hard
# 2) 주기 스윕
sw() { # design periods
  ODB=$ORFS/flow/results/asap7/$1/base/1_synth.odb OUTF=$F/sweep_$1.txt PERIODS="$2" \
    openroad -exit $SP/sta_sweep.tcl 2>&1 | grep -v -E "STA-1212|ODB-0" > $F/sweep_$1.log
  echo "sweep $1: $(wc -l < $F/sweep_$1.txt) points  $(date +%T)"
}
PA="1000 1200 1400 1500 1600 1700 1800 1900 2000 2100 2200 2400"
for d in refchip baseline_A adapath_A baseline_wm adapath_wm baseline adapath; do sw $d "$PA"; done
rm -rf $GL/reports_extra; cp -r $F $GL/reports_extra
echo "EXTRA_DONE $(date +%T)"
