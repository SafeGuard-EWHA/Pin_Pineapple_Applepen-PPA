"""ORFS(OpenROAD-flow-scripts) 합성 패키지 생성.

../orfs/ 아래에
    src/adapath/*.v               RTL 일체 (+ thresholds.vh, shifts.vh)
    src/adapath/<variant>_npu.v   VARIANT 고정 wrapper 3종
    asap7/<variant>/config.mk     ORFS 설계 설정 (동일 SDC / 동일 utilization)
    asap7/<variant>/constraint.sdc
    sta_prelayout.tcl             합성 넷리스트에 대한 pre-layout STA + power (OpenROAD)
    run_synth.sh                  WSL 에서: 설치 -> 3종 synth -> STA -> 리포트 수집
를 만든다.

    python gen_orfs.py --prefix mnist
"""
import argparse
import os
import shutil

VARIANTS = [("baseline", 0), ("earlyexit", 1), ("adapath", 2)]
RTL_FILES = ["mac_tree.v", "conv1_engine.v", "conv2_engine.v", "maxpool_relu_n.v",
             "fmap_buffer.v", "early_classifier.v", "fc_engine.v", "top2_finder.v",
             "score_margin_calc.v", "difficulty_decoder.v", "mode_control_fsm.v",
             "adapath_top.v", "ref/conv1_buf.v", "ref/conv2_buf.v"]

WRAPPER = """//  {name}_npu.v  -  adapath_top VARIANT={var} 고정 wrapper (ORFS 합성용, 자동 생성)
module {name}_npu #(
    parameter C1 = 3, parameter C2 = 8, parameter C2_MED = 4, parameter N_CLASS = 10
) (
    input                         clk,
    input                         rst_n,
    input                         start,
    input  [7:0]                  pixel_in,
    input  [C1*25*8-1:0]          w_conv1,
    input  [C1*16-1:0]            b_conv1,
    input  [C2*C1*25*8-1:0]       w_conv2,
    input  [C2*16-1:0]            b_conv2,
    input  [N_CLASS*C1*16*8-1:0]  w_fce,
    input  [N_CLASS*16-1:0]       b_fce,
    input  [N_CLASS*C2_MED*16*8-1:0] w_fcl,
    input  [N_CLASS*16-1:0]       b_fcl,
    input  [N_CLASS*C2*16*8-1:0]  w_fcf,
    input  [N_CLASS*16-1:0]       b_fcf,
    output [$clog2(N_CLASS)-1:0]  decision,
    output                        valid_out,
    output [1:0]                  mode_out,
    output [11:0]                 margin_out
);
    `include "shifts.vh"
    adapath_top #(.VARIANT({var}), .C1(C1), .C2(C2), .C2_MED(C2_MED), .N_CLASS(N_CLASS),
                  .SH_CONV1(SHIFT_CONV1), .SH_CONV2(SHIFT_CONV2),
                  .SH_FCE(SHIFT_FC_EARLY), .SH_FCL(SHIFT_FC_LIGHT), .SH_FCF(SHIFT_FC_FULL)) u (
        .clk(clk), .rst_n(rst_n), .start(start), .pixel_in(pixel_in),
        .w_conv1(w_conv1), .b_conv1(b_conv1), .w_conv2(w_conv2), .b_conv2(b_conv2),
        .w_fce(w_fce), .b_fce(b_fce), .w_fcl(w_fcl), .b_fcl(b_fcl), .w_fcf(w_fcf), .b_fcf(b_fcf),
        .decision(decision), .valid_out(valid_out), .mode_out(mode_out), .margin_out(margin_out));
endmodule
"""

CONFIG = """# AdaPath-NPU / {name}  -  ORFS ASAP7 설정 (자동 생성)
# 3종 아키텍처는 동일 SDC, 동일 utilization 으로 합성해 상대 비교한다.
export PLATFORM               = asap7

export DESIGN_NAME            = {name}_npu
export DESIGN_NICKNAME        = {name}

export VERILOG_FILES = $(sort $(wildcard $(DESIGN_HOME)/src/adapath/*.v)) \\
                       $(sort $(wildcard $(DESIGN_HOME)/src/adapath/ref/*.v))
export VERILOG_INCLUDE_DIRS = $(DESIGN_HOME)/src/adapath
export SDC_FILE      = $(DESIGN_HOME)/$(PLATFORM)/{name}/constraint.sdc

export ABC_AREA               = 1
export SYNTH_HIERARCHICAL     = 0

# Feature Map Buffer(144 x 36 bit = 5,184 bit) 등 소형 온칩 버퍼를 SRAM 매크로 대신
# 플립플롭으로 합성한다. ORFS 기본 상한(4,096 bit)을 넘으므로 명시적으로 올린다.
# 3종 모두 동일 값이라 상대 비교에는 영향이 없다.
export SYNTH_MEMORY_MAX_BITS  = 65536

# extract_fa(가산기 추출)는 MAC 675개 설계에서 시간이 지나치게 오래 걸려 생략한다.
# ABC 가 표준 매핑으로 처리하며, 3종 동일 조건이므로 상대 비교는 유효하다.
export ADDER_MAP_FILE         =

export CORE_UTILIZATION       = 40
export CORE_ASPECT_RATIO      = 1
export CORE_MARGIN            = 2
export PLACE_DENSITY          = 0.65
export TNS_END_PERCENT        = 100
"""

