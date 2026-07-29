# 다중 LSM 변수명 매핑표

> 대상 계층은 `lsm_core_variables.md`의 T1(보고서 축) · T2(내부 체크).
> 출처 = 각 모델 **실제 출력 파일 헤더**(2026-07-29 확인). 문서가 아니라 헤더 기준.

| 모델 | 읽은 파일 | 비고 |
|---|---|---|
| **LM4+** | `19960101.land_month{,_cmip}.tile1.nc` (`lm4_spinup30`) | native 194변수 + **CMIP 표준명 스트림 별도 존재** |
| **CLM5** | LMWG `variable_master4.3.ncl` | 진단 표준명 = CLM 출력명 |
| **Noah-MP** | `199801020000.LDASOUT_DOMAIN1` (HRLDAS) | |
| **JULES** | `test_dgvm_gf.monthly.2010.nc` | **출력 변수 15개뿐 — 확장 필요** |

---

## ★ 핵심 발견: LM4는 이미 CMIP 표준명으로 쓰고 있다

`land_month_cmip` / `land_daily_cmip` 스트림이 **CMIP6 land 변수명 그대로** 출력 중입니다
(`mrro` `mrros` `mrso` `mrsos` `mrsol` `mrsfl` `mrsll` `tsl` `tran` `evspsblsoi` `evspsblveg` `snw` `snd` `snc` `snm` `lai` `gpp` `npp` `ra` `rh` `nbp` `cVeg` `cSoil` `cLitter` `treeFrac` `grassFrac` `cropFrac` `mrtws` `tasLut` …).

**의미**: 모델 간 공통 언어를 CLM 이름(LMWG)이 아니라 **CMIP 이름**으로 잡는 게 맞습니다.
- ILAMB이 먹는 게 CMIP 규격 → LM4는 **변환기가 사실상 불필요**(CLM은 `clm_to_mip`가 필요했던 그 단계).
- 따라서 아래 표의 기준열은 **CMIP 표준명**입니다.

---

## T1 — 보고서 축

### T1-a 식생

| CMIP | 물리량 | LM4 (native) | LM4 (cmip) | CLM5 | Noah-MP | JULES |
|---|---|---|---|---|---|---|
| `lai` | 엽면적지수 | `lai` | `lai` | `TLAI` | `LAI` | `lai` |
| `gpp` | 총일차생산 | `gpp` | `gpp` | `GPP` | `GPP` | `gpp_gb` |
| `npp` | 순일차생산 | `npp` | `npp` | `NPP` | `NPP` | `npp_gb` |
| `cVeg` | 식생 탄소 | `btot`(`bl`+`br`+`bwood`+`bsw`) | `cVeg` | `TOTVEGC` | `LFMASS`+`STMASS`+`WOOD`+`RTMASS` | `cv` |
| `treeFrac` 등 | PFT 분율 | `frac_ntrl`/`frac_crop`/`frac_past` + `species` | `treeFrac`·`grassFrac`·`cropFrac` | `PCT_*_PFT` | `FVEG`(총피복만) | — |

- **Noah-MP `cVeg`는 4개 풀 합산 필요**(잎+줄기+목재+뿌리). 단일 변수 없음.
- **Noah-MP·JULES는 PFT 분율 출력이 사실상 없음** — Noah-MP는 총 식생피복(`FVEG`)뿐, JULES는 없음. T3-5(식생분포 귀책) 진단이 두 모델에선 제한됨.

### T1-b 유출 — *지면→해양 매개*

| CMIP | 물리량 | LM4 (native) | LM4 (cmip) | CLM5 | Noah-MP | JULES |
|---|---|---|---|---|---|---|
| `mrro` | **총 유출** | **`runf`** | `mrro` | `TOTRUNOFF` | `SFCRNOFF`+`UGDRNOFF` | `runoff` |
| `mrros` | 지표 유출 | `soil_rie`(침투초과)+`soil_rsn`(포화) | `mrros` | `QOVER` | `SFCRNOFF` | — |
| (지하) | 지하 배수 | `soil_rbf`(baseflow) | — | `QDRAI` | `UGDRNOFF` | — |
| `mrtws` | 총 육수저장 | `water_soil`+`water_lake` | `mrtws` | `TWS` | — (계산 필요) | — |
| — | **고체(빙설) 유출** | **`frunf`** | — | `QRGWL`(부분) | — | — |
| — | **하천 방류** | **없음** | 없음 | MOSART 별도 | 없음(라우팅 미탑재) | 없음 |

**★ 하천 방류 (2026-07-29 갱신 — 최초 판단은 오판이었음)**:
1. **CLM5는 이미 출력 중**입니다 — `clm5_bgc_ad.mosart.h0.*`에 `RIVER_DISCHARGE_OVER_LAND_LIQ`·`DIRECT_DISCHARGE_TO_OCEAN_LIQ`·`TOTAL_DISCHARGE_TO_OCEAN_*`·`areatotal`(유역 상류면적).
2. **LM4도 river 모듈이 계속 돌고 있었고**(`INPUT/river.res.tile1~6.nc` + `&river_nml`), diag_table에만 안 걸려 있었습니다. **2026-07-29에 `river_month`/`river_daily` 추가 → 1997 세그먼트부터 출력.** 핵심 필드 `dis_liq`(해양 액체방류), `rv_Qavg`(**m³/s**, GRDC와 동일 단위). 상세 `LM4_SPINUP_NOTES.md` §13.28.
3. Noah-MP(HRLDAS)·JULES는 라우팅 미탑재 — 격자 runoff까지만.
2. **고체 유출은 LM4만 별도 변수(`frunf`)를 냅니다.** 담수 총량을 모델 간 같은 정의로 맞추려면 성분 정의를 문서에 못박아야 함(§13.24 오인 전례).

