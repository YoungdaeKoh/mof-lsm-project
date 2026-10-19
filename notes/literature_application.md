# MOF_LSM_project — 문헌 위키 적용 기록 (literature_application)

> 공통 문헌 위키 `/Volumes/data01/notes/literature/`는 **공개 문헌의 사실·문헌 간 비교**만 둔다(위키 AGENTS.md 범위 규칙). 이 프로젝트의 **미공개 설정·결과·적용 판단과 문헌의 대조**는 여기에 둔다. 링크는 프로젝트 → 위키 방향만.
> 2026-10-15 생성(사용자 결정, 위키 issues.md O-10): 위키에 섞여 있던 항목을 **원문 그대로** 옮겼다. 각 항목의 근거·조건·불확실성·GPT 검토 상태는 옮긴 문구 안에 보존되어 있다. **확인 범위는 원문 대조·해석 검토**이며 데이터·코드 재현이 아니다. 옮기기 전 위키 상태는 `/Volumes/data02/_snapshots/20261015_before_separation/`.

## 이동 대응표
| # | 원래 위치(위키) | 이 문서 절 | 위키 노트(공개 부분) |
|---|---|---|---|
| 1 | `papers/weng2015_bg.md` — weng2015_bg — 3.1 기존 기록과의 대조 | §1 | `/Volumes/data01/notes/literature/papers/weng2015_bg.md` |
| 2 | `papers/shevliakova2024_james.md` — shevliakova2024_james — 3.1 기존 기록과의 대조 | §2 | `/Volumes/data01/notes/literature/papers/shevliakova2024_james.md` |
| 3 | `papers/peano2021_bg.md` — peano2021_bg — 3.1 기존 기록과의 대조 | §3 | `/Volumes/data01/notes/literature/papers/peano2021_bg.md` |
| 4 | `papers/peano2025_bg.md` — peano2025_bg — 3.1 기존 기록과의 대조 | §4 | `/Volumes/data01/notes/literature/papers/peano2025_bg.md` |
| 5 | `papers/orsolini2019_tc.md` — orsolini2019_tc — 3.1 기존 기록과의 대조 | §5 | `/Volumes/data01/notes/literature/papers/orsolini2019_tc.md` |
| 6 | `reports/2026-10-15_six_paper_test.html` — 비교 보고서 2절 관계표 행 — shevliakova2024 관계표 | §6 | `/Volumes/data01/notes/literature/reports/2026-10-15_six_paper_test.html` |
| 7 | `reports/2026-10-15_six_paper_test.html` — 비교 보고서 2절 관계표 행 — weng2015 관계표 | §7 | `/Volumes/data01/notes/literature/reports/2026-10-15_six_paper_test.html` |
| 8 | `reports/2026-10-15_six_paper_test.html` — 비교 보고서 2절 관계표 행 — peano2021 관계표 | §8 | `/Volumes/data01/notes/literature/reports/2026-10-15_six_paper_test.html` |
| 9 | `reports/2026-10-15_six_paper_test.html` — 비교 보고서 2절 관계표 행 — orsolini2019 관계표 | §9 | `/Volumes/data01/notes/literature/reports/2026-10-15_six_paper_test.html` |
| 10 | `reports/2026-10-15_six_paper_test.html` — 비교 보고서 4절 — MOF 결론(원문 그대로) | §10 | `/Volumes/data01/notes/literature/reports/2026-10-15_six_paper_test.html` |

## §1. weng2015_bg — 3.1 기존 기록과의 대조
원래 위치: `/Volumes/data01/notes/literature/papers/weng2015_bg.md` · 이동 2026-10-15

