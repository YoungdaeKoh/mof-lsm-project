# LM4 Offline Spin-up — 상세 작업 로그 & 현황 (2026-06-22~25)

_**완료(2026-06-25): 300년 static-veg 평형 IC `IC_static_300yr` 확보 (§10).** Global 평형 도달, server+로컬 이중보존._

_climate 서버. UFS LND-LM4(gfortran). 빌드·48h 실행은 `PORTING_NOTES.md` 참조. 이 문서는 그 다음 **spin-up 단계** 전체._
_**실행법(스크립트·설정·재현)** → [`RUN_GUIDE.md`](RUN_GUIDE.md). 출력 변수 그림용 NC 변환 → `lm4_to_latlon.py`._
_**핵심 결과(2026-06-23)**: cold-start 캐노피 overshoot = **qscomp clamp로 해결**(§4·§7), **NOLEAP 전환**(§9c), 30년 세그먼트 warm-start 방식으로 평형 spin-up 진행 중(§9d)._

## 0. 목표
오프라인 LM4를 장기 cycle forcing으로 spin-up → 평형 RESTART를 본 실험(ERA5)의 초기조건(IC)으로.
LUMIP/CMIP6 프로토콜(Lawrence et al. 2016 GMD; GFDL E.Shevliakova): ① potential-veg spin-up(PI forcing cycling) → ② land-use transient(1700-1850) → ③ historical. 오프라인판은 재분석 cycling으로 ①을 대체.

## 1. 인프라 — 전부 해결됨 (spin-up 돌릴 준비 완료)
| # | 문제 | 해결 |
|---|---|---|
| 1 | **48코어 layout(2,4) 교착** — land 분해에서 일부 PET가 land점 0개 → init collective hang | **24코어(layout 2,2)** 사용. INPES/JNPES=2,2 |
| 2 | PBS 클린환경 `libnsl.so.1` 없음(시스템 전체 부재) | `/data2/ydkoh/lm4/runtime_libs/libnsl.so.1 → /usr/lib64/libnsl.so.2` 심볼릭링크 |
| 3 | openmpi hcoll 플러그인 dlopen → libhcoll/libnsl 필요 + hcoll init 실패(IB 필요) | LD_LIBRARY_PATH에 HPCX hcoll/ucx/ucc + `OMPI_MCA_coll=^hcoll`(단일노드 hcoll 비활성) |
| 4 | diag_table cell_measures(soil_area/land_area) 누락 → FATAL | diag_table_lm4_spinup.IN에 area 측정필드 추가 |
| 5 | CDEPS cycle 경계 dtlimit(1.5) 초과 | streams dtlimit=1.0e30 |
| 6 | 멀티데이 잡 → 로그인노드 금지 | PBS `host=climate01`(compute), walltime 24h, 30년 세그먼트 |

실행: `bash setup_lm4_spinup.sh <YEARS> <CORES> <CPLSEC> <FORCING>` → `qsub spinup24.pbs`.
스크립트 전부 `climate:/data2/ydkoh/lm4/`.

## 2. Forcing 분석 (3종 비교, 1980-82 검증)
| forcing | 격자 | SW 최대 | 강수보정 | q/풍속 | 비고 |
|---|---|---|---|---|---|
| **GSWP3** (`/data1/CESM2_INPUT/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516/`) | 0.5°(lon0-360) | **~1580-1630 (아티팩트!)** | GPCC보정됨 | QBOT/WIND 직접 | 매년 수백 셀 SW>1360 |
| **ERA5 raw** (`/data1/ERA5/single_level/hourly_0.25/`) | 0.25° 일별 | 1267-1288 (깨끗) | 미보정 | dewpoint→q, u/v→풍속 필요 | 변환 多 |
| **★GPCP+ERA5 (JULES)** (`/data1/backup/ChanhyukChoi/002.JULES_RUN/INPUT_DATA/monitoring/92.GPCPobs_ERA5obs/`) | **0.5°(lon-180~180)** | **957 (깨끗)** | **GPCP보정** | **이미 q·풍속 계산됨** | 최적 |

**GPCP+ERA5 자료**(채택): 월별 `YYYY-MM.nc`, 1978-12~, 6시간별, ~1.8GB/파일. 변수 `Tair`(K)·`Qair`(kg/kg)·`Wind`(m/s)·`PSurf`(Pa)·`SWdown`·`LWdown`(W/m²)·`Rainf`(kg/m²/s) — **전부 CDEPS-ready 단위, 변환 불필요**. (GSWP3 SW 아티팩트는 raw 데이터의 알려진 특성; CLM은 견디나 LM4는 엄격.)