---

## T2 — 내부 체크 (계산·저장만, 보고서 제외)

### T2-a 에너지 플럭스

| CMIP | 물리량 | LM4 (native) | CLM5 | Noah-MP | JULES |
|---|---|---|---|---|---|
| `hfss` | 현열 | `sens` | `FSH` | `HFX` | **없음** |
| `hfls` | 잠열 | `levapv`+`levapg`+`levaps` | `LHEAT` | `LH` | `latent_heat` |
| `tran` | **증산** | `transp` | `FCTR` | **`ETRAN`** | — |
| `evspsblveg` | **차단증발** | `levapv`/`fevapv` | `FCEV` | **`ECAN`** | — |
| `evspsblsoi` | **지면증발** | `evap_soil`/`levapg` | `FGEV` | **`EDIR`** | — |
| `hfdsl` | 지중 열플럭스 | `grnd_flux` | `FGR` | `GRDFLX` | — |
| `albedo` | 알베도 | `albedo_dir`/`albedo_dif` | `ASA` | `ALBEDO` | — |
| (순복사) | 순복사 | `fsw`−`flw` (또는 swdn/up·lw) | `RNET`(=FSA−FIRA) | `FSA`−`FIRA` | — |
| — | 수분스트레스 | `w_scale`·`soil_water_supply` | `BTRAN` | `BTRAN`(출력X) | — |

**★ ET 3성분 분해는 LM4·CLM5·Noah-MP 모두 가능** (Noah-MP `ECAN`/`ETRAN`/`EDIR`이 정확히 대응). **JULES만 불가** — 현재 출력에 현열조차 없음.

### T2-b 토양

| CMIP | 물리량 | LM4 (native) | LM4 (cmip) | CLM5 | Noah-MP | JULES |
|---|---|---|---|---|---|---|
| `tsl` | 층별 토양온도 | `soil_T` | `tsl` | `TSOI` | `SOIL_T` | `t_soil` |
| `mrsol` | 층별 토양수분 | `soil_liq`+`soil_ice` | `mrsol` | `H2OSOI` | `SOIL_M` | `smcl` |
| `mrsos` | 표층 수분 | `theta`(표층) | `mrsos` | `H2OSOI`(1층) | `SOIL_M`(1층) | `sthu`(1층) |
| `mrso` | 총 토양수분 | `water_soil` | `mrso` | `TOTSOILLIQICE` | — (합산) | `smc_tot` |
| `mrfso` | 토양 동결수 | `soil_ice` | `mrfso` | `SOILICE` | (SOIL_M−SOIL_W) | — |
| — | 지하수면 | `soil_wt_4` | — | `ZWT` | `ZWT`·`WA` | — |
| `cSoil` | 토양 탄소 | `tot_soil_C`(`fsc`+`ssc`) | `cSoil` | `TOTSOMC` | `FASTCP`+`STBLCP` | `cs` |

### T2-c 적설

| CMIP | 물리량 | LM4 (native) | LM4 (cmip) | CLM5 | Noah-MP | JULES |
|---|---|---|---|---|---|---|
| `snw` | SWE | `snow_soil` | `snw` | `H2OSNO` | `SNEQV` | `snow_mass_gb` |
| `snd` | 적설심 | (계산) | `snd` | `SNOWDP` | `SNOWH` | — |
| `snc` | 적설 피복률 | `snow_frac` | `snc` | `FSNO` | `FSNO` | — |
| `snm` | 융설 | `melt`·`meltg_soil` | `snm` | `QSNOMELT` | `QMELT`·`ACSNOM` | — |

### T2-d 강제장 대조군

| CMIP | 물리량 | LM4 (native) | CLM5 | Noah-MP | JULES |
|---|---|---|---|---|---|
| `tas` | 2 m 기온 | `t_ref` | `TSA` | `T2MV`/`T2MB` | `tstar_gb`(지표온도, 대용 아님) |
| `pr` | 강수 | `precip` | `PREC` | `RAINRATE` | — |

---

## 정리 — 모델별 준비도

| 모델 | T1 식생 | T1 유출 | T2 | 조치 |
|---|---|---|---|---|
| **LM4+** | ✓ 완비 | ✓ (하천 방류만 ✗) | ✓ 완비 | river 스트림 추가 검토 |
| **CLM5** | ✓ | ✓ (+MOSART 하천) | ✓ | post-AD 생산런 출력 설정 시 반영 |
| **Noah-MP** | △ (cVeg 합산·PFT 없음) | △ (TWS·라우팅 없음) | ✓ (ET 3성분 O) | 파생변수 계산식 정의 |
| **JULES** | ✓ | △ (총유출만) | **✗ 심각** | **출력 프로파일 확장 필수** |

**★ JULES가 병목입니다.** 현재 월별 출력이 15변수뿐이고 **현열·ET 성분·적설피복률·유출 성분이 전부 없습니다.** JULES는 1차년도 점검항목 ①의 "벤치마크 모델"로 지정된 모델인데, 지금 출력으로는 다른 3개 모델과 같은 표에 올릴 수가 없습니다. → **JULES 출력 namelist(`output.nml`) 확장이 다음 우선순위.**
