#!/bin/bash
# 레퍼런스 chip / WM-811K Baseline / WM-811K AdaPath 합성 + STA
set -u
SP=/mnt/c/Users/yhe44/AppData/Local/Temp/claude/C--Users-yhe44-OneDrive----IDEC-----------/6d138761-2b93-4e6f-9ffd-1767ee64f5a6/scratchpad
ORFS=$HOME/OpenROAD-flow-scripts; PKG=$HOME/adapath_pkg; V3=$PKG/reports_v3
export PATH="$ORFS/tools/install/OpenROAD/bin:$ORFS/tools/install/yosys/bin:$PATH"
mkdir -p $V3
echo "---- v2 (Top-2 tree) results ----"
for v in region2 adapath earlyexit baseline; do
  echo "$v: $(grep -h wns $PKG/reports_v2/${v}_sta.txt 2>/dev/null)  area: $(grep -h 'Chip area' $PKG/reports_v2/${v}_synth_stat.txt 2>/dev/null)"
  grep -m2 -hE "Startpoint|Endpoint" $PKG/reports_v2/${v}_sta.log 2>/dev/null
done
cp $SP/stage/sta_prelayout.tcl $PKG/sta_prelayout.tcl
for d in refchip adapath_wm; do rm -rf $ORFS/flow/designs/src/$d; cp -r $SP/stage/src/$d $ORFS/flow/designs/src/$d; done
for v in refchip baseline_wm adapath_wm; do mkdir -p $ORFS/flow/designs/asap7/$v; cp $SP/stage/cfg/$v/* $ORFS/flow/designs/asap7/$v/; done
cd $ORFS/flow
for v in ${VARIANTS:-refchip adapath_wm baseline_wm}; do
  top=$(grep DESIGN_NAME designs/asap7/$v/config.mk | awk '{print $NF}')
  echo "======== synth $v ($top)  $(date +%T)"
  make DESIGN_CONFIG=./designs/asap7/$v/config.mk clean_synth synth > $V3/${v}_synth.log 2>&1
  echo "   exit $?  $(date +%T)"
  cp reports/asap7/$v/base/synth_stat.txt $V3/${v}_synth_stat.txt 2>/dev/null
  sed 's/set clk_period 1000/set clk_period 2500/' designs/asap7/$v/constraint.sdc > $V3/${v}_2500.sdc
  for P in 1000 2500; do
    SDC=designs/asap7/$v/constraint.sdc; suf=""; [ $P = 2500 ] && { SDC=$V3/${v}_2500.sdc; suf=25; }
    PLATFORM_DIR=$ORFS/flow/platforms/asap7 NETLIST=$ORFS/flow/results/asap7/$v/base/1_2_yosys.v \
    SDC=$SDC TOP=$top REPORT=$V3/${v}_sta$suf.txt openroad -exit $PKG/sta_prelayout.tcl > $V3/${v}_sta$suf.log 2>&1
  done
  echo "$v: $(grep -h wns $V3/${v}_sta.txt)  area: $(grep -h 'Chip area' $V3/${v}_synth_stat.txt)"
done
echo "ALL DONE $(date +%T)"
