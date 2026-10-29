# 최종 보고서 검토 및 현서 추가 검증 통합

## 입력과 범위

- 본문 기준: main `dc151207b527216164528630ab8e1add2a63edff`.
- 추가 검증: `exp-hyunseo-final`의 `7364903c0ec1f4352448bcc64ae6c9e193811a37`.
- 추가 근거 36개 파일은 해당 커밋의 Git blob SHA와 일치함을 확인하였다.
- 수정 대상은 보고서 생성 코드 및 생성 문서, 교정·검토 기록이다. 확정된 `report/results.json`, 모델, RTL/TB, 제출 ZIP은 수정하지 않았다. 실험은 재실행하지 않았다.
- `make_results.py`, `make_extra.py`는 실행하지 않았다.

## 반영한 내용

| 위치 | 반영 내용 | 근거·의미 |
|---|---|---|
| 3.3 교차평가 설명 | 각 seed에서 두 held-out 절반을 합친 OOF 평가임을 명확히 함 | 5개 seed의 표준편차를 별개 테스트셋 간 불확실성으로 오해하지 않도록 함 |
| 오류 분석 | Full이 복구한 오분류 58장뿐 아니라 반대 방향 52장도 함께 설명 | 순 정확도 차이는 6장, 0.06 %p |
| 3.5.5 신규 절 | 4개 제어 조건 검사표, 검사 횟수 및 위반 건수 | A/WM의 검사된 조건 위반 0건. A Medium은 미실행으로 표시 |
| 3.5.5 제한사항 | 마지막 start 미평가, 초기 decision X 및 입력 X 관측, 형식 검증과 구분 | 전체 입력 공간 검증 또는 전체 I/O X-free 주장 방지 |
| 3.9.1 | WM 세 번째 입력의 Medium 파형과 판정 근거 | margin 16, mode 1, ch_en 0x0F, Light FC 활성, Full FC 비활성, 유효 decision 0 |
| 3.9.1 파형 캡션 | 실제 VCD 재도식화, Vivado 2024.1, 기능 클럭 10 ns 명시 | A 파형의 10 ps 논리 시간축 및 물리적 Fmax와 구분 |
| 결론 | 개선 요소를 Early Classifier·버퍼·판단·제어 통합으로 설명 | Score Margin 하나만으로 얻은 개선처럼 표현하지 않음 |
| 결론 | A의 Easy 에너지 손익분기 비율을 WM에 그대로 적용하지 않음 | WM none 클래스의 83.3%가 Hard인 실제 분석을 반영 |
| 재현성 | Vivado 2024.1의 다른 PC 검증과 WM 제출 프로젝트 생성 명령 구분 | 본래 Vivado 2023.1 결과를 다른 버전의 결과로 치환하지 않음 |
| 조판 | 짧은 표의 연속 배치, 캡션 문단 유지, TOC 스타일 수정 | 페이지 사이의 짧은 표 분리와 잘못된 목차 스타일 방지 |

새 제어 조건 표는 `results_hs/assertions/summary.json`을 직접 읽어 생성한다. 새 그림은 `results_hs/medium_wave/medium_wave_measured.png`를 사용한다. 그림·표 번호는 `LBL`에서 자동 산출한다.

## 보고서에 남긴 해석상의 한계

- PPA는 ASAP7 pre-layout 합성·STA와 게이트레벨 VCD 기반 전력·에너지 **추정**이다.
- MAC 감소율과 에너지 감소율을 동일시하지 않는다. Reference 대비 A는 MAC 약 23.8%, 에너지 약 8.9% 감소이며 면적은 약 55.4% 증가한다.
- 0.5 %p는 내부 동작점 선정 규칙이다. 주최 측 정확도 유지 조건과 동일한 기준으로 표현하지 않는다.
- WM 에너지는 10-class B의 모드별 에너지를 사용하는 **대리 추정**이며 4-class WM 직접 전력 측정 결과가 아니다.
- `input_1000.txt`의 1,000회는 고유 100장 × 10회 반복으로 독립 통계 표본 1,000장으로 취급하지 않는다.
- 원본 A 제출 ZIP의 무작위 TB 채점 966/1000과 순차 입력 결과 970/1000을 구분한다. 새 관측기의 1,001회 완료 거래 수는 1,000회 채점 표본 수와 다르다.
- A의 Medium 경로 검사 횟수는 0이며 미실행을 합격으로 표현하지 않는다. WM의 167장·27,555개 Medium 활성 cycle이 실제 검사 근거이다.
- 동적 어서션 0건은 검사한 조건과 입력에 한정된다. 마지막 A start 미평가 및 초기 X 관측을 숨기지 않는다.

## 검증과 재생성

저장소 루트에서:

```text
python report/make_final_report.py
python results_sh/final_review/validate_report.py
# 현재 DOCX를 PDF로 내보낸 뒤:
python results_sh/final_review/validate_report.py --pdf
```

`validation.json`에 원본 커밋, 추가 검증 커밋, 산술 검산, 문서 SHA-256, 그림·표 수 및 PDF 검사 결과를 남긴다. 생성 코드의 변경 뒤에는 DOCX와 PDF를 함께 재생성해야 한다.

Word가 가능한 PC에서는 `report/export_pdf.ps1`로 필드·목차를 갱신한 뒤 PDF를 내보낼 수 있다. 현재 실행 환경에서는 Word COM 초기화가 권한 오류로 실행되지 않아 이 스크립트의 Word 실행 성공을 확인하지 못하였다. PDF 변환·전 페이지 검토 결과는 최종 검토 기록에 별도로 남긴다.

## 최종 PDF 검토 결과

- 최종 문서는 **38쪽, 그림 24개, 표 31개**이다. 인수인계의 28쪽보다 이후 main에 추가된 내용이 많으며, 검토 시작 시 실제 main PDF는 36쪽이었다.
- LibreOffice 26.8.2.2를 로컬에서 사용하여 목차·쪽번호 필드를 갱신하고 DOCX와 PDF를 함께 저장하였다. 보고서를 외부 변환 서비스에 업로드하지 않았다.
- 재현용 변환기는 `report/export_pdf_lo.py`이다. LibreOffice에 포함된 Python으로 실행하며 `--soffice`와 쓰기 가능한 `--profile` 경로를 지정한다. 매크로 실행은 비활성화한다.
- 표지 포함 PDF **1~38쪽을 Poppler 115 dpi로 렌더링하여 전 페이지를 확인**하였다. 그림·표·주석의 잘림이나 겹침을 발견하지 못하였다.
- 표 25는 길이 때문에 29~30쪽에 걸치며 머리글이 반복된다. 짧은 표는 주석과 함께 유지되도록 보완하였다. 그림 24개 모두 해당 캡션과 같은 페이지에 있다.
- 3.5.5 제어 조건 검사표는 **표 14, PDF 19쪽**, 실제 WM Medium 파형은 **그림 19, PDF 28쪽**이다.
- 문서의 `@`, `%%`, `%(`, 편집용 강조 마크 잔여물, 빈 목차를 검사하였다. 본문·표 산술 대조, 새로운 제어 조건 수치 대조 및 DOCX 구조 검사가 통과하였다.
- `visual_review.json`과 `validation.json`에 검토 대상 파일 해시를 남겼다. 이후 재생성하거나 Word/HWP에서 조판을 바꾸면 PDF 검토도 다시 수행해야 한다.

제출 형식·마감 확인 사항은 [submission_requirements.md](submission_requirements.md)에 정리하였다. GitHub 반영은 대회 접수 완료를 뜻하지 않는다.
