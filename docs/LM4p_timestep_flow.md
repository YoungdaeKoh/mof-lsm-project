# LM4p 계산 흐름 — 대기 forcing을 받아서 대기로 돌려보내기까지

작성 2026-10-03. 대상: KIOST-ESM2의 lm4P (우리 offline 설정: `do_ppa=T`, `do_cohort_dynamics=T`, `do_patch_disturbance=T`,
`do_phenology=T`, `do_biogeography=F`, 질소 off, `photosynthesis_to_use='leuning'`, `albedo_to_use='brdf-params'`).
호출 순서는 소스에서 직접 추출(`src/lm4P/land_model.F90`, `vegetation/vegetation.F90`, `src/coupler/full/*`).
식은 이해용으로 단순화한 형태 — 실제 코드는 보정항이 더 많다. "(확인 필요)"는 소스로 끝까지 추적하지 않은 부분.

시간 규모 세 개:
- **fast = 30분** (`dt_atmos=1800`): 물·에너지·광합성. 매 스텝.
- **slow = 1시간** (`dt_cpld=3600`) 안에서 **하루/한 달/한 해가 바뀔 때만** 식생 구조(생장·사망·계절·번식) 갱신.
- 하천은 fast 끝에 매번.

---

## 0. 전체 흐름 한 장

```
 [ATMOSPHERE / FORCING]  (offline: WFDE5 via data_override, coupler_main.F90:797,863)
   T_bot, q_bot, p_surf, u_bot, v_bot, SW (vis/nir, dir/dif), LW_down, rain, snow, coszen, CO2
        |
        v
 (A) sfc_boundary_layer  ── coupler: turbulence coefficients on the exchange grid
 (B) flux_down_from_atmos ── coupler: radiation + precipitation handed to land
        |
        v
 ================= update_land_model_fast  (every 30 min, land_model.F90:1166) =================
 (C) groundwater exchange between tiles in a grid cell (hlsp_hydrology_1)
 for each grid cell, for each tile:  update_land_model_fast_0d  (land_model.F90:1446)
   (1) step_1 of the substrate  : soil_step_1 / lake_step_1 / glac_step_1   -> heat-conduction coefficients
   (2) snow_step_1              : snow heat-conduction coefficients
   (3) land_turbulence          : canopy-air <-> atmosphere, canopy-air <-> leaves/ground resistances
   (4) vegn_step_1              : soil-water supply -> PHOTOSYNTHESIS + STOMATA per cohort -> transpiration terms
   (5) qscomp / land_lw_balance : saturation humidity, longwave balance of leaves and ground
   (6) land_surface_energy_balance : solve ONE linear system for
                                    canopy-air T & q, leaf T, ground T, snow/ice melt  (implicit)
   (7) vegn_step_2              : update canopy water/snow on leaves, leaf temperature
   (8) snow_step_2              : snowpack mass/heat, melt, refreeze, compaction
   (9) soil_step_2 (or lake/glac): soil heat + water (Richards-type), infiltration, runoff, drainage
  (10) vegn_step_3              : carbon integration: add photosynthesis to each cohort's store (NSC)
  (11) soil_step_3              : soil-carbon diagnostics            (12) update_fire_fast
  (13) update_cana_tracers      : canopy-air CO2 and other tracers
  (14) update_land_bc_fast      : prepare surface state to send back (T_surf, albedo, roughness, q, CO2)
 end tiles
 (15) update_river              : route runoff through the river network -> discharge to ocean
 ==============================================================================================
        |
        v
 (D) flux_up_to_atmos (coupler) : final sensible/latent/LW-up fluxes, land diagnostics, stocks
 (E) flux_land_to_ice           : river discharge + calving -> ocean/ice side
        |
        v
 [BACK TO ATMOSPHERE]  sensible heat H, latent heat LE (evaporation E), upward LW, surface albedo,
                       roughness, canopy-air humidity and CO2 (net ecosystem CO2 exchange)
 [TO OCEAN]           river discharge (liquid + frozen)

 ================= update_land_model_slow  (every 1 h, land_model.F90:2782) =====================
  vegn_nat_mortality_ppa, fire_transitions, land_transitions (land use; off in lufix)
  update_vegn_slow (vegetation.F90:2602):
    every new MONTH : fire data, fuel, (LM3-mode phenology)
    every new DAY   : vegn_growth (allocate stored carbon to leaf/root/sapwood/wood),
                      starvation, PPA phenology, kill tiny cohorts, harvest
    every new YEAR  : annual climate stats, [biogeography: OFF], peat, disturbance,
                      reproduction / relayer cohorts by height / merge similar cohorts
  update_land_bc_slow
```

