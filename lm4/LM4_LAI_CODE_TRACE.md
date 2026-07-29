# LM4P 역학식생 LAI — 코드 추적

> 소스: `/data2/ydkoh/lm4/esm4p5-lm4p-offline/src/lm4P/` (climate00). 행번호는 2026-07-29 확인 기준.
> 이 문서만 보고 코드를 열지 않아도 확인 가능하도록 작성. 요약은 `LM4_SPINUP_NOTES.md` §13.29.

## 0. 한 줄 요약

**LAI는 예후변수가 아니다.** 예후변수는 `bl`(잎 탄소량, kg C/individual)이고, **LAI는 매 스텝 `bl`을 `LMA`로 나눠 만드는 진단량**이다. 따라서 "LAI가 왜 이런가"는 항상 **"`bl`이 왜 이런가"**로 내려가야 한다.

```
NSC(비구조탄수화물) --배분--> bl(잎 탄소) --÷LMA--> leafarea --÷crownarea--> cc%lai
                                   ^                                            |
                                   |                                            v
                            phenology(낙엽/개엽)                     복사·광합성·기공전도도
```

## 1. 변수 정의

| 위치 | 내용 |
|---|---|
| `vegetation/vegn_cohort.F90:89` | `real :: lai = 0.0 ! leaf area index, m2/m2` — **코호트 구조체의 멤버** |
| `vegetation/vegn_data.F90:220` | `real :: LMA = 0.036 ! leaf mass per unit area, kg C/m2` — **종별 상수** |
| `vegetation/vegn_data.F90:1259` | `sp%LMA = 1.0/specific_leaf_area` — namelist에서 SLA로 줘도 됨 |
| `vegetation/vegn_data.F90:520` | `min_lai_pheno = 1e-5` — 낙엽이 이 아래로 떨어뜨리면 0 처리 |

## 2. 핵심 식 — `vegn_cohort.F90:567-578`

```fortran
function leaf_area_from_biomass(bl, species, layer, firstlayer) result (area)
  if (layer > 1 .AND. firstlayer == 0) then
     area = bl/(spdata(species)%LMA_understory_factor*spdata(species)%LMA)  ! 하층엽은 더 얇음
  else
     area = bl/spdata(species)%LMA
  endif
end function
```

**개체당 잎면적 = 잎 탄소량 / LMA.** 하층(understory) 코호트는 `LMA_understory_factor`로 잎을 더 얇게 만들어 같은 탄소로 더 넓은 면적을 얻는다(음지적응).

## 3. 코호트 LAI 확정 — `vegetation.F90:2307-2530` (`update_derived_vegn_data`)

계산 본체는 **2416-2424**:

```fortran
cc%layerfrac = cc%crownarea*cc%nindivs*(1-spdata(sp)%internal_gap_frac)/scale
cc%leafarea  = leaf_area_from_biomass(cc%bl, sp, cc%layer, cc%firstlayer)
cc%lai       = cc%leafarea/(cc%crownarea*(1-spdata(sp)%internal_gap_frac))*scale
if(cc%lai < min_lai) then
   cc%leafarea = 0.0 ;  cc%lai = 0.0
endif
```

- `crownarea`로 나눠 **"수관 안에서 본 LAI"**로 변환. `internal_gap_frac`은 수관 내부 빈틈.
- `scale`은 PPA 층별 캐노피 신축 보정 (`scale_g` 초본 / `scale_t` 목본, 2408-2412).
- **2429**: `sp >= NSPECIES`(LM2 계열 종)이면 계산하지 않고 **처방값** `spdata(sp)%dat_lai` 사용. lm4P 7종은 여기 해당 없음.

## 4. `bl`이 변하는 지점 (실제 동역학)

