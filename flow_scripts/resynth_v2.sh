#!/bin/bash
# Top-2 Finder 토너먼트 트리 적용 후 재합성 + STA (v2)
set -u
SP=/mnt/c/Users/yhe44/AppData/Local/Temp/claude/C--Users-yhe44-OneDrive----IDEC-----------/6d138761-2b93-4e6f-9ffd-1767ee64f5a6/scratchpad
ORFS=$HOME/OpenROAD-flow-scripts
PKG=$HOME/adapath_pkg
export PATH="$ORFS/tools/install/OpenROAD/bin:$ORFS/tools/install/yosys/bin:$PATH"
V2=$PKG/reports_v2; mkdir -p $V2 $HOME/netlist_v1
[ -d $PKG/reports_v1 ] || cp -r $PKG/reports $PKG/reports_v1
for v in region2 adapath earlyexit baseline; do
  f=$ORFS/flow/results/asap7/$v/base/1_2_yosys.v
  [ -f $HOME/netlist_v1/$v.v ] || { [ -f $f ] && cp $f $HOME/netlist_v1/$v.v; }
done
cp $SP/top2_finder.v $PKG/src/adapath/top2_finder.v
cp $SP/top2_finder.v $ORFS/flow/designs/src/adapath/top2_finder.v
cd $ORFS/flow
for v in ${VARIANTS:-region2 adapath earlyexit baseline}; do
  top=$(grep DESIGN_NAME designs/asap7/$v/config.mk | awk '{print $NF}')
  echo "======== synth $v ($top)  $(date +%T)"
  make DESIGN_CONFIG=./designs/asap7/$v/config.mk clean_synth synth > $V2/${v}_synth.log 2>&1
  echo "   exit $?  $(date +%T)"
  cp reports/asap7/$v/base/synth_stat.txt $V2/${v}_synth_stat.txt
  sed 's/set clk_period 1000/set clk_period 2500/' designs/asap7/$v/constraint.sdc > $V2/${v}_2500.sdc
  for P in 1000 2500; do
    SDC=designs/asap7/$v/constraint.sdc; [ $P = 2500 ] && SDC=$V2/${v}_2500.sdc
    suf=""; [ $P = 2500 ] && suf=25
    PLATFORM_DIR=$ORFS/flow/platforms/asap7 NETLIST=$ORFS/flow/results/asap7/$v/base/1_2_yosys.v \
    SDC=$SDC TOP=$top REPORT=$V2/${v}_sta$suf.txt \
      openroad -exit $PKG/sta_prelayout.tcl > $V2/${v}_sta$suf.log 2>&1
  done
  grep -h wns $V2/${v}_sta.txt
done
echo "ALL DONE $(date +%T)"