> 검토 상태: GPT 검토 반영 v2 (gpt-6.1-sol/high, 2026-10-15; #R15–#R18 해당).

## 3.1 기존 기록과의 대조
| 기존 기록 | 내용 | 대조 결과 |
|---|---|---|
| `MOF_LSM_project/notes/findings.md:56` | "원형 = Weng et al. 2015 BG 12:2655 부록 A3·Table: GDDcrit 320 °C·day, Tcrit 10 °C, Tpheno=0.95·old+0.05·Td, \"unchanged from LM3\"(Shevliakova 2009; Milly 2014) — 값 자체의 관측 근거 인용 없음" | **일치** (노트에 인용된 문장 내용 범위; 프로젝트 파일의 행 번호·코드는 GPT 미확인) |
| 같은 줄 "GDD는 가을 잎 지기 때 0으로 초기화" | 코드 관찰 | **부분확인 (누적 기점만)** — 원문은 "days from the end date of the last growing season". 정확한 코드 리셋 시점은 미확인; p = 0 전환 뒤 낙엽이 시작되므로 완전 낙엽일과는 구분 |
| `MOF_LSM_project/notes/findings.md:55` | 끄기 판정 "20일 평활 `tc_pheno`" | 원문 T_pheno의 가중 0.05(시간 척도 약 19–20일, 계산)와 **부합**. 원문에 "20-day" 표현 없음; 코드 변수 `tc_pheno`가 같은 식인지는 판정하지 않음 |
| `MOF_LSM_project/notes/decisions.md:22` | 낙엽송 LMA 0.038 "문헌 부합 값" | 0.038은 이 논문의 **붉은단풍** 값(표 1·C3)이며 낙엽송 값으로 제시되지 않음 → 이 논문을 낙엽송 LMA 0.038의 **직접 근거로 쓸 수 없음**(다른 문헌에서 가능한지까지 부정하지는 않음) |

## §2. shevliakova2024_james — 3.1 기존 기록과의 대조
원래 위치: `/Volumes/data01/notes/literature/papers/shevliakova2024_james.md` · 이동 2026-10-15

> 검토 상태: GPT 검토 반영 v2 (gpt-6.1-sol/high, 2026-10-15; #R14 동의).

## 3.1 기존 기록과의 대조
| 기존 기록 | 내용 | 대조 결과 |
|---|---|---|
| `MOF_LSM_project/notes/decisions.md:22` | 낙엽송 LMA "문헌 부합 값 0.038 kgC m⁻²(field_table 주석에 남은 원래 값)", 문헌 범위 0.026–0.046 | 0.038은 LM4.1 표 B1의 **Temperate tree** 값과 같음. LM4.1에는 낙엽송 유형이 없으므로 이 논문은 **낙엽송 고유 LMA의 직접 근거가 아님**. 수치가 같다고 해서 기존 값이 이 표에서 왔다고 추정하지 않음. 0.026–0.046 범위의 출처·타당성은 이 논문에 없음 → 연구자 판단 필요 (GPT #R14 동의) |
| `MOF_LSM_project/notes/findings.md` (2026-10-15 항목) | 종별 GDD·기온 문턱 "출처 주석 없음" | 이 논문에서도 출처 확인 불가(1.4) |

## §3. peano2021_bg — 3.1 기존 기록과의 대조
원래 위치: `/Volumes/data01/notes/literature/papers/peano2021_bg.md` · 이동 2026-10-15

> 검토 상태: GPT 검토 반영 v2 (gpt-6.1-sol/high; #R15 동의 — '직접 지지'·'확인됨').

## 3.1 기존 기록과의 대조
| 기존 기록 | 내용 | 대조 결과 |
|---|---|---|
| `MOF_LSM_project/notes/decisions.md:26–28` | "관측 SOS 자체의 불확실성이 큼 … Peano 2021도 위성 3종 사용" | **확인됨 (직접 지지)** — 위성 3종(LAI3g·MODIS·CGLS)으로 관측 불확실성을 고려(§2.1, §4.2). 제품 간 GSS **방향**은 원문 안에서 충돌(C1). 이 논문의 GSS는 월 해상도·20% 문턱 정의 |

## §4. peano2025_bg — 3.1 기존 기록과의 대조
원래 위치: `/Volumes/data01/notes/literature/papers/peano2025_bg.md` · 이동 2026-10-15

> 검토 상태: GPT 검토 반영 v2 (gpt-6.1-sol/high; #R18 — '직접 지지'와 '부분 지지(맥락)' 분리).

## 3.1 기존 기록과의 대조
| 기존 기록 | 내용 | 대조 결과 |
|---|---|---|
| `MOF_LSM_project/notes/decisions.md:28` | "관측 SOS 자체의 불확실성이 큼 … 위성 3종 사용" | "위성 3종 사용"은 **직접 지지**(Part 2도 3종, 기준 CGLS). "관측 SOS 자체의 불확실성이 큼"은 **부분 지지(맥락)** — 이 논문은 SOS가 아니라 peak·trough를 평가하고, 겨울 결측(C8)은 trough와 연결됨 |

## §5. orsolini2019_tc — 3.1 기존 기록과의 대조
원래 위치: `/Volumes/data01/notes/literature/papers/orsolini2019_tc.md` · 이동 2026-10-15

> 검토 상태: GPT 검토 반영 v2 (gpt-6.1-sol/high; #R14·#R15로 v1 판정을 '적용상의 추론'·'불확실성 영향 범위의 부분 지지'로 축소).

## 3.1 기존 기록과의 대조
| 기존 기록 | 내용 | 대조 결과 |
|---|---|---|
| `MOF_LSM_project/notes/decisions.md:15` | SWE 관측 = ERA5-Land 월 `sd` | 이 논문은 **시험용 ERA5L-CTRL(공식 출시 전 구성)의 눈깊이**를 **TP 33개 관측소**와 비교해 크게 과대(8.54 vs 0.23 cm)였고 과다 강설이 주원인 후보라 보고. **공식 ERA5-Land의 SWE를 직접 검증하지 않음** → "고산에서 ERA5-Land SWE 기준 자료가 과대일 수 있다"는 **적용상의 추론**(편향 방향·크기를 이 논문으로 확인한 것은 아님; 연구자 판단 필요) |
| `MOF_LSM_project/notes/decisions.md:20` | "산악(>1500 m) 모델 SWE 과소(vs ERA5-Land)는 모델 결함으로 쓰지 않음 … forcing에 민감한 영역" | **부분 지지 — "기준 재분석과 기상 강제의 불확실성도 비교에 영향을 줄 수 있다"는 범위에서만**. SNF50은 강설 강제에 대한 눈깊이 민감도를 보일 뿐, NH 산악 전체·1500 m 초과 영역·특정 모델의 SWE 과소 원인을 시험하지 않음(이 논문의 1500 m는 ERA5 IMS 동화 제외 기준). "모델 결함으로 쓰지 않음" 결정 자체를 입증하지 않음 |

## §6. 비교 보고서 2절 관계표 행 — shevliakova2024 관계표
원래 위치: `/Volumes/data01/notes/literature/reports/2026-10-15_six_paper_test.html` · 이동 2026-10-15

> 보고서 2절(논문별 관계 판정)에서 이동. 판정 근거는 위키 노트 2.2·해당 3.1 이동 항목.

```html
<tr><td>MOF decisions:22 (낙엽송 LMA 0.038)</td><td><span class="tag">범위 축소</span> 낙엽송의 직접 근거가 아님</td></tr>
```

## §7. 비교 보고서 2절 관계표 행 — weng2015 관계표
원래 위치: `/Volumes/data01/notes/literature/reports/2026-10-15_six_paper_test.html` · 이동 2026-10-15

> 보고서 2절(논문별 관계 판정)에서 이동. 판정 근거는 위키 노트 2.2·해당 3.1 이동 항목.

```html
<tr><td>MOF findings:55–56 (20일 평활, 문턱 출처)</td><td><span class="tag">변경 없음</span> 기존 기록과 일치(재확인)</td></tr>
```

## §8. 비교 보고서 2절 관계표 행 — peano2021 관계표
원래 위치: `/Volumes/data01/notes/literature/reports/2026-10-15_six_paper_test.html` · 이동 2026-10-15

> 보고서 2절(논문별 관계 판정)에서 이동. 판정 근거는 위키 노트 2.2·해당 3.1 이동 항목.

```html
<tr><td>MOF decisions:26–28 (관측 SOS 불확실)</td><td><span class="tag">강화</span> 위성 3종 사용은 직접 지지</td></tr>
```

## §9. 비교 보고서 2절 관계표 행 — orsolini2019 관계표
원래 위치: `/Volumes/data01/notes/literature/reports/2026-10-15_six_paper_test.html` · 이동 2026-10-15

> 보고서 2절(논문별 관계 판정)에서 이동. 판정 근거는 위키 노트 2.2·해당 3.1 이동 항목.

```html
<tr><td>MOF decisions:20 (산악 SWE 과소를 모델 결함으로 쓰지 않음)</td><td><span class="tag">부분 지지</span> "기준 자료·강제 불확실성도 비교에 영향" 범위만. 공식 ERA5-Land SWE를 검증한 것은 아님</td></tr>
```

## §10. 비교 보고서 4절 — MOF 결론(원문 그대로)
원래 위치: `/Volumes/data01/notes/literature/reports/2026-10-15_six_paper_test.html` · 이동 2026-10-15

> 4절 전체(MOF·SAH 포함)를 그대로 보존. SAH 부분은 SAH 노트에도 복사.

```html
<h2>4. 연구에 바로 쓰이는 결론</h2>
<div class="card">
<b>MOF (LM4+ phenology·눈)</b>
<ul>
<li>코드의 <code>tc_pheno</code> 20일 평활과 10 °C 끄기는 Weng 2015 식과 맞아요. 다만 <b>320 °C·day, 10 °C의 관측 근거는 문헌에 없어요</b>. 코드 기본값 360, 낙엽송 180은 Weng과도 달라서 출처 미확인이에요.</li>
<li>위성 phenology는 제품·정의(20% 문턱, 최대 월, 사인 위상)·고위도 겨울 결측에 따라 달라요. 그래서 <b>"SOS 일수로 튜닝하지 않고 플럭스로 판정"하는 방향이 문헌으로 지지돼요</b>.</li>
<li>낙엽송 LMA 0.038은 <b>붉은단풍(Weng)·온대 수목(LM4.1) 값</b>이에요. 낙엽송 고유 근거가 필요해요.</li>
<li>ERA5-Land를 산악 SWE 기준으로 쓸 때는 TP의 ERA5 계열 강설 과다 사례를 주의해야 해요(공식 ERA5-Land SWE 검증 문헌은 아직 없음).</li>
</ul>
<b>SAH</b>
<ul>
<li>Yang 2024(별도 노트)의 "봄 선행" 주장은 실험으로 분리되지 않았어요. LBM/SWM에서 안 나온다고 관계가 없는 건 아니지만, 원 논문의 근거도 여름 가열이에요.</li>
<li>TP 눈 자료를 쓸 때 재분석·예보 모델의 눈 과대(강설 과다)를 감안해야 해요.</li>
</ul>
</div>
```

## §11. 위키 issues L-39 ⑤ — lm4P 코드 확인의 MOF 쪽 근거 (2026-10-16)
위키에는 공개 코드의 식 구조만 두고, 내부 경로·MOF 설정값은 여기 둔다(O-10 기준).
- 대상 코드: `lm4/patches/phenoff_work/*.orig` = MOF 패치 적용 전 lm4P 사본(upstream 저장소와 동일성 대조 안 함).
  - `vegn_dynamics.F90.orig:1969–2056` `vegn_phenology_lm3`(월 1회, `.not.do_ppa`; `vegetation.F90.orig:2784–2786`)
  - `vegn_dynamics.F90.orig:2061–2228` `vegn_phenology_ppa`(매일, `do_ppa`; `vegetation.F90.orig:2776`), 켜기·끄기 `:2112–2143`
  - GDD 누적 `vegetation.F90.orig:2659–2661`(군락 공기 온도 일 최저·최고 `:2270–2271`), `tc_pheno` 평활 `:2664`
  - 기본값 `vegn_data.F90.orig:261–263`: `tc_crit` 283.16 K, `gdd_crit` 360, `gdd_base_T` 273.16 K
- **MOF 실행 설정** `lm4/config/field_table.ctl`(offline_fast도 같음): larix `gdd_crit = 180`, `tc_crit = 278.15`(:2283–2284); c3grass 같은 값(:2513–2514); acer·c4grass는 기본값(360, 10 °C); picea·prioria 상록.
- 비교: Weng 2015 320 °C·day / 코드 기본값 360 / MOF larix·c3grass 180. 180은 Botta 2000 모델 2a 냉량 낙엽활엽수림 180 ± 72(0 °C)와 수치만 같고 누적 정의가 다름(이동창 vs 낙엽 후 누적) — 출처 미확인.
- **실행 경로 확인 (2026-10-16, 서버 grep)**: `climate:/data2/ydkoh/lm4/RUN/*/input.nml` 11개 런 전부 `do_ppa = .TRUE.`(:1766; lm4_offline_probe만 :1762) — ctl_1979-2024·ctl2_co2·lufix·spinup30·replant 포함. 주요 3런(ctl·ctl2_co2·lufix)은 `do_phenology = .TRUE.`(:1808). → **MOF 실행의 phenology = `vegn_phenology_ppa`(GDD 경로)로 확정**, `vegn_phenology_lm3`는 쓰이지 않음. 분석·개선은 PPA 루틴 중심.
- 연구 함의: GDD에 달력 시작일이 없어 가을 낙엽 뒤 0 °C 넘는 날이 모두 이듬해 개엽 GDD에 들어감 → "SOS 오차 vs 직전 가을·겨울 기온" 상관 분석과 직접 연결.

## 변경 이력
- 2026-10-16 v3 (Claude): §11 한계 닫음 — 서버 input.nml 11개 런 `do_ppa = .TRUE.` 확인. 사용자 결정: PPA 중점.
- 2026-10-16 v2 (Claude, 사용자 요청 "MOF 폴더에서 확인"): §11 추가 — 위키 L-39 ⑤의 내부 경로·MOF 설정값.
- 2026-10-15 v1 (Claude, 사용자 결정): 위키에서 분리해 생성. 위키 쪽 변경 이력은 각 노트 끝과 issues.md O-10.
