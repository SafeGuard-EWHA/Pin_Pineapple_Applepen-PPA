#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ORFS=${ORFS:-$HOME/OpenROAD-flow-scripts}
export PATH="$ORFS/tools/install/OpenROAD/bin:$PATH"
export PLATFORM_DIR=${PLATFORM_DIR:-$ORFS/flow/platforms/asap7}
VCD_DIR=${VCD_DIR:-$HERE/run}
OUT=${OUT:-$HERE/power_results}
mkdir -p "$OUT"
command -v openroad >/dev/null
for tag in wm_ada_easy wm_ada_med wm_ada_hard wm_base; do
  top=adapath_wm_npu; net=adapath_wm_net.v
  if [[ $tag == wm_base ]]; then top=baseline_wm_npu; net=baseline_wm_net.v; fi
  NET="$VCD_DIR/$net" TOP="$top" SDC="$HERE/constraint_10ns.sdc" VCD="$VCD_DIR/$tag.vcd" SCOPE=tb_gatelevel/dut \
    openroad -exit "$HERE/vcd_power_net.tcl" > "$OUT/power_$tag.rpt" 2>&1
  if grep -Eq 'Error|ERROR' "$OUT/power_$tag.rpt"; then cat "$OUT/power_$tag.rpt" >&2; exit 1; fi
  grep '^Total' "$OUT/power_$tag.rpt"
done
echo POWER_DONE
