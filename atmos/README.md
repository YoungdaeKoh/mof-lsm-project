# atmos/ — 대기모델 계산 흐름 이해 (AM4.5 vs CAM6)

2026-10-19 생성. 결합 진단(2·3차년도, atmospheric leg) 대비 학습 자료.

| 파일 | 내용 |
|---|---|
| `atmos_timestep_AM45_vs_CAM6.pdf` (+ `.html` 원고) | **메인 결과물 6쪽**: 읽는 법·핵심 숫자 / AM4.5 흐름도 / CAM6 흐름도 / 책 5단계 기준 나란히 비교 / 지면–대기 implicit vs explicit / 공통점·차이점·책 쪽수 색인 |
| `book/GettelmanRood2016_annotated_AM45_CAM6.pdf` | Gettelman & Rood (2016) 사본에 20곳 형광펜(단계 색) + 여백 태그 + 메모(코드 위치). 북마크 맨 위 "★ AM4.5/CAM6 대응" |
| `book/annotate_book.py` | 위 주석 생성 스크립트 (원본 `~/Documents/978-3-662-48959-8.pdf`는 수정 안 함) |
| `book/book_text.txt` | 책 전문 텍스트 추출 (grep용, `=====PDFPAGE n=====` 구분) |
| `code_trace/am45_timestep_trace.md` · `cam6_timestep_trace.md` | 호출 순서 + file:line + 검증된 설정값 |
| `code_trace/am45_input.nml.KIOST-ESM2` · `cam6_atm_in.F_2000climo_f09` | 서버 namelist 사본 (설정 근거) |
| `src/` (git 제외) | 서버 소스 미러: `am45/` ← climate:~/ESM4p5_KIOSTv2b/src/{atmos_drivers,atmos_phys,GFDL_atmos_cubed_sphere,coupler}, `cam6/` ← climate:~/CESM/components/cam/src (.F90만) |

PDF 재생성: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --no-pdf-header-footer --print-to-pdf=atmos_timestep_AM45_vs_CAM6.pdf file://$PWD/atmos_timestep_AM45_vs_CAM6.html`

책 쪽 번호 주의: 인쇄 쪽 ≠ PDF 쪽 − 상수 (장마다 11–14 차이). 문서엔 둘 다 표기.