---

## 1. 받는 것 — 대기 forcing (A, B)

| 받는 양 | 기호 | 우리 offline 출처 |
|---|---|---|
| 최하층 기온, 비습, 기압, 바람 | T_a, q_a, p_s, u, v | WFDE5 (data_table `"ATM","t_bot"` 등) |
| 단파 복사 (가시·근적외 × 직달·산란) | SW↓ | WFDE5 `flux_sw` 10종 |
| 장파 복사 | LW↓ | WFDE5 `flux_lw` |
| 비, 눈 | P_l, P_s | WFDE5 `lprec`, `fprec` |
| 태양천정각 | cos z | WFDE5 `coszen` |
| CO₂ | — | 얼어붙은 대기 최하층 값 (override 없음) |

- **(A) `sfc_boundary_layer`**: 대기 최하층과 지표 사이의 **난류 교환 계수**를 Monin–Obukhov 상사 이론으로 계산.
  - 플럭스 기본형: **H = ρ c_p C_H |u| (T_s − T_a)**, **E = ρ C_E |u| (q_s − q_a)**
  - C_H, C_E는 대기 안정도(리처드슨 수)와 거칠기 길이 z₀에 따라 달라짐.
- **(B) `flux_down_from_atmos`**: 복사·강수를 지면 격자로 넘겨줌.
- 참고: Monin & Obukhov (1954); GFDL 결합기 구조 Balaji et al. (2006, FMS) (확인 필요).

## 2. 30분 스텝 안의 계산 (C, 1–15)

### (C) 타일 사이 지하수 교환 — `hlsp_hydrology_1`
한 격자 안의 타일(자연·농지·2차림 등)과 고도대 사이에 지하수를 옮김. Milly et al. (2014) LM3 수문.

### (1)(2) 토양·눈 열전도 준비 — `soil_step_1`, `snow_step_1`
각 층의 열용량·열전도도를 계산해 **지면 온도 방정식의 계수**를 만든다. 실제 온도는 (6)에서 한꺼번에 풂.
- 열전도: **C ∂T/∂t = ∂/∂z (λ ∂T/∂z)**, λ는 수분·얼음 함량의 함수.

### (3) 캐노피 난류 — `land_turbulence` (+ `cana_v_turb`, `cana_g_turb`, `surface_resistances`)
LM4는 **캐노피 공기(canopy air)**라는 중간 저장소를 둔다.
```
 atmosphere  --r_a-->  canopy air (T_ca, q_ca, CO2_ca)  --r_v--> leaves (T_v)
                                                       --r_g--> ground/snow (T_g)
```
- 각 화살표가 저항. 잎 쪽은 **기공 저항 r_s**가 더해짐 (4에서 계산).
- 참고: LM3 캐노피 공기 구조 Milly et al. (2014); Shevliakova et al. (2009) (확인 필요).

### (4) 광합성과 기공 — `vegn_step_1` → `soil_data_beta`, `vegn_photosynthesis`
cohort(나무 크기 무리)마다:
1. **토양수분 공급 β** (`soil_data_beta`): 뿌리 분포 × 토양수분 → 얼마나 물을 뽑을 수 있나. 가뭄이면 β↓.
2. **광합성** (`photosynthesis_to_use='leuning'`): Collatz et al. (1991, C3; 1992, C4) 형의 Farquhar 계열 광합성
   - **A = min(J_c, J_e, J_s) − R_d** — Rubisco 제한, 빛 제한, 산물 수송 제한 중 가장 작은 것.
3. **기공** — 단순화된 Leuning (1995):
   - **g_s = g₀ + m · A / [(c_s − Γ*) (1 + D_s / D₀)]**
   - c_s = 잎 표면 CO₂, D_s = 수증기압차. 광합성↑ → 기공 열림, 공기 건조 → 닫힘.
