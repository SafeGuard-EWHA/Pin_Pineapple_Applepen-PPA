#!/usr/bin/env bash
# run_synth.sh - WSL(Ubuntu) 의 ORFS 에서 3종 아키텍처 합성 + pre-layout STA/power
#   bash run_synth.sh [ORFS_DIR]          (기본 ~/OpenROAD-flow-scripts)
#   VARIANTS="adapath" bash run_synth.sh  (일부만)
set -e
ORFS=${1:-$HOME/OpenROAD-flow-scripts}
HERE="$(cd "$(dirname "$0")" && pwd)"
VARIANTS=${VARIANTS:-"baseline earlyexit adapath"}
export PATH="$ORFS/tools/install/OpenROAD/bin:$ORFS/tools/install/yosys/bin:$PATH"

# 1) 설계 파일 설치
mkdir -p "$ORFS/flow/designs/src/adapath/ref"
cp "$HERE"/src/adapath/*.v "$HERE"/src/adapath/*.vh "$ORFS/flow/designs/src/adapath/"
cp "$HERE"/src/adapath/ref/*.v "$ORFS/flow/designs/src/adapath/ref/"
for v in $VARIANTS; do
  mkdir -p "$ORFS/flow/designs/asap7/$v"
  cp "$HERE/asap7/$v/config.mk" "$HERE/asap7/$v/constraint.sdc" "$ORFS/flow/designs/asap7/$v/"
done
mkdir -p "$HERE/reports"

# 2) 합성 + STA
cd "$ORFS/flow"
for v in $VARIANTS; do
  echo "================ synth: $v ================"
  make DESIGN_CONFIG=./designs/asap7/$v/config.mk clean_synth synth 2>&1 | tail -5
  cp reports/asap7/$v/base/synth_stat.txt "$HERE/reports/${v}_synth_stat.txt"
  cp results/asap7/$v/base/1_synth.v      "$HERE/reports/${v}_1_synth.v" 2>/dev/null || true
  echo "---------------- STA/power: $v ----------------"
  PLATFORM_DIR="$ORFS/flow/platforms/asap7" \
  NETLIST="$ORFS/flow/results/asap7/$v/base/1_synth.v" \
  SDC="$ORFS/flow/designs/asap7/$v/constraint.sdc" \
  TOP="${v}_npu" REPORT="$HERE/reports/${v}_sta.txt" \
    openroad -exit "$HERE/sta_prelayout.tcl" 2>&1 | tail -3
done
echo "reports -> $HERE/reports/   (python parse_ppa.py 로 표 생성)"
