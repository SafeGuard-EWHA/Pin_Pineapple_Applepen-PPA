#!/bin/bash
# Reference(refchip) 와 AdaPath_A 를 같은 2 ns 클럭 제약으로 ORFS 전체 흐름(배치, CTS, 배선, finish) 실행.
exec > /mnt/c/Users/yhe44/idec_glsim/postlayout_main.log 2>&1
ORFS=$HOME/OpenROAD-flow-scripts
export PATH="$ORFS/tools/install/OpenROAD/bin:$ORFS/tools/install/yosys/bin:$PATH"
OUT=/mnt/c/Users/yhe44/idec_glsim/postlayout; rm -rf $OUT; mkdir -p $OUT
pkill -f "make DESIGN_CONFIG=./designs/asap7/(refchip|adapath_A)" ; pkill -f "openroad -exit -no_init" ; sleep 2
cd $ORFS/flow
for d in refchip adapath_A; do
  n=${d}_pl; mkdir -p designs/asap7/$n
  sed -e "s/DESIGN_NICKNAME *= *$d/DESIGN_NICKNAME        = $n/" -e "s#/$d/constraint.sdc#/$n/constraint.sdc#" designs/asap7/$d/config.mk > designs/asap7/$n/config.mk
  sed -e 's/^set clk_period 1000/set clk_period 2000/' designs/asap7/$d/constraint.sdc > designs/asap7/$n/constraint.sdc
  grep -H "NICKNAME\|SDC_FILE" designs/asap7/$n/config.mk; grep -H clk_period designs/asap7/$n/constraint.sdc | head -1
done
run() {
  n=$1_pl
  echo "START $n $(date +%T)"
  make DESIGN_CONFIG=./designs/asap7/$n/config.mk > $OUT/flow_$n.log 2>&1
  rc=$?
  mkdir -p $OUT/$n
  cp -r reports/asap7/$n/base/. $OUT/$n/ 2>/dev/null
  cp logs/asap7/$n/base/*.json $OUT/$n/ 2>/dev/null
  cp results/asap7/$n/base/6_final.odb results/asap7/$n/base/6_final.v results/asap7/$n/base/6_final.sdc $OUT/$n/ 2>/dev/null
  echo "END $n rc=$rc $(date +%T)"
}
run refchip &
run adapath_A &
wait
echo "ALL_DONE $(date +%T)"
