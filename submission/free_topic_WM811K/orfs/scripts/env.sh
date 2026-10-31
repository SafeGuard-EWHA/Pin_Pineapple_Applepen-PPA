# 사용: source orfs/scripts/env.sh
# ORFS 설치 경로를 ORFS 환경변수로 지정한다(기본값 $HOME/OpenROAD-flow-scripts).
export ORFS=${ORFS:-$HOME/OpenROAD-flow-scripts}
export PLATFORM_DIR=${PLATFORM_DIR:-$ORFS/flow/platforms/asap7}
export PATH="$ORFS/tools/install/OpenROAD/bin:$ORFS/tools/install/yosys/bin:$PATH"
[ -d "$PLATFORM_DIR/lib" ] || echo "경고: PLATFORM_DIR($PLATFORM_DIR)에 lib 폴더가 없습니다. ORFS 경로를 확인하세요." >&2