| 과정 | 위치 | 코드 |
|---|---|---|
| **성장(배분)** | `vegn_dynamics.F90:1710` | `cc%bl = cc%bl + deltaBL` |
| 목표 상한 | `vegn_dynamics.F90:1692-1701` | `G_LFR = max(0, min(cc%bl_max - cc%bl + ..., G_LFR))` |
| 일일 증가 상한 | `vegn_dynamics.F90:1690` | `G_LFR = min(G_LFR, deltaLAI_max*sp%LMA*cc%crownarea)` |
| **낙엽** | `vegn_dynamics.F90:2188` | `cc%bl = cc%bl - dead_leaves_C` |
| 낙엽 후 즉시 LAI 갱신 | `vegn_dynamics.F90:2192-2193` | `cc%lai = leaf_area_from_biomass(...)/(crownarea*(1-gap))` |
| LM3 경로 전량 낙엽 | `vegn_dynamics.F90:2036-2038` | `cc%bl = 0.0; cc%lai = 0.0` |
| 교란·솎음 | `vegn_dynamics.F90:1338` | `cc%bl = (1-f)*cc%bl` |

**목표 잎량** (`vegn_dynamics.F90:2117`, 초본 기준):
```fortran
cc%bl_max = sp%LMA * sp%laimax * cc%crownarea * (1.0-sp%internal_gap_frac)
```
→ **종별 `laimax`가 LAI 천장을 결정**한다. LAI 편차 진단 시 1순위로 볼 파라미터.

## 5. 개엽/낙엽 스위치 — `vegn_dynamics.F90:2061-2228` (`vegn_phenology_ppa`)

트리거는 **2109-2135**:

```fortran
if (sp%phent==PHEN_EVERGREEN) then
   cc%status = LEAF_ON ; cycle          ! 상록수는 항상 ON, 아래 판정 안 함
endif

wilt       = soil%w_wilt(1)/soil%pars%vwc_sat
theta_crit = max(0, min(1, sp%cnst_crit_phen + wilt*sp%fact_crit_phen))
drought    = (sp%psi_stress_crit_phen <= 0 .and. cc%theta_av_phen  < theta_crit) &
        .or. (sp%psi_stress_crit_phen  > 0 .and. cc%psist_av_phen > sp%psi_stress_crit_phen)

case (LEAF_OFF):  gdd > gdd_crit .and. tc_pheno >= tc_crit .and. .not.drought  →  LEAF_ON
case (LEAF_ON) :  tc_pheno < tc_crit  →  LEAF_OFF  (한랭낙엽, gdd 리셋)
                  drought            →  LEAF_OFF  (건조낙엽, gdd 리셋 안 함)
```

- **건조낙엽에서 gdd를 리셋하지 않는 이유가 소스 주석에 명시**: 리셋하면 아열대 건조지에서 임계 적산온도를 다시 못 채워 잎이 영영 안 나옴.
- 개엽 시 초본은 `bl_max`·`br_max`를 그 해 조건으로 재설정(2117-2118) — 전년 목표 재사용 방지.

## 6. 저장

**restart**: 코호트 구조체가 `RESTART/vegn1.res.tile*.nc`에 코호트 단위로 저장된다.
**★ LAI는 restart에 없다** — `bl`만 저장되고 LAI는 재시작 시 다시 계산된다. 그래서 warm start 후 LAI는 즉시 복원된다(§13.21의 tile/cohort 구조 확인이 유효했던 이유).

**진단 출력 2종** (`vegetation.F90`):

| 스트림 | 등록 | 송출 | 정의 |
|---|---|---|---|
| native `lai` (`land_month`) | `:915` `register_cohort_diag_field('lai')` | **`:2120`** `send_cohort_data(id_lai, c%lai, weight=c%layerfrac, op=OP_SUM)` | 코호트 LAI를 **층분율 가중 합** |
| CMIP `lai` (`land_month_cmip`) | `:1225` `register_tiled_diag_field(cmor_name,'lai')` | **`:2138`** `send_tile_data(id_lai_cmor, sum(c%nindivs*c%leafarea))` | **Σ(개체수 × 개체잎면적)** = 지면 단위면적당 총 잎면적 |

**★★ 두 `lai`는 같은 양이 아니다. §7 참조.**

## 7. ★★ native `lai` vs CMIP `lai` — 정의 차이 (함정)

| | native (`land_month`) | CMIP (`land_month_cmip`) |
|---|---|---|
| 계산 | `Σ_cohort (cc%lai × cc%layerfrac)` | `Σ_cohort (cc%nindivs × cc%leafarea)` |
| `cc%lai`에 이미 들어간 보정 | `crownarea`·`internal_gap_frac`·`scale`(층 신축) | 없음 (원시 잎면적) |
| 물리적 의미 | 수관 내부 LAI를 층분율로 가중 | **지면 단위면적당 총 잎면적** |
| 관측(GIMMS/MODIS) 정의와의 대응 | 간접 | **직접 대응** |