SDC = """# AdaPath-NPU 공통 타이밍 제약 (3종 동일)
set clk_name  clk
set clk_port_name clk
set clk_period {period}
set clk_io_pct 0.2

set clk_port [get_ports $clk_port_name]
create_clock -name $clk_name -period $clk_period $clk_port

set non_clock_inputs [lsearch -inline -all -not -exact [all_inputs] $clk_port]
set_input_delay  [expr $clk_period * $clk_io_pct] -clock $clk_name $non_clock_inputs
set_output_delay [expr $clk_period * $clk_io_pct] -clock $clk_name [all_outputs]
"""

STA_TCL = """# sta_prelayout.tcl - 합성 넷리스트(1_synth.v)에 대한 pre-layout STA + 전력 추정
# 사용:  openroad -exit sta_prelayout.tcl   (환경변수 PLATFORM_DIR NETLIST SDC TOP REPORT)
set platform_dir $::env(PLATFORM_DIR)
set netlist      $::env(NETLIST)
set sdc          $::env(SDC)
set top          $::env(TOP)
set report       $::env(REPORT)

# OpenROAD 는 read_verilog 전에 기술(LEF)이 필요하다
foreach lef [glob -nocomplain $platform_dir/lef/*tech*.lef] { read_lef $lef }
foreach lef [glob -nocomplain $platform_dir/lef/asap7sc7p5t*.lef] { read_lef $lef }
foreach lib [glob -nocomplain $platform_dir/lib/NLDM/*RVT_TT*.lib.gz $platform_dir/lib/NLDM/*RVT_TT*.lib] {
    read_liberty $lib
}
read_verilog $netlist
link_design $top
read_sdc $sdc

# 전력 활동률 가정 (벡터 없는 상대 비교용):
#   가중치/bias 포트 = 0 (추론 중 고정)  /  픽셀 입력 = 0.25  /  제어 = 0.05
set_power_activity -input -activity 0.0
catch { set_power_activity -input_ports [get_ports pixel_in*] -activity 0.25 }
catch { set_power_activity -input_ports [get_ports scores_flat*] -activity 0.25 }
catch { set_power_activity -input_ports [get_ports {start front_done back_done valid_in}] -activity 0.05 }

set fp [open $report w]
puts $fp "=== $top ==="
puts $fp "--- report_checks (setup, worst) ---"
puts $fp [report_checks -path_delay max -format full_clock_expanded -digits 1 -group_count 1]
puts $fp "--- WNS / TNS ---"
puts $fp "wns [sta::worst_slack -max]   tns [sta::total_negative_slack -max]"
puts $fp "--- report_power ---"
puts $fp [report_power -digits 6]
close $fp
puts "written $report"
"""

RUN = """#!/usr/bin/env bash
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
  PLATFORM_DIR="$ORFS/flow/platforms/asap7" \\
  NETLIST="$ORFS/flow/results/asap7/$v/base/1_synth.v" \\
  SDC="$ORFS/flow/designs/asap7/$v/constraint.sdc" \\
  TOP="${v}_npu" REPORT="$HERE/reports/${v}_sta.txt" \\
    openroad -exit "$HERE/sta_prelayout.tcl" 2>&1 | tail -3
done
echo "reports -> $HERE/reports/   (python parse_ppa.py 로 표 생성)"
"""


def main(a):
    base = os.path.dirname(os.path.abspath(__file__))
    work = os.path.dirname(base)
    rtl = os.path.join(work, "rtl")
    rd = os.path.join(work, "out", "rtl_data_" + a.prefix)
    out = os.path.join(work, "orfs")
    src = os.path.join(out, "src", "adapath")
    os.makedirs(os.path.join(src, "ref"), exist_ok=True)

    for f in RTL_FILES:
        shutil.copy(os.path.join(rtl, f), os.path.join(src, f))
    for f in ("thresholds.vh", "shifts.vh"):
        shutil.copy(os.path.join(rd, f), os.path.join(src, f))

    for name, var in VARIANTS:
        open(os.path.join(src, name + "_npu.v"), "w", encoding="utf-8").write(
            WRAPPER.format(name=name, var=var))
        d = os.path.join(out, "asap7", name)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "config.mk"), "w", encoding="utf-8").write(CONFIG.format(name=name))
        open(os.path.join(d, "constraint.sdc"), "w", encoding="utf-8").write(SDC.format(period=a.period))

    open(os.path.join(out, "sta_prelayout.tcl"), "w", encoding="utf-8", newline="\n").write(STA_TCL)
    open(os.path.join(out, "run_synth.sh"), "w", encoding="utf-8", newline="\n").write(RUN)
    print("ORFS package -> " + out)
    print("  clk_period = %s ps (ASAP7 단위),  thresholds/shifts from " % a.period + rd)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--prefix", default="mnist")
    p.add_argument("--period", default="1000", help="clk period [ps] (ASAP7). 1000ps = 1GHz")
    main(p.parse_args())
