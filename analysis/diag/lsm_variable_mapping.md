# 다중 LSM 변수명 매핑표

> 대상 계층은 `lsm_core_variables.md`의 T1(보고서 축) · T2(내부 체크).
> 출처 = 각 모델 **실제 출력 파일 헤더 + 소스 코드**(2026-07-29 확인). 문서가 아니라 코드 기준.

| 모델 | 근거 | 비고 |
|---|---|---|
| **LM4+** | `19960101.land_month{,_cmip}.tile1.nc` (`lm4_spinup30`) + `src/lm4P/river/river.F90` | native 194변수 + **CMIP 표준명 스트림 별도 존재** |
| **CLM5** | LMWG `variable_master4.3.ncl` + `clm5_bgc_ad.mosart.h0.*` | 진단 표준명 = CLM 출력명 |
| **Noah-MP** | `199801020000.LDASOUT_DOMAIN1` (HRLDAS) | |
| **JULES** | `src/io/model_interface/variable_metadata.inc` (672 식별자) | 출력 12→**36변수로 확장**(2026-07-29) |

---

## ★ 핵심 발견 1: LM4는 이미 CMIP 표준명으로 쓰고 있다

`land_month_cmip` / `land_daily_cmip` 스트림이 **CMIP6 land 변수명 그대로** 출력 중입니다
(`mrro` `mrros` `mrso` `mrsos` `mrsol` `mrsfl` `mrsll` `tsl` `tran` `evspsblsoi` `evspsblveg` `snw` `snd` `snc` `snm` `lai` `gpp` `npp` `ra` `rh` `nbp` `cVeg` `cSoil` `cLitter` `treeFrac` `grassFrac` `cropFrac` `mrtws` `tasLut` …).

**의미**: 모델 간 공통 언어를 CLM 이름(LMWG)이 아니라 **CMIP 이름**으로 잡는 게 맞습니다.
- ILAMB이 먹는 게 CMIP 규격 → LM4는 **변환기가 사실상 불필요**(CLM은 `clm_to_mip`가 필요했던 그 단계).
- 따라서 아래 표의 기준열은 **CMIP 표준명**입니다.

## ★ 핵심 발견 2: "출력에 없다"와 "모델이 계산 안 한다"는 다르다

하천 방류를 "4개 모델 어디에도 없다"고 처음 판단했으나 **오판**이었습니다.
- **CLM5**: MOSART가 이미 방류를 출력 중이었음.
- **LM4**: river 모듈이 계속 돌고 있었고(`INPUT/river.res.tile*.nc` + `&river_nml`) `diag_table`에만 안 걸려 있었음 → 2026-07-29 추가.
- **JULES**: `frac`(타일 분율)·`ftl_gb`(현열) 등이 "없다"고 봤으나 소스엔 있었고 출력 프로파일에만 빠져 있었음.

→ **변수 부재를 보면 먼저 소스의 등록 목록(`register_diag_field` / `variable_metadata.inc`)과 restart/INPUT을 확인할 것.** 출력 헤더만으로 매핑표를 만들면 모델 능력을 과소평가하게 됩니다.

---

## T1 — 보고서 축

### T1-a 식생

| CMIP | 물리량 | LM4 (native) | LM4 (cmip) | CLM5 | Noah-MP | JULES |
|---|---|---|---|---|---|---|
| `lai` | 엽면적지수 | `lai` | `lai` | `TLAI` | `LAI` | `lai` |
| `gpp` | 총일차생산 | `gpp` | `gpp` | `GPP` | `GPP` | `gpp_gb` |
| `npp` | 순일차생산 | `npp` | `npp` | `NPP` | `NPP` | `npp_gb` |
| `cVeg` | 식생 탄소 | `btot`(`bl`+`br`+`bwood`+`bsw`) | `cVeg` | `TOTVEGC` | `LFMASS`+`STMASS`+`WOOD`+`RTMASS` | `cv` |
| `treeFrac` 등 | PFT/타일 분율 | `frac_ntrl`/`frac_crop`/`frac_past` + `species` | `treeFrac`·`grassFrac`·`cropFrac` | `PCT_*_PFT` | `FVEG`(총피복만) | **`frac`** |

- **Noah-MP `cVeg`는 4개 풀 합산 필요**(잎+줄기+목재+뿌리). 단일 변수 없음.
- **PFT 분율이 진짜 없는 건 Noah-MP뿐** — 총 식생피복(`FVEG`)만 있음. JULES는 `frac`(각 표면타입 분율)으로 가능. T3-5(식생분포 귀책) 진단은 Noah-MP에서만 제한됨.