4. 여기에 β(물 부족)를 곱해 **증산 E_t**와 잎 수분 관련 미분항을 만든다. 식물 수리학 변수(뿌리·물관·잎 수포텐셜 ψ_r, ψ_x, ψ_l)도 이 단계.
- 참고: Collatz et al. (1991, 1992); Leuning (1995); LM3 광합성 Shevliakova et al. (2009); PPA 캐노피 층 Weng et al. (2015).

### (5) 포화 습도, 장파 — `qscomp`, `land_lw_balance`
- 포화 비습 q_sat(T) (Clausius–Clapeyron). **우리 offline 패치 `qscomp clamp`가 여기** (온도 범위 밖이면 잘라 줌).
- 잎·지면의 장파 흡수/방출: **LW↑ = ε σ T⁴** (+ 반사분).

### (6) ★ 에너지 수지를 한 번에 풂 — `land_surface_energy_balance` (+ `ludcmp`/`lubksb`)
LM4의 핵심. 잎·지면·캐노피 공기 각각의 에너지·수분 수지를 **연립 일차방정식**(행렬 A X = B)으로 세워
**캐노피 공기 T·q, 잎 온도, 지면 온도, 눈·얼음 융해량**을 30분 동안 **암시적(implicit)으로 동시에** 푼다.
- 각 표면의 수지: **R_net = H + LE + G (+ 융해 잠열)**
  - R_net = 순복사(SW 흡수 + LW 흡수 − LW 방출), H = 현열, LE = 잠열(증발×기화열), G = 땅속 열.
- 미분항(∂E/∂T 등)을 써서 선형화 → 한 번에 풂. 그래서 시간 간격을 크게 잡아도 안정.
- 참고: Milly et al. (2014) LM3; Zhao et al. (2018) LM4.0 (확인 필요).

### (7)(8)(9) 각 저장소 갱신 — `vegn_step_2`, `snow_step_2`, `soil_step_2`
(6)에서 구한 온도·플럭스로 상태를 실제로 바꿈.
- **잎**: 잎에 맺힌 물·눈(차단), 잎 온도.
- **눈**: 적설량, 융해·재동결, 다짐.
- **토양**: 열 + 물. 물은 Richards 방정식 형태:
  - **∂θ/∂t = ∂/∂z [K(θ)(∂ψ/∂z − 1)] − S(뿌리흡수)**
  - 지표 침투, **지표 유출**, 바닥 배수/기저유출(지하수 → 하천).
- 참고: Milly et al. (2014) LM3 토양수문.

### (10) 탄소 적분 — `vegn_step_3` → `vegn_carbon_int_ppa`
30분 동안의 광합성에서 호흡을 빼고(**NPP = GPP − R_a**) 각 cohort의 **저장 탄소(NSC)**에 쌓음.
실제로 잎·뿌리·줄기에 나누는 건 하루에 한 번(아래 slow). 질소 침착 호출은 있지만 질소 off라 무영향.
- 토양 유기물 분해(CENTURY-like): **dC/dt = 입력 − k · f(T) · f(θ) · C** (호출 위치 확인 필요).
- 참고: Weng et al. (2015); Shevliakova et al. (2009).

### (11)(12)(13) 진단·화재·캐노피 공기 트레이서
`soil_step_3`(토양탄소 진단 출력), `update_fire_fast`(화재 빠른 부분), `update_cana_tracers`(캐노피 공기의 CO₂·수증기 갱신 → 순 생태계 CO₂ 교환).

### (14) 대기로 돌려보낼 표면 상태 준비 — `update_land_bc_fast`
복사 온도 T_surf, 캐노피 공기 T·q·CO₂, **알베도**(`brdf-params`, 가시·근적외 × 직달·산란), 거칠기 길이, 방출률.

### (15) 하천 — `update_river`
모든 타일의 유출을 하천망으로 흘려 바다로 보냄(Milly et al. 2014의 하천 모델). 우리 진단의 `river_month` 출력이 여기서 나옴.

## 3. 돌려보내는 것 (D, E)

| 대기로 | 무엇 |
|---|---|
| 현열 H, 잠열 LE (증발 E) | `flux_up_to_atmos`에서 (14)의 상태로 최종 보정 |
| 상향 장파 LW↑, 지표 알베도 | 다음 스텝 대기 복사 계산용 |
| 거칠기, 캐노피 공기 q·CO₂ | 다음 스텝 난류·CO₂ 교환용 |

