#!/bin/bash
set -u
SP=/mnt/c/Users/yhe44/AppData/Local/Temp/claude/C--Users-yhe44-OneDrive----IDEC-----------/6d138761-2b93-4e6f-9ffd-1767ee64f5a6/scratchpad
GL=/mnt/c/Users/yhe44/idec_glsim
ORFS=$HOME/OpenROAD-flow-scripts; PKG=$HOME/adapath_pkg; F=$PKG/reports_final
export PATH="$ORFS/tools/install/OpenROAD/bin:$ORFS/tools/install/yosys/bin:$PATH"
mkdir -p $F
echo "wait for synth_v3 $(date +%T)"
while pgrep -f synth_v3.sh > /dev/null; do sleep 30; done
echo "start $(date +%T)"
# 1) 아키텍처 A 합성
rm -rf $ORFS/flow/designs/src/adapath_A; cp -r $SP/stage/src/adapath_A $ORFS/flow/designs/src/adapath_A
cd $ORFS/flow
for v in baseline_A adapath_A; do
  mkdir -p designs/asap7/$v; cp $SP/stage/cfg/$v/* designs/asap7/$v/
  echo "======== synth $v  $(date +%T)"
  make DESIGN_CONFIG=./designs/asap7/$v/config.mk clean_synth synth > $F/${v}_synth.log 2>&1
  echo "   exit $?  $(date +%T)"
  cp reports/asap7/$v/base/synth_stat.txt $F/${v}_synth_stat.txt
  cp results/asap7/$v/base/1_2_yosys.v $GL/${v}_net.v
done
echo "A_NETLISTS_READY $(date +%T)"
# 2) STA (ODB) 전 설계
for v in refchip baseline_A adapath_A baseline earlyexit adapath baseline_wm adapath_wm; do
  bash $SP/sta_one.sh $v $F 2>&1 | head -6
  grep -h "Chip area" $F/${v}_synth_stat.txt $PKG/reports_v2/${v}_synth_stat.txt $PKG/reports_v3/${v}_synth_stat.txt 2>/dev/null | head -1
done
echo "STA_DONE $(date +%T)"
# 3) VCD 전력 (B, 레퍼런스)
vp() { # design vcd scope tag
  PLATFORM_DIR=$ORFS/flow/platforms/asap7 ODB=$ORFS/flow/results/asap7/$1/base/1_synth.odb \
  SDC=$SP/stage/constraint_10ns.sdc VCD=$GL/$2 SCOPE=$3 \
    openroad -exit $SP/vcd_power_odb.tcl 2>&1 | grep -v -E "STA-1212|ODB-0" > $F/power_$4.log
  echo "power $4: $(grep -E '^Total' $F/power_$4.log)  end=$(tail -c 3000 $GL/$2 | grep '^#' | tail -1)  $(date +%T)"
}
for m in easy med hard; do vp adapath gl_ad_$m.vcd tb_gatelevel/dut B_$m; done
for m in a b c; do while [ ! -f $GL/gl_ref_$m.vcd ]; do sleep 30; done; vp refchip gl_ref_$m.vcd tb_gl_ref/dut ref_$m; done
echo "ALL DONE $(date +%T)"
