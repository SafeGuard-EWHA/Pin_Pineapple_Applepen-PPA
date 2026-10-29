#!/bin/bash
SP=/mnt/c/Users/yhe44/AppData/Local/Temp/claude/C--Users-yhe44-OneDrive----IDEC-----------/6d138761-2b93-4e6f-9ffd-1767ee64f5a6/scratchpad
GL=/mnt/c/Users/yhe44/idec_glsim
ORFS=$HOME/OpenROAD-flow-scripts; F=$HOME/adapath_pkg/reports_final
export PATH="$ORFS/tools/install/OpenROAD/bin:$PATH"
while pgrep -f queue_final.sh > /dev/null; do sleep 30; done
vp() {
  PLATFORM_DIR=$ORFS/flow/platforms/asap7 ODB=$ORFS/flow/results/asap7/$1/base/1_synth.odb \
  SDC=$SP/stage/constraint_10ns.sdc VCD=$GL/$2 SCOPE=$3 \
    openroad -exit $SP/vcd_power_odb.tcl 2>&1 | grep -v -E "STA-1212|ODB-0" > $F/power_$4.log
  echo "power $4: $(grep -E '^Total' $F/power_$4.log)  $(date +%T)"
}
vp adapath_A gl_adA_easy.vcd tb_gatelevel/dut A_easy
vp adapath_A gl_adA_hard.vcd tb_gatelevel/dut A_hard
vp baseline_A gl_baA.vcd tb_gatelevel/dut Abase
rm -rf /mnt/c/Users/yhe44/idec_glsim/reports_final; cp -r $F /mnt/c/Users/yhe44/idec_glsim/reports_final
echo "POWER_A_DONE $(date +%T)"