## 3. ERA5GPCP CDEPS 설정 (구축 완료)
- **mesh**: `gen_scrip.py`(0.5° SCRIP) → `ESMF_Scrip2Unstruct` → `/data2/ydkoh/lm4/forcing_ERA5GPCP/ERA5GPCP_05deg_ESMFmesh.nc` (lon-180~180 격자順, GSWP3 mesh와 다름)
- **streams**: `gen_streams_era5gpcp.py` — Tair→Sa_tbot, Qair→Sa_shum, Wind→Sa_wind, PSurf→Sa_pbot/pslv, SWdown→Faxa_swdn, LWdown→Faxa_lwdn, Rainf→Faxa_precn. 3 stream(coszen/nearest/linear)+topo, cycle 1981-2010.
- setup: `setup_lm4_spinup.sh ... era5gpcp` 가 위 generator 호출.
- **파일은 변환 안 함** — CDEPS가 in-place로 읽고 stream에서 이름만 매핑.

## 4. cold-start 캐노피 overshoot (★해결됨 — §7 qscomp clamp + §9d)
**증상:** 식생 캐노피 `cohort%Tv` → 100-114°C(374-387K) → `qscomp`→`lookup_es` 테이블 overflow → **FATAL**.
| 시도 | 크래시 |
|---|---|
| GSWP3 3600s (동적) | Aug 1981 SW 아티팩트 크래시 → SW clamp 적용. ~~"4.3년까지"~~ **(2026-06-22 반증: 1982~1985 restart·로그 전무, PORTING_NOTES엔 48h만. 4.3년은 미검증 오기 — 실제론 1년 내 크래시 추정)** |
| ERA5GPCP 3600s | **day 3** |
| ERA5GPCP 900s | Feb 1 (지연될 뿐, 또 터짐) |
| **static_veg ON, ERA5GPCP (2026-06-22 잡2862)** | leaf Tv 사라짐 ✓ — 그러나 `T_ca`(캐노피 공기온도) 391K 폭주 → 05:00 시작, 06:00 FATAL. 인도네시아 열대림셀(lon137-139E lat-2~-8). static veg 정상 로드. |
| **★ static_veg ON, GSWP3 (2026-06-22 잡2863)** | **1981-01-01→02-02 (한 달+) 완주!** ERA5GPCP 5h 대비 대폭 개선 — GSWP3 부드러워 열대 셀 토양수분 spin-up 성공, T_ca 통과. 크래시는 `grnd_T`(지면온도) 374K, **`nbad=1` 단일 병리셀** NZ남섬 산악(lon172.6E lat-41.4), 1981-02-02 02:00. overshoot가 Tv→T_ca→grnd_T로 옮겨가나 **매번 훨씬 오래 버팀.** |
| **★★ qscomp clamp + static_veg + GSWP3 (2026-06-22 잡2864)** | **clamp 성공!** 2863이 죽은 02-02를 통과해 **1981-05-07(4개월+) FATAL 없이 진행** (4분 wall). `qscomp out of range` 경고 0건 — clamp가 qsat 정상화로 **runaway 자체를 damping**(크래시 방지 그 이상). throughput ~1yr/6min → 24h에 30~60yr 가능. → **cold-start spin-up이 마침내 굴러감.** |

**근본 원인:** **오프라인(DATM 고정 = 대기 피드백 없음)** + cold-start 미평형 캐노피(열용량 작음) + 건조 사막셀 + 강일사 → 캐노피 runaway. **결합(coupled) GFDL은 대기 피드백으로 damping되어 안 터짐**; CLM 오프라인은 clamp로 견딤; **LM4 오프라인은 es-FATAL로 엄격**. timestep은 지연만(증상), forcing 탓 아님(둘 다 정상값).

**★ 두더지잡기 확인 (2026-06-22):** overshoot는 식생모드에 종속된 게 아님. **동적식생→leaf `Tv`, static veg→캐노피공기 `T_ca`** 로 *옮겨갈* 뿐 둘 다 `lookup_es` FATAL. 즉 **역학식생 끄는 것만으론 해결 안 됨.** 모든 온도변수가 `lookup_es`를 거치므로 **그 지점(qscomp/es-table) 가드가 유일하게 둘 다 잡음**(§5-1 "모든 caller 보호"의 의미 입증). → es-clamp가 구조적으로 필요한 fix이거나, cana까지 평형된 restart 필요.

