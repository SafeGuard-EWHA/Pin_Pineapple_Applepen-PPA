# 인계: 자유주제(WM-811K) 적용 전후 직접 전력 측정 (마감 10/31 24:00)

## 왜 필요한가
조교 공지 5번: 자유주제도 **기법 적용 전 vs 후 PPA(Fmax/Power/Area)와 측정 방법**을 제출해야 한다.
현재 WM의 Area와 Fmax는 직접 측정값이지만, **Power(에너지)는 모델 B의 모드별 에너지를 WM 모드 비율로 가중한 대리 추정**이다.
이를 WM 넷리스트의 게이트레벨 VCD 전력(지정주제와 같은 방법)으로 바꾸는 것이 남은 작업이다.

## 완료 (21:45)
- 측정 완료: Baseline_WM 29.46 nJ → AdaPath_WM 26.86 nJ (−8.8 %), 평균 전력 Baseline 2.970 mW, AdaPath Easy 2.395 / Medium 2.865 / Hard 3.213 mW (100 MHz).
- AdaPath_WM 12장의 게이트레벨 판정, 모드, Margin은 `wm_expect.txt`와 모두 일치.
- 보고서(3.9절 표, 2장 목표 표, 요약 핵심 결과, 결론), 자유주제 패키지 README와 `power/`, `submission/PPA_final_submission.zip` 반영 완료.

## 이전 상태 (19:40 기준)
- 윤홍은 노트북에서 아래 1단계 시뮬레이션 4개가 실행 중이다(`C:\Users\yhe44\idec_glsim\wm`). 끝나면 Claude가 2~4단계를 진행하고 main에 올린다.
- 노트북 결과가 안 올라오면 아래 절차를 각자 PC에서 그대로 실행하면 된다. 필요한 파일은 모두 `glsim/wm/`에 있다.

## 파일 (`glsim/wm/`)
| 파일 | 내용 |
|---|---|
| `adapath_wm_net.v.gz`, `baseline_wm_net.v.gz` | ORFS 합성 넷리스트 (ASAP7, 보고서 면적/Fmax와 같은 합성) |
| `std_cell_fn/` | ASAP7 표준셀 기능 모델 (지정주제 게이트레벨과 동일) |
| `tb_gl_wm.v` | 게이트레벨 TB (100 MHz, 이미지마다 리셋 12 cycle, `+I0..+I3`로 이미지 4장 지정, 전체 VCD 덤프) |
| `run_wm.sh` | Icarus 컴파일 + 4개 실행 (AdaPath Easy/Medium/Hard 각 4장, Baseline 4장) |
| `vcd_power_net.tcl`, `power_wm.sh` | OpenROAD `read_vcd` + `report_power` (넷리스트 기반, ODB 불필요) |
| `energy_wm.py` | 평균 전력 × 관측 시간 ÷ 4 → 이미지당 에너지, AdaPath는 RTL 모드 비율 404/167/383 가중 |

선택한 이미지(`vivado/wm_data/wm_expect.txt`에서 정답이고 모드가 같은 앞쪽 4장): Easy 8, 10, 18, 22 / Medium 2, 3, 5, 24 / Hard 0, 1, 4, 9 / Baseline 0, 1, 2, 3.

## 절차
1. **시뮬레이션** (Windows Git Bash + Icarus 12, 또는 Linux iverilog)
   ```bash
   cd glsim/wm
   NET_DIR=<넷리스트와 VCD를 둘 폴더> bash run_wm.sh     # .v.gz는 자동으로 풀린다. VCD가 수 GB일 수 있다
   ```
   로그(`wm_*.log`)의 `img N : decision=.. mode=..`가 `wm_expect.txt`(label decision mode margin)와 같은지 확인한다.
   Easy 실행은 mode=0, Medium은 1, Hard는 2여야 한다.
2. **전력** (WSL/Linux, OpenROAD 설치 필요)
   ```bash
   VCD_DIR=<위 NET_DIR의 WSL 경로> ORFS=$HOME/OpenROAD-flow-scripts bash glsim/wm/power_wm.sh
   ```
3. **에너지**: `python glsim/wm/energy_wm.py <VCD_DIR>` → `glsim/wm/power_results/energy_wm.json`
4. **보고서 반영** (`report/make_final_report.py`)
   - 3.9절 표 "WM-811K 적용 전후 비교"의 `추론당 에너지 (nJ, 대리 추정)` 행을 직접 측정값으로 바꾸고 표 주석을 "WM 넷리스트의 게이트레벨 VCD 기반 추정(100 MHz, 모드별 4장, RTL 모드 비율 가중)"으로 수정한다. 현재 값은 `E_WM`, `E_WM_BASE` 변수에서 온다.
   - 2장 "설계 목표 및 결과" 표의 WM 행 판정 "부분 확인"과 "WM 자체의 전력 평가는 미완료" 문장을 수정한다.
   - 4장 결론의 WM 문장에 에너지 변화율을 추가할 수 있다.
   - `python report/make_final_report.py` 후 Word로 PDF 생성: PowerShell에서 `report/export_pdf.ps1 -DocxPath <docx 절대경로> -PdfPath <pdf 절대경로>` (한글 경로라 인수를 명시해야 한다).
5. **자유주제 패키지**: `submission/free_topic_WM811K/README.md`의 1절 표 에너지 행과 3절 "전력/에너지" 설명을 직접 측정으로 바꾸고, `glsim/wm/`의 TB, 스크립트, `power_results/`를 패키지에 복사한 뒤 zip을 다시 만든다.
6. **최종 제출 zip**: `결과보고서_PPA.pdf`, `vivado/submit/PPA_AdaPath_NPU_A.zip`, `submission/PPA_free_topic_WM811K.zip` 세 개를 `PPA_final_submission.zip`으로 묶어 제출한다.

## 주의
- 결과가 대리 추정과 달라도(예: 감소율이 작거나 증가) 측정값을 그대로 쓴다.
- 시간이 부족하면 1~3단계 결과만이라도 README와 보고서에 반영한다. 아무 결과가 없으면 현재 제출본(대리 추정 명시)으로 낸다.
- 커밋에 AI 서명(Co-Authored-By 등)을 넣지 않는다.
