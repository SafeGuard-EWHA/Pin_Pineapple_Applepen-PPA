#!/bin/bash
# 합성 결과(1_synth.odb)에 대해 (1) 1,000 ps / 2,500 ps 단일 STA와 (2) 클럭 주기 스윕 STA를 수행한다.
# 결과: OUT(기본 ./out)/<design>_sta.txt, <design>_sta25.txt, sweep_<design>.txt (각 .log 포함)
set -u
PKG=$(cd "$(dirname "$0")/../.." && pwd)
S=$PKG/orfs/scripts
source "$S/env.sh"
OUT=$(mkdir -p "${OUT:-$PWD/out}" && cd "${OUT:-$PWD/out}" && pwd)
PERIODS=${PERIODS:-"1000 1200 1400 1500 1600 1700 1800 1900 2000 2100 2200 2400"}
cd "$ORFS/flow"
for v in baseline_wm adapath_wm; do
  ODB=results/asap7/$v/base/1_synth.odb
  [ -f "$ODB" ] || { echo "없음: $ODB (synth_wm.sh를 먼저 실행)" >&2; continue; }
  sed 's/set clk_period 1000/set clk_period 2500/' designs/asap7/$v/constraint.sdc > "$OUT/${v}_2500.sdc"
  for P in 1000 2500; do
    SDC=designs/asap7/$v/constraint.sdc; suf=""; [ $P = 2500 ] && { SDC=$OUT/${v}_2500.sdc; suf=25; }
    ODB=$ODB SDC=$SDC REPORT=$OUT/${v}_sta$suf.txt openroad -exit "$S/sta_odb.tcl" 2>&1 | grep -v -E "STA-1212|ODB-0" > "$OUT/${v}_sta$suf.log"
  done
  ODB=$ODB OUTF=$OUT/sweep_$v.txt PERIODS="$PERIODS" openroad -exit "$S/sta_sweep.tcl" 2>&1 | grep -v -E "STA-1212|ODB-0" > "$OUT/sweep_$v.log"
  echo "$v: $(cat "$OUT/${v}_sta.txt"), sweep $(wc -l < "$OUT/sweep_$v.txt") points"
done