## 5. 해결 선택지
1. **(band-aid) qscomp 온도 clamp** — `sphum.F90` qscomp에서 escomp 전에 T를 es테이블 범위(~173~373K)로 clamp(로컬 Tc). 2줄+인자교체. 모든 caller 보호. CLM식 관대 처리. → **사용자: 코드 패치 비선호.**
2. **(정석) 평형 동적식생 restart IC에서 시작** (cold-start 회피). 필요: **LM4 동적식생 restart, C96_OM4_025 격자**.
   - `c96_LM4/19810101.static_veg...` = **LM3.2 정적식생** (use_static_veg용) → 동적식생 IC 부적합.
   - **GFDL ESM4/CM4 동적식생 restart = 공개 배포 안 됨 (2026-06-22 웹조사 확정)**: ESGF/CMIP6·GFDL nomads는 **출력변수만** 배포(restart는 CMIP6 대상 아님); UFS 공개 regtest 버킷(`noaa-ufs-regtests-pds.s3`)은 **static_veg restart + 48h cold-start뿐**(공식 `datm_cdeps_lm4_c96_gswp3`가 48h cold start라 캐노피 overshoot 도달 전에 끝남). EPIC 안내 = "**GFDL Land Team 직접 문의**". → 정식 동적식생 IC는 GFDL/동료 직접 요청만이 유일 경로.
   - **jjeehoon** 사용자도 `lm4_spinup` 잡 돌림 → 그쪽 setup/restart 문의 여지. 단 `/home/jjeehoon` 읽기권한 없어 직접 복사 불가, 본인 공유 요청 필요.
   - 디스크 전체(`/data1`·`/data2`) `*.vegn2.res.*` 스캔 = 깨진 cold-start 런 외 **동적식생 restart 0건** (2026-06-22).
3. **(반쪽짜리) static_veg substrate spin-up → 동적식생 IC** — CESM SP→BGC 이식 아이디어. **소스 확인 결과 crash 해결책 아님 (2026-06-22).** `vegetation.F90`: `use_static_veg`=동역학 off+규정식생 읽기(바이오매스 적립 안 함); 동적식생 cold-start cohort는 `init_cohort_bl=bwood=bsw=0.05 kgC/m2`(line 120–124, 419–423)로 **거의 맨땅에서 재성장**. → substrate(토양·수문·적설) 스핀업은 넘어가 절약되나, **식생·탄소 스핀업은 동적식생 켜는 순간 0.05부터 다시 시작**(사용자 기억대로). 얇은 캐노피=작은 열용량 = **cold-start Tv overshoot 조건 재현 → 크래시 신뢰성 회피 불가.** 결론: "토양 스핀업 단축"일 뿐.
4. **(미검증 지렛대) `init_cohort_bwood`/`bl` namelist 상향** — cold-start 초기 cohort 바이오매스를 키워 캐노피 열용량 확보 → Tv runaway 차단. **소스패치 아닌 namelist만**으로. 스핀업 궤적 바뀜·과학적 정당성 확인 필요.

## 6. 파일/스크립트 (climate:/data2/ydkoh/lm4/)
- `setup_lm4_spinup.sh`(args: YEARS CORES CPLSEC FORCING), `spinup.pbs`/`spinup24.pbs`(48/24코어), `run_lm4.sh`/`run_lm4_spinup.csh`
- `gen_streams.py`(GSWP3), `gen_streams_era5gpcp.py`, `gen_scrip.py`, `mkmesh.sh`
- `INPUTDATA/input-data-20251015/`(GSWP3·LM4·MOM6_FIX·CPL_FIX·FV3 grid), `forcing_ERA5GPCP/`(mesh,scrip), `runtime_libs/`(libnsl symlink)
- `RUN/lm4_spinup/`(런 디렉토리), `PORTING_NOTES.md`, `LM4_porting_guide.html`, `LM4_diag_fields.html`

