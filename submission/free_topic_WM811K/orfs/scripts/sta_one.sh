#!/bin/bash
# 사용: sta_one.sh <design> <outdir>
v=$1; OUT=$2; ORFS=$HOME/OpenROAD-flow-scripts
export PATH="$ORFS/tools/install/OpenROAD/bin:$PATH"
SP=/mnt/c/Users/yhe44/AppData/Local/Temp/claude/C--Users-yhe44-OneDrive----IDEC-----------/6d138761-2b93-4e6f-9ffd-1767ee64f5a6/scratchpad
cd $ORFS/flow; mkdir -p $OUT
sed 's/set clk_period 1000/set clk_period 2500/' designs/asap7/$v/constraint.sdc > $OUT/${v}_2500.sdc
for P in 1000 2500; do
  SDC=designs/asap7/$v/constraint.sdc; suf=""; [ $P = 2500 ] && { SDC=$OUT/${v}_2500.sdc; suf=25; }
  PLATFORM_DIR=$ORFS/flow/platforms/asap7 ODB=results/asap7/$v/base/1_synth.odb SDC=$SDC REPORT=$OUT/${v}_sta$suf.txt \
    openroad -exit $SP/sta_odb.tcl 2>&1 | grep -v -E "STA-1212|ODB-0" > $OUT/${v}_sta$suf.log
done
echo "$v: $(cat $OUT/${v}_sta.txt)"; grep -m2 -E "Startpoint|Endpoint" $OUT/${v}_sta.log; grep -m1 "data arrival" $OUT/${v}_sta.log; grep -E "^Total" $OUT/${v}_sta25.log
