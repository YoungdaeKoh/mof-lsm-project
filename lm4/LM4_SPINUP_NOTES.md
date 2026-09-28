# LM4 Offline Spin-up — 상세 작업 로그 & 현황 (2026-06-22~25)

_**완료(2026-06-25): 300년 static-veg 평형 IC `IC_static_300yr` 확보 (§10).** Global 평형 도달, server+로컬 이중보존._

_climate 서버. UFS LND-LM4(gfortran). 빌드·48h 실행은 `PORTING_NOTES.md` 참조. 이 문서는 그 다음 **spin-up 단계** 전체._

**★ 모델 provenance (2026-07-20 소스 실체 확인, 논문 method용):**
- exe: `/data2/ydkoh/lm4/ufs-weather-model/build/ufs_model` (**ufs-weather-model**, gfortran, 2026-06-22 빌드)
- Land 컴포넌트: **NOAA-GFDL/LM4-NUOPC-driver** 서브모듈 `LM4-driver` (branch develop)
  - commit **`513b67312510a15ae178ea5c3eddb0854e41486b`**, `git describe` = **`baseline_change_240904-8-g513b673`** (2024-09-04 baseline +8)
  - 실제 LM4 코드: `LM4-driver/LM4/` (vegetation/vegn_data.F90 등)
- **버전 = GFDL LM4.1 계열**(ESM4.1 land, Shevliakova). 소스에 LM4.0/4.1/4.2 backward-compat 플래그 존재(`vegn_data.F90` "reproduce LM4.1" 트리거) → 엄밀히는 LM4.1/4.2 lineage 모던 LM4, 통상 **LM4.1**로 인용. C96 cubed-sphere, CDEPS DATM.
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

## 11. ★★ 동적식생 warm-start 검증 완료 (2026-07-15, 잡2934-2936)

**한 줄:** `IC_static_300yr`(300년 평형)에서 warm-start + 동적식생 ON + GSWP3 1년 → **크래시 없이 완주(rc=0)**. 노트 §5의 `lookup_es` overshoot 우려가 평형 warm-start로 해소됨. 월별 지면변수(분석용 13종) + raw 보존까지 세팅.

### 11.1 동적식생 크래시 회피 (§5 숙제 해결)
- **한 줄 변경**: `input.nml &static_veg_nml use_static_veg = .TRUE. → .FALSE.` (vegn_nml `do_cohort_dynamics/do_phenology`는 이미 TRUE).
- **크래시 안 남**: §5가 우려한 "동적식생 cold-start 얇은 캐노피 → Tv overshoot → `lookup_es` FATAL"이 **재현 안 됨**. 이유 = `IC_static_300yr`에 **`cana.res`(캐노피공기)·`vegn1/vegn2.res`(식생 cohort)가 300년 평형 상태로 존재** → §5-2가 짚은 "cana까지 평형된 restart" 조건 그대로라 overshoot 조건 자체가 없음. es-clamp 패치는 추가 안전망.
- 1981년 1년 완주(1981-01-01→1982-01-01), `lookup_es`/qscomp/forrtl FATAL **0건**, NaN 0. 식생 진화 확인(LAI 0~10.5, bwood 1.8, nep −0.26).

### 11.2 테스트 run dir 구성
- 새 dir `RUN/lm4_dynveg_test`(300년 spin-up dir 불변). config 복사 + INPUT 경계자료(6GB) 복사 + `IC_static_300yr` restart 48개를 undated `.res`로 스테이징(`build_dynveg_test.sh`). exe 심링크, `nhours_fcst=8760`(1년).
- PBS `dynveg_test.pbs`: spinup.pbs 복제(climate01 48코어, spack-stack + HPC-X, `OMPI_MCA_coll=^hcoll`) + 경로만 변경. ~7분/년.

### 11.3 ★ 월별 지면변수 출력 (diag_table `land_month` 추가)
CLM5 SpinupStability 분석([[cesm/CLM5_SPINUP_NOTES §7]])을 LM4에도 적용하려면 **동적식생 수렴의 느린 모드=탄소**를 월별로 봐야 함. diag_table에 `land_month`(1,"months", FMS 진짜 월평균) 추가, 13변수:

| 분석 대응(CLM) | LM4 필드 | 모듈 |
|---|---|---|
| FSH 현열 | `sens` | land |
| EFLX_LH_TOT 잠열 | `evap` | land |
| TSOI 토양온도 | `soil_T` | soil |
| H2OSOI 토양수분 | `soil_liq`,`soil_ice` | soil |
| **TOTVEGC 총식생탄소** | `btot` | vegn |
| **TOTSOMC 토양탄소** | `slow_soil_C`,`fast_soil_C` | soil |
| GPP/생산성 | `nep` | vegn |
| TLAI | `LAI` | vegn |
| (부수) | `bwood`,`runf`,`soil_wtdep` | vegn/land |

- **flux 필드명 규명**: `sens`·`evap`는 **module `land`**(land_model.F90 line 3129/3219). 앞서 "LM4는 flux가 diag_table에 없어 6패널 불가"였던 것 해소. `latent`/`cSoil`은 `ocean_model`/`cmor_name` 모듈이라 회피, 검증된 `soil`/`vegn` 필드 사용.
- 검증: land_month 12개월(1981-01~12), `average_DT`=31/28/31…(진짜 월평균), 미등록필드 0.

### 11.4 raw 보존 (PBS 내장)
- `dynveg_test.pbs` 끝에 rsync(`--delete` 없음) → `/data2/ydkoh/lm4/history_raw/lm4_dynveg_test/`(land_month/annual/static + RESTART). 잡2936에서 자동 아카이브 확인(land_month 6타일 + restart 97). [[lsm-spinup-raw-preservation]]

### 11.5 다음 (2·3단계)
- **2단계 WFDE5 forcing 구축**: WFDE5 raw(0.5°, lon −180~180, 552개월)는 있으나 LM4 CDEPS용 mesh/streams 미준비. **ERA5GPCP mesh(lon −179.75~179.75)가 WFDE5와 격자 일치 → 재사용 후보**. WFDE5 변수(Tair/Rainf…) → CDEPS datamode 매핑 필요.
- **3단계 실행 의도 미정**: (a) 식생·탄소 spin-up(cyclic 반복, 탄소 느려 장기) vs (b) historical(WFDE5 1979-2024 순차). forcing 구성·compute 좌우.

## 12. WFDE5 forcing 테스트런 (2026-07-15)

`lm4_dynveg_test`(GSWP3 1년) 구성을 복제해 **forcing만 WFDE5로 교체**한 `lm4_wfde5_test`. 목적: WFDE5(CLM포맷 연간파일 `YYYY_wfde5.nc`)로 LM4 dynamic-veg 구동 검증. warm-start IC = 동일(`IC_static_300yr`), model start 1981.

### 12.1 datm.streams 변환 (GSWP3 → WFDE5)
- GSWP3는 **월별 3그룹**(Solar/Precip/TPQW) 파일리스트, WFDE5는 **연 1파일에 7변수 통합**. → 스트림 01/02/03의 `stream_data_files`를 동일 WFDE5 연간파일(1979-2024)로 교체(3스트림이 같은 파일 공유, 각자 변수 추출). `stream_data_variables` 매핑·`mapalgo`·`tInterpAlgo`는 그대로(변수명 동일: FSDS/PRECTmms/TBOT/QBOT/PSRF/WIND/FLDS).
- years: yearFirst=1979/yearLast=2024/yearAlign=1979 (model year = forcing year). topo 스트림(04)은 불변.
- WFDE5 time축: 6h 중점(0.125,0.375…=03/09/15/21시), noleap 1460/년. GSWP3(3h 중점)와 호환.