## 7. 적용한 소스 패치 (git submodule update시 사라짐 — 재적용)
- `CMakeModules/Modules/FindESMF.cmake`: ESMF::ESMF 타겟 생성
- `LM4-driver/CMakeLists.txt`: GNU일 때 .F90 → intel fpp 전처리 → gfortran (`#`/`##` 매크로)
- `LM4-driver/nuopc_cap/lm4_cap.F90`: alloc_atmforc를 init_driver 앞으로 (gust SEGV)
- `LM4-driver/nuopc_cap/lm4_import_export.F90`: SW 4밴드 min(.,1360) clamp (GSWP3 아티팩트; ERA5엔 무해 no-op)
- **★ `LM4/shared/sphum.F90` qscomp clamp (2026-06-22 적용·검증)**: escomp 호출 전 `Tc = min(max(T,173.16),372.16)`로 es-table 범위 clamp, escomp(Tc) 2곳. 모든 qscomp caller(Tv·T_ca·grnd_T) 보호. 잡2864에서 효과 확인(크래시 0, runaway damping). 원본 백업 `sphum.F90.orig`, 패치 사본 `lm4/patches/sphum.F90.clamp`. **평형 도달용 비계 — 평형 후 무발동이면 제거 가능(검증: qscomp 경고 0 확인).**

## 8. 다음 단계
**핵심 정리 (2026-06-22 static_veg 테스트로 갱신):** overshoot는 식생모드 무관 — 끄면 Tv→T_ca로 옮겨갈 뿐(§4). 식생측 완화(static veg, init_cohort 상향)는 Tv만 막고 T_ca는 못 막음. 모든 온도변수가 `lookup_es`를 거치므로 **그 지점 가드(es-clamp)만이 구조적 해결.** 대안은 cana까지 평형된 동적식생 restart(공개 없음).
1. **★ qscomp/es-table clamp 적용** (§5-1) — `sphum.F90`에서 escomp 호출 전 T를 es테이블 범위(~173–373K)로 clamp. 2줄, **모든 caller(Tv·T_ca 등) 보호**. cold-start transient 생존의 유일한 구조적 fix로 확인됨. CLM 표준 방식(꼼수 아님). → 사용자 패치 비선호였으나 테스트로 불가피성 입증, 재논의 필요.
2. fallback: GFDL/jjeehoon에 평형 동적식생 restart 직접 요청 (§5-2) — 공개 배포 없음, 회신 불확실. 받아도 cana 평형 포함돼야 T_ca 회피.
3. **patch 후 검증**: static_veg ON 유지(diag 비교 표준모드 + Tv path 제거) + es-clamp → 24h 완주 확인 → 동적식생으로 전환해 재확인.
4. 생존 확보 후: 재분석(GPCP+ERA5) cycling spin-up → 평형 모니터링(annual: soil_T/liq, biomass, fast/slow_soil_C, LAI) → baseline IC 아카이빙.  **→ §9에서 완료됨.**

## 9. ★ 30년 spin-up 완료 (2026-06-22~23, 잡2865)
- **GSWP3 1981–2010 (1 cycle) + static veg + qscomp clamp, 30년 cold-start spin-up exit=0 완주** (~3.5h, np24, ~8.5min/yr). clamp가 cold-start 30년 완전 견딤(FATAL 0).
- **평형 확인** (`lm4_equil.py`, 연간 restart 29개 land-mean): 심층 토양온도 287.04→272.53K, 연변화 -2.43→**-0.038 K/yr** (98% 수렴); 전층 토양수분 3348→3232 kg/m². **표층·근권 평형 완료**(진단=플럭스용 충분), 심층온도만 미세 잔여. 그림 `figures/lm4_spinup_convergence.png`.
- **30년분 임시 아카이브: `climate:/data2/ydkoh/lm4/IC_GSWP3_staticveg_spin30/`** (FMS 9종×6타일+coupler.res, 35MB, 2010-01-01). ※아래 ★ 따라 **아직 미평형 — 90년판으로 대체 예정.**

### 9b. 전 저수지 평형 진단 (`lm4_equil2.py`, 2026-06-23) → 30년 불충분 판정
| 저수지 | 30년차 연drift | 상태 |
|---|---|---|
| 표층 soil T | +0.02 K/yr | ✅ 평형 |
| 심층 soil T | **-0.038 K/yr** | ⏳ 느림 |
| column soil water | **-2.5 kg/m²/yr** | ⏳ **laggard** (= water-table 평형, 아래) |
| groundwater (별도 배열) | 0.000 (항상) | — **'hill' 스킴이라 별도배열 미사용** |
| snow water | +0.11 kg/m²/yr (초기 +35→) | ✅ 평형 |