| 바다로 (`flux_land_to_ice`) | 하천 유출(액체 + 얼음) — 해양모델의 담수 유입 = 과제 핵심 경로 |

※ **우리 offline 설정**에서는 대기가 얼어 있어 이 값들을 받는 쪽이 없음. 그래서 B+C 패치가 "대기 격자로 옮기는 부분"만 생략해도
지면 결과가 비트 동일했다(LM4 notes §13.63). 지면 진단과 하천 유출은 그대로 계산·출력된다.

## 4. 느린 시간 규모 — 식생 구조 (slow, `update_vegn_slow`)

```
 every hour   : natural mortality (PPA), fire / land-use transitions (land use off in lufix)
 new MONTH    : fire data, fuel load, (phenology in LM3 mode only)
 new DAY      : vegn_growth      -> stored carbon (NSC) allocated to leaves, fine roots, sapwood, wood
                                    => LAI = leaf area of all cohorts; tree height/diameter grow (allometry)
                starvation       -> cohorts with too little NSC lose biomass / die
                phenology (PPA)  -> leaf-out / leaf-drop by temperature and soil water
                kill tiny cohorts, harvest (off in lufix)
 new YEAR     : annual climate statistics (t_ann, t_cold, p_ann, growing months)
                biogeography     -> OFF (do_biogeography=F): species would change by climate rules
                peat redistribution, disturbance
                reproduction     -> seeds become new small cohorts
                relayer cohorts  -> sort by height into canopy layers (PPA: tallest fill the canopy first)
                merge cohorts    -> combine similar cohorts to keep the count manageable
```
- **PPA (Perfect Plasticity Approximation)**: 키 큰 cohort부터 캐노피를 채우고, 캐노피가 차면 나머지는 그늘층.
  그늘층 cohort는 빛이 적어 광합성이 작고, 성장이 느리거나 굶어 죽는다(Purves et al. 2008; Weng et al. 2015).
- **알로메트리(allometry)**: 직경 D로 키와 수관 면적을 정함. 예: **H = a · D^b**, 수관 면적 = c · D^d (Weng et al. 2015).
- **우리 spin-up 문제와의 연결**: 목재(bwood)와 뿌리(cRoot)는 **하루 단위 배분 + 연 단위 사망·번식**의 결과라
  평형에 가는 데 수십~수백 년. 이게 LM4p spin-up이 느린 이유(LM4 notes §13.62–13.65).

---

## 5. 참고문헌

- Collatz, G. J. et al. (1991) Physiological and environmental regulation of stomatal conductance, photosynthesis and transpiration… *Agric. For. Meteorol.* 54.
- Collatz, G. J., Ribas-Carbo, M., Berry, J. A. (1992) Coupled photosynthesis–stomatal conductance model for leaves of C4 plants. *Aust. J. Plant Physiol.* 19.
- Farquhar, G. D., von Caemmerer, S., Berry, J. A. (1980) *Planta* 149.
- Leuning, R. (1995) A critical appraisal of a combined stomatal–photosynthesis model for C3 plants. *Plant Cell Environ.* 18.
- Milly, P. C. D. et al. (2014) An enhanced model of land water and energy for global hydrologic and earth-system studies (LM3). *J. Hydrometeorol.* 15.
- Monin, A. S., Obukhov, A. M. (1954) Basic laws of turbulent mixing in the surface layer of the atmosphere.
- Purves, D. W. et al. (2008) Predicting and understanding forest dynamics using a simple tractable model. *PNAS* 105.
- Shevliakova, E. et al. (2009) Carbon cycling under 300 years of land use change (LM3V). *GBC* 23.
- Weng, E. S. et al. (2015) Scaling from individual trees to forests… height-structured competition (LM3-PPA). *Biogeosciences* 12.
- Zhao, M. et al. (2018) The GFDL global atmosphere and land model AM4.0/LM4.0. *JAMES* 10.
- 우리 설정·패치: `lm4/LM4_SPINUP_NOTES.md` §13.11–13.20 (offline 구조), §13.63 (B+C 패치), §13.65 (가속·C–N).
