#!/bin/bash
# 이 패키지의 RTL과 ORFS 설정을 ORFS flow 폴더에 배치한다. 기존 폴더는 지우지 않는다.
#   rtl/                    -> $ORFS/flow/designs/src/adapath_wm/
#   orfs/adapath_wm/*       -> $ORFS/flow/designs/asap7/adapath_wm/
#   orfs/baseline_wm/*      -> $ORFS/flow/designs/asap7/baseline_wm/
# 대상 폴더가 이미 있으면 중단한다. OVERWRITE=1이면 기존 폴더를 <이름>.bak_<시각>으로 옮긴 뒤 배치한다.
set -eu
PKG=$(cd "$(dirname "$0")/../.." && pwd)
source "$PKG/orfs/scripts/env.sh"
F=$ORFS/flow
place() { # src dst
  if [ -e "$2" ]; then
    if [ "${OVERWRITE:-0}" = 1 ]; then mv "$2" "$2.bak_$(date +%Y%m%d%H%M%S)"; else
      echo "중단: $2 가 이미 있습니다. 덮어쓰려면 OVERWRITE=1 로 다시 실행하세요." >&2; exit 1; fi
  fi
  mkdir -p "$2"; cp -r "$1"/. "$2"/
}
place "$PKG/rtl" "$F/designs/src/adapath_wm"
place "$PKG/orfs/adapath_wm" "$F/designs/asap7/adapath_wm"
place "$PKG/orfs/baseline_wm" "$F/designs/asap7/baseline_wm"
echo "배치 완료: $F/designs/src/adapath_wm, $F/designs/asap7/{adapath_wm,baseline_wm}"
