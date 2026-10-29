# AdaPath-NPU / earlyexit  -  ORFS ASAP7 설정 (자동 생성)
# 3종 아키텍처는 동일 SDC, 동일 utilization 으로 합성해 상대 비교한다.
export PLATFORM               = asap7

export DESIGN_NAME            = earlyexit_npu
export DESIGN_NICKNAME        = earlyexit

export VERILOG_FILES = $(sort $(wildcard $(DESIGN_HOME)/src/adapath/*.v)) \
                       $(sort $(wildcard $(DESIGN_HOME)/src/adapath/ref/*.v))
export VERILOG_INCLUDE_DIRS = $(DESIGN_HOME)/src/adapath
export SDC_FILE      = $(DESIGN_HOME)/$(PLATFORM)/earlyexit/constraint.sdc

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
