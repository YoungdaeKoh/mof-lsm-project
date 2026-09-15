# LAI — LM4P 역학식생 잎면적 추적

해수부 KIMST 1.7 **1차년도 검증 대상 3개**(토양수분·토양온도·**식생**) 중 식생 담당 폴더.
마일스톤 원문 `2026/해수부_마일스톤.md:14` ③ "1979–현재 offline → 토양수분/온도·식생 기본성능 진단".

## 파일

| 파일 | 내용 |
|---|---|
| `LAI_flow.pdf` | **인쇄용.** 계산 흐름 모식도 + 단계별 행번호 + 조정 가능한 계수 목록 (6쪽) |
| `LAI_flow.html` | 위 PDF의 원본. 수정 후 아래 명령으로 PDF 재생성 |
| `reference/` | 참고논문 5편 |

PDF 재생성:

```bash
cd lm4/LAI
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="LAI_flow.pdf" "file://$PWD/LAI_flow.html"
```

## 한 줄 결론

LAI는 예후변수가 아니다. `bl`(잎 탄소)에서 `LAI = bl/LMA`로 매 스텝 만들어지는 **진단량**이고,
`bl`은 `nsc`(비구조탄소 저장고)에서 인출된다. 그래서 손잡이는 세 종류뿐이다 —
**천장**(`LMA`·`LAImax`) · **인출속도**(`f_NSC`·`growth_resp`) · **위상**(`tc_crit`·`gdd_crit`).

## 소스 (행번호의 기준)

```
/data2/ydkoh/lm4/esm4p5-lm4p-offline/src/lm4P/vegetation/
```

**주의**: 같은 lm4P 클론이 `ufs-weather-model-lm4p`에도 있으나, `ufs-weather-model` 쪽
`vegn_dynamics.F90`은 633줄짜리 **PPA 없는 구버전**이라 행번호가 전혀 맞지 않는다.
생산런 exe는 `esm4p5-lm4p-offline/exec/fms_esm4.5_compile_v3_1007_fix.x` (KIOST-ESM2 계열).

## 참고논문

`reference/` 10편 확보. 목록·미확보 1편은 `reference/_받을것.md` 참조.

| # | 문헌 | 왜 필요한가 |
|---|---|---|
| 01 | Weng et al. (2015) BG 12, 2655–2694 | **핵심.** `f_NSC`=eq.A7, `f_WF`=eq.A12로 소스 주석에 명시 |
| 02 | Weng et al. (2019) BG | 광 경쟁, 상/하층 천장 차이 |
| 03 | Shevliakova et al. (2024) JAMES | LM4.1 공식 모델 기술문서 — 인용 기준 |
| 04 | CRESCENDO (2025) BG | 다중모델 LAI 편차 통상 크기 — 우리 편차가 특이한지 판단할 기준선 |
| 05 | Kim, Lee & Seo (2019) J. Climate 32 | **방법론 템플릿.** Q10 상수 → 관측회귀 함수 |
| 06–09 | Medlyn 2002 · Hoch 2003 · Wilson 2001 · Bernacchi 2001 (*Plant Cell Environ*) | 광합성 온도의존성, NSC 저장비율의 실측 근거 |
| 10 | Paulsen & Körner (2014) *Alpine Botany* | 수목한계선 모델 (`vegn_data.F90:538`) |

미확보: **Farquhar & von Caemmerer (1982)** 단행본 章 — C3 광합성 표준식.
같은 내용이 06·09에 최신 형태로 있어 실무상 급하지 않다.

## 이어지는 작업

- [ ] LAI 편차가 **크기인가 위상인가** 판정 → 후보 A(`LMA`) / 후보 B(`gdd_crit`) 결정.
      §13.41·§13.26 자료로 **새 실험 없이** 가능
- [ ] `diag_table`에 `bl_max`·`nsc` 추가 → 포화 여부·탄소제한 여부 진단 (PDF §4의 4·6번)
- [ ] 1차년도 나머지 두 변수(**토양수분·토양온도**) 동일 형식 추적 — 미착수

관련 노트: `lm4/LM4_SPINUP_NOTES.md` §13.29(요약)·§13.30(native vs CMIP 함정)·
§13.40·§13.46(표류)·§13.53(목재는 발산, LAI는 수렴) · 상세 `lm4/LM4_LAI_CODE_TRACE.md`