**groundwater 주의:** input.nml `geohydrology_to_use='hill'`(hillslope/TOPMODEL식, gw 활성). restart `groundwater` 배열이 0인 건 **비활성이 아니라**, 'hill'이 포화대를 soil column `wl` 안에서 표현하기 때문. → **느린 water-table 평형은 column soil water(laggard)에 이미 포함됨.** LAI 지도(prescribed, 평균 3.09): `figures/lm4_lai_map.png`.
→ **30년은 완전 평형 아님.** 느린 모드 2개(심층 T, column water)가 미수렴. **결정: drift 끝낸 뒤 그걸로 본 실험 warm-start** (미평형 상태로 warm-start하면 잔여 drift 혼입). 감속 추세상 ~90년(3 cycle) 예상.

### 9c. 90년 한방 실패 → NOLEAP 전환 + 세그먼트 방식 (2026-06-23)
- **90년 한 잡(잡2866) = init 즉사**: `ESMF_ClockSet() Value out of range` (`nhours_fcst=788400`). **ESMF 시계가 90년 길이 거부.** 30년(262800h, 잡2865)은 OK. → **한 잡에 30년이 한계, 90년은 안 됨.**
- **leap 발견 (사용자 지적)**: 잡2865 30년이 2010-12-31 아닌 **2010-12-25에 끝남** = 1981–2010 윤년 7일. UFS 기본 = **Gregorian(leap)**. JULES/CLM은 **NOLEAP**.
- **★ NOLEAP 전환 (검증완료, 잡2867)**: `lm4_cap.F90`이 `model_configure`의 `calendar:` 읽음(기본 gregorian, **NOLEAP case 지원**). **`model_configure`에 `calendar: 'NOLEAP'` 한 줄 추가** → 1년 테스트 exit=0, **1982-01-01에 정확히 끝남**, forcing 정상. → NOLEAP에선 30년=262800h가 2010-12-31에 딱. **JULES/CLM 정합 + 365일 static_veg와도 일관 + leap drift 소멸.**
- **결정: NOLEAP cold-start 새로(option 2), 30년 세그먼트 × 3 (warm-start 이어붙여 ~90년 평형).** continue/warm-start = regtest `_rst` 방식(`RUNTYPE=continue`, `WARM_START=.true.`, restart를 INPUT/에 dated prefix로 스테이징, start date=restart날짜). 물리 restart는 calendar 독립이라 재사용 가능; cycling은 매 cycle 시계 1981 리셋.

### 9d. NOLEAP 시도 실패 → leap 유지 결정 (2026-06-23)
- **잡2868 (NOLEAP 30년)**: **1984-02-29에서 크래시** (exit=1). 모델이 Feb 29에 도달 = NOLEAP인데 윤일 존재 → **calendar 불일치**.
- **원인**: `model_configure`의 `calendar: 'NOLEAP'`은 `lm4_cap.F90`의 `set_calendar_type`로 **LM4 FMS 내부 달력만** 바꿈. **ESMF 드라이버 master 시계는 gregorian(기본값, 미설정)** 그대로 → 1984-02-29 진행 → noleap LM4가 거부. (1년 테스트는 1981에 윤일 없어 통과 — 첫 윤년 1984에서 발현.)
- **완전 NOLEAP 필요조건**: 드라이버 소스에 `ESMF_CalendarSetDefault(ESMF_CALKIND_NOLEAP)` 패치 + CDEPS GSWP3 스트림 달력 = 침습적·불확실. (CDEPS/driver에 calendar 노브 없음.)
- **★ 전략 판단: spin-up 달력은 JULES/CLM 정합과 무관.** 만드는 건 IC(평형 land 상태)이고 **restart 물리상태는 calendar 독립**. 달력 정합은 **production 비교 단계** 문제.
- **★★ 최종 결정 (2026-06-23, 사용자): leap 그대로 쓰고, 달력 차이는 분석 단계에서 처리.** 30년 세그먼트당 윤일 차 ~5–7일(climatology 무영향). JULES/CLM(no-leap) 비교 시 **LM4의 Feb 29만 제거**해 정렬. → NOLEAP 드라이버 패치 등 침습적 작업 불필요. spin-up·production 전부 leap.

### 9e. leap 30년 spin-up segment 1 재실행 (잡2869, 진행중 ~3.5h)
- `RUN/lm4_spinup/` = GSWP3 + `use_static_veg=.TRUE.` + leap(calendar 줄 없음, 2865와 동일 검증설정) + 30yr(262800h) + 연간 restart. clamp 빌드.
- **다음(자동)**: 완료 → `lm4_equil2.py` 평형검증 → **`IC_GSWP3_staticveg_spin30b/`로 아카이빙** → segment 2 warm-start(60년) → segment 3(90년) → 평탄화까지.
- **그 다음**: ① 본 실험을 평형 IC로 warm-start. ② 동적식생 필요시 평형 물리상태에서 동적식생 ON. ③ 평형서 clamp 무발동 검증 후 순정 빌드로 제거 가능.