### T1-b 유출 — *지면→해양 매개*

| CMIP | 물리량 | LM4 (native) | LM4 (cmip) | CLM5 | Noah-MP | JULES |
|---|---|---|---|---|---|---|
| `mrro` | **총 유출** ※ | **`runf`** ※ | `mrro` ※ | `TOTRUNOFF`(=`QRUNOFF`) ※ | `SFCRNOFF`+`UGDRNOFF` **(누적 mm!)** ※ | `runoff` ※ |
| `mrros` | 지표 유출 | `soil_rie`(침투초과)+`soil_rsn`(포화) | `mrros` | `QOVER` | `SFCRNOFF` | **`surf_roff`** |
| (지하) | 지하 배수 | `soil_rbf`(baseflow) | — | `QDRAI` | `UGDRNOFF` | **`sub_surf_roff`** |
| `mrtws` | 총 육수저장 | `water_soil`+`water_lake` | `mrtws` | `TWS` | — (계산 필요) | — (계산 필요) |
| — | **고체(빙설) 유출** | **`frunf`** | — | `QRGWL`(부분) | — | — |
| — | **하천 방류(해양)** | **`dis_liq`·`dis_ice`** | — | `DIRECT_/TOTAL_DISCHARGE_TO_OCEAN_LIQ` | 없음 | 없음 |
| — | **하천 유량** | **`rv_Qavg`** (m³/s) | — | `RIVER_DISCHARGE_OVER_LAND_LIQ` | 없음 | 없음 |

**※ 이 행의 셀들은 서로 같은 양이 아니다 (2026-07-29 실측).** LM4 안에서만도 native `runf`와 CMIP `mrro`가 **37% 다르다**(1995 전지구 평균 8.504e-6 vs 5.340e-6, 공간상관 0.918, 격자 수는 동일하므로 마스크 아님).

```fortran
runf = snow_lrunf + snow_frunf + subs_lrunf   ! land_model.F90:2550 — 고체유출 포함, 빙하·호수 타일 포함
mrro = lrunf_ie + lrunf_sn + lrunf_bf + lrunf_nu ! soil.F90:2996 — 액체만, soil 타일만
```

- **해양 담수 총량**(과제 핵심)에는 빙설 융해수가 들어가야 하므로 **`runf` 계열**.
- **ILAMB·CMIP 표준 비교**에는 `mrro`를 쓰되 **빙설·빙하 기여 제외**를 명시.
- 검사 도구: `lm4/scripts/cmp_native_vs_cmip_streams.py`. 상세 `lm4/LM4_LAI_CODE_TRACE.md` §10.

### ※※ 4개 모델 총유출 정의 대조 (2026-07-29, 전부 소스 확인)

| 모델 | 변수 | 단위 | 실제 정의 | 근거 |
|---|---|---|---|---|
| **LM4** | `runf` | kg/(m²s) | `snow_lrunf+snow_frunf+subs_lrunf` — **고체 포함**, 빙하·호수 타일 포함 | `land_model.F90:2550` |
| | `mrro` | kg/(m²s) | `lrunf_ie+lrunf_sn+lrunf_bf+lrunf_nu` — 액체만, soil 타일만 | `soil.F90:2996` |
| | `frunf` | | 고체(빙설) 유출 단독 | §13.24 |
| **CLM5** | `TOTRUNOFF` | mm/s | **`QRUNOFF`의 별칭일 뿐** (진단패키지가 그대로 읽음) | `lnd_diag/shared/lnd_func.ncl:159-161` |
| | `QRUNOFF` | mm/s | "total **liquid** runoff not including correction for land use change" | `WaterfluxType.F90:326` |
| | `QSNWCPICE` | mm H2O/s | "excess **solid** h2o due to snow capping" — **고체 유출 별도 변수** | `WaterfluxType.F90:453` |
| | `QRGWL` | mm/s | 빙하(액체)·습지·호수 유출, **QSNWCPICE의 융해분 포함** | `variable_master4.3.ncl` |
| **Noah-MP** | `SFCRNOFF` | **mm (누적)** | "Accumulatetd surface runoff" | LDASOUT 헤더 |
| | `UGDRNOFF` | **mm (누적)** | "Accumulated underground runoff" | LDASOUT 헤더 |
| **JULES** | `runoff` | kg/(m²s) | `sub_surf_roff_gb + surf_roff_gb` — 격자평균 두 성분 합 | `extract_var.inc:978-980` |

