# LM4P 검증·개선 학습 로드맵 (2026-08~)

> 목적: ydkoh를 지면-식생모델(LSM) 검증·개선 **준전문가**로. 답 대신 원리·판단근거를 익히는 방향. (memory: user-wants-mentorship-to-expert)

---

## 1. 우리 과제의 계보 (왜 우리가 이걸 하는가)

두 선행 보고서를 읽고 확인한 위치:

| 연구 | 한 일 | 우리와의 관계 |
|---|---|---|
| **GAIA 최종 (KIOST, 2019)** | KIOST-ESM **개발·결합** (GFDL CM2.1→GAIA→KIOST-ESM, CM2.5 큐브구+지면식생+TOPAZ+UNICON). 연구원에 김영호 | 우리 모델의 **직계 전신**. 지면-식생 **진단은 공백** |
| **APCC 테스트베드 (2024)** | GloSea6 JULES 지면모델 **개선·검증** (GLEAM/FluxCom/GRDC) | 우리가 쓸 **검증 방법론** |
| **우리 과제 (2026~)** | KIOST-ESM 지면-식생 **진단·개선** | GAIA가 만든 걸 APCC 방식으로 진단 = 두 연구 사이 빈칸 |

→ 진도보고서 서론에 이 계보를 쓰면 과제 정당성 명확.

## 2. 검증 방법론 (반복 각인할 핵심)

**순서가 중요 — 코드부터가 아니다:**

1. **관측 비교 (What)**: 모델 출력이 관측처럼 나오는가. 지표 = **bias, RMSE, 상관**. 유역/biome별로 나눠서.
2. **원인 진단 (Why)**: 편차를 발견한 뒤에야 코드/프로세스로 내려가 원인 규명 (APCC "프로세스 기반 원인 분석").

**성분별 벤치마크 자료** (APCC 보고서에서 채택):

| 검증 대상 | 기준자료 | 상태 |
|---|---|---|
| 증발산·토양수분 | **GLEAM** | 확보 필요 |
| 현열·잠열 | **FluxCom** (FLUXNET 기반) | 확보 필요 |
| 하천 유량 | **GRDC** (유역별 관측) | 확보 필요 |
| LAI | **GIMMS LAI4g** | ✓ 완료 (bias +0.69, r 0.66; 열대 과대·아북극 과소) |
| 염분·SST·해류 | 해양 재분석 ORAS5 | 결합실험 시 |

## 3. LM4P 식생 — 이미 파악한 것 (코드+논문)

- **예후(prognostic) LAI** — 역학식생 ON (처방 아님)
- **종 조성 고정** — `do_biogeography=.FALSE.` (관측 기반 cover_type.nc, 진단에 유리)
- **PPA 코호트 기반, 7 PFT**: prioria(열대상록)·picea(가문비)·larix(낙엽송)·acer(단풍)·c4grass·c3grass·default
- **질소순환 OFF** — `soil_carbon_model='CENTURY-like'` (CORPSE-N 아님)

## 4. 8월 목표 — 논문 → 코드 → 원인 진단

```
1주: 논문으로 식생 모의 원리 (Weng 2015 PPA → Shevliakova 2024 LM4.1)
2주: 원리↔코드 매핑 (Q10·탄소배분·phenology가 어느 F90/서브루틴/namelist)
3-4주: 관측 비교 확장(GLEAM/FluxCom/GRDC) + 편차의 코드적 원인 targeted 진단
```

**논문 먼저인 이유**: LM4P는 55개 F90 → 코드부터 읽으면 길 잃음. 논문이 지도 → 코드 해당부만 본다.

**논문 읽기 우선순위** (reference/papers/):
1. Weng2015_PPA_BG.pdf — 코호트 경쟁·식생 동역학 뼈대
2. Shevliakova2024_LM4.1_JAMES.pdf — LM4.1 전체 구조, **Q10·탄소순환 위치**
3. CRESCENDO_LAI_Part2_BG2025.pdf — 다중LSM LAI 편향 (우리 결과 맥락화)
4. Weng2019_competition_BG.pdf — 질소·경쟁 (Phase 2용)

## 5. Q10 — 관심 손잡이 (사용자 기억)

- GAIA에서 울산과기원이 **토양분해 온도민감도 Q10을 식생타입별로 재분석 다변량회귀로 처방**.
- Q10은 **고위도(아북극) 식생·탄소를 좌우** → 우리가 본 "아북극 LAI 과소"와 직결 가능성.
- Q10 수정엔 많은 시도 필요 → **먼저 코드에서 Q10 계산·사용 위치 확인**이 우선 (예상: `soil_carbon.F90`).
- 이게 8월 코드 이해의 구체적 첫 표적.
