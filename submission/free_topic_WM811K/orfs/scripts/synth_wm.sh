#!/bin/bash
# Baseline_WM과 AdaPath_WM을 ORFS로 합성한다(make synth). 기존 결과를 지우지 않는다.
# 처음부터 다시 합성하려면 먼저 수동으로: make DESIGN_CONFIG=./designs/asap7/<design>/config.mk clean_synth
# 결과: $ORFS/flow/results/asap7/<design>/base/{1_2_yosys.v,1_synth.odb}, 합성 통계는 OUT(기본 ./out)/<design>_synth_stat.txt
set -u
PKG=$(cd "$(dirname "$0")/../.." && pwd)
source "$PKG/orfs/scripts/env.sh"
OUT=$(mkdir -p "${OUT:-$PWD/out}" && cd "${OUT:-$PWD/out}" && pwd)
cd "$ORFS/flow"
for v in baseline_wm adapath_wm; do
  echo "== synth $v $(date +%T)"
  make DESIGN_CONFIG=./designs/asap7/$v/config.mk synth > "$OUT/${v}_synth.log" 2>&1
  echo "   exit $?"
  cp "reports/asap7/$v/base/synth_stat.txt" "$OUT/${v}_synth_stat.txt"
  grep -E "Chip area|sequential" "$OUT/${v}_synth_stat.txt"
done
