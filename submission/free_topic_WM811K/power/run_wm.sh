#!/usr/bin/env bash
# Replay the published windows. The original testbench and netlists are unchanged.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"
NET_DIR=${NET_DIR:-$HERE/run}
mkdir -p "$NET_DIR"
NET_DIR=$(cd "$NET_DIR" && pwd)
command -v iverilog >/dev/null
command -v vvp >/dev/null
for d in adapath_wm baseline_wm; do
  gzip -dc "$HERE/${d}_net.v.gz" > "$NET_DIR/${d}_net.v"
done
defs=("-DDATA=\"$HERE/weights/\"" "-DWM_INPUT=\"$HERE/data/wm_input_954.txt\"")
iverilog -g2012 "${defs[@]}" -o "$NET_DIR/gl_wm_ada.vvp" "$NET_DIR/adapath_wm_net.v" "$HERE"/std_cell_fn/*.v "$HERE/tb_gl_wm.v" > "$NET_DIR/compile_ada.log" 2>&1
iverilog -g2012 -DTOP_BASELINE "${defs[@]}" -o "$NET_DIR/gl_wm_base.vvp" "$NET_DIR/baseline_wm_net.v" "$HERE"/std_cell_fn/*.v "$HERE/tb_gl_wm.v" > "$NET_DIR/compile_base.log" 2>&1
run() {
  local exe=$1 tag=$2; shift 2
  vvp "$NET_DIR/$exe" "+I0=$1" "+I1=$2" "+I2=$3" "+I3=$4" "+VCD=$NET_DIR/$tag.vcd" > "$NET_DIR/$tag.log" 2>&1
  test "$(grep -c '^img ' "$NET_DIR/$tag.log")" = 4
  if grep -Eiq 'ERROR|FATAL|cycles=4000|decision=[xz]' "$NET_DIR/$tag.log"; then cat "$NET_DIR/$tag.log" >&2; return 1; fi
  grep -E '^img |gate-level WM done' "$NET_DIR/$tag.log"
}
# Serial execution avoids excessive RAM use; within-window ordering is unchanged.
run gl_wm_ada.vvp wm_ada_easy 8 10 18 22
run gl_wm_ada.vvp wm_ada_med 2 3 5 24
run gl_wm_ada.vvp wm_ada_hard 0 1 4 9
run gl_wm_base.vvp wm_base 0 1 2 3
echo ALL_SIM_DONE