**★★ 함정 3개 (전부 조용히 틀린 답을 준다)**

1. **Noah-MP는 유량률이 아니라 누적값(mm)이다.** `ACSNOM`(융설)도 마찬가지. **시간차분 후 Δt로 나눠야** 다른 모델(mm/s)과 같은 양이 된다. 안 하면 단위부터 다른데 숫자는 그럴듯하게 나온다.
2. **고체(빙설) 유출을 별도 변수로 내는 건 LM4(`frunf`)와 CLM5(`QSNWCPICE`)뿐이다.** Noah-MP(HRLDAS offline)·JULES에는 그 개념이 없다 — Noah-MP는 빙하 역학이 없어 빙상 SWE가 상한까지 쌓이기만 하고([[lsm-spinup-ice-mask-convergence]]), **빙상 담수 기여가 구조적으로 결여**된다.
3. **"총 유출"의 타일 범위가 제각각**이다. LM4 `mrro`는 soil 타일만, LM4 `runf`·CLM `QRUNOFF`는 빙하·호수 포함, JULES는 전 타일 격자평균.

**★ 모델 간 비교 시 지킬 규칙**
- 4모델 공통 최대공약수는 **"액체 총유출"**: LM4 `runf − frunf`(또는 `mrro`, 단 타일범위 주의) · CLM `QRUNOFF` · Noah-MP `d(SFCRNOFF+UGDRNOFF)/dt` · JULES `runoff`.
- **해양 담수 총량**을 볼 때는 고체가 필요하므로 LM4 `runf`, CLM `QRUNOFF+QSNWCPICE`. **Noah-MP·JULES는 이 비교에 참여 불가**(변수 부재).
- **빙상 격자는 마스크할 것.** 모델마다 빙하 물리 자체가 달라 그대로 평균 내면 물리 차이가 아니라 구현 유무를 비교하게 된다.

**하천 라우팅 정리**:
1. **CLM5** — MOSART(별도 ROF 컴포넌트)가 이미 출력 중. `areatotal`(유역 상류면적)까지 포함.
2. **LM4** — river 모듈 활성, 2026-07-29에 `river_month`/`river_daily` 스트림 추가 → **1997 세그먼트부터 출력**. `rv_Qavg`가 **m³/s**라 GRDC와 단위 변환 없이 비교 가능. 상세 `LM4_SPINUP_NOTES.md` §13.28.
3. **Noah-MP(HRLDAS)·JULES** — 라우팅 미탑재. 격자 runoff까지만. → **이 두 모델은 GRDC 유량 검증 불가**, 격자 유출 지도 비교로 한정.
4. **고체 유출은 LM4만 별도 변수(`frunf`)를 냅니다.** 담수 총량을 모델 간 같은 정의로 맞추려면 성분 정의를 문서에 못박아야 함(§13.24 오인 전례).

---

## T2 — 내부 체크 (계산·저장만, 보고서 제외)

### T2-a 에너지 플럭스

| CMIP | 물리량 | LM4 (native) | CLM5 | Noah-MP | JULES |
|---|---|---|---|---|---|
| `hfss` | 현열 | `sens` | `FSH` | `HFX` | **`ftl_gb`** |
| `hfls` | 잠열 | `levapv`+`levapg`+`levaps` | `LHEAT` | `LH` | `latent_heat` |
| `tran` | **증산** | `transp` | `FCTR` | `ETRAN` | **`et_stom_gb`** |
| `evspsblveg` | **차단증발** | `levapv`/`fevapv` | `FCEV` | `ECAN` | **`ecan_gb`** |
| `evspsblsoi` | **지면증발** | `evap_soil`/`levapg` | `FGEV` | `EDIR` | **`esoil_gb`** |
| `sbl` | 승화 | `levaps` | — | — | **`ei_gb`** |
| — | 총 수분플럭스 | `evap_land` | `QFLX_EVAP_TOT` | — | `fqw_gb` |
| `hfdsl` | 지중 열플럭스 | `grnd_flux` | `FGR` | `GRDFLX` | **`surf_ht_flux_gb`** |
| `albedo` | 알베도 | `albedo_dir`/`albedo_dif` | `ASA` | `ALBEDO` | **`albedo_land`** |
| (순복사) | 순복사 | `fsw`−`flw` | `RNET`(=FSA−FIRA) | `FSA`−`FIRA` | **`rad_net`** |
| — | 수분스트레스 | `w_scale`·`soil_water_supply` | `BTRAN` | `BTRAN`(출력X) | **`fsmc_gb`** |