### 12.2 디버깅 (3회 시도)
- **① `ufs.configure` 누락**: clone 시 config 파일 하나 빠뜨려 ESMF_Initialize 실패. → dynveg config 파일셋 전체 대조 후 복사.
  - `start_type=continue`이나 mediator restart(ufs.cpl.r) 없음 = **mediator/DATM은 cold-init**, LM4 land만 INPUT/*.res(무날짜)를 IC로 읽음. rpointer는 시작 때 불필요(끝에만 생성).
- **② ★ WFDE5 land-only fill → init abort (핵심)**: GSWP3 ESMFmesh 재사용이 원인. GSWP3 mesh elementMask=**100% valid**인데 WFDE5는 valid 35.8%(ocean=1e20 fill). bilinear remap이 연안에서 fill을 육지로 섞음 → LM4 init 데이터 read 때 **MPI_ABORT**(FP 트랩 없는 깨끗한 abort, UFS.F90 Initialize). `_FillValue=1e20` 있어도 mesh mask가 valid면 remap이 포함.
  - **해결 = WFDE5 land-mask mesh**: GSWP3 ESMFmesh 복사 후 elementMask를 WFDE5 valid격자로 교체(각 요소 `centerCoords`로 WFDE5 TBOT valid 직접조회 → flatten순서 무관). `mk_mesh.py` → `/data2/ydkoh/2026_MOF_LSM/Atm_forc/wfde5_landmask_ESMFmesh.nc`. 지리검증(사하라 land·중태평양 ocean·아마존 land) 통과. datm.streams 스트림 01-03의 stream_mesh_file을 이걸로. **CLM5도 WFDE5 CDEPS 먹일 때 동일 mesh 필수.**
- **③ 성공(Job 2951)**: init 통과, 정상 적분(1981-01-25 확인, ~44분/년 — WFDE5 10.6G 연간파일 I/O로 GSWP3보다 약간 느림). raw 보존 → `history_raw/lm4_wfde5_test/`.

## 13. WFDE5 dynveg 메인 spin-up — 300년(30yr×10 cycle) (2026-07-15)

`lm4_wfde5_spinup`. 검증된 test 구성 상속(dynveg ON·월별출력·WFDE5 land-mask mesh) + 30년 cycle 자동연쇄.

### 13.1 cycle 길이·달력 (★ GSWP3 spin-up과 정확히 일치시킴)
- **cycle당 `nhours_fcst=262800`** (=30×8760, noleap-hours). LM4는 gregorian(leap)이라 10950일이 **윤년 7일(1984/88/92/96/2000/04/08)만큼 짧아 2010-12-25 종료**. 이게 기존 GSWP3 300yr spin-up(`lm4_spinup`)이 12-25에 끝난 이유. start 1981-01-01.
- LM4는 **매년 Jan-01 알람으로 restart 자동 생성**(restart_fh 빈칸이어도) → 1982-01-01…2010-01-01(29개) + 무날짜 run-end(2010-12-25).
- **chain point = 마지막 Jan-01(20100101) 스냅샷** (run-end 12-25 아님). 계절위상 정렬(새 cycle 1월을 이전 cycle 1월 상태에서 시작). `IC_static_300yr`이 20100101인 것이 이 관행의 증거. `lm4_spinup/RESTART`에 1982-2010 Jan-01 + 무날짜 run-end 확인.

### 13.2 체이닝 (self-chaining PBS `spinup_chain.pbs`)
- cycle N 완주 → ① 완주판정(`RESTART/20100101.000000.cana.res.tile1.nc` 존재?) → ② raw보존(monthly history + 20100101 chain restart → `history_raw/lm4_wfde5_spinup/cycleNN/`) → ③ 다음 IC 스테이징(`20100101.*.res` → `INPUT/`, 날짜strip, 9종: cana/glac/lake/land/landuse/snow/soil/vegn1/vegn2) → ④ `qsub -v CYCLE=N+1`.
- **완주 가드**: 20100101 restart 없으면(walltime kill 등) 연쇄 중단·exit 1. exit code로 판정 안 함(LM4 종료 아티팩트 주의).
- cycle-1 IC = `IC_static_300yr`(GSWP3 static-veg 평형)에서 pristine 스테이징. dynveg가 목질부·탄소 재평형 시작.
- forcing: WFDE5 1981-2010 cyclic(yearFirst=1981/Last=2010/Align=1981), 각 cycle이 date 1981 리셋이라 동일 30년 반복.
- **walltime**: ~44분/년×30 ≈ 22h < 24h(여유 적음). cycle 1 실제 완주시간 보고 필요시 2×15yr 분할 검토. raw보존은 [[lsm-spinup-raw-preservation]].

### 13.3 ★★ 크래시 디버깅 → gustiness 하한 fix (2026-07-16)
cycle 1이 **1981-02-18(bilinear)·01-31(nn)에 크래시** — `lm4_surface_flux.f90:188`(`escomp` 포화수증기압, t_ca가 NaN/범위이탈). 반복 진단:
- **forcing 데이터는 깨끗**(NaN/극단값 0). 개별 필드(FLDS·WIND 저값)는 **GSWP3가 더 극단인데 정상작동**이라 전부 기각.
- **mapalgo bilinear→nn 바꿔도 크래시**(타이밍만 Feb18→Jan31) = unmapped 문제 아님.
- **dt_atmos 900→450 축소도 동일 Jan-31 크래시** = 수치누적 아님, **모델날짜 고정**(forcing이 ~30일간 한랭셀을 몰고감).
- **발산점 특정**(Jan-30 `cana.res` temp): 몽골(104E,44.5N)·동부티벳(97E,31N) 등 **한랭 대륙점**. Jan-30 최저 206K(정상)→Jan-31 1스텝 NaN 발산.
- **근본원인 = `&surface_flux_nml`의 gustiness 하한 부재**: 한랭 안정조건(표면<대기)에서 유효풍속 하한이 없어 **난류교환→0, 지표-대기 decoupling → 복사냉각 런어웨이 → t_ca NaN**. GSWP3는 이 임계 안 넘었고 WFDE5(약간 다른 한랭 forcing)는 넘음.
- **★ gustiness 두 방식 (코드 확인)**: `alt_gustiness=.TRUE.` → `w_atm=max(풍속, gust_const)` (무풍셀만 max로 올림, targeted). `alt_gustiness=.FALSE.` → `w_atm=sqrt(풍속²+w_gust²)`, `w_gust=max(driver_gust, gust_min)` (전셀 quadrature). driver `atmos_prescr_nml gustiness=5.0`(기본)이 alt_gustiness=.TRUE.땐 dormant.
- **FIX 이력**: ① 첫 시도 `alt_gustiness=.FALSE.`+gust_min=1.0 → driver의 5.0을 활성화해 **전지구 5 m/s quadrature 하한**(막았지만 무풍역 과결합). ② **최종 = `alt_gustiness=.TRUE.` + `gust_const=3.0`** (targeted 3 m/s max-하한, 무풍셀만 보정). 원래 gust_const=1.0은 부족(크래시), 3.0은 디버그 45일 완주로 충분 확인. `gust_to_use='computed'`는 CDEPS와 비호환(ustar/bstar 없음)이라 탈락.
- **진단 함정 기록**: FMS diag_manager는 crash 시 버퍼를 flush 안 해 land_month/land_day가 time=0(빈 파일) → **발산셀 특정은 restart(cana.res/soil.res)로**. diag 출력 의존 금지.
- **디버그 방법**: `lm4_wfde5_debug`(단발 PBS, nhours 짧게, 크래시 직전서 멈춰 restart 확보). [[lsm-spinup-raw-preservation]]

### 13.4 2차 크래시 → 탄소보존 tolerance 완화 (2026-07-16)
gustiness fix 후 **1981-12-31(연말)까지 통과**하고 연 전환에서 다시 크래시:
```
FATAL update_land_model_fast_0d: conservation of carbon is violated;
before=276.4987 after=276.4988 diff=6.6e-6  time=1982-01-01 00:00:00
```
- input.nml(협력자 설정)에 `do_check_conservation=.true.`, `carbon_cons_tol=1e-6`, `water_cons_tol=1e-8`. 위반량 6.6e-6 > 1e-6 → FATAL. 상대오차 **2e-8 = 순수 roundoff**(탄소질량 276 대비). 1e-6 절대tol은 비현실적으로 타이트.
- **GSWP3 1년 테스트가 통과한 이유**: nhours=8760이 **1982-01-01에 정확히 run-end** → 그 시점 fast-update(탄소체크) 미실행. 30년 런은 진행해서 밟음 = **WFDE5 무관, 다년 dynveg 런의 일반 이슈**.
- **FIX**: `carbon_cons_tol=1e-3`, `water_cons_tol=1e-3`(roundoff 위, 실제 누출은 여전히 감지). `&land_debug_nml` 아님 — 별도 nml(land_debug.F90의 protected 변수, input.nml 162-164줄에 이미 설정돼 값만 교체). (대안: `do_check_conservation=.false.`=코드 기본값, 안전망 제거라 미채택.)
- **확인**: 두 fix(gustiness+tol)로 **연경계·표면플럭스 둘 다 통과**, 30년 cycle 완주 확인(land_month 359개월, 20100101 chain-restart). 페이스 ~30분/년 → 30년 ≈ 15h.

### 13.5 최종 config + gustiness 정제 (2026-07-16)
- 첫 완주 cycle 1은 **5 m/s(quadrature)** 였으나 무풍역 과결합 → **gust_const=3.0(targeted)로 정제**하기로. cycle 1 완주본은 `history_raw/.../cycle01_5ms_deprecated`로 보존.
- **최종 production config** (Job 2965~, IC_static_300yr pristine 재시작, 10 cycle 전부 동일):
  - `&surface_flux_nml`: `alt_gustiness=.TRUE.`, `gust_const=3.0` (3 m/s 무풍하한)
  - 탄소/수분 보존: `carbon_cons_tol=1e-3`, `water_cons_tol=1e-3`
  - 나머지: WFDE5 1981-2010 land-mask mesh + nn, dynveg ON, nhours_fcst=262800, 월별출력, 자동연쇄.
- **교훈**: ① 1년 테스트는 연경계 체크·다주 drift를 안 밟을 수 있음(다년 검증 필수). ② forcing 바꾸면 잠복 이슈(한랭 불안정·보존 roundoff) 발현. ③ 진단 함정: FMS diag는 crash 시 flush 안 함 → restart로 디버그.

### 13.6 ★★ 연속(continuous) 300년 런 + 심층토양 진단 — forcing loop-back 열충격 (2026-07-19)
**연속법**: 모델날짜를 1981→2264로 계속 전진(날짜 리셋 없음), DATM이 forcing만 1981-2010 반복(`yearAlign=1981`). run dir `/data2/ydkoh/lm4/RUN/lm4_wfde5_cont`, C96 dynveg, 크래시로 7개 세그먼트(start-date 파일명 1981/2020/2080/2086/2145/2204/2263 = spin-up yr 1/40/100/106/165/224/283)로 쪼개짐. Job 8255가 최종 세그먼트(yr283→300) 실행 중.

**심층토양 T(2 m, zfull_soil idx 12) 진단 — 결론이 뒤집힘:**
- **★ 압축 전 "연속법이 심층 스파이크를 제거한다"는 결론은 틀렸다.** 그건 **restart 날짜 착시**(restart별 다른 계절: Jan차가움 vs Dec따뜻함, 2m 위상지연)에서 나온 flawed 추출이었음.
- **올바른 추출**: land_month의 `time`(`days since 1981-01-01`, **GREGORIAN**)을 달력디코딩→실제 연도로 연평균 그룹핑. 이전 `tv//365`는 **윤일 표류**로 ~120년 후 월 경계를 넘겨 12월/1월을 섞음(가짜 스파이크). (land_area는 이 diag에서 전부 0 → C96 준등면적이라 **무가중 셀평균** 사용, [[lsm-landmean-comparability]].)
- **진짜 결과**: 심층T가 **매 30년 forcing 되감기(모델연 ≡ 1981 mod 30 = spin-up yr 1·31·61·91·…·271)에서 ~+6 K 스파이크** 후 ~2년 감쇠. 광역 승온(격자 70%가 +2K↑, 중앙값 +7.8K, max 308K로 **폭주 아님**)이라 수치불안정 아님.
- **★ 원인 = 날짜 리셋이 아니라 forcing 되감기 불연속(WFDE5 Dec-2010→Jan-1981)**. 증거: 연속런(날짜 리셋 無, 세그먼트 경계는 40·100·106…로 30년과 무관)인데도 리셋런(yr1·31·61·91 스파이크)과 **동일 위상·동일 크기**(연속 276.5K vs 리셋 277.0K)로 스파이크. 리셋의 날짜 리셋이 마침 forcing wrap과 겹쳐 그동안 원인이 가려졌던 것.
- **베이스라인(30년 중 29년)은 수렴 우수**: yr10=270.49 → yr50/110/200=270.61 → yr280=270.50, 무가중셀평균 baseline **270.82 K, non-wrap std 0.73 K**. 즉 심층토양 물리상태는 yr~10에 평형, 이후 forcing 반복에 의한 주기적 톱니만 얹힘.
- **함의**: cyclic-forcing offline spin-up의 **본질적 아티팩트** — 연속/리셋 선택과 무관. 진단·비교 시 wrap 연도(≡1 mod 30) 제외하거나 명시. 심층T는 수렴지표로 약함(경계조건·forcing 톱니에 지배) → **자유 예후변수(토양수분·탄소풀)로 판정**([[lsm-spinup-ice-mask-convergence]] 정신과 동일).
- 추출/그림: `lm4/scripts/lm4_extract.py`(서버, anaconda), `lm4/scripts/plot_lm4_cont_vs_reset.py`, `lm4/data/cont_deepT_annual_v2.csv`, `figures/lm4_cont_vs_reset_deepT.png`.

**JJA 평균 수렴 진단 (8변수, 무가중 셀평균, 2026-07-20):**
- 추출 `lm4/scripts/lm4_jja.py`(JJA=6-8월, gregorian 디코딩) → `lm4/data/jja_spinup_cont.csv`, 그림 `lm4/scripts/plot_lm4_jja_cont.py` → `figures/lm4_jja_cont_spinup.png`.
- **모든 변수의 30년 진동 = forcing 반복(1981-2010)이지 표류 아님.** 수렴은 주기평균 안정으로 판정.
- **~150년에 평형**: NEP −1.23→**−0.012**(→0, dynveg 탄소평형 결정신호), btot 1.135→1.122(−0.001/yr), colwater/sens/evap/deep-T 베이스라인 모두 last-30yr 기울기≈0.
- **soilC만 slow pool로 느림**: 385→266 kg C/m²(초반 집중), last-30yr −0.033/yr(연 0.01%)로 감속·거의 정착. 완전평형엔 수백~수천년(BGC 공통 → CLM5는 AD로 우회).
- deep-T 30년 스파이크는 forcing-wrap 열충격이 JJA 잔열로 보이는 것. [[lsm-cyclic-forcing-wrap-shock]]

**★ C96 좌표 복구 (grid-safety, 2026-07-20) — land 출력의 geolat/geolon이 전부 0일 때:**
- 이 run의 `land_month`·`land_static`의 `geolat_t/geolon_t`·`land_area`가 **전부 0**(diag 미기록). 가짜좌표 금지.
- 복구법: `grid_index`(CF `compress="grid_yt grid_xt"`, **0-based**, C96면 max 9214=95×96+94) → **j=idx//96, i=idx%96** → **`INPUT/C96_grid.tile{t}.nc`의 supergrid x/y(193×193)에서 셀중심 `[2j+1, 2i+1]`** = 실제 lon/lat. lon>180이면 −360.
- 검증: 좌표 없이 산점도 → 대륙 모양·위도 그래디언트 확인(열대 292K > 극 238K) 후 지도화. 통과.
- 스크립트: `lm4/scripts/lm4_seasmap.py`(값 추출), `lm4/scripts/lm4_coords.py`(좌표복구), `lm4/scripts/lm4_maps.py`(Cartopy). 데이터 `lm4/data/seasmap_last30.npz`. 그림 `figures/lm4_seasmap_{soilT_top,soilT_deep,sens,evap,LAI}.png`(마지막30년 yr271-300 계절평균).

### 13.7 ★★★ dynveg 식생이 거의 안 만들어짐 = `vegn_to_use='uniform'` 오설정 (2026-07-20)
**증상**: 마지막30년 grid-mean LAI가 습윤열대(Amazon 2.1·해양성 동남아 1.2)만 있고 **Congo·동아시아·유럽·Taiga(양쪽)·Sahel 전부 0**(현실 MODIS/GIMMS는 2~6). Sahara만 맞게 0. btot 1.1·LAI 0.29로 전지구 과소.
**원인 (소스 확인)**: `&vegn_data_nml vegn_to_use='uniform'`. `vegn_data.F90:231-238` 정의 — 'uniform'=**"global constant vegetation, e.g. to reproduce MCM"**(전지구 상수 1개 타입, index `vegn_index_constant=1`). 즉 경쟁 없는 최퇴화 모드. **이 값은 UFS regtest 템플릿 `tests/parm/input_datm_lm4.nml.IN:339`에서 상속**(48h 기술검증용, 과학설정 아님).
- 옵션 3종: **`'multi-tile'`**(격자당 다중 PFT 공존=진짜 areal 경쟁) · **`'single-tile'`**(기본값, 격자당 지역별 지배 PFT 1개) · `'uniform'`(상수). `init_cover_field`(land_io.F90:95)가 single/multi 모두 `INPUT/cover_type.nc`를 읽음 — **그 파일 이미 존재**(→common_LM4/cover_type.nc). single-tile은 셀별 최대frac PFT만 남김.
- **"1000년 더 돌려도 안 됨"**: btot 30yrRM 1.19→1.18·LAI 0.295→0.293 **~150년부터 flat 평형**. 희박식생이 이 config의 평형이라 시간으론 안 늘어남. **fix=모드 변경 후 새 dynveg spin-up**(cover_type.nc 기반). LM4 multi-tile은 정식 지원(JULES의 areal 미해결과 무관).
- vegn restart: tile=1·cohort=1(uniform 결과). 식생 fraction 별도 변수 출력엔 없음(grid-mean만).

### 13.8 ★★★ multi-tile 전환 시도 → offline lm4P(LM4.2) 방향 전환 (2026-07-20)
**multi-tile(`vegn_to_use='multi-tile'`, cover_type.nc=11PFT분율) cold-start 시도 = 실패:**
- **full cold-start**(start_type=startup, .res 전부 제거): cover map cold-start는 성공하나 **soil이 첫 스텝 NaN**(`soil: Advection: conservation of Energy violated; before=NaN, time=1981-01-01`). 원인: 이 UFS-LM4 config는 **soil을 진짜 cold-start한 적이 없음**(static run도 start_type=continue+regtest restart warm-start). soil_nml에 init_temp=288·init_w=150은 있으나 full cold-start 경로가 NaN.
- **하이브리드**(IC_static soil/cana/snow/glac/lake/land warm-start, vegn만 cold-start): soil NaN은 피했으나 **24분+ 0개월 stall**. 근본 문제 = **LM4는 soil·veg가 같은 tile 구조 공유** → warm `land.res`(단일타일 구조)에 multi-tile veg가 갇힘. soil.res만 가져오고 나머지 cold-start도 **tile_index 불일치**로 불가.
- 결론: **multi-tile은 land+soil 동시 cold-start 필수인데 그게 NaN** → offline LM4.1(land_lad2)로는 벽.

**★ 해결 방향 = KIOST-ESM2의 lm4P(LM4.2)를 offline로:**
- **KIOST-ESM2/AMIP INPUT에 평형 multi-tile 식생 restart 실재**(C96, `vegn1.res` **tile=13, tile_index=15085, cohort=61, cohort_index=162058** = 다중 PFT 경쟁 평형, 400년+ 결합 spin-up).
- **단 offline LM4.1(NOAA `land_lad2` branch)로는 못 읽음** — 버전/포맷 불일치: KIOST=lm4P(LM4.2, **질소순환·균근·식물수리·7species**, vegn2 ~180var), offline=LM4.1(5species, N cycle 없음, ~65var, `Anlayer_acm/bl_previous/lai_light_max` 요구하나 KIOST엔 없음). soil.res도 litter_C 풀 차이.
- **→ 올바른 경로**: **lm4P(LM4.2)를 offline(data-atmosphere)로 빌드·구동**. ESM4.5 소스 `src/coupler/simple/coupler_main.F90`에 **`do_land` 스위치 존재** → FMS coupler로 land-only 구동 가능. 그러면 (a) 버전일치로 KIOST 평형 restart warm-start(cold-start 회피), (b) offline이라 대기피드백 없이 순수 지면성능 평가(AMIP은 결합이라 부적합), (c) 진짜 ESM land(multi-tile veg+BGC) 사용.
- KIOST restart 경로: `/home/ydkoh/KIOST-ESM2{,_AMIP}/INPUT/{vegn1,vegn2,soil,land,...}.res.tile*.nc` (04010101).

**★ Phase 1 결론 (2026-07-20): offline lm4P = "NUOPC driver의 LM4 소스 스왑"(Route A)이 유력:**
- **lm4P도 land_lad2** (`lm4P/land_version.inc`에 `#define _USE_LAND_LAD2_`). offline LM4-driver의 LM4(NOAA `land_lad2` branch, LM4.1)와 **같은 land_lad2 코드베이스의 다른 버전**(LM4.2).
- **`land_model_init` 시그니처 완전 동일**(`cplr2land,land2cplr,time_init,time,dt_fast,dt_slow`) → NUOPC cap(`lm4_cap.F90`: land_model_init/update_land_model_fast/slow) 그대로 작동 기대.
- 소스 차이 작음: lm4P 55개 .F90 = land_lad2 51개 **+7개**(`nitrogen_sources·vegn_fire·soil_util·vegn/soil_accessors·transition_io·vegn_util` = LM4.2의 N cycle·fire·util).
- **→ Route A = `LM4-driver/LM4`를 lm4P 소스로 교체 + `lm4_src_files.cmake`에 7파일 추가 + 재빌드.** 우리 CDEPS/WFDE5/C96/gfortran 인프라 재사용. FMS coupler 통째 신축(Route B)보다 훨씬 작음.
- **Phase 2+**(다음 집중작업): ① lm4P 소스 스왑·빌드(컴파일 이슈 해결) → ② KIOST 평형 restart(version 일치) warm-start → ③ WFDE5 offline 짧은 테스트(multi-tile 식생 확인) → ④ 본 spin-up/평가. 리스크: lm4P의 추가 모듈 의존성·cap 세부 인자 차이·N cycle 입력자료(ndep 등).

### 13.9 Route A 스왑 시도 → 두 벽 확인 → Route A/B 갈림길 (2026-07-20, 미결)
**Route A(UFS CMake에 lm4P 스왑) 진행분 (clone: `/data2/ydkoh/lm4/ufs-weather-model-lm4p`, 원본 미변경):**
- clone 완료(669M, .git/build 제외), `LM4-driver/LM4`를 lm4P로 rsync 덮음(원본 백업 `LM4.lad2_orig`), NOAA glue 4개 보존, `lm4_src_files.cmake`에 lm4P 7파일 추가.
- **벽 1 (빌드환경)**: `cmake`가 **ESMF 8.8.0 못 찾음**(`FindESMF.cmake`). `spack load /evn6nxf`만으론 부족 → **`export ESMFMKFILE=/data2/ydkoh/spack-stack/spack/opt/spack/linux-sapphirerapids/esmf-8.8.0-3cfkk4a.../lib/esmf.mk`** 필요(원본 build CMakeCache에서 확인). 쉬운 수정.
- **벽 2 (브랜치 갈라짐, 더 근본)**: NOAA `land_lad2`와 lm4P가 diverge. land_lad2 전용 4파일(`land_chksum`·`predefined_tiles/tiling_input{,_types}`·`read_remap_cohort_data_new.inc`=**offline 타일 초기화 glue**)이 lm4P엔 없어 유지했으나, 공통 모듈을 lm4P로 덮어서 **glue↔lm4P API 불일치 컴파일 에러 예상**(빌드가 ESMF에서 먼저 멈춰 미도달).
- **★ 전략 재고 (사용자 지적)**: **KIOST-ESM2는 GFDL FMS-make(Intel, mkmf)로 lm4P를 네이티브 빌드** 완료(smoke test OK). UFS CMake(gfortran) 빌드와 별개 시스템(둘 다 FMS 라이브러리 사용).
  - **Route A** = UFS CMake 스왑: CDEPS/WFDE5/DATM offline 인프라 재사용(forcing 해결됨) BUT 브랜치 통합 컴파일 반복 + ESMF 환경.
  - **Route B** = GFDL FMS-make로 lm4P + `coupler/simple`(`do_land` 스위치) land-only + data-atmosphere: **lm4P 네이티브(스왑·divergence 없음)** + KIOST 빌드 이미 됨 BUT offline data-atmosphere forcing 드라이버 새로 구성.
  - **결정 미정** — 다음 세션 첫 작업 = Route 선택 후 착수. (Fable 5로 잠깐 전환했다 Opus로 복귀.)

### 13.10 ★★★ Route B 확정 + 재정의 — full coupler에 data-atmosphere가 이미 내장 (2026-07-20)

**Route A 실측 = 폐기 권고.** clone(`/data2/ydkoh/lm4/ufs-weather-model-lm4p`)에서 확인: NOAA offline 개조는 "7파일 추가"가 아니라 **core tile 모듈 안에 짜여 있음**. 원본 land_lad2에서 offline glue(`tiling_input`·`land_chksum`)를 참조하는 파일 7개(`land_tile_io`·`soil_tile`·`vegn_cohort_io`·`glac_tile`·`lake_tile`·`land_tile` + glue). lm4P로 덮은 뒤 참조 **0건 = glue 고아**. `vegn_static_override.F90`의 `read_remap_cohort_data_new.inc` include(2곳)도 lm4P엔 없음. 덮어쓴 8개 파일 diff 합계 **~7,800줄**(land_model.F90만 4,577, lm4P가 1,052줄 더 김). 즉 스왑이 아니라 merge이고, NOAA offline 개조와 LM4.1→LM4.2 과학업그레이드가 같은 파일에 섞여 분리 불가.

**★ 노트 13.8의 Route B 전제는 틀렸었다**: `coupler/simple`의 `do_land`는 land-only 스위치가 아니라 **완전결합 루프 안에서 land만 껐다 켜는 토글**(atmos/ice 호출은 무조건 실행, `do_atmos`/`do_ocean` 없음, 기본값 `.FALSE.`). 게다가 KIOST가 실제 빌드한 건 `coupler/full`이라 **`coupler/simple`은 이 환경에서 컴파일된 적 없음**(`exec/coupler/Makefile`이 전부 `full/`).

**★★ 진짜 답은 full coupler (사용자 지적: "AMIP과 비교해봐라" → 결정타).** AMIP이 결합을 줄인 손잡이가 그대로 land-only로 확장됨:
- `coupler/full/coupler_main.F90:484-490` — **`do_atmos`·`do_land`·`do_ice`·`do_ocean`·`do_flux` 전부 coupler_nml 스위치**("If .FALSE., then execution is skipped"). AMIP은 이미 `do_ocean=.false.`+`ocean_npes=0`+`use_lag_fluxes=.false.`+`concurrent=.false.`로 MOM6를 껐음. `.not.do_atmos` 전용 init 분기 실재(1383·1492행) → **GFDL이 무대기 구동을 설계에 넣어둠**.
- `full/atm_land_ice_flux_exchange.F90` — **LM4가 필요로 하는 모든 강제장에 `fms_data_override('ATM',...)` 훅이 이미 있음**: `t_bot`·`z_bot`·`p_bot`·`u_bot`·`v_bot`·`p_surf`·`slp`·`gust`(874-881), 트레이서 `q_bot`(897), **`flux_lw`·flux_sw 10종·`lprec`(2114-2125)·`fprec`·`coszen`(2149-2150)**.
- data_table 기구는 AMIP에서 이미 실증(`"ICE","sic_obs","siconcbcs",...,"bilinear",0.01` — 0.5° lat-lon input4MIPs → C96 이중선형).
- **→ Route B = 새 드라이버 작성이 아니라 namelist + data_table 작업. 신규 Fortran 0줄 전망.**

**`Surf_Diff` 우려도 해소**: `flux_down_from_atmos`에서만 7필드 사용. `dtmass=0`·delta/dflux=0이면 `gamma=1/(1-0)=1` → 보정항이 정확히 소거되고 explicit flux만 남음, 0으로 나누는 곳 없음. `do_atmos=.false.`면 `update_atmos_model_down`이 안 돌아 초기값 유지 → 0 확인만 필요.

**남은 리스크(미검증)**: ① `do_ice`는 켜둬야 할 가능성(교환격자 마스크; AMIP도 SIS2 SPECIFIED_ICE 유지) → 예상 config `do_atmos=.F., do_ocean=.F., do_ice=.T.(specified), do_land=.T., do_flux=.T.` ② `.not.do_atmos` 경로가 FV3 격자 초기화와 맞물려 실제로 도는지 미검증 ③ **WFDE5는 육지만 있는 0.5° 자료 → bilinear override 시 해안 결측 오염 위험**(grid-verify 대상) ④ Atm 구조체 할당이 do_atmos=.F.에서도 유효한지.

**작업 clone**: `/data2/ydkoh/lm4/esm4p5-lm4p-offline/{src,exec,bin}` (1.4G, DATA·tar 제외). 원본 `~/ESM4p5_KIOSTv2b` 미변경.

### 13.11 ★★★★ Route B 성공 — offline lm4P land-only 완주 + 평형 multi-tile 식생 보존 (2026-07-20)

**결과: `rc=0`, FATAL 0, RESTART 119, `vegn1.res.tile1` = `tile=13 / tile_index=15085 / cohort=61 / cohort_index=162058`** — §13.8이 목표로 삼은 KIOST 400년 결합 spin-up 평형 multi-tile 식생이 **offline에서 그대로 보존**됨. §13.7의 `vegn_to_use='uniform'` 희박식생 문제를 우회하는 경로 확보.

**신규 Fortran 0줄.** 구성 = `coupler/full` + namelist + data_table 뿐:
- run dir `/data2/ydkoh/lm4/RUN/lm4_offline_probe` (AMIP config 복제, INPUT·exe는 심링크로 원본 재사용, 원본 `~/KIOST-ESM2_AMIP` 미변경).
- `&coupler_nml`: `do_atmos=.false.` · `do_ocean=.false.` · `do_ice=.true.` · `do_land=.true.` · `use_lag_fluxes=.false.` · `concurrent=.false.` · `atmos_npes=24`(= 총 rank수, 필수) · `hours=1`.
- `data_table`: `"ATM"` 강제장 전부 **상수**로 주입(파일명 공란 → factor가 상수값). ICE는 AMIP sic/sit/sst 유지.
- 24 PE @climate01, 초기화 atmos 3분35초 → land 42초 → ice 1초, 총 5분26초.

**구조 확인 (소스 근거)**:
- `coupler_main.F90:484-490` — `do_atmos/do_land/do_ice/do_ocean/do_flux` 전부 namelist 스위치. `.not.do_atmos` 분기 주석에 **"data atmos"** 명시(1383·1492행) → GFDL 설계 의도.
- **`atmos_model_init`은 `do_atmos`가 아니라 `Atm%pe`로 게이팅**(1712행) → 대기는 여전히 init됨(화학·에어로졸 포함). 시간적분(`update_atmos_model_*`)만 스킵. **AMIP INPUT 24GB 전량 필요**, 초기화 비용도 잔존.
- **`flux_down_from_atmos`는 `if(do_atmos)` 블록 바깥에서 무조건 호출**(블록 853행 종료, 호출 859행). `sfc_boundary_layer`는 `do_flux` 게이트. → **강제장 주입 훅과 flux 계산은 do_atmos와 무관하게 작동**. 이게 Route B의 핵심 근거.
- ATM override 훅 위치: 상태변수 `sfc_boundary_layer`(874-881, +`sphum_bot` 897), 복사·강수 `flux_down_from_atmos`(2114-2150).

**낮/밤 대조로 확인한 것 (중요)**: 상수 SW=200 W/m²를 전지구 밤낮 없이 주면 `vegetation.F90:1800`→`sphum.F90:31 qscomp`→`lookup_es` overflow로 FATAL(= §4·§5의 cold-start 캐노피 overshoot와 동일 traceback). **SW=0(야간)으론 완주.** 즉 **크래시는 엉터리 상수 강제장 아티팩트이지 구조 문제가 아님.** 실제 WFDE5로 갈 때 재발하면 `lm4/patches/sphum.F90.clamp`의 2줄 clamp가 lm4P `shared/sphum.F90`에 **구조 동일하게 그대로 이식 가능**(escomp 2곳 + check_temp_range). 단 KIOST restart는 cana까지 평형이라 §13.6-154행 논리상 재발 가능성 낮음.

**부수 수정**: probe 사본의 `sst_degk=.true.`→`.false.` (§KIOST 노트 12의 단위 버그, 원본 AMIP은 미수정).

**다음 = 진짜 forcing.** `data_override`는 **단순 파일 리더**(시간·공간 보간만, 강제장 유도 로직 없음). CDEPS DATM이 해주던 걸 **전처리로 옮겨야 함**:
- WFDE5(`/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5/{year}_wfde5.nc`) 보유 7종 = `TBOT·QBOT·PSRF·FSDS·FLDS·PRECTmms·WIND` (0.5°=360×720, 6시간, 1460스텝, noleap, lat **ascending** −89.75→89.75, lon **0-360**).
- 필요 14종과의 격차: `u_bot/v_bot`(WIND 스칼라뿐→분해) · `flux_sw` 4종(FSDS 전천→vis/nir×dir/dif 분할) · `lprec/fprec`(PRECTmms→상 분리) · `coszen`·`z_bot`·`gust`·`slp`(생성).
- **grid-verify 결과(1981 파일)**: 육지 92,889/259,200 = **35.8%**, 물리범위 정상(TBOT 220.3~314.5 K, FSDS 0~1048 W/m², PRECT max 3.9e-3 mm/s). **1D 좌표변수 없음 — `LATIXY/LONGXY` 2D뿐 → data_override의 `bilinear`가 못 읽음. CF 1D lat/lon으로 재작성 필수.**
- **해안 리스크 정량**: 4-이웃 중 하나라도 결측인 육지셀 = **7,936개 = 육지의 8.5%**. bilinear가 fill값을 섞을 수 있는 셀. **동아시아 연안이 정확히 여기 해당**(과제 과학목표와 직결) → 전처리에서 해양측 nearest-neighbor 외삽으로 메운 뒤 넘길 것.
- **CDEPS/DATM 자체 이식은 금지** — NUOPC/ESMF라 FMS coupler와 비호환, Route A의 merge 문제 재현. 유도 로직만 Python 전처리로 옮길 것.

### 13.12 ★★★★ Route B 실제 WFDE5 구동 성공 (2026-07-20, job 8269)

**`rc=0`, FATAL 0, RESTART 119, 1 model-day (1981-01-01 03:00 시작), 24 PE @climate01, 8분 56초.**
- `vegn1.res.tile1`: `tile=13 / tile_index=15085 / cohort=57 / cohort_index=143546` — multi-tile 평형 구조 유지, **cohort 61→57로 변화 = 역학식생이 실제로 진화**.
- 물리 검증(`land_daily`, 무가중 셀평균, C96 준등면적): **precip 2.604e-05 kg/m²/s = 2.25 mm/day**(관측 육지평균 ~2와 일치, max 102 mm/day), **npp 0.387 kg C/m²/yr**(관측 0.4~0.5 범위, 1월이라 음수격자 존재, NaN 1398=빙설·비식생). → **강제장이 지면까지 실제로 도달함이 수치로 확인.**
- `land_month`는 월평균이라 1일 런에선 전부 fill(9.969e+36)이 정상 — 단기 검증은 `land_daily`/`land_8xdaily_*`로 볼 것.

**성공까지 밟은 4개 실패와 각 원인 (재현용):**
1. `time_interp_external: time is before range` — **WFDE5 레코드가 03/09/15/21 UTC**인데 `current_date`를 00:00으로 둠. → `current_date = 1981,1,1,3,0,0` + `force_date_from_namelist=.true.`. (장기런은 전처리에서 연초/연말 경계 레코드를 덧붙이는 게 정석.)
2. `vegetation.F90:1800 → sphum.F90:31 qscomp → lookup_es overflow` — **§4·§5의 cold-start 캐노피 overshoot**. restart는 무날짜 이름이라 평형 캐노피를 정상 warm-start 중이었음에도 발생. 원인 = **KIOST restart는 "결합" 평형**이라 대기 피드백 damping에 의존했는데 offline로 오면서 그게 사라짐(§4가 예측한 그대로). → **clamp 패치로 해결**(아래).
3. `diag_integral_mod: field_count equals zero for field_name prec` — `do_atmos=.false.`면 대기 적분이 누적 안 됨. → `&diag_integral_nml output_interval`을 런보다 길게.
4. `set_time_i: time is negative. days=-24856` — 위 값을 `1.0e8`로 줬더니 **int32 오버플로**(days×86400 < 2^31 → **24,855일이 상한**). → `output_interval = 20000.0`(54.8년).

**★ qscomp clamp를 lm4P에 이식 (clone 전용, 원본 미변경)**:
- `esm4p5-lm4p-offline/src/lm4P/shared/sphum.F90`의 `qscomp`에 **추가 2줄**(`real :: Tc` 선언 + `Tc = min(max(T,173.16),372.16)`) **+ 수정 2줄**(`escomp(T,...)`→`escomp(Tc,...)`, `escomp(T+del_temp,...)`→`escomp(Tc+del_temp,...)`). 주석 포함 실제 diff = 12줄 추가·2줄 수정. **동작을 바꾸는 건 수정 2줄** — 추가분만으론 Tc를 계산해놓고 안 쓰므로 무효과(§5의 "2줄+인자교체"가 정확한 표현). lm4P의 qscomp가 land_lad2와 **구조 동일**해서 `lm4/patches/sphum.F90.clamp`가 그대로 이식됨. 원본 `~/ESM4p5_KIOSTv2b/.../sphum.F90`은 clamp 0건으로 확인.
- 재빌드: `BASEDIR=/data2/ydkoh/lm4/esm4p5-lm4p-offline` 로 `make lm4P/liblm4P.a` → 재링크. 증분빌드 동작(나머지 라이브러리 up-to-date), 실행파일 233 MB. 스크립트 `build_lm4p_clamp.sh`.
- **clamp 발동 2775건/1일** — `Tv` 374.2 K(101°C), 위치 **27.27°E 19.28°S(칼라하리) 남반구 한여름** = §4의 "건조 사막셀+강일사" 조건과 정확히 일치. 결합→offline 전환 transient라 예상된 동작이나, **장기런에서 발동 횟수가 줄어드는지 추적할 것**(평형서 무발동이면 clamp 제거 가능).

**운영 메모**: run dir에 이전 상수-forcing 테스트의 `19790101.*` 산출물이 남아 있음(정리 대상). 실행파일 심링크는 이제 clone 빌드를 가리킴.

### 13.13 디스크 정리 (2026-07-20) — 4.19 TB 회수
`/data2` 여유 **4.2 T → 8.4 T**(98%→95%). 삭제 전 백업 무결성 확인 후 진행.
- `PET*.ESMF_LogFile` **362개 0.58 TB** 삭제. 개당 18.5 GB 디버그 로그(크래시루프 시기 팽창), 과학적 가치 0.
- `ufs.cpld.cpl.hi.*` **269,014개 3.61 TB** 삭제(전부 `RUN/` 아래, 백업 디렉토리엔 0개로 확인 후). CMEPS mediator history = LM4 진단에 미사용([[lm4-cont-spinup-runaway-disk]]). 좌표는 §13.6의 C96 supergrid 복원법으로 대체됨.
- **★ 삭제 전 발견한 백업 공백 (중요)**: `lm4_wfde5_cont`(§13.6 분석의 원본 300년 연속런)의 **월별 history가 백업 없었음**. `spinup_raw`는 restart+land_annual만 보존(land_month **0개**), `history_raw`엔 cont 항목 자체가 없었음. → **`history_raw/lm4_wfde5_cont`에 land_month/annual/static 120개 30 GB 복사**, 최종 IC를 **`IC_wfde5_cont_yr299`(22791205, 49파일 35 MB)**로 아카이브. 30년평균·전구맵 재작도에 필요한 raw는 이제 확보됨.

### 13.14 48 PE 해금 + diag_table 정리 (2026-07-20, job 8270→8271)

**★ "48코어 금지"는 UFS 한정 — FMS 빌드엔 해당 없음.** §10 표의 "48코어 layout(2,4) 교착(land 분해에서 일부 PET가 land점 0개 → init collective hang)"은 **UFS/NUOPC의 ESMF PET 분해** 문제였음. FMS mpp 도메인 분해는 경로가 달라 **동일한 layout 2,4가 49초에 통과**(job 8270: atmos init 19:41:57 → land 19:42:46 → ice 19:42:49, `coupler_init`이 Atmos/Land/Ice PE range 0–47 정상 배정, Ocean은 `do_ocean=.false.`로 미설정 인식). CPU 99.4%로 정상 적분 확인.
- **48 PE 전환 시 같이 바꿀 것 4개**: `coupler_nml atmos_npes=48`(총 rank와 반드시 일치) · `fv_core_nml layout=2,4` · **`land_model_nml layout=2,4`**(빠뜨리기 쉬움) · `SIS_layout LAYOUT=6,8`. C96은 96×96이라 2,4=48×24로 정확히 나뉘고, 해양 720×576은 6,8=120×72로 나뉨.

**★ diag_table이 안 도는 컴포넌트를 계속 쓰고 있었음 (4.3 TB 사고와 동종 낭비).** AMIP diag_table(3,713줄)을 그대로 쓰면 `do_atmos=.false.`인 얼어붙은 대기와 존재하지 않는 해양의 진단을 매번 계산·기록 → 적분 5분 만에 run dir 534 MB(`atmos_daily_cmip` 타일당 12.6 MB 등).
- **land 전용으로 필터링**: 유지 22 스트림(land_* 21 + grid_spec), **제거 89 스트림**(atmos/ocean/aerosol/ice). 필드 855 유지 / **2,478 제거(74%)**. 줄 수 3,714→1,147.
- 스크립트 `lm4/scripts/lm4p_offline_trim_diag_table.py`, 결과 `lm4/config_offline/diag_table.land`. 원본은 run dir에 `diag_table.amip_full`로 보존.
- land 스트림은 **전부 유지**(land_month뿐 아니라 land_daily·land_forcing·land_month_by_species 등) — 나중에 30년평균·전구맵을 다시 그리려면 raw history가 필요하다는 원칙([[lsm-spinup-raw-preservation]]). 특히 `land_forcing`은 지면이 실제 받은 강제장이 기록되어 WFDE5 전달 검증용.

**★ 처리량 추정 오류 정정**: 1일 probe(24 PE, 8분 56초)를 그대로 곱해 "364일 = 20시간"이라 추정했으나 **틀림**. 그 9분 중 초기화 4분 + 종료 시 restart 119개·진단파일 130여 개 쓰기가 대부분이고 1년 런에선 1회로 분산됨. **기록된 LM4 실제 처리량은 연당 7~44분**(§: GSWP3+static veg np24 8.5분/년, dynveg_test 7분/년, WFDE5 연간파일 I/O 44분/년, gustiness+tol 후 30분/년). **단기 런 wall-clock으로 장기 처리량을 외삽하지 말 것.**

### 13.15 ★★★ 성능 — `do_atmos=.false.`가 복사를 안 끈다 (coupler 버그) + 실측 처리량 (2026-07-20)

**★★ 근본 문제: `update_atmos_model_radiation`만 `do_atmos` 게이트 밖에 있음.** `coupler/full/coupler_main.F90`:
- 839행 직렬 경로 `if (.not.do_concurrent_radiation)` — **`do_atmos` 안 봄**
- 920행 동시 경로 `if (do_concurrent_radiation)` — **역시 안 봄**
- 형제 호출은 전부 `if (do_atmos)`: `_dynamics`(830) · `_down`(849) · `_up`(902) · `_state` · `atmos_tracer_driver_gather_data`(789).
- → **어느 쪽으로 설정해도 복사는 반드시 실행됨. namelist로 끌 방법 없음.** 24 PE 1일 probe 프로파일에서 `Radiation` 48회 **148.0초 = main loop(264.7초)의 56%**. 물리적으론 무해(계산 결과를 `flux_down_from_atmos`가 data_override 값으로 덮어씀) — **순수 낭비**.
- **패치(clone 전용, 2곳)**: `if (do_atmos .and. .not.do_concurrent_radiation)` / `if (do_atmos .and. do_concurrent_radiation)`. 재빌드 후 `Radiation` **0회 0.000초** 확인.

**★ 실측 처리량 (job 8272, 48 PE @climate01, 5 model-day, 복사 OFF + diag_table land 전용, rc=0)**
| 구간 | 시간 | 비중 |
|---|---|---|
| Total runtime | 631.2 s | |
| Initialization | 177.8 s | 28% (`atmos_model_init` 154.3 = 얼어붙은 대기 init) |
| **Main loop** | **442.1 s** | **70%** → **모델 1일 88.4 s** |
| Update-Land-Fast | 256.8 s | main loop의 58% (원하는 비용) |
| land_tracer:ddep | 80.6 s | **18% — 건성침착, 다음 최적화 후보** |
| SFC boundary layer | 39.6 s | 9% |
| Ice | 13.7 s | 3% |
| Radiation | **0.0 s** | 패치 확인 |

- **모델 1년 = 8.96시간** (88.4 s/day × 365). 복사 켜짐 24 PE(264.7 s/day) 대비 **3배 개선**.
- **30년 = 269시간 = 11.2일.** 세그먼트는 5년(45시간)×6 권장 — 초기화 178초는 세그먼트당 1회라 무시 가능.

**★ "UFS LM4는 연당 7~44분인데 왜 100배 느리냐"는 잘못된 비교**: 그 런들은 `vegn_to_use='uniform'`(§13.7) = **tile 1개·cohort 1개**였음. 지금은 KIOST 평형 **tile 13·cohort 57 multi-tile 경쟁 식생**이라 지면 계산량 자체가 자릿수로 다름. 즉 느린 건 우리가 원한 과학(다중 PFT 경쟁)의 대가이지 설정 실패가 아님. 추가로 FV3 도메인·교환격자·SIS2를 계속 지고 감(§13.11 "정직한 부채").

**★★ 방법론 교훈 — 진행률/처리량은 로그 문자열로 재지 말 것.** 이 세션에서 3번 틀림: ① 1일 런 wall-clock 외삽 → 20시간/년(고정비 미분리) ② `Total Ice Mass` 블록을 결합스텝당 1개로 가정 → 87.6시간/년(실제는 블록당 ~4.8 모델시간, 5배 과소평가) ③ 그 보정값 → 18시간/년. **정답은 FMS 클록의 `Main loop`** (모델이 직접 잰 값). 벤치마크는 짧은 런(5일)으로 돌리고 클록을 읽을 것.

**미해결/후속**
- `land_tracer:ddep` 80.6초(18%): field_table `land_mod` 화학 트레이서 ~40종이 유발. 제거하면 restart 정합성 위험 → 별도 검증 필요.
- 48 PE는 24 PE 대비 정상 스케일(CLM5 벤치 1.55×와 정합). §13.14의 "48 PE 3.3배 느림"은 위 ② 오측정에서 나온 것으로 **철회**.

### 13.16 ★★★ `do_atmos=.false.`는 대기를 다 끄지 못한다 — 3겹 잔존 계산 제거 (2026-07-20)

offline 성능의 핵심. `do_atmos=.false.`로도 **세 종류의 대기 계산이 계속 돌았고**, 각각 해법이 다름.

| # | 잔존 계산 | 비용 | 해법 | namelist로 가능? |
|---|---|---|---|---|
| 1 | **복사(radiation)** | main loop의 **56%** (148 s/264.7 s @24PE) | **소스 패치** | **불가** |
| 2 | **대류권 화학(tropchem)** | 초기화 154.3→86.4 s, main loop −12% | `do_tropchem=.false.` | 가능 |
| 3 | **트레이서 건성침착(ddep)** | main loop의 7.5% (29 s/387 s) | field_table 양쪽 제거 | 가능 |

**#1 복사 — 유일하게 소스 패치가 필요한 항목.** `coupler/full/coupler_main.F90`:
- 839행 직렬 `if (.not.do_concurrent_radiation)` / 920행 동시 `if (do_concurrent_radiation)` — **둘 다 `do_atmos`를 안 봄.** `do_concurrent_radiation`을 어느 값으로 줘도 **하나는 반드시 실행** → namelist 탈출구 없음.
- 형제 호출은 전부 `if (do_atmos)`: `_dynamics`(830)·`_down`(849)·`_up`(902)·`_state`·`atmos_tracer_driver_gather_data`(789). **복사만 누락** = GFDL 쪽 버그로 보고할 만함(data-atmosphere 모드를 쓰는 누구나 겪음).
- 패치 = 두 조건에 `do_atmos .and.` 추가. **동작 변경이 아니라 원래 의도대로 정렬.** 물리적으로도 무해(복사 결과를 `flux_down_from_atmos`가 data_override 값으로 덮어씀).
- 보존: `lm4/patches/coupler_main.F90.radiation_gate.diff`.

**#3 트레이서 — 양쪽을 함께 제거해야 함(한쪽만 빼면 FATAL).**
- 지면만 빼면: `atmos_tracer_utilities_init: Dry deposition of atmospheric tracer "X" is done on land side, but corresponding land tracer is not defined in the field table.` → 초기화 시점 **정합성 검사**이지 계산상 필요가 아님.
- 따라서 **atmos_mod 트레이서의 `dry_deposition` 선언도 같이 제거**해야 함. 스크립트 `lm4/scripts/lm4p_offline_trim_field_table.py`, 결과 `lm4/config_offline/field_table.land_only`.
- **★ 함정: field_table이 `"TRACER"`와 `"tracer"`를 섞어 씀.** 대소문자 구분 정규식으로 파싱하면 atmos_mod 트레이서 **37개만 잡히고 108개를 놓침**(so4 등) → 두 번 헛돌았음. `re.IGNORECASE` 필수. 이후 145개 인식, 활성 `dry_deposition` 0개.
- **남긴 land_mod 트레이서 2개: `sphum`·`co2`.** co2는 **필수** — `co2_to_use_for_photosynthesis='interactive'`(input.nml:1206)라 캐노피 공기 CO2가 광합성을 구동. 빼면 탄소흡수가 깨짐.

**★ 제거해도 되는 과학적 근거 (4중 확인)**
1. 대기 화학이 안 돌아 침착 결과를 소비할 상대가 없음(일방통행 사장).
2. **오존 손상 과정 없음** — `vegn_photosynthesis.F90` 및 식생 모듈 전체에 ozone 0건.
3. **질소순환 자체가 꺼져 있음** — `soil_carbon_model_to_use = 'CENTURY-like'  !Nitrogen turned off`(input.nml:1454). 옵션 4종 중 질소를 쓰려면 `CORPSE-N` 필요. **결합런·AMIP도 동일** → 우리가 깬 게 아니라 물려받은 설정.
4. 설령 질소를 켜더라도 N은 **`ndep_nit.nc`/`ndep_amm.nc` 처방 지도**에서 받음(`nitrogen_sources.F90`, `n_deposition_type='interpolate-two-maps'`) — **트레이서 침착과 완전히 별개 경로**. 단 현재 `do_nitrogen_deposition=.FALSE.`(기본값)이고 `nitrogen_deposition_nml`도 ndep 파일도 없음. **질소를 켜는 건 새 spin-up + 새 입력자료가 필요한 별도 실험.**
5. 캐노피 공기 트레이서는 **빠른 변수**(난류교환으로 수 시간 평형) → cana.res에서 빠져도 결합런 복귀 시 즉시 재평형. 토양탄소/식생 같은 느린 상태가 아님.

**★ 성능 개선 궤적 (5 model-day 벤치, 48 PE @climate01)**
| 설정 | Main loop | 모델 1년 |
|---|---|---|
| 원래(24 PE, 복사 ON, AMIP diag_table 전체) | 264.7 s/**day** | ~26.8 h |
| 48 PE + diag_table land 전용 + **복사 OFF** | 442.1 s | **8.96 h** |
| + **tropchem OFF** | 387.0 s | **7.85 h** |
| + **트레이서 43종 제거** | (job 8277 측정중) | ~7.3 h 예상 |

- 초기화도 동반 감소: `atmos_model_init` 212 s(24PE) → 154.3 → **86.4 s**.
- 30년 spin-up ≈ 220~235시간. 세그먼트 5년(≈37~40 h)×6 권장.

### 13.17 ★★ "LM4.1은 안 이랬는데 왜 느리냐" — 같은 일을 하는 게 아니다 (2026-07-20)

restart 헤더 직접 비교(둘 다 C96 tile1):

| | UFS LM4.1 (`IC_static_300yr/20100101...vegn1.res.tile1.nc`) | 현재 lm4P (KIOST 평형) | 배수 |
|---|---|---|---|
| tile (셀당 최대) | 1 | 13 | |
| **tile_index (총 타일)** | **3,867** | **15,085** | **3.9×** |
| cohort | 1 | 57 | |
| **cohort_index (총 코호트)** | **3,867** | **143,546** | **37.1×** |

- 식생 물리(광합성·호흡·배분·경쟁)는 **코호트 수에 비례** → **37배**. 토양·눈·에너지는 타일 수 비례 → 3.9배.
- 실측 정합: 지면만 떼면 `Update-Land-Fast` 241 s/5day = **4.9 h/model-yr**. UFS LM4.1은 7~44분/년이었으므로 **7~40×** — 위 배수 범위와 일치.
- **★ 즉 UFS가 빨랐던 건 `vegn_to_use='uniform'`(§13.7)의 최퇴화 모드(식생 1종·코호트 1개)였기 때문.** 지금 느린 건 §13.7에서 문제로 지목한 그것을 실제로 고쳤기 때문 — **성능 저하가 아니라 과학의 비용**. 처리량 비교 시 반드시 tile/cohort 수를 함께 볼 것.

### 13.18 ★★ 트레이서 제거 실패 — `dry_deposition` 정합성 검사는 segfault 방어막이었다 (2026-07-20, job 8275~8277)

§13.16의 #3(트레이서 침착 제거)은 **실패. field_table은 원본 유지가 정답.**
- 지면 트레이서만 제거 → `atmos_tracer_utilities_init: ... corresponding land tracer is not defined` **FATAL**(초기화 검사).
- 그 검사를 없애려 atmos_mod 쪽 `dry_deposition` 선언까지 제거 → 초기화는 통과하나 **첫 결합스텝에서 `forrtl: severe (174) SIGSEGV`**, 스택 `xgrid.F90:4097 get_from_xgrid` ← `atm_land_ice_flux_exchange.F90:1484` ← `sfc_boundary_layer`.
- **원인: 교환격자가 대기(145종)↔지면(2종) 트레이서 배열 크기 일치를 전제.** 그 정합성 검사가 **바로 이 segfault를 막던 방어막**이었음. **경고를 지운다고 원인이 없어지지 않는다** — 검사를 우회한 게 잘못.
- 줄이려면 대기 트레이서까지 일관되게 줄이고 `fv_tracer.res`도 재구성해야 함 → 배보다 배꼽. **잔여 낭비 `land_tracer` 29 s = main loop의 7.5%는 수용.**
- **★ 진단 함정: 죽은 뒤에도 잡이 큐에 R로 남고 CPU 99.7%로 보임.** 일부 rank가 SIGSEGV로 죽고 나머지가 `mpi_wait`에서 무한 대기. **CPU 사용률이 높다 ≠ 계산 중.** 판정은 **로그 mtime**으로 — 17분간 로그가 안 자라면 행. (이 세션에서 "정상 적분 중"이라고 두 번 오판.)

**★ `dt_atmos`는 1800 s 유지 (성능 최적화 대상 아님).**
- `num_atmos_calls = dt_cpld/dt_atmos` = 3600/1800 = 2. 이 루프에서 ① `sfc_boundary_layer`(여기서 ATM data_override = 강제장 시간보간) ② `flux_down_from_atmos`(복사·강수 주입) ③ `update_land_model_fast`(지면 물리)가 함께 돎. 즉 **강제장 갱신 주기이자 지면 물리 timestep**.
- 3600 s로 늘리면 지면 호출 절반 → main loop 387→~266 s(약 −31%, 7.85→5.4 h/yr). **그러나 이건 "아무도 안 쓰는 계산 제거"가 아니라 정확도 거래.**
- **유지 근거**: ① WFDE5가 6시간 자료라 1800 s는 보간만 촘촘할 뿐 정보 증가 없음 — 실질 차이는 지면 적분 해상도 ② **CLM5 `clm5_spinup_gswp3`의 `ATM_NCPL=48` = 1800 s로 동일**(`LND_NCPL=$ATM_NCPL`). 다중 LSM 비교가 과제 핵심인데 LM4만 바꾸면 모델 차이인지 적분간격 차이인지 구분 불가 ③ KIOST 결합런과도 동일. → 바꾸려면 1800 vs 3600 각 1년 돌려 잠열·현열·토양온도 비교하는 **별도 실험**으로.

### 13.19 ★ PE 스케일링 실측 — 48 PE 확정 (2026-07-20, job 8274 vs 8278)

**동일 설정**(복사 OFF·tropchem OFF·diag_table land 전용·field_table 원본·`dt_atmos=1800`·5 model-day·climate01 단독)으로 직접 비교:

| | 24 PE (job 8278) | 48 PE (job 8274) | 배수 |
|---|---|---|---|
| **Main loop** | **547.2 s** | **387.0 s** | **1.41×** |
| Update-Land-Fast | 364.6 s | 241.1 s | 1.51× |
| land_tracer | 44.4 s | 29.0 s | 1.53× |
| Initialization | 135.3 s | 109.1 s | 1.24× |
| `Init: atmos_model_init` | 116.0 s | 86.4 s | 1.34× |
| Total runtime | 692.2 s | 504.3 s | 1.37× |
| **모델 1년** | **11.1 h** | **7.85 h** | |
| **30년** | **333 h** | **235 h** | |

- **병렬효율 70%**(1.41/2). CLM5 벤치 77%와 동급 = 정상 스케일링. 메모리 대역폭 포화 징후 없음(단일 잡 기준).
- layout: 24 PE = `fv_core`/`land_model` 2,2 + `SIS_layout` 6,4 / 48 PE = 2,4 + 6,8.
- **§13.14의 "48 PE 3.3× 느림"은 완전 철회** — 로그 블록을 결합스텝 1개로 오인한 측정 오류였음(실제 블록당 ~4.8 모델시간).
- **결론: 48 PE 사용.** climate01 48코어 단독 점유 가능하므로 24를 쓸 이유 없음(30년 기준 +98시간 손해).

**★ 최종 확정 설정 (전부 실측 검증)**: 48 PE(layout 2,4 / SIS 6,8) · 복사 OFF(소스 패치 `coupler_main.F90.radiation_gate.diff`) · `do_tropchem=.false.` · `diag_table.land` · **field_table 원본** · `dt_atmos=1800`/`dt_cpld=3600` · qscomp clamp(`sphum.F90.clamp.lm4P`) · `sst_degk=.false.` · `diag_integral output_interval=20000.0` · `current_date=1981,1,1,3,0,0` + `force_date_from_namelist=.true.`
→ **7.85 h/model-yr**. 세션 시작 시점(24 PE·복사 ON·AMIP diag 전체, 26.8 h/yr) 대비 **3.4× 개선**.

### 13.20 ★★ KIOST 400년 초기장의 식생 상태 — 역학은 spin-up 됐으나 종 조성은 고정 (2026-07-20)

warm-start 하는 KIOST 평형 restart가 "역학식생까지 평형인가"를 namelist·소스로 확인. **결합런과 우리 offline 런의 식생 스위치는 완전히 동일**(아래 행번호는 각각 `~/KIOST-ESM2/input.nml` / `lm4_offline_1yr/input.nml`).

| 스위치 | 값 | 의미 | 상태 |
|---|---|---|---|
| `use_static_veg` | `.FALSE.` | 식생 고정 아님 | 켜짐 |
| `do_cohort_dynamics` | `.TRUE.` | 코호트 생장·경쟁 | **400년 구동됨** |
| `do_patch_disturbance` | `.TRUE.` | 교란·사망 | **400년 구동됨** |
| `do_phenology` | `.TRUE.` | 계절 위상 | **400년 구동됨** |
| **`do_biogeography`** | **`.FALSE.`** | **기후에 따른 종 전환** | **꺼짐** (lm4P 기본값은 `.TRUE.`, KIOST가 명시적으로 끔) |

- **`do_biogeography`의 실체**(`vegn_dynamics.F90:2231 vegn_biogeography`): 매년(`year1/=year0`) 각 코호트에 대해 `update_species(cc, vegn%t_ann, vegn%t_cold, vegn%p_ann*seconds_per_year, vegn%ncm, vegn%landuse)` 호출 → **연평균기온·한랭월기온·연강수·성장월수에 따라 코호트의 species를 교체**. 끄면 **종 조성이 초기 `cover_type.nc`에서 동결**되고, 기존 종 안에서 생물량·수고·LAI·코호트 구조만 진화.
- **결론**: tile=13 / cohort=57 구조와 생물량은 **진짜 역학식생 평형**. 단 **"어떤 PFT가 어디 사는가"는 spin-up 된 것이 아니라 처방된 것.**
- **우리 spin-up엔 오히려 유리**: 종 조성이 고정이라 warm-start transient가 짧음(조정 대상 = 생물량·물·에너지). 1차년도 진단 목표(지면-대기 결합·물수지·플럭스)에도 무해.
- **★ 한계 (Phase 2 직결)**: 식생 재분포 질문("온난화로 타이가가 북상하는가", 역학식생 과제)은 `do_biogeography=.TRUE.`가 필수이고 **그건 새 spin-up이 필요**. 지금 결과로는 답할 수 없음.

**★ `vegn_to_use = 'uniform'`이 아직 namelist에 남아 있음 (결합런·offline 동일).** §13.7이 지목한 그 설정. **단 이건 cold-start 초기화 경로에서만 작동**하고, restart를 읽는 warm start에서는 무시됨 — 우리 출력이 tile 13/cohort 57로 나온 것이 증거. **cold start를 하는 순간 다시 uniform 함정(식생 희박)에 빠지므로**, 향후 cold start가 필요해지면 `'multi-tile'`로 바꿀 것.

**결정 (2026-07-20): 1차년도 spin-up·진단은 `do_biogeography=.FALSE.` 유지.**
왜: 끄면 종 조성이 `cover_type.nc`(관측 기반 지면피복)에 고정되어, 플럭스·물수지 편차를 **모델 물리 탓으로 해석**할 수 있음. 켜면 모델이 스스로 종을 정하는데 역학 biogeography는 관측에서 벗어나는 게 흔해, "이 편차가 물리 때문인가 식생 분포가 틀려서인가"를 구분할 수 없게 됨 — 진단 프레임워크의 목적을 훼손. 다수 기관이 같은 이유로 끔.
Phase 2 역학식생 실험은 **이 30년 offline 평형을 초기장으로 삼아 biogeography만 켜서 이어달리면 됨**(처음부터 재실행 불필요). 그 실험에서는 "식생 분포가 관측에서 얼마나 벗어나는가"가 곧 결과 = LM4 biogeography 성능 평가.

### 13.21 ★★ 1981 시험 세그먼트: warm start 확인 O, 체이닝은 분산 restart로 막힘 (2026-07-21, job 8280)

**과학은 정상**: rc=0, 07:14 완주(7h35m/model-yr — walltime 여유), RESTART 146개, FATAL 0.
- **★ silent cold start 아님 (확정)**: `RESTART/vegn1.res.tile1.nc.0001` 헤더 = **tile=14, cohort=63**. cold start였다면 §13.7 uniform 모드(tile=1, cohort=1)로 리셋. → KIOST 평형 multi-tile 식생을 정상 warm-start, 1년간 식생 진화(cohort 57→63대).
- **심층토양 T 판정법 주의**: `land_month`의 soil_T **최하층**은 하부경계라 mean 286.9K로 나옴(>285 오탐). §13.6의 270K 기준은 **2 m 깊이(zfull_soil idx 12)**였음 — 최하층 아님. **silent cold start 판정은 vegn tile/cohort 구조로 하는 게 확실**(soil_T 임계값은 층·baseline 의존).

**★★ 블로커: 48 PE는 restart를 분산 조각(`.res.tile1.nc.0001`, `.0002`)으로 씀.**
- `io_layout=1,1`인데도 분산됨 — LM4 land의 compressed-by-gathering(grid_index/tile/cohort) 포맷은 io_layout 무시하고 io-domain별 조각 출력으로 추정. **24 PE probe(job 8269)는 결합 `vegn1.res.tile1.nc` 생성**했으므로 PE수/layout에 의존.
- **결합 도구 없음**: `combine-ncc`·`mppnccombine`·`FRE-NCtools` 모듈 전부 climate00에 부재(tomo는 `intel19/FRE-NCtools` 썼음). KIOST AMIP INPUT의 결합 restart는 tomo에서 결합된 것.
- **guard 3 오탐**: 체인이 `RESTART/cana.res.tile1.nc`(결합명)을 찾는데 실제는 `.0001/.0002` → stat 실패 → "not newer" ABORT. 실제론 정상 완주. guard가 세그먼트를 죽여 데이터 오염은 없었음(의도된 안전 방향).

**미결 — 다음 세션 결정 필요 (셋 중 택1)**:
1. **24 PE로 실행**: 결합 restart 네이티브 생성, 체이닝 깨끗, 도구 불필요. 대신 11.1 h/yr(48 PE 7.85 대비 1.4×). 30년 333h vs 235h(+98h).
2. **FRE-NCtools 빌드**: 48 PE 속도 유지, 단 mppnccombine + **combine-ncc**(land 압축포맷 전용) 빌드 필요.
3. **분산 restart 직접 read**: INPUT의 stale 결합본 제거 후 분산 조각만 두고 read. 매 세그먼트 동일 48 PE/layout이라 이론상 가능하나, io_layout=1,1인데 2조각인 모순 미해결 → 검증에 8h 런 필요, 리스크.
- **권고: 옵션 1(24 PE)**. 도구 빌드·검증 리스크 없이 즉시 굴러감. 98h 손해는 combine 빌드·디버그 시간과 상쇄. forcing·config·clamp·guard는 그대로 재사용.

**★ 왜 24 PE는 결합, 48 PE는 분산인가 (근본 원인, 소스 확인)**: `io_layout=1,1`은 **정형 격자(대기·해양)에만** 적용됨. LM4 land는 **비정형 격자(UG, compressed land-tile)**라 별도 파라미터 `npes_io_group`(land_model_nml, KIOST config에 **=8** 설정됨)로 I/O 그룹을 나눔. `land_data.F90:408-409`: `ug_io_layout = mpp_get_io_domain_UG_layout(ug_domain); append_io_id = (ug_io_layout>1)` — 이 값이 1보다 크면 `.0001` 접미사(분산)가 붙음. UG 도메인은 **육지점 보유 PE만** 포함하므로 실제 조각 수는 PE 배치에 의존: 24 PE(2,2)→ug_io_layout=1→결합, 48 PE(2,4)→ug_io_layout=2→분산. **즉 io_layout이 같아도 land restart 형식이 갈린 건 io_layout이 애초에 land에 적용 안 되기 때문.** → **가능성(미검증): `npes_io_group`을 전체 PE수(48) 이상으로 키우면 48 PE에서도 ug_io_layout=1(결합)이 나올 수 있음** → 48 PE 속도 유지 + combine 도구 불필요. 단 diag 형식·I/O 성능 영향 있어 세그먼트 1회 검증 필요. **PE 수를 바꿀 때는 반드시 land restart 형식을 재확인할 것.**

### 13.22 2년치(1981-82) 진단 그림 — spin-up 정상 확인 (2026-07-22)

첫 2 세그먼트 월별 출력으로 시계열+맵. 스크립트 `lm4/scripts/lm4p_spinup_{extract_monthly,extract_maps,plot_timeseries,plot_maps}.py`. 서버에서 전지구 육지평균 CSV·맵 npz 추출(무가중 셀평균, C96 준등면적) → 로컬 작도. 좌표는 §13.6 supergrid 복원 재사용.
- **계절순환 정확·재현성 좋음**: 증발산·GPP·LAI 북반구 여름 최대, SWE 겨울 최대. 맵 격자검증 통과(LAI 아마존/콩고/동남아 짙음, 사막 0; 토양수분 사막 건조).
- **★ 느린 풀 안정 = KIOST 평형 warm-start 확인**: tot_soil_C 7.40-7.49 kg C/m²(±1%), col_water 3405-3433 kg/m²(±0.8%) — 계절 톱니만, 표류 거의 없음.
- **★ 함정 1: 22개월(24 아님)** — 세그먼트가 Jan 1 03:00 시작이라 **각 해 1월이 부분월로 diag에서 누락**. WFDE5 레코드가 03/09/15/21이라 03시 시작 불가피. spin-up 궤적엔 무관하나 **계절 climatology 만들 때 1월 부재 처리 필요**.
- **함정 2: 맵 극지 부채꼴 산점 아티팩트**(runoff/sens) — C96 극 조밀 + 빙하타일. 값 아닌 표시 문제, 본토 패턴 정상. runoff는 육지 값이 작아(mean 0.05 mm/day) vmax=4에서 거의 흰색 → 육지만 보려면 vmax 낮출 것.

### 13.23 GIMMS LAI4g grid-verify 통과 (2026-07-22)
`/Volumes/data02/LAI/GIMMS_LAI4g_V1.2_1982_2020.nc` — LM4 LAI 평가용. 5검사 전부 통과:
- 좌표: lat **오름차순** −90→90, lon **0-360**, 0.5°(361×720). time = days since **1979-01-01**(index0 = 1982-01, 468개월 = 1982-2020). **JJA 1982 = time index 5,6,7**.
- **원본배열 플롯(무좌표)**: 아마존/콩고/동남아 짙음, 사막·빙설 마스킹, 위도 그래디언트 정상 = 실제 대륙. 깨진 자료 아님.
- 값: LAI 0-6.6, **_FillValue=65535** → `>100` 가드로 마스킹. valid JJA 17.9%(식생지만; 사막·빙설은 제품이 마스킹, 정상). tropics 3.05 > boreal 2.50.
- 스크립트 `lm4/scripts/gridverify_gimms.py`, 검증그림 `figures/_gridverify_gimms.png`.

### 13.24 LAI 다년 비교 + PFT 분해 + runoff 변수 정정 (2026-07-22)

**★ 정정: §13.22의 "1월 누락"은 틀림 — 실제는 12월 누락.** 세그먼트가 364d21h로 다음 해 Jan 1 00:00에 끝나 12월 flush 전 종료. land_month에 1~11월 존재, 12월 부재. JJA엔 무관.

**★★ runoff 변수 함정**: §13.22 그림에서 "runoff"로 쓴 `frunf`는 **고체(빙설) 유출**("total rate of solid runoff")이라 육지가 거의 0(흰색)이었음. **총 유출은 `runf`**. 성분 분해도 있음: `soil_rbf`(baseflow)·`soil_rie`(침투초과)·`soil_rsn`(포화)·`hrunf`(현열). 과제 핵심 "지면→해양 결합 매개(담수유출)"엔 `runf` 또는 하천 라우팅(river.F90) 사용. **runoff 그림 재작성 필요**.

**LAI vs GIMMS LAI4g (JJA)**: 단일해(1982) + 5년평균(1982-1986). GIMMS 1982부터라 공통기간 1982-1986. 스크립트 `lm4/scripts/{extract_lm4_lai_jja,extract_lm4_lai_years,plot_lai_compare,plot_lai_compare_5yr}.py`, 그림 `figures/lm4_vs_gimms_lai_jja{1982,_5yr}.png`.
- 5년평균 **공간상관 0.66, bias +0.69**. 공간패턴 좋음(r 안정 0.63-0.65), 계통편차 = **열대 LM4 과대, 아북극 LM4 과소** = [[CRESCENDO 다중LSM 평가]]의 공통 편향과 일치(커뮤니티 공통 난제, LM4 고유 결함 아님).
- **★ LAI 아직 상승 중**: 전지구 JJA LAI 2.37(1982)→2.50(1986), +5.5%. GIMMS는 2.11에서 평평 → bias가 매년 벌어짐(+0.61→+0.75). **느린 풀(토양탄소·목재)은 평형이나 잎(LAI)은 결합→offline 전환 후 아직 조정 중.** LAI 안정엔 ~10년 필요 추정.
- **사막 처리 차이**: LM4는 사막도 0에 가까운 작은 양수(사하라 0.01), **GIMMS는 극건조 사막 마스킹(NaN)**. bias는 GIMMS 유효(식생)격자에서만 계산 → 사막 오염 없음. 반건조(호주내륙)는 둘 다 값 있음(LM4 0.31 vs GIMMS 0.27).

**PFT 분해** (`land_month_by_species`, species=7): prioria(열대상록), picea(가문비), larix(낙엽송), acer(단풍), c4grass, c3grass, default. 종별 `lai`(time,species,grid_index)로 PFT share = lai_sp/total. 스크립트 `lm4/scripts/{extract_pft,plot_pft}.py`, 그림 `figures/lm4_pft_composition.png`.
- 고LAI 지역별 우점 PFT(물리적 타당): **Amazon prioria 52%·c3grass 39% / Congo·SE Asia prioria 83-84% / Boreal N.Am picea 60% / Siberia c3grass 50%·picea 38% / E-US acer 77%**. 전지구 잎면적 share: c3grass 39%·prioria 32%·picea 15%·acer 10%.

**논문**(reference/papers/, Notion 문헌DB 등록): Shevliakova 2024 JAMES(LM4.1 공식), Weng 2015 BG(PPA 원전), Weng 2019 BG(경쟁·N/CO2), CRESCENDO 2025 BG(다중LSM LAI 방법론+공통편향).

### 13.25 12년치(1981-1992) spin-up 궤적 — 느린 풀 평형, LAI·유출은 아직 조정 중 (2026-07-27, 박제 2026-07-29)

`lm4_spinup30` 첫 12 세그먼트 월별 land-mean. 데이터 `lm4/data/monthly_11yr.csv`(서버 `RUN/lm4_spinup30/monthly_11yr.csv` 복사본), 스크립트 `lm4/scripts/{extract_monthly_11yr,plot_11yr}.py`, 그림 `figures/lm4_spinup_11yr.png`. **132 레코드 = 12년 × 11개월**(§13.24의 12월 누락 그대로) → 연평균은 **Jan-Nov 평균**. 표류 판정엔 무해(매년 동일 계절 샘플).

| 변수 | 1981 | 1992 | Δ (11년) | 연 표류 | 판정 |
|---|---|---|---|---|---|
| **bwood** (목재 C) | 1.678 | 1.667 | **−0.7%** | −0.0005 kgC/m²/yr | **평형** |
| col_water | 3422.6 | 3392.1 | −0.9% | −2.68 kg/m²/yr | 준평형(느린 배수) |
| theta_sfc | 0.598 | 0.590 | −1.4% | −0.0008 m³/m³/yr | 준평형 |
| SWE | 85.8 | 84.9 | −1.1% | −0.124 kg/m²/yr | 준평형 |
| GPP | 1.137 | 1.149 | +1.0% | +0.0022 kgC/m²/yr² | 준평형 |
| soilC | 7.430 | 7.675 | +3.3% | **+0.021 kgC/m²/yr** | 완만 상승 |
| **LAI** | 2.075 | 2.271 | **+9.4%** | **+0.0153 /yr** | **미평형** |
| **runoff (`runf`)** | 0.764 | 0.667 | **−12.7%** | −0.0058 mm/d/yr | **미평형** |
| soilT_2m | 288.65 | 289.29 | +0.2% | +0.060 K/yr | 상승 中 |

- **★ 계층적 수렴이 뚜렷**: 목재(가장 느린 탄소풀)가 이미 평형인데 **잎(LAI)만 +9.4%로 계속 상승** → KIOST 결합 평형에서 offline WFDE5로 갈아탄 뒤 **엽면적이 새 강제장에 재적응 중**. §13.24의 5년치 추정(+5.5%, "안정에 ~10년")과 일관 — **12년 시점에도 아직 안 멈춤**.
- **★ runoff −12.7%는 LAI 상승의 귀결로 읽힘**: 잎이 늘면 증산·차단이 늘어 유출이 준다. evap은 −2.4%로 거의 평평한데 runoff만 크게 준 건 **col_water 감소(−30 kg/m²)와 짝** → 물수지가 아직 재분배 중. **1차년도 진단에서 유출을 관측(GRDC)과 비교할 땐 초기 수년을 버리고 후반부를 쓸 것.**
- **soilT_2m +0.06 K/yr**: 2 m 심층온도가 아직 상승 中. §13.6의 wrap 열충격([[lsm-cyclic-forcing-wrap-shock]])과 별개 — 이 런은 아직 1 cycle 내부라 되감기 미발생.
- **결론: 30년 중 12년 시점에서 "느린 탄소·물 저장고는 평형, 식생-수문 결합은 조정 中".** 진단용 기간은 **후반 10~15년**(1996~2010)을 권장.

### 13.26 LAI vs GIMMS 재계산 — 공통 1° 격자·datakit native (2026-07-27, 박제 2026-07-29)

§13.24의 비교를 **격자 정합을 제대로 잡아** 다시 계산. 스크립트 `lm4/scripts/{gv_datakit_gimms,lai_metrics_1deg,plot_lai_1deg}.py`, 그림 `figures/lai_1deg_compare.png`.
- **방법 변경**: GIMMS를 `/Users/youngdaekoh/data2/LAI-DataKit/derived/gimms_lai4g/native0083/consolidated`(**native 1/12°**, 2160×4320, 반월별)에서 읽어 **12×12 픽셀 박스평균으로 1°로 상향**, LM4 C96 점은 각 1° 박스에 binning. 양쪽 유효 격자(GIMMS 유효 = 식생지)에서만 지표 산출.
- **결과 (JJA 1982-1986, n=12,401 육지 1°셀)**: **r = 0.71 · bias = +0.61 · RMSE = 1.60**.
- **★ §13.24(0.5°, r 0.66/bias +0.69)와 다른 값이지만 결론은 동일** — 격자·집계 방법이 달라서지 결과가 바뀐 게 아님. 1°로 올리면 소규모 잡음이 평균돼 **r이 오르는 게 정상**. 다른 모델과 비교 표를 만들 땐 **반드시 같은 공통격자·같은 마스크로** 재계산할 것([[lsm-landmean-comparability]]).
- **편차 구조 재확인**: 차이맵은 **열대(Amazon·Congo·SE Asia) 진한 적색(LM4 과대)**, **북미 boreal·시베리아 청색(LM4 과소)**. 동일 위도대 zonal-mean에서 적도 LM4 ~6.0 vs GIMMS ~4.4, 60-70°N은 LM4가 약간 낮음. = CRESCENDO 공통편향과 일치.
- **★ 중간산출 npz 미보존**: `lm4_lai_jja_1982_1986.npz`(서버 추출본)·`lai_1deg_1982_1986.npz`가 로컬에 없음 — 작업 cwd에서 실행돼 유실. 재작도하려면 `extract_lm4_lai_years.py`부터 다시 돌려야 함. **다음부터 중간 npz는 `lm4/data/`에 저장할 것**([[lsm-spinup-raw-preservation]]).

### 13.27 진행 상황 스냅샷 (2026-07-29 13:00)

| 잡 | 진도 | 실측 페이스 | 완료 예상 |
|---|---|---|---|
| 8305 `lm4_spinup30` (24 PE, WFDE5 1981-2010, dynveg) | **1996 세그먼트 = 16/30년** | 11.1 h/model-yr (§13.19 예측치와 일치) | 8월 초순 |
| 8306 `clm5_bgc_ad` (48 PE, climate02) | **restart 0092 = 91/200년** | **~2.5 h/model-yr** | 8월 중순 |

**★ CLM5 BGC-AD는 Sp 벤치(35.3분/년, `CLM5_SPINUP_NOTES.md` §5)의 약 4배 느림.** BGC(탄소·질소) 비용. 200년을 다 채우기보다 **TOTECOSYSC 표류 ≤1 gC/m²/yr 도달 시 조기 종료** 판단이 현실적.

**남은 작업 (우선순위)**: ① 평가용 **토양수분·토양온도 관측 DB** 미착수(1차년도 점검기준 명시 항목, 최대 갭) — ERA5-Land/ESA CCI SM/GLEAM ② runoff 그림 `runf`로 재작성(§13.24) ③ FluxCom·GRDC 확보 ④ 30년 완주 후 후반 10~15년으로 진단 기간 확정(§13.25).

### 13.28 ★★ river 모듈은 처음부터 돌고 있었다 — 출력만 안 걸려 있었음 (2026-07-29)

**발단**: 다중 LSM 변수 매핑(`analysis/diag/lsm_variable_mapping.md`) 중 "하천 방류가 4개 모델 어디에도 없다"고 판단 → 오판이었음. 확인 결과 **CLM5는 MOSART가 이미 방류를 출력 중**이었고(`clm5_bgc_ad.mosart.h0.*`에 `RIVER_DISCHARGE_OVER_LAND_LIQ`·`DIRECT_DISCHARGE_TO_OCEAN_LIQ`·`TOTAL_DISCHARGE_TO_OCEAN_*`·`areatotal`), **LM4도 river 모듈이 활성**이었음.

**LM4 river가 살아있다는 증거** (추측 아님):
- `INPUT/river.res.tile1~6.nc` (하천 상태 restart, KIOST 평형에서 warm-start) + `river_data.tile*.nc`(하천망) + `river_iron.nc`
- `input.nml`에 `&river_nml`(dt_slow=86400, DHG 하폭수리기하 계수)·`&river_physics_nml` 설정됨
- **즉 물은 하천망을 따라 흘러 바다로 나가고 있었고, 그 값을 파일에 안 썼을 뿐.** `diag_table`의 river 항목 수 = **0**이었음.

**소스에서 확인한 river 진단 필드** (`src/lm4P/river/river.F90` `register_diag_field`, 모듈명 `river`):

| 필드 | 설명 | 단위 |
|---|---|---|
| **`dis_liq`** | **liquid discharge to ocean** | kg/(m² s) |
| `dis_ice` | ice discharge to ocean | kg/(m² s) |
| `dis_heat` | 열 방류 | |
| **`rv_Qavg`** | long-time average vol. flow | **m³/s** |
| `rv_o_<tr>` / `rv_i_` / `rv_s_` 등 | 하천 유출/유입/저류 (tracer: `h2o`·`ice`·`het`) | |
| `rv_depth`·`rv_width`·`rv_veloc` | 하천 수심·폭·유속 | |

- **★ `rv_Qavg`가 m³/s** → **GRDC 관측 유량과 단위 변환 없이 직접 비교 가능.**
- 격자: 6타일이면 `grid_xt`/`grid_yt` + `geolon_t`/`geolat_t` aux (land 스트림과 동일 C96) → 기존 land 분석 좌표 그대로 재사용 가능.

**조치 (2026-07-29 적용)**: `diag_table`에 `river_month`(8필드)·`river_daily`(4필드) 스트림 추가. 서버 원본은 `diag_table.bak_20260729`로 백업. 편집은 scp→로컬→scp 패턴.
- **재컴파일·잡 중단 불필요**: FMS는 세그먼트마다 실행파일을 새로 띄우며 diag_table을 재독. → **1997 세그먼트부터 자동 반영**, 진행 중이던 1996 세그먼트엔 영향 없음.
- 일별을 같이 건 이유: GRDC가 대개 일유량이고 홍수 첨두는 월평균에서 소실됨.

**★ 출력 구성이 세그먼트 중간에 바뀐 상태**: 1981-1996 = river 출력 없음 / 1997-2010 = 있음. **§13.25 결론(진단 기간 = 후반 10~15년)과 겹쳐서 실질 손실은 거의 없음.** 다만 전 기간 시계열을 그리면 1997에서 계열이 시작되므로 그림 캡션에 명시할 것.

**미검증 (다음 세션 확인)**: 1997 세그먼트 산출물에 `19970101.river_month.tile*.nc`·`river_daily`가 실제로 생기는지. 필드명 오타가 있으면 FMS가 경고만 내고 조용히 건너뛰므로 **파일 존재 + 변수 목록을 반드시 눈으로 확인할 것.**

**교훈**: "출력에 없다 ≠ 모델이 계산 안 한다." 진단 변수 부재를 보면 **먼저 소스의 `register_diag_field`와 restart/INPUT을 확인**할 것. 매핑표를 출력 헤더만으로 만들면 이런 착각을 한다.

### 13.29 ★★ LAI가 코드에서 어떻게 만들어지는가 — 전체 추적 (2026-07-29)

**상세 문서: `lm4/LM4_LAI_CODE_TRACE.md`** (파일·행번호·식·소비처·위도의존성까지. 코드를 안 열어도 확인 가능하도록 작성). 아래는 요약.

**★ LAI는 예후변수가 아니다.** 예후변수는 `bl`(잎 탄소, kg C/individual)이고 **LAI = `bl`/`LMA`로 매 스텝 만드는 진단량**. `LMA`(leaf mass per area, 기본 0.036 kg C/m²)는 **종별 상수**(`vegn_data.F90:220`, namelist로 `specific_leaf_area`=1/LMA로도 지정 가능). → **"LAI가 왜 이런가"는 반드시 "`bl`이 왜 이런가"로 내려가야 함.**

| 단계 | 위치 |
|---|---|
| 핵심 식 `area = bl/LMA` | `vegn_cohort.F90:567-578` (`leaf_area_from_biomass`) |
| 코호트 LAI 확정 | `vegetation.F90:2307-2530`, 계산 본체 **2416-2424** |
| `bl` 성장(배분) | `vegn_dynamics.F90:1710`, 상한 `bl_max`(1692-1701)·`deltaLAI_max`(1690) |
| `bl` 낙엽 | `vegn_dynamics.F90:2188`, 직후 LAI 재계산 2192 |
| 개엽/낙엽 스위치 | `vegn_dynamics.F90:2061-2228`, 트리거 **2109-2135** |

- **목표 잎량** `bl_max = LMA × laimax × crownarea × (1-internal_gap_frac)` → **종별 `laimax`가 LAI 천장**. 편차 진단 시 1순위 파라미터.
- **phenology 트리거**: 상록수는 항상 LEAF_ON. 낙엽수는 `gdd > gdd_crit .and. tc_pheno >= tc_crit .and. .not.drought` → 개엽 / `tc_pheno < tc_crit`(한랭, gdd 리셋) 또는 `drought`(건조, **gdd 리셋 안 함** — 아열대에서 잎이 영영 안 나는 걸 막기 위함, 소스 주석에 명시) → 낙엽.
- **restart에 LAI는 없다.** `bl`만 저장, 재시작 시 재계산.
- **소비처**: 복사(`vegn_radiation.F90:199,242,256-258`) · 광합성(`vegn_photosynthesis.F90:276,298`) · **`:380` `stomatal_cond = stomatal_cond*cohort%lai`**. → **기공전도도가 LAI에 정비례** = §13.25의 `LAI +9.4% ↔ runoff −12.7%` 연쇄가 나오는 지점.

**★ 위도별로 다른 식이 아니다.** 코드에 위도 항 자체가 없고 전 지구 동일 식. 위도 효과는 ① 종 분포(`cover_type.nc` 처방, `do_biogeography=.FALSE.`) ② 종별 파라미터(`LMA`·`laimax`·`tc_crit`·`gdd_crit`·`phent`) ③ 국지 기후(`tc_pheno`·`gdd`·토양수분) **세 경로로만 간접 진입**. → §13.26의 아북극 과소편차는 **①/②/③ 중 무엇인지 갈라야** 손잡이가 정해짐(각각 `cover_type.nc` / `laimax`·`LMA` / `gdd_crit`·`tc_crit`).

### 13.30 ★★ native `lai`와 CMIP `lai`는 다른 필드다 — 마스크가 −9% 차이 (2026-07-29)

같은 코호트 상태에서 **두 개의 서로 다른 LAI 진단이 동시에 출력**되고 있음(`vegetation.F90`):

| 스트림 | 송출 코드 | 정의 |
|---|---|---|
| native `lai` (`land_month`) | `:2120` `send_cohort_data(..., weight=layerfrac, op=OP_SUM)` | 코호트 LAI를 층분율 가중 합 |
| CMIP `lai` (`land_month_cmip`) | `:2138` `send_tile_data(sum(nindivs*leafarea))` | 지면 단위면적당 총 잎면적 |

**실측 (1995, 11개월, `lm4/scripts/cmp_lai_native_vs_cmip.py`)**:

| | native | cmip |
|---|---|---|
| 유효 육지격자 | 17,306 | **18,704** |
| 전지구 평균 | **2.2822** | **2.0721** |
| 공통격자 평균 | 2.2822 | 2.2395 (−1.9%) |
| 상관 | **0.9977** | 비율 median 0.9990 (p5 0.92) |

1. **값 자체는 거의 동일** (r=0.998). → **§13.24·§13.26의 bias·상관 결론 재계산 불필요.** 우리가 쓴 건 전부 native(`extract_lm4_lai_years.py:35`·`extract_monthly_11yr.py:45`가 `land_month`를 읽음).
2. **★ 진짜 차이는 마스크**: cmip은 `fill_missing=.TRUE.`(`vegetation.F90:1227`)라 **식생 없는 격자를 0으로 채움** → 격자 1,398개 추가, 전지구 평균이 **2.28 → 2.07 (−9%)**.

**규칙**: 전지구 평균 LAI를 인용할 땐 **스트림·마스크를 반드시 명시**(§13.24의 "2.37→2.50"은 native 기준). GIMMS 비교는 GIMMS 유효격자에서만 계산하므로 영향 없음. **CMIP 아카이브·ILAMB 입력엔 cmip 스트림**을 쓸 것. [[lm4-lai-native-vs-cmip]]

### 13.31 ★★★ 12월이 없는 진짜 이유 = 월 경계가 03:00 앵커, 3시간 부족 (2026-07-29)

**§13.22/§13.24의 "12월 누락"을 끝까지 파고든 결과.** 원인은 FMS 동작이 아니라 **산술**이었다.

`land_month` 시간축 실측 (1983):
```
첫 레코드 중심 : 1983-01-16 15:00        → 1월 구간 = Jan 1 03:00 ~ Feb 1 03:00
마지막 구간    : 1983-11-01 03:00 → 1983-12-01 03:00
따라서 12월 구간 = Dec 1 03:00 → Jan 1 03:00
런 종료        = Jan 1 00:00                    ← 3시간 부족
```
- **월 구간이 00:00이 아니라 03:00에 앵커된다.** FMS diag_manager가 월 간격을 **모델 시작시각**에서 한 달씩 더해가는데, WFDE5 레코드가 03/09/15/21시라 런이 03:00에 시작하기 때문.
- FMS는 평균 구간이 **완성돼야** 레코드를 쓴다 → 12월은 3시간 모자란 채 런이 끝나 **애초에 생성되지 않는다**(파일에서 빠지는 게 아님).
- `chain_spinup30.sh` 주석의 *"lands exactly on Jan 1 00:00 ... so every year writes exactly 12 land_month records"* 는 **월 경계가 00:00이라는 잘못된 가정**에 근거. 실측은 15년 전부 11개.

**★ 달력은 NOLEAP이다 (§121 기록 정정).** `input.nml` `coupler_nml`에 `calendar = 'NOLEAP'`. §121은 "leap 그대로 쓰고 spin-up·production 전부 leap"으로 적혀 있으나 **실제 실행 설정과 다르다.**
- 근거: 모델 출력 `land_forcing` 자체가 `calendar=noleap`, 1984년 파일에 **Feb 29 레코드 0개**.
- 강제장도 noleap: WFDE5 원본은 `proleptic_gregorian`(1984-02 = 116레코드)이지만, **CLM용 변환 단계에서 noleap으로 만들어졌고**(1460 레코드, 평년·윤년 동일) LM4 변환기가 `v.calendar = tvar.calendar`로 그대로 상속(`lm4p_offline_wfde5_to_atm.py:79`).
- CLM5 케이스가 `NO_LEAP`이라 **CLM 입장에선 정당**하고, LM4도 NOLEAP이라 **모델·강제장이 일치**한다. 날짜 어긋남 없음.
- **따라서 윤년 분기가 필요 없다**: 모든 해가 365일. `days=365, hours=0`이면 12월 구간이 정확히 닫히고, 강제장은 365.375일까지 있어 9시간 여유.
- 덤: 현재 설정의 "연 경계 3시간 gap"(체인 주석이 인정)도 함께 사라진다.

### 13.32 12월 복원 경로 — 변수별로 갈린다 (2026-07-29)

월별 스트림에만 12월이 없다. **일별·3시간 스트림에는 있다.**

| 스트림 | 12월 | 변수 |
|---|---|---|
| `land_daily` | **1~30일** | precip · runf_soil · snow_soil · snow_lake · npp · soil_liq · soil_ice · evap_land · t_ref_max/min · vegn_temp_max/min |
| `land_daily_cmip` | 1~30일 | mrso · mrsos · snc · snw · mrro |
| `land_8xdaily_cmip` | **1~31일 전부** | mrro |
| `land_8xdaily_inst` | 1~31일 | mrsos |

- **복원 가능**: 유출 · 토양수분 · 적설 · 증발 · 강수 · NPP → **1981년부터 DJF 가능**
- **복원 불가**: **`lai` · `gpp` · 잠열/현열 · `soil_T` · 탄소풀** — 일별 스트림에 없음

**★ DJF는 남반구 성장기다.** "LAI는 성장기(MJJAS)만 보면 되니 12월 없어도 된다"는 **북반구 한정 논리**. 아마존·콩고·남아프리카·호주를 성장기에 평가하려면 DJF가 필수이고, 하필 §13.26에서 **열대 과대편차가 가장 컸던 지역**이다. → LAI도 12월이 필요하고, 일별로는 복원이 안 되므로 **재실행 외에 방법이 없다.**

### 13.33 표류 종료 시점 재측정 — §13.25 정정 (2026-07-29)

1995년까지 15년으로 다시 계산 (`lm4/scripts/plot_15yr.py`, `figures/lm4_spinup_15yr.png`, `lm4/data/monthly_15yr.csv`).

| | 1981-86 | 1987-92 | 1993-95 | **1990-95 선형추세** |
|---|---|---|---|---|
| LAI | 2.187 | 2.264 | 2.274 | **−0.04 %/yr** |
| runoff | 0.757 | 0.715 | 0.726 | +0.35 %/yr |
| col_water | 3418 | 3401 | 3398 | −0.01 %/yr |
| GPP | 1.142 | 1.154 | 1.150 | −0.23 %/yr |
| SWE | 85.2 | 84.4 | 84.6 | −0.00 %/yr |
| **soilC** | 7.523 | 7.647 | 7.700 | **+0.14 %/yr (미평형)** |

- **§13.25의 "LAI 아직 상승 중 +0.015/yr"는 1981-1992 창에서 본 값**이고, 1981-89의 상승이 그 적합을 지배했다. 실제로는 **LAI가 1986-87에 평평해진다.**
- 변수별 평형 시점: **LAI ~1986-87 / 컬럼수분 ~1992 / 토양탄소는 1995까지도 미평형.**
- → **진단 창을 1990부터**로 잡는 것이 안전(보수적). 1990-2010 = 21년.

### 13.34 12월 재실행 (1990-1996) 착수 + 함정 2개 (2026-07-29)

**설정**: `/data2/ydkoh/lm4/RERUN/wA`, climate02 단독 24랭크, 7년 순차(≈78시간).
스크립트 `lm4/scripts/rerun_worker.sh`·`run_rerun.sh`(호스트 템플릿). 각 해는 **독립** — `archive/y(Y-1)`의 restart로 시작하므로 원 궤적을 그대로 재현하고 12월만 추가된다(체인 아님).

**★ 함정 1 — FMS는 area measure 필드도 diag_table에 요구한다.**
river 스트림 추가(§13.28) 후 첫 실행이 즉사:
```
FATAL: register_diag_field: river/dis_liq AREA measures field NOT found in diag_table
```
`dis_liq`·`dis_ice`·`dis_heat`·`rv_o_*`가 `area = id_cellarea`로 등록돼 있고(`river.F90:1393`), 그 area 필드(`river/cell_area`, static, `:1345`)가 **같은 출력 파일에 함께 선언돼야** 한다. → 두 river 파일에 `"river", "cell_area", "cell_area", <file>, "all", .false., "none", 2` 추가로 해결.
**본 체인도 같은 diag_table을 읽으므로 1997 세그먼트 시작 시 똑같이 죽었을 것** — 재실행 덕에 미리 잡혔다.

**★ 함정 2 — FORCING 디렉토리를 런끼리 공유하면 안 된다.**
모델은 고정 이름 `./FORCING/wfde5_atm.nc`(심링크)를 읽고, 체인이 매년 그 링크를 갈아끼운다(`chain_spinup30.sh:37`). 워커의 FORCING을 본 런 것에 심링크했더니 본 체인이 맞춰둔 1996을 읽어 즉사:
```
FATAL: time 19900101.033000 is before range 19960101.030000-19970101.090000
```
→ **워커 전용 FORCING 디렉토리**를 만들고 워커가 자기 링크만 갱신하도록 수정.
**반대 방향이 더 위험**: 워커가 공유 링크를 1990으로 바꿨다면 **1996을 돌던 본 체인이 조용히 1990 강제장을 읽었을 것.** 읽기만 해서 드러났다.

### 13.35 CLM5 BGC-AD 정지 (2026-07-29 16:00, year 93/200)

climate02를 12월 재실행에 쓰기 위해 정지. **수렴 판정은 이미 충족**(면적가중 재계산):

| | 최근 10년 | 최근 20년 | 기준 |
|---|---|---|---|
| **TOTECOSYSC** | **−0.58 /yr** | −0.35 /yr | **≤1 gC/m²/yr → 충족** |
| TOTSOMC | −0.56 | −0.06 | |
| TOTVEGC | +1.31 | +0.32 | 추세보다 진동(889~905 범위) |
| TLAI | +0.003 | +0.001 | 정지 |

**★ `clm5_bgc_ad_chain.sh`가 백그라운드에서 자동 재제출한다.** 잡만 `qdel`하면 체인이 즉시 다음 청크를 올린다(실제로 8306 삭제 직후 8310이 올라와 climate02를 다시 점유). **체인 드라이버 프로세스도 함께 kill해야 한다.**

**재개 방법**: `rpointer.lnd` = `clm5_bgc_ad.clm2.r.0093-01-01-00000.nc`, restart는 매년 기록되어 92개 보유 → 손실 최대 1년(≈2.5h). 체인 로그 마지막: `chunk 11: submitting from year 0093, 8 years -> 0101`. 같은 청크를 다시 제출하면 이어짐.

### 13.36 ✅ 12월 확보 확인 — `days=365, hours=0` 검증 완료 (2026-07-30)

**재실행 y1990 결과 (`RERUN/wA/archive/y1990/19900101.land_month.tile1.nc`)**:
```
records = 12   calendar = noleap
[10] 11월  window 1990-11-01 03:00 -> 1990-12-01 03:00
[11] 12월  window 1990-12-01 03:00 -> 1991-01-01 03:00   <- 종전에 미완성으로 버려지던 구간
```
- **11 → 12개.** §13.31의 진단(월 경계 03:00 앵커, 3시간 부족)과 FMS 소스 확인(`diag_manager_end` → `closing_file`의 `time >= next_output`)이 실물로 검증됐다.
- 본 체인도 2026-07-29 20:02에 v2로 교체되어 **1997부터 동일 설정**(job 8326). handoff 로그: `y1996 archived: 245 files` → `restart handed to 1997` → `v2 started`.
- 워커는 자동으로 1991로 진행(job 8332). 나머지 5년도 같은 방식.

**★ 12월이 왜 필요했는지 숫자가 보여준다.** y1990 전지구 육지평균 LAI 월별:
```
Jan 2.602  Feb 2.547  Mar 2.490  Apr 2.510  May 2.656  Jun 2.496
Jul 2.311  Aug 2.112  Sep 2.048  Oct 2.231  Nov 2.431  Dec 2.583
```
- **연중 최대가 1월(2.602), 최소가 9월(2.048)** — 북반구 여름(Jul-Aug)이 오히려 낮다.
- §13.26의 **열대 과대·아북극 과소** 편향과 정합: LM4의 전지구 LAI가 열대·남반구에 지배되어 **DJF에 정점**을 찍는다.
- → **종전 11개월 자료로는 모델 LAI의 연중 최대값을 아예 볼 수 없었다.** MJJAS(북반구 성장기)만 보는 접근이 왜 부족한지에 대한 직접적 증거.

**진단 가능 구간 (확정)**: 재실행 1990-1996 + v2 체인 1997-2010 = **1990-2010 21년, 12개월 완전**. 표류도 1990 이후 |추세| < 0.4 %/yr(§13.33)이라 진단 창과 일치.
**남은 결손**: 1981-1989 9년은 11개월. 필요해지면 같은 워커로 연도 목록만 바꿔 재실행(9 × 12.5h ≈ 113시간).

### 13.37 ⏸ 서버 정지로 전체 중단 (2026-07-30 16:08) — 재개 절차

서버 점검(사용자 통보)으로 실행 중인 모든 잡·드라이버를 정지. **드라이버를 먼저 kill한 뒤 잡을 `qdel`** 했으므로 재제출 루프는 없다.

| 정지한 것 | 중단 시점 |
|---|---|
| job 8326 — 본 체인 **1997** (v2) | 모델 1997-09-02, 20시간 경과 (69%) |
| job 8332 — 재실행 **1991** | 모델 1991-11-21, 11시간 49분 (89%) |
| `chain_spinup30_v2.sh` 드라이버 (pid 1618753) | kill |
| `finish_y1991.sh` 감시 (pid 2480274) | kill |
| 재실행 워커 | 이미 정지(15:38, 사용자 요청) |
| CLM5 AD + `clm5_bgc_ad_chain.sh` | 2026-07-29 16:00 정지(§13.35) |

**★ 손상 없음**: LM4 restart는 `restart_interval` 미설정으로 **세그먼트 끝에만** 기록된다(§13.34 확인) → 중간 종료로 깨질 파일이 없다. 잃은 것은 계산시간뿐(1997 20h, 1991 11.8h)이고, 두 해 모두 시드 restart가 온전해 **그 해부터 다시** 돌리면 된다.

**보존 상태**

| 자료 | 위치 | 월 수 |
|---|---|---|
| 본 런 1981–1996 | `RUN/lm4_spinup30/archive/y1981`~`y1996` (각 245파일) | **11** |
| **재실행 1990** | `RERUN/wA/archive/y1990` (245파일) | **12 ✓** |
| 1997 시드 | `RUN/lm4_spinup30/INPUT/` (y1996 말 상태) | |
| 1991 시드 | `RUN/lm4_spinup30/archive/y1990` | |

**재개 명령** (서버 복구 후)
```bash
# 본 체인: 1997부터, v2 = 12개월 + river 출력
cd /data2/ydkoh/lm4/RUN/lm4_spinup30
nohup bash chain_spinup30_v2.sh 1997 2010 >& chain_driver_v2.out &

# 12월 재실행: 남은 해
cd /data2/ydkoh/lm4/RERUN/wA
nohup bash /data2/ydkoh/lm4/rerun_worker.sh /data2/ydkoh/lm4/RERUN/wA \
      1991 1992 1993 1994 1995 1996 >& worker.out &

# CLM5 BGC-AD: year 93부터 (§13.35)
cd ~/CESM/cases/clm5_bgc_ad
nohup bash clm5_bgc_ad_chain.sh 202 >& ~/clm5_bgc_ad_chain.out &
```

**★ 재개 시 주의 3가지**
1. **워커 정지 시 archive 공백**: 워커는 각 해의 archive도 담당한다. 워커 없이 잡만 끝나면 출력이 런 디렉토리에 남고, **다음 워커 실행이 시작 시 `rm -f $R/*.nc`로 지운다.** 잡만 따로 돌릴 때는 archive를 수동으로 하거나 `finish_y*.sh` 같은 마무리 스크립트를 함께 걸 것.
2. **노드 경합 확인 필수**: 2026-07-30 시점에 다른 사용자 작업이 PBS **밖에서** 돌고 있었다(Chanhyuk `LIS`가 climate01·02 양쪽, jjeehoon `jules_fixed.exe` 876%). PBS는 24만 할당했다고 보는데 실제 load는 climate01 44 / climate02 **60**(48코어 초과)였고, 본 체인이 29 → 11.2 model-days/hour로 **2.6배 감속**됐다. → 재개 전 `ssh climateNN uptime`과 `ps -eo user,comm,pcpu`로 **실제 부하**를 볼 것. `qstat`만으로는 안 보인다.
3. **1981은 재실행 불가**: 워커는 `archive/y(Y-1)`에서 시작하는데 아카이브가 y1981부터라 **`y1980`이 없다.** 1982–1996은 그대로 가능. 1981을 재실행하려면 원래 warm-start 시드(KIOST 400년 평형 restart, §13.21)의 경로를 먼저 특정해야 한다.

**진단 구간 현황** (§13.36 기준 목표 = 1990–2010 12개월 완전)
- 확보: **1990** ✓
- 남음: 1991–1996 재실행 6년 + 1997–2010 v2 체인 14년
- 1981–1989는 표류 구간(§13.33)이라 진단 지표에는 부적합 — 재실행 값어치는 "30년 완결 기록" 목적에 한정.

### 13.38 ★★★ §13.36의 월별 LAI 수치는 오류 — 연중 최대는 7월이다 (2026-07-31)

§13.36이 y1990 재실행 자료라며 적은 월별 LAI(`Jan 2.602 ... Sep 2.048 ... Dec 2.583`,
"연중 최대가 1월")는 **같은 파일을 다시 계산하면 재현되지 않는다.** 위상이 어긋나 있다.

재계산 (`lm4/scripts/chk_y1990_lai.py`, 서버 원본 `RERUN/wA/archive/y1990/19900101.land_month.tile{1..6}.nc`,
native 스트림, 6타일, `_FillValue=-1` 마스크):

| month | 1 | 2 | 3 | 4 | 5 | 6 | **7** | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 무가중 | 2.057 | **2.050** | 2.062 | 2.108 | 2.257 | 2.485 | **2.559** | 2.515 | 2.458 | 2.298 | 2.185 | 2.171 |
| soil_area 가중 | 1.964 | 1.942 | 1.938 | 1.981 | 2.140 | 2.392 | 2.497 | 2.471 | 2.414 | 2.224 | 2.107 | 2.085 |

- **연중 최대 = 7월(2.559), 최소 = 2월(2.050).** 전지구 육지의 대부분이 북반구이므로 물리적으로 정상.
- Jan–Nov 11개 값이 `lm4/data/monthly_15yr.csv`(`extract_monthly_11yr.py`)의 1990년과 **소수점까지 일치** →
  로컬 CSV 추출은 정확하고 재현된다. 틀린 건 §13.36의 빠른 확인 쪽.
- 값은 `lm4/data/monthly_y1990_12mo.csv`에 박제.

**★ 뒤집히는 결론 3개 (§13.32·§13.36 정정)**
1. **"MJJAS만 보는 건 북반구 한정 논리"는 전지구 평균에 대해선 틀렸다.** MJJAS(2.455)가 연중 정점을
   담는 올바른 성장기 창이다. DJF(2.092)는 연중 최저 구간. **단 지역별(아마존·콩고·호주)로는
   DJF가 남반구 성장기라는 §13.32의 지적이 그대로 유효** — 전지구 평균과 지역을 구분할 것.
2. **"11개월 자료로는 모델 LAI의 연중 최대를 아예 볼 수 없었다"(§13.36)는 사실이 아니다.**
   최대인 7월은 11개월 자료에 처음부터 들어 있었다.
3. **12월은 낮은 달이다**(2.171 < 11월 2.185). 11개월 드롭의 연평균 오차는 **+0.39%**
   (2.2757 vs 2.2669)이고 부호는 **과대**. §13.36이 암시한 과소 방향이 아니다.

**여전히 유효한 것**: 12월을 되살린 `days=365` 수정 자체(§13.31·§13.36의 진단·검증)는 옳다.
레코드 12개는 실측으로 확인됐다(time_bnds 4349.125→4380.125, 31일). 연주기·탄소수지·지역 DJF
진단에는 12월이 필요하다. 다만 **"MJJAS 진단이 12월 결손에 영향받는다"는 근거로 재실행을
정당화하면 안 된다** — MJJAS는 12월과 무관하다.

**★ 교훈**: 노트에 숫자를 박제할 땐 **재현 가능한 스크립트 경로를 함께** 남길 것. §13.36은 스크립트 없이
콘솔 출력만 옮겨 적어 3일간 잡히지 않았고, 그 위에 "DJF가 중요하다"는 서술이 쌓였다.
그리고 **원본이 서버에만 있으면 로컬에서 교차검증이 불가능**하다 — 진단에 쓰는 연도는 월별
land-mean CSV를 로컬에 남길 것.

### 13.39 ★★ 전지구 land-mean에 빙상이 섞여 있었다 — SWE는 86 %가 빙상 (2026-07-31)

`land_month` 변수는 **두 종류의 면적 위에 얹혀 있고**, 우리는 그걸 섞어 평균해 왔다.

| `cell_measures` | 변수 | 유효격자 | 남극(<60°S) | 그린란드 |
|---|---|---|---|---|
| `area: soil_area` | **lai · water_soil · tot_soil_C** | 17,306 | **0** | 189 |
| `area: land_area` | **snow · runf · evap_land** | 18,704 | **1,234** | 318 |

차이 1,398점(중앙값 −74.1°S)이 빙상이고, **이 수는 §13.30에서 native와 cmip 마스크 차이로 나온 격자 수와 정확히 같다** — cmip이 `fill_missing`으로 0을 채우던 게 이 빙상 격자들이었다.

**y1990 연평균, as-is → non-ice**
```
SWE      84.39 -> 13.85 kg/m2   (-83.6 %)   <- 우리가 그려온 "적설"은 사실상 빙상 축적 지수
evap                            (+7.5 %)
runoff                          (+1.1 %)
LAI / col_water / soilC         (+0.00 %)   <- soil_area 기반이라 원래 남극이 없었음
```
- Noah-MP에서 빙상 SWE가 상한까지 쌓여 수렴 판정을 오염시킨 것과 **같은 구조**([[lsm-spinup-ice-mask-convergence]]). offline엔 빙하 역학이 없어 쌓이기만 한다.
- **대책**: `soil_area>0`(= `lai` 유효)에서 마스크를 한 번 만들어 **모든 변수에 동일 적용**. 그린란드는 별도 박스로 제거하되 아이슬란드(62.5–67.5°N, 25–12°W)는 살림 → **17,136점**.
- 스크립트 `lm4/scripts/extract_monthly_noice.py`, 자료 `lm4/data/monthly_noice_16yr.csv`(1981–1996), 그림 `figures/lm4_monthly_noice.png`.
- **SWE는 전지구 평균 진단에서 제외**했다. 쓰려면 non-ice 마스크 필수.

### 13.40 ★★★ 1981–89 LAI 상승은 표류다 — GIMMS로 검증 (2026-07-31)

forcing이 transient WFDE5라 "상승이 실제 기후신호일 가능성"을 이 런만으로는 배제할 수 없었다. 관측으로 갈랐다.
스크립트 `lm4/scripts/{extract_lm4_lai_8296,lai_trend_vs_gimms}.py`, 그림 `figures/lai_trend_vs_gimms.png`.
공통 1° 격자 12,319셀(양쪽 15년 전부 유효), cos(lat) 가중.

| 창 | LM4 | GIMMS | |
|---|---|---|---|
| 1982–89 | **+0.63 %/yr** | +0.27 %/yr | 모델이 **2.4배** |
| 1990–96 | −0.03 %/yr | **+0.15 %/yr** | 관측만 계속 녹화 |

- **표류 확정 근거 3중**: ① 관측 대비 2.4배 초과 ② 지수 완화 적합이 거의 완벽(평형 2.299, 진폭 0.206, **e-folding τ=2.5 yr**, 잔차 sd 0.0123 = 연변동 크기) ③ 1990에 정확히 멈춤 — 실제 녹화는 멈추지 않는다.
- **안전 시점 계산**: 잔여 표류 `0.206·exp(-Δt/2.52)`가 연변동(0.0123)보다 작아지는 건 **1988년부터**. 1985년은 표류가 연변동의 3.4배 → 쓰면 안 됨.
- **→ 진단창 1990– 결정이 관측으로 검증됐다.** 최종 보고서는 **2001–2010 마지막 10년** 권장(초기화에서 20년 이상), 경년변동 평가는 1990–2010.
- **부수 발견**: 표류가 끝난 뒤 모델엔 **녹화 추세가 전혀 없다**(관측 +0.15~0.23 %/yr vs 모델 −0.03~−0.09). 원인 후보 = CO₂ 비료효과 부재. 단 `data_table`에 `co2_gblannualdata.nc`가 연결돼 있어 **CO₂ 고정 여부는 미확인** — `cana.res`의 연도별 CO₂로 확인할 것.

### 13.41 LAI 편차의 공간구조 — 평균과 추세 (2026-07-31)

`lai_meanmap_vs_gimms.py` · `lai_trendmap_vs_gimms.py`, 그림 동명 PNG.

**평균 bias (MJJAS, 공통 1°)**

| 창 | LM4 | GIMMS | bias | RMSE | r |
|---|---|---|---|---|---|
| 1982–1996 | 2.850 | 2.014 | **+0.836 (+41.5 %)** | 1.651 | 0.750 |
| 1990–1996 | 2.874 | 2.010 | **+0.864 (+43.0 %)** | 1.735 | 0.736 |

- **★ 표류 구간을 빼도 bias가 줄지 않는다**(+0.836 → +0.864). → **이 과대편차는 spin-up 잔재가 아니라 구조적 모델 편차.** 진단창을 바꿔도 사라지지 않으므로 "정리하면 나아질 것"이라 말하면 안 됨.
- 위도대별 bias(1990–96): 60–85°N +0.12 → 30–60°N +0.34 → 0–30°N +1.12 → 30°S–0 +1.26 → **60–30°S +1.94**. 저위도로 갈수록 단조 증가.
- r=0.74 = **패턴은 맞히고 진폭이 과대**. CRESCENDO 다중 LSM 공통편향과 같은 성격.
- **추세**(1982–96): 면적가중 평균 LM4 +0.074 vs GIMMS +0.014 /decade(5.2배). 양/음 격자 비율은 비슷(61 % vs 67 %)인데 **국지 추세 크기 p98이 1.87 vs 0.14로 13배** → 패턴은 맞고 진폭만 과대. 차이맵의 아마존·콩고 적청 쌍극자 = PFT 구성 이동 중.
- **60–30°S가 평균·추세 양쪽에서 최악**(bias +1.94, 추세 부호 반대) → 개선 1순위 지역.
- **★ 해석의 열쇠**: `do_biogeography=.FALSE.`라 종 조성이 관측 `cover_type.nc`에 고정돼 있다(§13.20). 따라서 **이 편차는 "식생 분포가 틀려서"가 아니라 모델 물리(탄소 배분·비엽면적·phenology) 때문**으로 좁혀진다. 1차년도 진단 프레임의 설계 의도가 그대로 작동한 결과.

### 13.42 ★★★ WFDE5 강제장 전달 검증 — 7종 전부 통과, 기압만 예외 (2026-07-31)

스크립트 `lm4/scripts/{chk_forcing_native,chk_rad_native,plot_forcing_check_native}.py`,
자료 `lm4/data/forcing_native_1990.npz`, 그림 `figures/forcing_check_native_1990.png`.
**C96 격자점에서 비교**(원본을 그 점들로 이중선형 보간). 1990 연평균.

| 변수 | 출처 | bias | rel% | r | bias / 원본 공간sd |
|---|---|---|---|---|---|
| 기온 | land_forcing | −0.0004 K | −0.000 % | **1.00000** | 0.0025 % |
| 비습 | land_forcing | −4e-5 g/kg | −0.000 % | **1.00000** | 0.0007 % |
| **하향단파** | **land_month** | **+8e-5 W/m²** | **0.000 %** | **1.00000** | 0.0002 % |
| 하향장파 | land_month | −0.148 W/m² | −0.047 % | 0.99994 | 0.20 % |
| 강수 | land_daily | −0.0002 mm/day | −0.008 % | **1.00000** | 0.008 % |
| 바람 | land_forcing | −0.013 m/s | −0.270 % | 0.99998 | 0.98 % |
| 지표기압 | land_forcing | **+5.33 hPa** | +0.570 % | 0.9876 | 5.9 % |

- **★ 단파가 `r=1.00000, bias=+8e-5 W/m²`** = 지면이 받은 SW는 모델이 계산한 복사가 아니라 **WFDE5 값 그 자체**. `flux_down_from_atmos`가 data_override로 덮어쓰기 때문이고, **복사 게이트 패치(§13.16)가 물리적으로 무해했다는 실측 증거**.
- **`land_forcing`은 복사·강수를 fill로만 쓴다** (`do_atmos=.false.`에서 등록만 되고 채워지지 않음). 처음에 "0.0"이 나온 건 all-NaN 합산의 허수였다. → **복사는 `land_month`(swdn_dir+swdn_dif, band 2개 합), 강수는 `land_daily`에서 검증할 것.**
- 장파의 해안선 띠 = 모델이 **WFDE5 land-mask mesh**로 remap(§6b)하는 반면 비교는 평범한 이중선형이라 바다측 값을 섞기 때문. 모델 쪽이 더 엄밀.

**★ 유일한 설정-동작 불일치: 지표기압이 정적이다**
```
1990 ps 시간표준편차 (격자점별)   모델 0.000 hPa   원본 3.191 hPa
```
- 모델 ps는 **1년 내내 전혀 변하지 않는다**. `data_table`에 `p_surf` 주입 줄이 있는데도, 실제로는 **상수 `slp=101325`와 모델 자기 지형고도**에서 재구성된 값을 쓴다. 지도의 산맥 구조(티베트·로키 +, 아마존 −)가 그 증거.
- **영향은 작다**: 0.57 % → 공기밀도 0.57 % → 플럭스 1 % 미만. 강제자료 자체의 불확실성보다 1~3자릿수 작다. **결과를 의심할 근거는 아니고 기록해둘 항목.**
- 미규명: `do_atmos=.false.`에서 override 적용 지점이 건너뛰어지는지 소스 확인 필요.

### 13.43 ★★ 방법론 — 격자 비교와 비선형 평균 (2026-07-31, 둘 다 실제로 틀렸던 것)

**① 격자가 다른 두 자료를 제3의 격자에 각각 담아 비교하지 말 것.**
C96과 0.5° WFDE5를 각각 1° 박스에 담아 비교했더니 기온 차이가 **표준편차 0.70 K, p99 2.4 K**로 나와 "강제장이 잘못 들어갔나" 의심했다. **모델 격자점에서 비교하니 0.0022 K** — 실제 오차의 **300배**가 비교 방식만으로 만들어졌다. 지형이 복잡한 곳에서 1° 박스 안에 C96 점이 하나뿐이라, 그 점의 고도와 박스평균 고도 차이가 그대로 ΔT로 나타난 것.
→ **모델 격자 위에서, 원본을 그 점들로 보간해 비교할 것.** 표시용 regrid는 **차이를 계산한 뒤** 하면 안전(차이의 평균이지 두 필드를 각각 옮긴 게 아니므로).

**② 비선형 변환은 평균 순서가 결과를 바꾼다.**
모델은 매 스텝 `√(u²+gust²)`를 계산해 평균하는데, 비교는 평균한 u에 씌웠다 → 바람 bias **+1.64 %**. 같은 순서로 계산하니 **−0.27 %**. `√`가 볼록이라 Jensen 부등식으로 **모델이 반드시 크게 나온다** — 부호까지 예측 가능했다.
→ 플럭스·풍속·포화수증기압처럼 비선형인 양은 **모델과 같은 순서로 계산**할 것.

### 13.44 ★ 그린란드를 위경도 박스로 자르면 캐나다 북극까지 잘린다 (2026-07-31, 정정)

§13.39의 그린란드 컷은 `lat>59 & −73<lon<−11`(아이슬란드 예외) 박스였다. **실제 그린란드 폴리곤(Natural Earth 50m)으로 판정하니 그 박스가 제거한 170점 중 87점이 그린란드 밖이었다** — 배핀만을 건너뛰어 **배핀·엘즈미어·데본섬(캐나다 북극)** 을 함께 잘랐다. 사용격자 면적의 0.246 %.

- **수정**: 박스 → **Natural Earth 그린란드 외곽선**(0.6° 버퍼로 팽창 후 0.25° 단순화, 69정점). 서버에 cartopy/shapely가 없어도 되도록 정점 좌표를 코드에 박고 numpy ray casting으로 판정. → `lm4/scripts/greenland_mask.py`
- **아이슬란드 예외 조항이 필요 없어졌다** — 폴리곤 밖이라 자동으로 살아남는다(검증: 걸리는 점 0개).
- 사용격자 **17,136 → 17,219** (+83). 전지구 평균 변화는 0.1 % 미만이나, 이 마스크는 CLM5·Noah-MP·JULES 비교에도 그대로 쓸 것이라 지금 바로잡음.
- 재생성: `monthly_noice_16yr.csv` · `lm4_lai_1982_1996.npz` 및 이를 쓰는 그림 5장 전부.

**교훈**: 대륙·섬을 위경도 박스로 자르지 말 것. 해협 건너 다른 땅이 같은 경도대에 있다. **자른 결과를 실제 폴리곤으로 검산**하거나, 애초에 폴리곤으로 자를 것. (같은 함정: 아이슬란드가 그린란드 박스 경도대에 들어옴 → 예외 조항을 손으로 넣어야 했던 것 자체가 신호였다.)

### 13.45 ★★★ cycle 1 완주 (1997–2010) + 30년 수렴 상태 (2026-08-11)

서버 정지(§13.37) 이후 재개된 v2 체인이 **2026-08-07 17:53 완주**했다. 1997–2010 14세그먼트, 각 245파일, `land_month` **전부 12 records**(y2010 time 값으로 Jan–Dec 직접 확인). 12월 문제는 v2에서 완결됐다. **남은 구멍은 1991–1996 6년(11개월)뿐**이고 재실행 워커는 재개되지 않았다.

**30년 궤적** (`lm4/data/monthly_noice_30yr.csv`, 비빙설 17,219점, **전 연도 Jan–Nov**로 통일 — 12월 유무가 섞이면 1997년에 샘플링 계단이 생긴다):

| 변수 | 1981 | 2010 | 마지막 10년 |
|---|---|---|---|
| col_water | 3420 | 3382 | −1.58 kg m⁻² yr⁻¹ (−0.047 %/yr) |
| theta_sfc | 0.5965 | 0.5913 | +0.002 %/yr |
| soilT 2m | 288.8 | 289.9 | +0.026 K/yr |
| **soilC** | 7.459 | 7.836 | **+3.7 gC m⁻² yr⁻¹** |
| **bwood** | 1.686 | 1.735 | **+3.0 gC m⁻² yr⁻¹** |

- **물·에너지는 수렴, 탄소는 아님.** CLM5-BGC 기준은 총생태계탄소 ≤1 gC m⁻² yr⁻¹인데 합 **6.7**. 게다가 bwood는 마지막 10년 기울기(+0.00296)가 30년 기울기(+0.00233)보다 **커서** 축적이 빨라지고 있다 — 평형 아님.
- ★ **단 1981–2010은 cyclic이 아니라 실제 온난화가 든 transient forcing**이다. 추세를 전부 "미수렴"으로 읽으면 안 된다. LAI는 GIMMS로 갈랐고(아래), 탄소는 아직 안 갈랐다.
- **LAI 표류는 1990년에 끝난다** — 2.086→1990년 2.287까지 오른 뒤 20년간 2.24~2.34 진동. §13.33·13.40이 30년 전체로 확인됐다.

### 13.46 ★★★ 표류가 관측 불일치를 가리고 있었다 — LAI 추세 (2026-08-11)

MJJAS, 공통 1° 12,366격자, cos(lat) 가중 (`lai_trend_vs_gimms.py`, 캐시 `gimms_1deg_1982_2010.npz`):

| 구간 | GIMMS | LM4 |
|---|---|---|
| 1982–1989 | +0.26 %/yr | **+0.67 %/yr** (2.6배 = 표류) |
| **1990–2010** | **+0.15 %/yr** | **−0.08 %/yr** ← **부호 반대** |
| 1982–2010 | +0.10 %/yr | +0.05 %/yr |

**전체 기간만 보면 "그럭저럭 맞는" 것처럼 보이는데, 앞의 표류가 뒤의 하락을 상쇄한 가짜 일치다.** 16년 자료(§13.26)로는 볼 수 없던 결과. **관측 비교는 반드시 1990 이후로 자를 것.**

공간구조 (1990–2010, %/decade, 셀 자기평균으로 정규화):

| 위도대 | LM4 | GIMMS | 차이 |
|---|---|---|---|
| 60–85N | **+11.4** | +0.66 | **+10.7** (17배) |
| 0–30N | **−0.46** | +1.93 | −2.39 |
| 30S–0 | +0.26 | +1.53 | −1.28 |

**북극 과잉녹화 + 열대 녹화실패(갈변).** 평균장도 같은 방향 — 1990–2010 bias **+0.836 (+41.2 %)**, RMSE 1.644, r 0.750, 70.9 %격자 과대이고 편차가 열대에 몰린다(0–30N +1.05, 30S–0 +1.21, 60–85N +0.20). **추세와 평균이 같은 곳을 가리킨다.**
→ 그림: `lm4_monthly_noice.png`(30년), `lai_trend_vs_gimms.png`, `lai_meanmap_vs_gimms.png`(1982–2010/1990–2010), `lai_trendmap_vs_gimms.png`(**1990–2010**, 표류 8년 제외).
- 12월 보정 offset은 이제 **실측 12월이 있는 14개 연도 평균**으로 잡는다(1990 단일표본 → n=14, sd 동시출력). 추정 12월은 열린 원으로만 표시.

### 13.47 ★★★ 되감기 블로커 = `landuse.res` (2026-08-11)

y2010 restart를 1979로 되감아 시작하면 **2분 만에 죽는다**:
```
FATAL from PE 30: land_transitions_init:
  current time is earlier than the time of last land use transition application
```
`INPUT/landuse.res`(한 줄 텍스트)에 **2011 1 1**이 박혀 있고 `transitions.F90:295-298`이 시작시각과 비교한다. **PE 수와 무관** — 24 PE 생산런도 똑같이 죽는다.

- **해결**: 그 줄을 시작연도로 바꾼다. `  1979     1     1     0     0     0        Time of previous landuse transition calculation`
- **`states.v20260127.nc`로 1979 토지이용을 다시 심는 건 답이 아니다.** `transitions.F90:138` 주석 = `state_file ... (for initial transition only)`, 그리고 `:355`의 분기는 `time0==0001-01-01`(=`landuse.res` 부재 = cold start)일 때만 탄다. 주석 그대로 **"initial transition from all-natural state"** — 이미 2010년 농경지 tile이 있는 restart에 자연→농경 전이를 또 얹어 **이중 전환**이 된다. 46년 spin-up된 식생·탄소를 버리는 길.
- **채택한 한계**: 상태는 2010년 토지이용 면적 + 1979–2024 전이 델타. 면적에 **수준 편향**은 있으나 전이는 델타라 이중계산은 없고, **추세를 만드는 델타는 정확**하다. cycle 1도 같은 성격(KIOST 평형 상태에서 1981 전이 시작)이었고 열대 갈변은 거기서도 나왔으므로 갈변의 원인은 농경지 과대가 아니다. **토지이용 면적 자체를 관측과 비교하는 진단에는 이 런을 쓰지 말 것.**

### 13.48 ★★★★ 48 PE는 restart만이 아니라 **진단 출력도** 조각낸다 (2026-08-11, job 8363/8364)

§13.21의 미결(옵션 3, "분산 restart 직접 read")을 1개월×2세그먼트 체이닝으로 실측했다.

**restart 읽기는 된다.** 세그먼트 1(1979-01)이 쓴 146개(**54개가 `.0001/.0002` 조각**, tile 1·2·3만)를 인계받아 세그먼트 2(1979-02)가 완주. cold start 아님을 식생 구조로 확정: `vegn1.res.tile1.nc.0001`이 **tile=16, cohort 63 → 61**(cold start면 tile=1/cohort=1). rc·FATAL로는 판별 불가 — 반드시 tile/cohort로 볼 것.

**그러나 생산런엔 쓸 수 없다.** 같은 tile 경계에서 **land 진단 출력도 전부 조각난다** — `land_month.tile1.nc.0001/.0002` … 총 **114 조각**, tile 4·5·6만 결합본.
```
chain:104  mv "$R"/*.land_*.nc "$R"/*.river_*.nc archive/   ← .nc.0001 매칭 안 됨
chain: 66  rm -f "$R"/*.nc.0* "$R"/*.nc                     ← .nc.0001 매칭 됨
```
→ **매년 모든 land 진단의 tile 1·2·3이 조용히 삭제된다.** rc=0이고 guard 2도 통과(`*.res*.nc` 90개 ≥ 40). 1997–2009 river를 잃은 것과 같은 구조인데 규모가 훨씬 크다.
- 결합 도구 부재 재확인: `mppnccombine`·`combine-ncc` 둘 다 NOT FOUND.
- **실측 처리량**: 1.71·1.75 분/model-day(1월·2월) → **약 10.5 h/model-year**. §13.19의 7.85는 5일 벤치라 월별 diag I/O가 빠진 낙관값. 24 PE cycle 1은 13 h/yr이지만 그건 `land_forcing` 쓰기 포함이라 공정비교 아님.
- **PE 수를 바꾸면 restart 형식뿐 아니라 diag 파일명까지 바뀐다.** 다음 검증은 `npes_io_group`(현재 8)을 PE수로 올리면 `ug_io_layout=1`이 되어 결합본이 나오는지 — §13.21이 남긴 가설.

### 13.49 climate01 루트 디스크가 차서 PBS가 멎어 있었다 (2026-08-11)

8/7 17:52 이후 climate01에 제출한 **모든 잡이 `substate=41`(PRERUN)에서 정지**. 1코어 `echo` 한 줄도 동일. `qdel` 무효, `qdel -W force`는 삭제가 아니라 **재큐잉**(`Rerunable=True`), `qsig`는 "Request invalid for state".

- **원인**: `/dev/sda4 379G 379G 44K 100% /`. `pbs_mom`이 잡 스크립트를 `/var/spool/pbs`(=`/`)에 못 써서 멎는다.
- **범인**: `/var/spool/pbs/undelivered/2886.climate00.OU` = **350.7 GB 단일 파일**, ydkoh 소유, 6/29 Noah-MP HRLDAS 잡이 `wrfinput_flnm: ...` 한 줄을 무한 반복한 stdout. 배달 실패분이 그대로 남았다.
- **관리자 없이 해결됨**: `undelivered`가 `drwxrwxrwt`(sticky) → 자기 소유 파일은 본인이 삭제 가능. 삭제 후 `/` 100 %→**8 %**, 프로브 잡 즉시 실행.
- ★ **유령 잡이 큐 전체를 막는다**: 노드는 `state=free`인데 서버 `resources_assigned.ncpus`가 48로 남아 1코어 잡도 dispatch 안 됨. 재큐잉된 뒤 `qdel`하면 풀린다.
- **교훈**: 잡이 R인데 `resources_used`·`stime`이 없고 노드 load가 0이면 **계산 문제가 아니라 mom 문제**다. `pbsnodes <node>`의 `last_used_time`으로 "언제부터 아무것도 안 돌았는지"를 먼저 볼 것. 그리고 **런의 stdout을 파일로 리다이렉트할 것** — 안 하면 PBS 배달 실패분이 노드 로컬 디스크를 채운다.

### 13.50 생산런 `lm4p_ctl_1979-2024` 준비 (2026-08-11)

cycle 1을 spin-up으로 확정하고, **1979–2024 46년 transient**를 생산런으로 분리했다. 이름은 Phase 2 섭동실험(`lm4p_snow-25` 등)의 기준선을 전제한 `ctl`.

- **새 디렉토리** `RUN/lm4p_ctl_1979-2024`. cycle 1은 `RUN/lm4_spinup30/archive_c1`으로 **이름만 바꿔 보존**(30년, 삭제 없음). 체인의 스킵가드가 `archive/y$Y` 존재를 보므로 같은 디렉토리를 재사용하면 46년을 전부 건너뛴다.
- **시드**: cycle 1 종료 상태(2011-01-01) → 시계만 1979-01-01 03:00으로 되감음(`force_date_from_namelist=.true.`가 coupler.res를 무시). `INPUT/`과 별도로 `SEED_2010/`에 한 벌 더 보존.
- **forcing 1979–2024 46년 준비 완료**. 원본 `2026_MOF_LSM/Atm_forc/1_CLM_WFDE5/`에 46년 전부 존재(전 연도 바이트 동일 크기 — 중복이 아님을 t_mean 276.00→277.35 K, 첫 레코드 전부 상이로 확인). 변환 ~4분/년.
- ★ **경계 레코드 필수**: 변환 산출물은 1460 records(마지막 day 364.875)인데 세그먼트는 day 365.125에서 끝난다 → **매 연말 3시간이 범위 밖**. `append_boundary_1979_2024.py`로 다음 해 첫 2레코드(365.125·365.375)를 붙여 **46년 전부 1462**로 맞춤. **부수효과 교정**: 옛 스크립트는 2010을 마지막 해로 보고 경계를 1981에서 감아왔는데, 46년 런에서 2010은 중간 연도이므로 2011에서 가져오도록 덮어씀(안 고치면 생산 구간 한복판에 6시간 이음매).
- **`land_forcing` 스트림 제거**(diag_table 1174→1160줄, 8.4 GB/yr·46년 252 GB 절약). 강제장 전달 검증(§13.42)은 끝났으므로 생산런엔 불필요.
- **restart는 세그먼트 끝(연 1회) 유지**. 1벌 5.0 GB → 46년 230 GB. 월별이면 2.76 TB이고 `/data2`는 이미 96 %. 분기점은 매년 1/1로 46개 확보되며, 연중 분기가 필요하면 그 해만 10.5 h 재실행하면 된다. **restart 주기는 12월 출력과 무관** — 12월은 세그먼트 길이(`days=365,hours=0`) 문제였고 이미 해결됨.
- **넣을 가드**: 세그먼트 끝에서 `land_month` 레코드가 12인지 검사하고 아니면 즉시 ABORT. 1996년처럼 11개월짜리가 15년 쌓인 뒤 발견되는 일을 구조적으로 막는다.

### 13.51 생산런 진행 + 산출 변수 검증 (2026-08-28)

`lm4p_ctl_1979-2024` 실행 중. **y1979–y2013 완료(35/46년)**, 실측 **10.3 h/model-year**,
완료 예정 2026-09-02. 매 세그먼트가 guard 4(12 records + 결합 tile 6개)를 통과하며 진행.

**★ y2010을 넘기면서 cycle 1이 덮던 전 구간(1981–2010)이 12개월 완비로 대체됐다.**
1991–1996의 11개월 결함 구간도 여기서 해소. y2011부터는 cycle 1에 없던 신규 구간.

**산출 변수 검증** (`lm4/scripts/chk_prod_vars.py`, y1979·y1995를 cycle 1 y1995와 대조):
진단 17종 전부 **12개월·유효격자 92.5 %**(비빙설 토양). cycle 1 대비 비율 —
lai 0.996 · soil_T 1.000 · water_soil 0.992 · runf 0.961 · evap 0.993 · precip 0.998.
같은 해·같은 강제장인데 0.4~4 % 차이 나는 것은 초기조건이 다르기 때문(정상).

- **되감기 열충격 없음**: y1979(되감기 직후) 심층 soil_T 289.46 K = cycle 1과 소수 둘째 자리까지
  일치. 전지구 규모 충격은 확인되지 않음. 단 y1979–1980은 애초에 흡수 구간으로 설계했으므로
  **진단은 1981 이후를 쓸 것**.
- **`dis_liq`(해양 유입 담수)가 y1979부터 정상 기록 중**(유효 100 %). cycle 1에서 아카이브 패턴
  누락으로 1997–2009를 잃었던 변수(§13.48)라, 북극해 담수유출 진단의 전제가 확보됐다.
- **탄소만 계속 축적**: bwood 비율이 y1979 1.035 → y1995 1.079, tot_soil_C 1.014 → 1.034.
  다른 변수가 1.00 근처인데 탄소만 3~8 % 높다. §13.45의 미수렴 판정과 일치하며,
  **탄소 진단에는 이 한계를 명시하고 쓸 것.**

### 13.52 ★★★ 생산런 vs cycle 1 — 물·에너지는 수렴, 목재 생물량만 발산 (2026-09-01)

같은 모델·같은 설정·같은 WFDE5 강제장으로 **초기조건만 다른 두 적분**이 겹치는 30년(1981–2010)을
해마다 비교. cycle 1은 KIOST 평형에서 1981 시작, 생산런은 cycle 1의 2010년 말 상태를 1979로
되감아 시작. 따라서 연도별 비(생산/cycle1)는 **초기조건 차이가 얼마나 오래 살아남는가**의 직접 측정이다.
도구 `lm4/scripts/cmp_prod_vs_cycle1.py`, 자료 `lm4/data/cmp_prod_vs_cycle1.csv`.
양쪽 다 **Jan–Nov 평균**(cycle 1은 1997 이전 12월이 없음), 비빙설 토양점.

| 변수 | 1981 | 1995 | 2010 | 추세 %/decade |
|---|---|---|---|---|
| **lai** | **1.1148** | 1.0002 | 0.9942 | −2.13 |
| **snow** | **0.8872** | 0.9833 | 0.9907 | +1.37 |
| soil_T | 1.0026 | 1.0001 | **1.0000** | −0.04 |
| evap_land | 1.0111 | 1.0070 | 1.0043 | −0.27 |
| sens | 1.0142 | 0.9923 | 0.9952 | +0.04 |
| water_soil | 0.9907 | 0.9921 | 0.9936 | +0.10 |
| runf | 0.9862 | 0.9821 | 0.9875 | +0.53 |
| tot_soil_C | 1.0561 | 1.0344 | 1.0296 | −0.66 |
| **bwood** | **1.0370** | **1.0781** | **1.0764** | **+1.00** |
| **precip** | **1.0000** | **1.0000** | **1.0000** | 0.00 |

**① 강제장 동일성 확정.** `precip`가 30년 전부 정확히 1.0000. §13.51에서 "0.998, 타일 가중 탓인가"라고
적었던 것은 **오류**였다 — 그때는 생산런 12개월과 cycle 1의 11개월을 비교했다. 창을 맞추면 완전히 일치한다.

**② 물·에너지는 씻겨나간다.** LAI가 +11.5 %에서 출발해 **15년 만에 1.000**, 적설은 −11 %→−1 %.
심층 soil_T는 1.0000으로 완전 일치. 초기조건을 30년 앞선 상태로 주어도 이 변수들은 같은 궤적으로 모인다.

**③ ★ 목재 생물량만 발산한다.** `bwood`가 1.037 → 1.078로 **벌어진 뒤 유지**(추세 +1.00 %/decade).
다른 모든 변수가 1로 수렴하는데 이것만 반대 방향. 평형이라면 초기조건이 달라도 같은 값으로 모여야 하므로,
**이는 탄소 미수렴의 독립적인 두 번째 증거**다(§13.45는 스핀업 표류량 6.7 gC/m²/yr 기준).
표류량 기준은 "임계값을 어떻게 잡느냐"의 여지가 있으나, **두 적분이 서로 수렴하지 않는다는 사실은
기준 선택과 무관하다.** `tot_soil_C`는 좁혀지는 중이나 30년에 5.6 %→3.0 %로 회전이 매우 느리다.

**→ 보고서 서술**: "물·에너지 변수는 초기조건 차이가 15년 내 1 % 이내로 사라지나, 목재 생물량은
30년 후에도 7~8 % 차이가 유지된다"가 탄소 한계의 근거로 표류량보다 방어력이 높다.

### 13.53 ★★★ 왜 목재만 발산하고 LAI는 수렴하는가 — 나무는 커지는데 잎은 안 는다 (2026-09-01)

§13.52의 "bwood만 반대 방향"이 무엇을 뜻하는지 종별 스트림(`land_month_by_species`)의
`bwood`·`height_ave`·`lai`로 확인. 생산런/cycle 1 비, 비빙설 토양점, Jan–Nov.

| 연도 | bwood 비 | **수고 비** | **LAI 비** | bwood/lai (prod) | (cyc1) |
|---|---|---|---|---|---|
| 1981 | 1.037 | 1.277 | 1.115 | 0.752 | 0.808 |
| 1995 | 1.078 | 1.135 | **1.000** | 0.790 | 0.733 |
| 2010 | 1.076 | 1.086 | **0.994** | 0.829 | 0.766 |

**같은 임관을 유지하면서 줄기만 굵어진다.** 1995년 이후 LAI는 완전히 일치(1.000·0.994)하는데
목재는 7.6~7.8 % 많고 나무는 8.6~13.5 % 높다. `bwood/lai`가 0.93 → 1.08로 커지는 것이 그 요약이다.

**메커니즘 (회전시간 + 포화)**
- **잎**: 회전 ~1년. 매년 새로 나므로 작년 상태가 아니라 **올해 기후가 결정**한다. 게다가 임관이
  닫히면 그 아래 잎은 빛을 못 받아 유지비만 들므로 `bl_max`·광경쟁으로 **포화**한다.
  → 초기조건이 30년 앞서 있어도 15년이면 같은 값으로 모인다.
- **목재**: 회전 수십~수백년, 상한 없이 누적. 고사로만 빠진다.
  → 초기 차이가 남고, 광합성 배분이 계속 목재로 가면서 유지된다.
- 따라서 **추가된 8 %의 탄소는 줄기·가지로 갔고 잎으로는 가지 않았다. LAI는 그것을 볼 수 없다.**

**★ 진단 가능 범위 (1차년도 판단 근거)**

| 항목 | 지금 자료로 | 근거 |
|---|---|---|
| LAI·식생 분포 | **사용 가능** | 초기조건 차이 소멸(1.000) |
| 토양온도·수분·유출·플럭스 | **사용 가능** | 전부 1 % 이내 수렴 |
| GPP | 조건부 가능 | 1.004, 거의 수렴 |
| **탄소 저장량(bwood·soilC)** | **절대값 불가** | 초기조건 의존, 미수렴 |

1차년도 점검항목(식생·토양온도·토양수분·유출)은 **전부 충족**되며 탄소 저장량은 점검 대상이 아니다.

**수렴시키려면**: 목재 회전시간이 수십~수백년이므로 8 %→1 %에 최소 100년, 열대림은 수백 년.
46년 실험을 몇 배로 늘려야 하므로 현실적이지 않고 필요하지도 않다. CLM5가 AD(가속분해)를 쓰는 이유가
같고, 그럼에도 post-AD 93년에 97 % 기준을 못 채운다(CLM5_SPINUP_NOTES §7j). **탄소 평형은 원래 이만큼 어렵다.**

**→ 보고서 서술**: "물·에너지·식생 변수는 초기조건 차이가 15년 내 1 % 이내로 소멸하나, 목재
생물량은 회전시간이 수십 년 이상이라 30년 후에도 7~8 % 차이가 유지된다. 따라서 본 진단은 식생
구조·수문·에너지 항목에 한정하며, 탄소 저장량의 절대값 평가는 향후 장기 적분 후 수행한다."

### 13.54 ★★★ 생산런 완료 = 1979–2023 (45년). 경계자료 두 벽 (2026-09-07)

`lm4p_ctl_1979-2024`가 **y1979–y2023 45년으로 마감**. 45년 전부 `land_month` 12 records,
아카이브 387 GB. 당초 목표 46년(→2024)에서 1년 모자라며, 이유는 모델이 아니라 **경계자료**다.

**벽 ①: AMIP 해빙·SST가 2022-12-16에서 끝남 (해결)**
```
FATAL time_interp_external: time 20221216.130000 is after range ... amipbc_sic_...nc
```
- `do_ice=.true.`라 커플러가 해빙 경계자료를 요구하는데 PCMDI AMIP 파일이 1870-01~2022-12(1836개월)까지다.
  세그먼트가 03:00 시작이라 마지막 레코드보다 **1시간 뒤** 값을 요구해 죽었다(2022-12-14까지는 완주).
- **★ 이 값은 지면에 도달하지 않는다.** land-only(`do_atmos=.false.`)라 해빙·SST는 해양격자에만 있고,
  §13.42에서 지면이 받은 강제장이 WFDE5와 `r=1.00000`으로 일치한 것이 그 증거다. 같은 `data_table`이
  이미 해빙 **두께**를 파일 없이 상수 2.0 m로 처방하고 있다(`"ICE","sit_obs","","","none",2.0`).
- **조치**: `lm4/scripts/extend_amip_bcs.py` — 2013–2022 월별 기후값으로 2023–2025를 이어붙인 확장본
  (`INPUT_amip_ext/*_ext2025.nc`, 1872 레코드)을 만들고 **심링크만 전환**. 값 연속성 확인
  (sic 25.56→24.53, sst 12.07→11.98). **원본(KIOST-ESM2_AMIP/INPUT)은 미변경**, `data_table`도 미변경.
  파일명에 `_ext2025`를 넣어 `ls -l INPUT`으로 무엇을 읽는지 드러나게 했다.
- 결과: 2022·2023 완주.

**벽 ②: LUH2 토지이용이 2023/2024에서 끝남 (해결 안 함 — 의도적)**
```
FATAL time_interp_list: time 20240101.030000 is after range (18500101 - 20240101)
  → land_dust_init의 관개·작물분율이 states 파일을 읽던 중
states.v20260127.nc      175개, 1850-01-01 .. 2024-01-01
transition_v20260127.nc  174개, 1850-01-01 .. 2023-01-01
```
- **★ 해빙과 성격이 정반대다. 토지이용은 지면 강제장 자체**(작물·목초 분율, 관개)라 없는 해를
  지어내면 그 해 결과가 조작값에 의존한다. 게다가 전이(transition)는 2023-01-01까지라 2024를 돌리려면
  전이까지 만들어야 한다.
- **판단: 확장하지 않고 1979–2023으로 마감.** 경계가 자의적이지 않고 "LUH2 토지이용 강제장이
  제공되는 기간"이라는 근거가 선다. 1년 얻자고 지면 강제장을 지어내는 것은 대가가 크다.

**교훈**: 경계자료가 지면에 도달하는지 여부로 처리가 갈린다. **도달하지 않으면 채워도 되고(해빙),
도달하면 채우면 안 된다(토지이용).** 판정 근거는 §13.42의 강제장 전달 검증이다.

**→ 보고서 수정**: "1979–2024" → **"1979–2023 (45년)"**. 사유는 LUH2 강제장 가용 기간.

### 13.55 ★★★★ 하구 유량 진단 착수 — 동아시아 (2026-09-08)

과제의 고유 축(지면→해양)을 처음으로 열었다. 지금까지 진단은 전부 지면에서 끝났는데,
**하구 방류량은 지면이 해양에 실제로 전달하는 양**이고 결합모델에서는 연안 염분·성층을 결정한다.

**관측**: Dai et al. (2025) — Dai & Trenberth(2002)의 2025년 갱신판.
`/Volumes/data02/runoff/Dai2025/coastal-stns-Vol-monthly.updated-Aug2025.nc`
**936개 하천, 1900-01~2024-12 월별**(1500개월), CC-BY-4.0, Zenodo 17379716.
우리 본실험(1979–2023)을 완전히 덮는다. 기존 GRDC/UNH 사본은 관측이 1994년에 끝나고
격자자료가 기후값이라 경년비교가 불가능했다.
- `FLOW`는 **관측소** 유량, `ratio_m2s`가 하구/관측소 비 → **반드시 곱해야** 하구 값이 된다.
- `annual-dis-*-scaled-con.nc`(격자형)는 미계측 유역까지 스케일업한 값이라 모델과 직접 비교 금지.

**결과** (`lm4/scripts/discharge_vs_dai.py`, 1979–2023 월별 기후값):

| 하천 | 관측 m³/s | 모델 | 모델/관측 | r(계절) |
|---|---|---|---|---|
| **장강** | 29,172 | 20,001 | **0.69** | **0.92** |
| **주강 3지류 합** | 9,812 | 5,544 | **0.56** | **1.00** |
| **황하** | 834 | 2,181 | **2.61** | 0.72 |
| 회하 | 1,847 | 217 | 0.12 | 0.95 |
| 오강 | 366 | 1,754 | 4.80 | 0.69 |
| 시나노(일) | 513 | 676 | 1.32 | **0.03** |
| 이시카리(일) | 480 | 154 | 0.32 | 0.80 |

**① 대하천은 위상 정확, 크기 30~44 % 과소.** 장강 r=0.92, 주강 r=1.00 — 몬순 강우에 대한
유출 타이밍은 맞고 양이 부족하다. G-RUN 전지구 유출 과소와 같은 방향의 **일관된 계통오차**.

**② ★ 황하 2.6배 과대는 모델 물리의 오류가 아니라 "인간 물이용 부재"다.**
황하는 관개 취수로 실제 유량이 자연 유량의 1/3 이하이며 1990년대엔 단류까지 갔다.
모델에 취수·댐이 없어 자연 유량을 그대로 낸다. **연안 담수 유입을 다루는 본 과제의 직접적 개선 항목.**

**③ 일본 하천은 융설 위상을 놓친다.** 시나노 관측은 4월 융설 첨두인데 모델은 7월(r=0.03),
이시카리도 4월 첨두 누락. 고위도 심층토양 한랭편차·진폭과대(§13.50대 토양온도)와 연결될 가능성.

### 13.56 ★★★ 세 번째 변수정의 함정 + C96 격자 함정 (2026-09-08)

**변수 함정 — `rv_Qavg`는 모의 유량이 아니다.**
단위가 `m3/s`이고 이름이 "river flow"라 처음에 이걸 썼는데 **계절선이 완전히 평평**했다.
소스: `river.F90:1439` `register_diag_field(..., 'rv_Qavg', ..., 'long-time average vol. flow')`
→ **라우팅 계수 `o_coef` 산정에 쓰는 처방된 다년평균**, 시간에 대해 상수다.
`dis_liq`(kg/m²/s → × cell_area/1000 = m³/s)로 바꾸니 장강 상관이 **0.15 → 0.92**.
→ **`runf`/`mrro`(§13.48), native/CMIP `lai`(§13.30)에 이은 세 번째.** 이 모델에서 유출·식생 관련
변수는 이름과 단위가 맞아 보여도 소스에서 등록부를 확인할 것.

**격자 함정 — C96에서 주강 3지류가 한 격자다.**
서강·북강·동강 하구가 약 100 km 격자 하나에 들어가, 따로 비교하면 두 개가 4~7배 과대로 보인다.
합쳐서 하나로 보면 0.56. 회하는 2.47° 떨어진 **장강 수로**를 잡아 10배 과대였다.
→ 매칭 규칙: ① 최근접이 아니라 **반경 내 최대 유량 격자**(하구는 유량의 국소 최대) ②
같은 격자에 걸린 관측소는 **합산해 하나의 계로** ③ 거리 1.75° 초과 매칭은 폐기.

### 13.57 유출 계산 사슬 — 코드 추적 (2026-09-08)

```
강수·융설
  ↓
토양 컬럼 (soil.F90) — 7개 경로
  lrunf_sn 포화초과(2536)  lrunf_ie 침투초과(3611)  lrunf_bf 기저(2529)
  lrunf_if 중간(2530)      lrunf_al 활동층(2531)    lrunf_sc 지하수(2591)
  lrunf_nu 수치과잉(3454)
  → soil_lrunf = 7성분 합 (2828)
  ↓
타일 면적가중 합 (land_model.F90:2441)  runoff += (snow_frunf+subs_lrunf+snow_lrunf+subs_frunf)*tile%frac
  ├─ runf = snow_lrunf+snow_frunf+subs_lrunf (2550)   ← 전 성분
  └─ mrro = lrunf_ie+lrunf_sn+lrunf_bf+lrunf_nu (soil.F90:2996) ← soil 모듈 4성분만
  ↓
update_river (land_model.F90:1335)
  ↓
하천 라우팅 (river_physics.F90)
  tocell(D8) 방향, travel(하구까지 거리) 순서로 상류부터 처리
  비선형 저수지: storage(t+1) = (avail^(1-o_exp) + o_coef*(o_exp-1)*dt)^(1/(1-o_exp))  (378)
                outflow = (avail - storage)/dt  (407)
  DHG: depth = d_coef*outflow^d_exp, width = w_coef*outflow^w_exp, vel = Q/(w*d)  (392)
  o_exp = 1/(AAS_exp%on_w + AAS_exp%on_d), o_coef ∝ outflowmean  (river.F90:407,411)
  말단 호수(tocell=0, landfrac≥1) → 바다로 안 나감 (216)
  ↓
discharge2ocean (river.F90:595) → /cellarea (624) → **dis_liq** (682)
```

성분별 진단(`id_lrunfs`·`id_lrunfg`·`lrunf_if` 등)은 **소스에 등록돼 있으나 diag_table에 없다.**
현재 출력에서 얻을 수 있는 분해: `mrro − mrros` = 기저+수치, `runf − mrro` = 중간+활동층+지하수+적설경로.
완전 분리하려면 diag_table 추가 후 1개월 시험적분(약 1시간) 필요.

### 13.58 ★★★★ 북극 하천 하구 유량 — 총량은 맞고 융설 위상이 이르다 (2026-09-08)

Dai 자료의 **북극해 유입 70개 하천** 중 상위 10개 계를 §13.55와 같은 방식으로 비교.
지역 선택은 경도 박스가 아니라 **유입 해역(`ocn_name` = ARC)** 으로 했다 — 시베리아 유역이
극을 감싸고 있어 경도로 자르면 반토막 난다.

| 하천(계) | 관측 m³/s | 모델 | 모델/관측 | r(계절) |
|---|---|---|---|---|
| **예니세이** | 19,796 | 20,064 | **1.01** | **0.99** |
| 오브+푸르 | 14,432 | 16,251 | 1.13 | 0.55 |
| 레나 | 17,623 | 11,616 | 0.66 | 0.83 |
| 매켄지 | 9,112 | 5,478 | 0.60 | 0.64 |
| 페초라 | 5,018 | 4,654 | 0.93 | 0.86 |
| 북드비나 | 3,479 | 3,198 | 0.92 | 0.84 |
| 콜리마 | 3,915 | 2,832 | 0.72 | 0.52 |
| 인디기르카 | 1,595 | 2,494 | 1.56 | 0.86 |
| 올레뇨크 | 1,268 | 1,296 | 1.02 | 0.73 |
| 야나 | 1,148 | 854 | 0.74 | 0.17 |

**★ 총량 대비: 북극 0.89 (2,442 → 2,169 km³/yr) vs 동아시아 0.71 (1,358 → 963).**
G-RUN 위도밴드에서 60–90N이 −12.5 %로 전 밴드 중 최선이었던 것과 **독립적인 방식으로 일치**한다.
격자 유출과 하구 유량이 같은 결론을 준다는 점에서 신뢰도가 높다.

**★ 계통적 위상 오류 — 융설 첨두가 한 달 이르고 감수가 너무 빠르다.**
예니세이·오브·콜리마·야나·올레뇨크·매켄지 모두 **모델 5월 / 관측 6월** 첨두. 첨두 뒤
7월부터 관측보다 훨씬 낮게 떨어진다(매켄지·레나·콜리마). 융설이 한꺼번에 빠져나가고
여름 유출이 유지되지 않는다.
→ **고위도 심층토양 한랭편차(−5 K)·계절진폭 과대(+66 %)와 같은 이야기일 가능성**:
동결·융해가 이르고 급격하면 융설 첨두도 이르고 감수도 빠르다. 다음 진단 대상.

**매칭 규칙 보완 — 탐색 반경은 유량이 아니라 유역면적에 비례시킬 것.**
```
radius_deg = 1.0 + 3.0 * min(1, area_mou / 2.5e6)
```
- 처음에 유량 기준으로 했더니 **황하가 탈락**했다. 취수로 관측 유량이 자연의 1/3이라
  반경이 작게 잡혔기 때문. **하구 크기는 유역 규모를 따르지 인간이 남긴 물의 양을 따르지 않는다.**
- 오브는 만 길이 800 km 탓에 모델 하구가 Dai 좌표에서 **3.50°** 떨어져 있다(모델 69.1N 75.9E vs
  Dai 66.8N 69.2E). 면적 기준이면 반경 4.0°로 잡혀 정상 매칭되고, 푸르와 같은 격자에 들어가
  **오브+푸르 하나의 계**로 합산된다.
- 모델 유량 50 m³/s 미만 격자에 걸린 매칭은 **실패로 간주하고 폐기**(하천이 아닌 격자).

### 13.59 ★★★ postprocess: C96 → lat-lon 변환기, 격자검증이 한대림 구멍을 잡았다 (2026-09-11)

도구 `lm4/postprocess/lm4p_to_latlon.py`. LM4P 지면출력은 `grid_index`(타일별 육지점만 담은
1차원) 위에 있어 좌표가 없다 — ncview로 못 연다. 좌표를 복원해 규칙격자 nc로 쓴다.

**좌표 복원의 함정**: `C96_grid.tile?.nc`는 193×193 **supergrid**(모서리·중점 교대)다.
셀 중심은 `[2j+1, 2i+1]`. `[j,i]`를 그냥 쓰면 **모서리 좌표가 붙어 반 셀씩 밀리고**,
지도는 "거의 맞게" 보인다. → `[1::2,1::2]`

**★ 격자검증이 실제 결함을 잡았다.** 첫 구현은 목표 칸에 떨어지는 점을 평균(`bin`)했는데:

| | bin | nearest |
|---|---|---|
| 유효 격자 | **22.1 %** | **31.1 %** (전지구 육지 비율과 일치) |
| 시베리아 62N/100E | **nan** | 1.32 |
| 고위도 | **점박이·구멍** | 정상 |

- 원인: 1° 경도 칸은 cos(lat)로 좁아지는데 C96 셀은 ~100 km 고정 → **55°N 이상에서 목표 칸
  상당수에 모델 점이 하나도 안 떨어진다.**
- **하필 그 구멍이 한대림 전체** — §13.26 아북극 편차를 보려던 바로 그 지역이었다.
  "값이 그럴듯하다"로는 절대 못 잡았을 결함이고, **원본 배열 플롯에서 눈으로 보여** 잡혔다.
- 해결: 구면 최근접(`cKDTree`, 3D 단위벡터) + 120 km 상한. 값을 만들어내지 않고
  이웃 값을 가져올 뿐이며, 바다는 상한 밖이라 결측으로 남는다.

**grid-verify 통과 (2026-09-11)**: dims (time,lat,lon)=(12,180,360), lat 오름차순
−89.5→89.5, lon −179.5→179.5, 단위 m²/m², 결측 1e20. 부호검정 아마존 6.65 · 콩고 6.51 ·
보르네오 6.54 · 사하라 0.00 · 남극 nan.

- **비교는 여전히 모델 격자에서** 할 것. 이 변환은 **보기 위한 것**이지 점수 매기려는 게 아니다.
  두 장을 제3의 격자에 올리면 어느 쪽에도 없는 오차가 생긴다. [[grid-compare-on-model-grid]]
- **★ `bl_max`·`nsc`가 이미 `land_month`에 있다.** §13.57·LAI PDF에서 "diag_table 추가 후
  1개월 시험적분 필요"라고 적은 것은 **틀렸다** — 포화 판정은 기존 출력만으로 지금 가능하다.

### 13.60 ★★★ 잎 상한 진단: 식생지 절반이 LAImax에 눌려 있다 → LMA는 knob가 아니다 (2026-09-15)

스크립트 `lm4/scripts/lai_ceiling_diagnosis.py`, 입력 §13.59 변환기의 bl·bl_max 1° (1982–2020,
생장기 평균: NH 5–9월 / SH 11–3월), cos(lat) 가중. 결과 `/Volumes/data02/LM4P/postprocess/lai_ceiling_1982_2020.npz`.

**논리**: `bl_max = LMA·LAImax·crownarea·(1-gap)`, `LAI = bl/(LMA·crownarea·(1-gap))` → bl=bl_max면
**LAI=LAImax, LMA가 정확히 소거**된다. 상한에 닿은 셀은 LMA를 얼마를 주든 LAI가 안 움직인다.

| bl/bl_max | 1° 재격자 (cos lat) | **native C96 (land_area)** |
|---|---|---|
| ≥0.90 (상한 제한) | 50.7 % | **49.0 %** |
| 0.50–0.90 | 40.4 % | 42.6 % |
| <0.50 (탄소 제한) | 9.0 % | 8.4 % |
| p50 / 평균 | 0.903 / 0.828 | 0.895 / 0.828 |

**보고서엔 native 열을 인용할 것.** 1° 열은 시각화용 최근접 재격자(§13.59)에서 잰 값이라 C96 육지점의
15.8 %가 어느 1° 셀에도 안 들어가고 고위도 점은 여러 셀에 복제돼 cos(lat) 가중이 모델의 land_area 가중과
같지 않다(2026-09-15 검토 지적 → 같은 날 native 검산 추가, `lai_ceiling_diagnosis.py` 말미). 차이는 ≤2 %p로
결론은 그대로. 위도대별 상한 비율(1° 기준): 0–30S 60 % · 30–60N 55 % · **60–90N 19 %**.
- 열대(아마존 0.998, 콩고 0.917, 보르네오 1.000)·미국 중서부 0.965 → **상한**. 여기의 LAI 편차는 LAImax 문제.
- 한대림은 상한 아래(캐나다 0.69, 시베리아 0.86, 스칸디나비아 0.83) → §13.26 아북극 편차만이 **탄소 공급**(GPP·할당) 쪽 문제.
- **결론**: LMA 튜닝은 전지구 LAI를 못 고친다. 열대·중위도는 `LAImax`(spdata), 한대는 탄소 사슬(§13.53)을 따로 봐야 한다.
- 주의: 비율이 1을 넘는 p95=1.004는 코호트 집계 순서(bl·bl_max를 각각 면적가중 후 나눔) 탓의 잔차이지 물리가 아님.

### 13.55 ★ 토지이용 전이 off 옵션 = CLM5식 "고정 토지이용" (2026-09-17, 미실행)

- 스위치: `&landuse_nml do_landuse_change`(`lm4P/transitions/transitions.F90:136`). ctl은 `.TRUE.`(LUH2 v20260127
  transition/states/landfrac, `distribute_transitions='min-n-tiles'`, `rangeland_is_pasture=.TRUE.`).
  `.FALSE.`면 `land_transitions_init`가 293행에서 return → 전이 없음, `landuse.res` 시각 검사(§13.47 블로커)도 안 탐,
  2023 LUH2 종료 제약도 사라짐.
- 형태: 타일 구성이 seed 상태(2010년 토지이용 면적, §13.47의 수준편향 포함)로 **동결** = CLM5 `2000_` compset의
  "고정 토지이용"과 같은 형태, 연도만 2010 vs 2000. CLM5 surfdata(PFT 분율)를 LM4 타일로 옮기는 변환기는 없고
  분류체계도 달라 "같은 파일"은 불가. 둘 다 LUH2 파생이므로 정합은 **연도**로 맞추는 것이 현실적: LM4 쪽을
  2000년으로 바꾸려면 all-natural seed에 states 2000을 초기 전이로 심어야 하는데(`transitions.F90:355`, cold start
  경로) 현 seed엔 이미 2010 LU 타일이 있어 이중 전환(§13.47) → 비현실적. 필요하면 **CLM5 쪽을 2010 fsurdat로**
  맞추는 게 싸다(별도 결정).
- 비용: 느림의 본체는 코호트 수(37×, §13.17). 전이 off는 secondary/crop 타일 증가분만 제거 → 처리량 개선은 부분적.
- 스크립트: `lm4/run_scripts/LM4p_WFDE5_ctl_1979_2024.sh`(ctl 전체 재구성, 한 파일) + `LANDUSE=off` 변수로 위 변형.
- **결정(2026-09-17, 사용자)**: LM4p 고정-토지이용 변형은 **2010 동결(`LANDUSE=off`)**로 간다. CLM5 `simyr2000`과의 10년
  차이는 수용 — 2000년으로 맞추려면 all-natural seed로 300년+ cold-start spin-up(≈4개월, 크래시 위험 재개)이 필요해
  얻는 것에 비해 비용이 과함. 세 모델 형태 정합: CLM5 2000 고정 / LM4p 2010 동결 / Noah-MP 토지이용 없음.
  실행 시점 = CLM5 생산런 종료 후.
- **착수 (2026-09-22 17:21, job 8474 @climate01)**: `lm4p_lufix_1979-2023` (45년, ctl·CLM5·Noah-MP와 기간 정합). 설정 스크립트
  `LM4p_WFDE5_ctl_1979_2024.sh`를 `LANDUSE`로 런 이름·PBS -N·Y1까지 파생하도록 파라미터화(디렉토리명 3곳 하드코딩 제거),
  `chain_lm4p_ctl.sh`는 `R=` env 오버라이드. **스크립트 결함 1건 수정**: cycle 1 템플릿은 `npes_io_group = 8`인데 스크립트가
  "이미 48"로 가정 → assert에서 ABORT. sed로 48 설정 추가. 결과 run dir은 ctl과 `input.nml.template` diff가
  **`do_landuse_change = .FALSE.` 한 줄뿐**(data/field/diag_table·SIS_layout 동일, seed = cycle 1 끝 2011-01-01 03Z, ctl SEED_2010과 바이트 동일).
  체인: `nohup env R=<dir> bash chain_lm4p_ctl.sh 1979 2023` (로그인 노드). 예상 10.5 h/yr → 45년 ≈ 20일(10/12경).
  /data2 여유 4.9 TB(98% 사용, 내 몫 ~3 TB: clm5_bgc_pad 955 G·lm4_spinup30 485 G·clm5_bgc_ad 398 G·ctl 397 G) — 런 중 4 TB 아래로 가면 정리.

### 13.61 ★★ 생산런 후처리 — 1° 연별 파일 45개 (세 모델 형식 통일, 2026-09-28)

- 파이프라인 2단계. ① `lm4/postprocess/lm4p_to_latlon.py`(§13.59 변환기)로 **36변수 × 1979–2023**을 변수별 1° 파일로
  (`postproc/lm4p_ctl/byvar/`, 스크립트 `lm4p_latlon_yearly.sh`, 1시간) → ② `lm4p_byvar_to_yearly.py`로 **연별 1파일 45개**
  (`postproc/lm4p_ctl/yearly/lm4p_ctl.YYYY.nc`, 12 records × 36변수, 62 MB/yr, 합 5.1 GB). CLM5·Noah-MP와 같은 레이아웃.
- **★ 변환기 결함 수정 — 층 변수 미지원**: `read_var`가 타일을 **axis=1 고정**으로 연결해 `soil_T(time,zfull_soil,grid_index)`에서
  층을 이어붙이려다 사망(`3839 vs 3939`). `grid_index`를 **이름으로 찾아 마지막 축**에서 연결하고, regrid는 선행차원을 접어
  처리, 출력에 층 차원을 그대로 실음. 이제 soil_T·soil_liq·soil_ice(zfull_soil 20) · swdn/swup(band 4)도 변환됨.
- **검증(native C96 대조, 제3격자 안 거침)**: 층 순서·깊이 정상(zfull_soil 0.01/0.04/0.08…), **계절진폭이 깊이 따라 단조 감소
  16.87 K(1층)→0.47 K(20층)** — 층 뒤섞임 없음의 물리적 증거. 1월 1층 육지평균 native 283.28 vs 변환 cos(lat)가중 **283.23 K**(차 0.05).
  무가중 변환평균 284.3 vs native 289.9의 −5.6 K 차이는 1° 무가중이 고위도를 과대대표하는 효과([[lsm-landmean-comparability]]), 변환 오류 아님.
- 연별 파일 감사: 45개 전부 12 records·월 1–12·36변수, byvar 대비 **max|diff| 0.000e+00**.
  45년 육지평균 추세/10년 — sens −0.42 W/m², t_ref +0.25 K, lai −0.015, snow −0.17 mm, gpp −0.005.
  **t_ref +0.25 K/dec는 CLM5(+0.24)·Noah-MP(+0.24)와 일치** — 같은 WFDE5를 받는 세 모델이 독립적으로 같은 온난화를 냄.
  단 lai·gpp는 세 모델 중 LM4p만 감소 추세 → §13.46·13.52의 목재 발산/표류와 연결해 별도 진단 필요.
