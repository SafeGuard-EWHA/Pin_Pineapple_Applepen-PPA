#!/bin/bash
# WSL(Ubuntu)에서 실행: 4개 VCD의 평균 전력을 OpenROAD로 계산한다.
# 사용: VCD_DIR=/mnt/c/.../idec_glsim/wm bash power_wm.sh
ORFS=${ORFS:-$HOME/OpenROAD-flow-scripts}
export PATH="$ORFS/tools/install/OpenROAD/bin:$PATH"
export PLATFORM_DIR=$ORFS/flow/platforms/asap7
HERE=$(cd "$(dirname "$0")" && pwd)
VCD_DIR=${VCD_DIR:-$HERE}
SDC=$HERE/../../flow_scripts/constraint_10ns.sdc
OUT=$HERE/power_results; mkdir -p $OUT
pw() { # tag top netlist
  NET=$VCD_DIR/$3 TOP=$2 SDC=$SDC VCD=$VCD_DIR/$1.vcd SCOPE=tb_gatelevel/dut \
    openroad -exit $HERE/vcd_power_net.tcl 2>&1 | grep -v -E "STA-1212|ODB-0" > $OUT/power_$1.rpt
  echo "$1: $(grep -E '^Total' $OUT/power_$1.rpt)  end=$(tail -c 3000 $VCD_DIR/$1.vcd | grep '^#' | tail -1)"
}
pw wm_ada_easy adapath_wm_npu adapath_wm_net.v &
pw wm_ada_med  adapath_wm_npu adapath_wm_net.v &
pw wm_ada_hard adapath_wm_npu adapath_wm_net.v &
pw wm_base     baseline_wm_npu baseline_wm_net.v &
wait
echo POWER_DONE