**★ ET 3성분 분해가 4개 모델 전부 가능해졌습니다.** Noah-MP `ECAN`/`ETRAN`/`EDIR`, JULES `ecan_gb`/`et_stom_gb`/`esoil_gb`가 각각 대응. 유출 편차의 원인을 같은 방식으로 캘 수 있습니다.

### T2-b 토양

| CMIP | 물리량 | LM4 (native) | LM4 (cmip) | CLM5 | Noah-MP | JULES |
|---|---|---|---|---|---|---|
| `tsl` | 층별 토양온도 | `soil_T` | `tsl` | `TSOI` | `SOIL_T` | `t_soil` |
| `mrsol` | 층별 토양수분 | `soil_liq`+`soil_ice` | `mrsol` | `H2OSOI` | `SOIL_M` | `smcl` |
| `mrsos` | 표층 수분 | `theta`(표층) | `mrsos` | `H2OSOI`(1층) | `SOIL_M`(1층) | `sthu`(1층) |
| `mrso` | 총 토양수분 | `water_soil` | `mrso` | `TOTSOILLIQICE` | — (합산) | `smc_tot` |
| `mrfso` | 토양 동결수 | `soil_ice` | `mrfso` | `SOILICE` | (SOIL_M−SOIL_W) | **`sthf`** |
| — | 지하수면 | `soil_wt_4` | — | `ZWT` | `ZWT`·`WA` | **`zw`** |
| `cSoil` | 토양 탄소 | `tot_soil_C`(`fsc`+`ssc`) | `cSoil` | `TOTSOMC` | `FASTCP`+`STBLCP` | `cs` |

### T2-c 적설

| CMIP | 물리량 | LM4 (native) | LM4 (cmip) | CLM5 | Noah-MP | JULES |
|---|---|---|---|---|---|---|
| `snw` | SWE | `snow_soil` | `snw` | `H2OSNO` | `SNEQV` | `snow_mass_gb` |
| `snd` | 적설심 | (계산) | `snd` | `SNOWDP` | `SNOWH` | **`snow_depth`** |
| `snc` | 적설 피복률 | `snow_frac` | `snc` | `FSNO` | `FSNO` | **`snow_frac`** |
| `snm` | 융설 | `melt`·`meltg_soil` | `snm` | `QSNOMELT` | `QMELT`·`ACSNOM` | **`snow_melt_gb`** |

### T2-d 강제장 대조군

| CMIP | 물리량 | LM4 (native) | CLM5 | Noah-MP | JULES |
|---|---|---|---|---|---|
| `tas` | 2 m 기온 | `t_ref` | `TSA` | `T2MV`/`T2MB` | **`t1p5m_gb`** (1.5 m) |
| `ts` | 지표온도 | `Tgrnd`·`Trad` | `TG` | `TG`·`TRAD` | `tstar_gb` |
| `pr` | 강수 | `precip` | `PREC` | `RAINRATE` | **`precip`** |

---

## 정리 — 모델별 준비도 (2026-07-29 기준)

| 모델 | T1 식생 | T1 유출 | T2 | 상태 |
|---|---|---|---|---|
| **LM4+** | ✓ 완비 | ✓ **완비**(river 추가 완료) | ✓ 완비 | 1997 세그먼트 산출물 확인만 남음 |
| **CLM5** | ✓ | ✓ (+MOSART 하천) | ✓ | post-AD 생산런 출력 설정 시 반영 |
| **Noah-MP** | △ (cVeg 합산·PFT 없음) | △ (라우팅 없음 → 격자 유출까지) | ✓ | 파생변수 계산식 정의 |
| **JULES** | ✓ (`frac` 포함) | △ (라우팅 없음, 성분분해는 O) | ✓ **해결** | **output.nml 서버 반영 + 시험 런 필요** |

**남은 조치 3개**
1. **JULES** — 확장된 `output.nml`을 서버에 올리고 짧은 시험 런으로 36변수가 실제로 나오는지 확인(변수명 오타 시 런이 죽음).
2. **LM4** — 1997 세그먼트에서 `river_month`/`river_daily` 파일 생성 확인. FMS는 미등록 필드를 경고만 내고 건너뛰므로 **파일 존재 + 변수 목록을 눈으로** 확인할 것.
3. **Noah-MP** — `cVeg`(4풀 합산)·`mrtws` 파생변수 계산식을 스크립트로 고정.
