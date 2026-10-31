# 인계: 현서 최종 마무리 (넷리스트 1,000장 단일 실행 → 보고서 반영 → 재제출)

윤홍은이 더 진행할 수 없어 **현서가 main까지 직접 올리고 최종 제출까지 마무리**한다. main에 바로 커밋, push 해도 된다.
현재 제출본: main `submission/PPA_final_submission.zip` (보고서 43쪽, WM 전력 직접 측정 반영). 사이트 장애로 오늘 밤 메일로 제출해 두고, 아래 결과가 나오면 사이트 복구 후 재제출한다.

## 1. 실행 (약 10~11시간)
1. main의 `evidence/vivado_netlist/netsim_full_run_package.zip`을 한글과 공백이 없는 경로(예: `C:\netsim`)에 압축 해제한다.
2. `run.bat` 실행. 컴파일 약 5분 후 시뮬레이션이 시작된다. **절전 해제, 충전기 연결, 창 닫지 않기.**
3. `net.log`에 `STEP k=.. wall=..s`와 이미지별 `input image ... ==> Success/Fail`, `OBS n=.. idx=.. dec=..` 줄이 계속 쌓이면 정상이다.
4. 끝나면 `net.log` 끝에 `Final Accuracy for 1000 Input Image`와 `Accuracy : ..%`가 나온다. 중간에 멈추려면 같은 폴더에 `stop.flag` 파일을 만든다.

## 2. 검증
```bash
python evidence/vivado_netlist/scripts/compare.py <net.log 경로> results_hs/corrected_tb/sequential.csv
```
- `decision_match`, `cycle_match`가 `images`와 같아야 한다. 인덱스 1000(X→0 치환) 출력은 cycle 기준값이 없으므로 cycle 대조에서 제외해 읽는다.
- Vivado 버전(2024.1 등)이 2023.1과 다르면 난수 순서가 달라 정답 수가 966이 아닐 수 있다. 정상이다.
- `net.log`, compare 결과 JSON, Vivado 버전을 `evidence/vivado_netlist/full_run/`에 저장한다.

## 3. 보고서 반영 (`report/make_final_report.py`, 3.5.7절)
- 표 "합성 넷리스트의 Vivado 기능 검증 결과" 아래 주석(`기본 시드는 %s회 출력 ...까지 확인하였다. 5개 시드의 부분 실행 합계이며, 원본 TB 한 번의 1,000회 실행 완료는 아니다.`)을 아래처럼 바꾼다.
  - 예: "별도로 Vivado <버전>에서 원본 TB 한 번의 1,000회 실행을 완료하였고, TB가 출력한 정확도는 `Accuracy : NN%`(정답 NNN / 1,000)였다. 이 실행의 채점 출력 1,000개도 같은 인덱스의 RTL 결과와 판정이 모두 일치하였다."
  - 실제 값과 일치 여부를 그대로 쓴다. 불일치가 있으면 그 수를 쓴다.
- 3.5.7 본문 마지막 문단이나 표 11 마지막 줄에 "원본 TB 1,000회 단일 실행 완료"를 한 줄 추가할 수 있다.
- 재생성: `python report/make_final_report.py` → PowerShell에서
  `report/export_pdf.ps1 -DocxPath <docx 절대경로> -PdfPath <pdf 절대경로>` (한글 경로라 인수 지정 필수, Word 필요).
- PDF 확인: 쪽수, `@`/`%%`/`^^`/`**`/가운데점 잔존 없음, 표 번호 참조 정상.

## 4. 최종 zip 재생성과 제출
- `submission/PPA_final_submission.zip` 안의 `결과보고서_PPA.pdf`만 새 PDF로 바꾼다. 나머지(`PPA_AdaPath_NPU_A.zip`, `PPA_free_topic_WM811K.zip`)는 그대로 둔다.
  ```python
  import zipfile
  fs = {'결과보고서_PPA.pdf': 'report/결과보고서_PPA.pdf',
        'PPA_AdaPath_NPU_A.zip': 'vivado/submit/PPA_AdaPath_NPU_A.zip',
        'PPA_free_topic_WM811K.zip': 'submission/PPA_free_topic_WM811K.zip'}
  with zipfile.ZipFile('submission/PPA_final_submission.zip', 'w', zipfile.ZIP_DEFLATED) as z:
      for name, src in fs.items(): z.write(src, 'PPA_final_submission/' + name)
  ```
- main에 커밋, push 한다. 커밋 메시지에 AI 서명(Co-Authored-By 등)을 넣지 않는다.
- 사이트가 복구되면 새 zip으로 제출한다(재제출이 안 되면 조교 메일로 회신).
- 결과가 안 나오거나 시간이 부족하면 **아무것도 바꾸지 말고** 기존 제출본을 유지한다.