**데이터 안전:** 평형 IC는 run dir 밖 `IC_*` 디렉토리에 아카이빙(run dir 재사용해도 보존). leap 30년판: `IC_GSWP3_staticveg_spin30/`(35MB, intact). 패치 `lm4/patches/sphum.F90.clamp`, 서버 원본 `sphum.F90.orig`. 진단코드 `lm4_equil.py`·`lm4_equil2.py`·`lai_extract.py`. 서버 python은 [[climate-server-python-anaconda]].

## 10. ★★ 300년 static-veg spin-up 완료 (2026-06-25)
**결과물 = `IC_static_300yr` (300년 GSWP3 static-veg 평형 IC, FMS 9종×6타일).** cold-start(backfill 1-30) → continue 세그먼트(30년씩 ×10 cycle) → 300년. leap calendar(NOLEAP은 컴포넌트만 바뀌어 윤일 충돌, §9d). 본 실험은 이 IC로 warm-start.

**Global 평형 확인 (`plot_global.py`, 290 누적점):** deepT@8.75m 287→272(완전평탄, drift ~0/cycle), column water 3348→3201(포락선 평탄, -0.6/cycle), snow 77→330(leveled, +1.8/cycle). → **Global 기준 평형 도달.** 그림 `figures/lm4_global_spinup.png`(Global 단독)·`lm4_region_spinup.png`(6지역+Global).

**지역 laggard (검증):** Sahara column water = **최저속**(269yr서도 +1.5/yr 축적, 평형 안 됨) — 사막 심층(8.75m) 재충전이 극히 느림(수백~수천 년). **단 global서 상쇄(작은 면적)되고 사막 표면 ET≈0이라 플럭스 진단엔 무영향.** Tibet 적설도 미세 상승, Siberia 적설은 평형. → **개별 사막 deep water는 안 끝나도 Global·플럭스엔 OK, 300년 충분.**

**★ 운영 교훈 (다음 spin-up 필수):**
- **raw restart 절대 자동삭제 금지** — 초기 오케스트레이터가 cycle 넘어갈 때 `rm RESTART/*`로 중간 raw를 지워 cycles 2-4 raw 손실(Global·맵 재계산 불가) → **`spinup_loop.sh`를 "cycle마다 spinup_raw/yN에 raw 전체(restart+land_annual+coords) 보존 후에만 run dir 정리"로 수정.** deterministic이라 손실분은 재실행으로 복구(cycles 2-3 climate02서 재생성).
- **이중 보존**: server `spinup_raw/` + 로컬 `/Volumes/data02/LM4/spinup/`(=Mac `/Users/youngdaekoh/data2/LM4/spinup`, 11GB). 로컬 puller(`pull_raw.sh`) 30분 주기 동기화.
- **두 노드 병렬**: climate01(메인) + climate02(복구) 동시 = contention 0. **단 같은 run dir에 두 잡 띄우면 충돌** → 노드·run dir·CSV 완전 분리 필수(복구는 `RUN/lm4_backfill`+`backfill_c02.pbs`+`region_recov.csv`).
- **continue 검증 강제**: 매 cycle 첫해 deep T<280 확인(`check_warm.py`), cold(287)면 즉시 중단(파일명 무날짜 스테이징 실패 = silent cold-start, §8).
- **48코어 노드에 24/24 동시 = 메모리 대역폭 포화로 둘 다 ~10x 느림** → 같은 노드 동시 실행 금지, 순차 또는 다른 노드.

**스크립트 (lm4/scripts/ + server /data2/ydkoh/lm4/):** `spinup_loop.sh`(오케스트레이터, raw보존), `recovery_c02.sh`(climate02 복구), `lm4_region_spinup.py`(지역+Global, `--plot_only`), `plot_global.py`, `check_warm.py`, `stage_restart.sh`, `pull_raw.sh`, `merge_recov.py`.

**다음 단계:** ① 본 실험 = `IC_static_300yr` warm-start(ERA5 등 forcing 교체). ② 동적식생 1200년+ 단계 = 이 평형 물리상태서 동적식생 ON 후 식생·탄소 추가 spin-up. ③ (선택) 91-119 raw 공백은 cycle 4 재실행으로 복구(맵 필요시).
