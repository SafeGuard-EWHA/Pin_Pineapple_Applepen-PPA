# 원본 TB 비교와 Vivado 레퍼런스 재현 검토

팀원 AI는 이 문서와 아래 원시 로그를 함께 읽고 독립적으로 검토한다. 대상은 **보관된 공식 배포본의 레퍼런스 RTL + 원본 TB**이며 AdaPath RTL을 실행한 결과와 구분한다. 원본 TB·RTL·제출 ZIP을 변경하지 않았다.

## 바로 확인할 근거

- [최신 Vivado 실행 로그](vivado_reference/simulation.log): 초기 채점 제외 출력 계수를 추가한 최종 실행
- [관찰 모듈](vivado_reference/official_observer.v) 및 [실행 Tcl](vivado_reference/run.tcl)
- [검증 결과 JSON](vivado_reference/validation.json): 버전, 카운터, 검증 범위
- [원본 TB 대 제출 TB 전체 차분](tb_origin_audit/TB差分.diff)
- [비교 결과 JSON](tb_origin_audit/comparison.json): 파일 해시와 변경된 34줄
- [원본 소스·데이터 해시](vivado_reference/source_hashes.json)
- [첫 실행 로그](vivado_reference/simulation_initial.log): 초기 출력 제외 카운터 추가 전 실행

## 확인된 사실

보관된 `2025KNU_CCDC.zip → Reference code.zip → Reference code/cnn_verilog/verilog/top_tb.v`와 A 제출 ZIP의 TB는 각 400줄이다. 줄바꿈과 `$readmemh` 경로의 `C:/cnn_verilog/data/` 접두사 차이를 제외하면 전체가 동일하다. 34줄의 변경은 모두 파일 경로 변경이며, 난수·픽셀 읽기·초기화·집계 로직 변경은 없다. B 제출 ZIP도 동일하게 확인하였다. 비교 JSON·차분의 직접 대상은 A이다. 원본 ZIP 해시는 인계 manifest와 대조하였다. 주최 측 서버의 최신 배포본·정오표 확인은 아니다.

설치된 Vivado 2024.1 SW Build 5076996에서 다음 결과를 관측하였다.

| 항목 | 결과 |
|---|---:|
| 이미지 인덱스 1000 선택 | 3회 |
| 범위 밖 픽셀 읽기 | 2,355회 |
| X 픽셀 읽기 | 2,355회 |
| valid_out에서 X decision | 0회 |
| 전체 valid_out 관측 | 1,001회 |
| state=X로 채점 제외된 초기 출력 | 1회 |
| 실제 채점·표시된 결과 | 1,000회 |
| accuracy 카운터 | 967 |

콘솔의 `Accuracy : 96%`는 정수 나눗셈 표시이다. 읽기 카운터는 `rst_n=1, state=0, cnt<1000`인 구간에서 관측했다. 내부 모든 신호의 X를 검사한 것은 아니다.

## 이전 설명의 정정 및 해석 범위

**전체 출력 1,001회 자체를 채점 개수 오류로 단정하지 않는다.** 1회는 state=X인 초기 채점 제외 출력이고, 실제 채점 로그는 1~1000번이다. 보고서 및 이전 진단에서 전체 출력 수만으로 종료·집계 오류라고 읽힐 수 있는 설명은 이 사실을 반영하여 재검토해야 한다. 이번 게시에서는 보고서 PDF·DOCX를 다시 편집하지 않았다.

반면 인덱스 1000 선택과 범위 밖 읽기는 원본 레퍼런스 + Vivado 2024.1에서도 실제 발생하였다. 이를 팀원의 TB 로직 변경이나 Icarus만의 현상으로 설명할 수는 없다. X 입력이 최종 decision의 X로 전파되지는 않았다. 해당 잘못된 입력이 정확도 카운터에 어떻게 반영되는지는 인덱스별 판정과 comparator 동작을 추가 추적해야 하며, 이 로그만으로 정확도 오염의 크기나 방향을 단정하지 않는다.

배포 프로젝트 저장 버전은 2023.2, 팀 과거 실행은 2023.1, 이번 실행은 2024.1이다. 대회 필수 버전은 확인하지 않았다. 다른 버전의 난수열·발생 횟수까지 동일하다고 일반화하지 않는다.

## 재현 조건

원본 ZIP의 `verilog/*.v`, `data/*.txt` 34개 파일을 추출하였다. 원본 TB가 요구하는 `C:/cnn_verilog/data`에 동일 데이터를 배치하고 실행 후 해시 일치를 확인하였다. 기존 파일이 다르면 덮어쓰지 않고 중단하였다. 원본 .v는 Verilog로 컴파일하고, 별도 관찰 모듈만 SystemVerilog로 컴파일하였다.

```powershell
# 원본 verilog 폴더, official_observer.v, run.tcl이 있는 별도 작업 폴더에서 실행
$rtlFiles = @(Get-ChildItem ./verilog -Filter '*.v' | ForEach-Object { $_.FullName })
& 'C:/Xilinx/Vivado/2024.1/bin/xvlog.bat' @rtlFiles
& 'C:/Xilinx/Vivado/2024.1/bin/xvlog.bat' --sv ./official_observer.v
& 'C:/Xilinx/Vivado/2024.1/bin/xelab.bat' top_tb_1000 official_observer -timescale 1ns/1ps -debug typical -s official_reference
& 'C:/Xilinx/Vivado/2024.1/bin/xsim.bat' official_reference -tclbatch run.tcl -log simulation.log
```

기본 `-timescale 1ns/1ps`는 선언이 없는 모듈에 적용하며 원본 TB의 `1ps/1ps` 및 `#5` 클럭은 변경하지 않았다. 원본 GUI 프로젝트의 모든 옵션이나 2023.2 환경 자체를 복제한 것은 아니다. 관찰 모듈은 DUT를 구동하거나 난수를 호출하지 않는다. 컴파일·엘라보레이션 로그도 같은 폴더에 있다.

원본 배포 ZIP 자체는 이번 게시에 추가하지 않았다. 원본을 가진 팀원은 comparison.json의 해시로 동일성을 확인할 수 있다. txt 설명 파일은 로컬 재현 당시 기록이므로 그 안의 “GitHub를 변경하지 않았다”는 문장은 당시 실행 범위를 뜻한다. 이 폴더는 이후 exp-hyunseo에 공유한 근거 자료이다.

## 팀원 AI에게 요청할 검토

1. 카운터의 관측 조건과 원본 코드 해석을 확인한다.
2. 인덱스 1000의 입력이 채점에 포함되는지 판정·라벨·accuracy 증가를 추적한다.
3. X 픽셀에도 숫자 decision이 나오는 이유를 comparator 코드로 확인한다.
4. 초기 채점 제외 출력과 785번째 픽셀 읽기의 의도·안전성을 구분한다.
5. 가능하면 팀의 Vivado 버전에서도 재현하고 확인된 사실·미확인 영향을 구분한다.

관련 별도 수정 TB의 AdaPath 재검증은 [corrected_tb](../corrected_tb/README.md)에 있다. 본 폴더의 원본 레퍼런스 재현과 혼동하지 않는다.