**우리가 지금까지 쓴 것 = native.** `lm4/scripts/extract_lm4_lai_years.py:35`·`extract_monthly_11yr.py:45` 둘 다 `land_month`를 읽는다 → §13.24(bias +0.69, r 0.66)·§13.25(LAI 궤적)·§13.26(1° r 0.71, bias +0.61)이 **전부 native 기준**이다.

### 실측 (1995, 11개월, `lm4/scripts/cmp_lai_native_vs_cmip.py`)

| | native | cmip |
|---|---|---|
| 유효 육지 격자 | **17,306** | **18,704** |
| 전지구 평균 | **2.2822** | **2.0721** |
| 공통격자 평균 | 2.2822 | 2.2395 (**−1.9 %**) |
| 상관 | **0.9977** | |
| 비율 cmip/native | median **0.9990**, p5 0.9200, p95 1.0000 | |

**결론 두 가지**:
1. **값 자체는 거의 같다** (공통격자 r=0.998, 중앙값 비율 0.999). `scale`(층 신축) 보정 때문에 다층 코호트에서만 native가 최대 4.8 더 큰 꼬리가 생긴다(p5=0.92). → **§13.24·§13.26의 bias·상관 결론은 스트림 선택에 거의 영향받지 않는다. 재계산 불필요.**
2. **★ 진짜 차이는 마스크다.** cmip은 등록 시 `fill_missing = .TRUE.`(`vegetation.F90:1227`)라 **식생 없는 격자를 결측이 아니라 0으로 채운다** → 유효격자가 1,398개 많고, 그 0들이 전지구 평균을 **2.28 → 2.07 (−9 %)** 로 끌어내린다.

**실무 규칙**:
- **전지구 평균 LAI를 말할 때는 반드시 스트림과 마스크를 명시**할 것. §13.24의 "전지구 JJA LAI 2.37→2.50"은 **native 기준**이다.
- 관측 비교(GIMMS)는 어차피 GIMMS 유효격자에서만 계산하므로 cmip의 0-채움 격자가 끼어들지 않는다 → 기존 결과 유효.
- CMIP 아카이브 제출·ILAMB 입력에는 **cmip 스트림**(표준 정의·`fill_missing`)을 쓸 것.

## 8. LAI가 소비되는 곳

| 소비처 | 위치 | 용도 |
|---|---|---|
| **복사** | `vegn_radiation.F90:199` | `vegn_lai = cohort%lai` |
| | `:242` | `fs = cohort%lai*fs/(cohort%lai+cohort%sai)` — 잎/줄기 배분 |
| | `:256-258` | `vegn_idx = max(lai,sai)` 또는 `lai` — 소산 계산 |
| **광합성** | `vegn_photosynthesis.F90:276` | `if (cohort%lai <= 0)` → 광합성 건너뜀 |
| | `:298` | `gs_Leuning(PAR_dn, PAR_net, Tv, ds, cohort%lai, ...)` |
| | **`:380`** | **`stomatal_cond = stomatal_cond * cohort%lai`** |

**`:380`이 물수지 연쇄의 시작점**이다. 기공전도도가 LAI에 **정비례**하므로:

```
LAI ↑ → 기공전도도 ↑ → 증산(transp) ↑ → 토양수분 ↓ → 유출(runf) ↓
```

§13.25에서 관측한 **LAI +9.4% ↔ runoff −12.7%**가 정확히 이 경로다. 유출 편차를 진단할 때 LAI를 먼저 볼 근거.

## 9. 위도마다 다른 식인가 → **아니다**

**코드 어디에도 위도 항이 없다.** 전 지구 동일한 식을 쓴다. 위도 효과는 전부 간접적으로 들어온다:

