# 전력 결과 재현

도구 설치 및 버전은 TOOL_SETUP.md와 environment.json을 따른다. 최종 분석은 Ubuntu-24.04에서 실행하였다. 아래 변수는 본인 경로로 지정한다. 기존 실험 디렉터리를 덮어쓰지 않는다. 원본 입력은 Git에 포함하지 않으며 input_audit.json의 SHA-256과 같은 파일을 준비한다.

## 전체 합성부터

`prepare_power.py --orfs ORFS경로 --stage 새작업경로`로 원본 RTL을 별도 복사하고 A 가중치·TB·설정 파일을 준비한다. `ref_data/input_1000.txt`에 입력을 배치한다. `prepare_cell_models.py ORFS경로/flow/platforms/asap7/verilog/stdcell 새작업경로/std_cell_fn`으로 기능용 셀 모델을 생성한다. `prepare_selected_tb.py 새작업경로`로 명시적 입력 인덱스를 지원하는 TB를 생성한다.

`run_rtl_full.py --help`, `run_synthesis.py --help`의 인자를 확인하여 동일 ORFS·작업 경로를 전달한다. 실제 합성 명령과 실행 시간은 power_results/synthesis/runs.json에 보존되어 있다. ORFS의 flow/platforms/common도 있어야 하며 이번 실행은 WSL RAM 10 GB와 swap 8 GB를 사용하였다. 새 구성에서는 기존 cg_a_ungated/cg_a_gated 소스 디렉터리와 충돌하지 않아야 한다.

각 합성 ODB에 다음과 같은 환경 변수를 지정하여 `openroad -exit buffer_clocks.tcl`을 실행한다. VARIANT는 ungated/gated 각각 지정한다.

```bash
export PLATFORM_DIR="$ORFS/flow/platforms/asap7"
export VARIANT=ungated
export ODB="$ORFS/flow/results/asap7/cg_a_${VARIANT}/base/1_synth.odb"
export OUT_ODB="$NETLIST_DIR/${VARIANT}.odb"
export OUT_VERILOG="$NETLIST_DIR/${VARIANT}.v"
openroad -exit "$EXPERIMENT/buffer_clocks.tcl"
```

gated 변형에도 동일하게 반복한다. 이 스크립트는 실제 CTS가 아닌 논리적 부하 모델을 생성한다. 최종 구조에서는 ICG 입력을 root clock에 직접 연결한다. 직렬 트리 실패 진단의 ODB를 사용하지 않는다.

```bash
python3 "$EXPERIMENT/run_gatelevel.py" --orfs "$ORFS" --stage "$STAGE" --netlist-dir "$NETLIST_DIR"
python3 "$EXPERIMENT/run_power.py" --orfs "$ORFS" --stage "$STAGE" --odb-dir "$NETLIST_DIR" --gate-pin u.u_backend_icg.u_icg/GCLK --clock-mode propagated
```

STAGE에는 dataA, ref_data, std_cell_fn, tb_gl_selected.v, power_10ns.sdc 및 전체 RTL 대조의 ungated_full.log가 있어야 한다. 게이트 수준 스크립트는 기존 VCD 덮어쓰기를 거부한다. 전력 스크립트는 6개 구간의 기능 대조가 통과해야 실행된다.

## 포함된 넷리스트로 기능 재현

power_results/ungated.v.gz와 gated.v.gz를 NETLIST_DIR에 풀면 합성·버퍼 삽입을 생략하고 같은 gate-level 명령을 실행할 수 있다. 전력 계산에는 대응하는 ODB가 필요하므로 ODB를 재생성하거나 원시 보관 경로의 해시 일치 파일을 이용한다. 넷리스트만 다르고 ODB가 이전 구조인 조합을 사용하면 안 된다.

최종 계산의 정확한 경로·환경 변수는 power_results/power_runs.json, 실제 입력 선택은 gatelevel_validation.json, 원본 파일 해시는 raw_artifact_manifest.json에 기록하였다. package_power.py는 증거를 수집하며 analyze_power.py는 전력 단위·텍스트/JSON 일치·활동도·타이밍·에너지 계산을 검산한다. write_power_report.py는 검산된 summary.json에서 표와 그림을 작성한다.

전력 라이브러리의 기존 STA-1212 경고는 원본 라이브러리의 output-to-output timing group에 관한 경고로 그대로 보존하였다. gated clock의 VCD 평균 주기와 SDC의 10 ns 주기가 다르다는 STA-1452 경고는 정지 구간이 포함된 gated clock의 실제 활동도에서 발생한다. 이를 동작 클럭 자체가 저속화되었다는 의미로 해석하지 않는다. 원시 로그에서 활동도 적용과 클럭 조건을 함께 확인한다.