| 경로 | 실체 |
|---|---|
| ① **종 분포** | `cover_type.nc`로 처방. `do_biogeography=.FALSE.`라 모델이 못 바꿈 (§13.20) |
| ② **종별 파라미터** | `LMA` · `laimax` · `tc_crit` · `gdd_crit` · `phent`(상록/낙엽) |
| ③ **국지 기후** | `vegn%tc_pheno`(한랭월 기온) · `cc%gdd`(적산온도) · 토양수분(`theta_av_phen`) |

**해석상 중요**: "고위도라서 LAI가 낮다"가 아니라 **"고위도에 배치된 종(picea)의 파라미터 + 그 격자의 낮은 기온·적산온도가 낮은 LAI를 만든다"**이다.

그래서 §13.26의 **아북극 LAI 과소편차**는 원인이 셋으로 갈리고 손잡이가 각각 다르다:
1. 종 배치가 틀림 → `cover_type.nc` (또는 `do_biogeography` 켜기)
2. 종 파라미터가 틀림 → `laimax`·`LMA`
3. phenology가 늦게 켜짐 → `gdd_crit`·`tc_crit`

**열대 과대편차**도 같은 방식으로 분해된다(주로 2번 `laimax` 의심).

## 10. ★★★ 다른 변수로 확대 — `mrro`는 native `runf`와 37% 다르다 (2026-07-29)

같은 방식으로 유출·토양수분을 비교(`lm4/scripts/cmp_native_vs_cmip_streams.py`, 1995, 11개월):

| 물리량 | native | cmip | 공통격자 corr | 차이 | 격자수 nat/cmip |
|---|---|---|---|---|---|
| LAI | `lai` 2.282 | `lai` 2.240 | 0.9977 | −1.9 % | 17,306 / 18,704 |
| **총 유출** | **`runf` 8.504e-6** | **`mrro` 5.340e-6** | **0.9178** | **−37.2 %** | **18,704 / 18,704** |
| 지표 유출 | `soil_rie+soil_rsn` 4.752e-6 | `mrros` 4.601e-6 | 0.9915 | −3.2 % | 17,306 / 18,704 |
| 토양수분 | `water_soil` 3397 | `mrso` 3312 | 0.9537 | −2.5 % | 17,306 / 18,704 |

**★ 총 유출만 격자 수가 같은데도 37% 차이** → 마스크가 아니라 **정의(구성 성분)가 다르다.** 소스에서 확인:

```fortran
! native runf  — land_model.F90:2550
call send_tile_data(id_runf, snow_lrunf + snow_frunf + subs_lrunf, tile%diag)
!                            눈 액체유출 + 눈 고체유출 + 하부면 액체유출(토양·빙하·호수 전 타일)

! CMIP mrro   — soil.F90:2996
call send_tile_data(id_mrro, lrunf_ie + lrunf_sn + lrunf_bf + lrunf_nu, diag)
!                            침투초과 + 포화 + 기저유출 + 수치포화잉여  (soil.F90 = 토양 타일)
```

- **`mrro`에는 고체(빙설) 유출 `snow_frunf`가 없다.** §13.24에서 `frunf`를 따로 봐야 한다고 한 그 성분.
- **`mrro`는 soil 모듈에서 송출**되므로 빙하·호수 타일 기여가 빠진다. 남극·그린란드가 큰 전지구 평균에서 이 차이가 −37 %로 나타난다.
- corr도 0.918로 다른 변수(0.95~0.998)보다 낮다 → 공간 패턴까지 다르다(빙설 지역에서 벌어짐).

**★ 실무 규칙 (담수유출은 과제 핵심이라 특히 중요)**
1. **"총 유출"을 인용할 때 반드시 `runf`인지 `mrro`인지 밝힐 것.** 37 %는 모델 간 차이보다 클 수 있다.
2. **해양으로 가는 담수 총량**을 볼 때는 고체 유출이 포함돼야 하므로 **native `runf`**(또는 `runf` 성분 분해 + `frunf`)가 맞다.
3. **CMIP 아카이브·ILAMB·다른 모델과의 표준 비교**에는 `mrro`를 쓰되, **정의상 빙설·빙하 기여가 빠져 있음을 명시**할 것.
4. 앞으로 새 변수를 쓸 때마다 이 스크립트로 **native/cmip 쌍을 먼저 대조**할 것. 이름이 같다고 같은 양이 아니다.
