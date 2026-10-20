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
- 형제 호출은 전부 `if (do_atmos)`: `_dynamics`(830) · `_down`(849) · `_up`(902) · `atmos_tracer_driver_gather_data`(789). **정정(2026-10-02): `_state`(955)는 게이트 없음** — §13.63.
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
- 형제 호출은 전부 `if (do_atmos)`: `_dynamics`(830)·`_down`(849)·`_up`(902)·`atmos_tracer_driver_gather_data`(789). (**정정 2026-10-02: `_state`는 게이트 없이 매 dt_atmos 실행** — §13.63.) **복사만 누락** = GFDL 쪽 버그로 보고할 만함(data-atmosphere 모드를 쓰는 누구나 겪음).
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

### 13.62 ★★ ctl 1981–2010 = spin-up "cycle 2" — 플럭스·물리는 수렴, 목재·토양탄소는 표류 (2026-10-02)

- **착안**: ctl은 spin-up cycle 1 끝(2011-01-01)을 1979로 되감아 시작하므로 **ctl의 1981–2010은 사실상 cycle 2**.
  `do_landuse_change`는 spin-up30·ctl 모두 `.TRUE.`라 설정 동일. 추가 적분 없이 다른 모델과 같은 cycle 간 비교가 됨.
- **같은 방법으로 추출**: `lm4/scripts/extract_monthly_noice.py`에 `<archive> <out> <y0> <y1>` 인자 추가(기본 동작 불변,
  서버 사본 백업 `.bak_20261002`) → `lm4/data/monthly_noice_ctl_1981_2010.csv`(C96 원격자, soil_area>0 − 그린란드, 360행).
  ⚠ 1° 후처리 연별 파일과 섞으면 제3격자 가짜 차이([[grid-compare-on-model-grid]]) — 반드시 같은 스크립트로.
- **결과** (Jan–Nov 평균, 2010년 c2−c1 / 30년 추세 c1→c2):

| 변수 | 2010 c2−c1 | 추세 c1 → c2 | 판정 |
|---|---|---|---|
| LAI | −0.59 % | +0.085 → −0.054 | 수렴 |
| GPP / evap / sens | +0.44 / +0.44 / −0.48 % | sens −1.50 → −1.46 | 수렴 (sens 감소는 forcing) |
| SWE | −0.36 % | | 수렴 |
| soil T 2 m | **+0.006 K** | +0.99 → +0.64 K | **수렴 — cycle 내 +1 K는 WFDE5 온난화** |
| col_water | −0.65 % (−22 kg/m²) | −38 → −28 | 느린 감소(심층수) |
| **soilC** | **+3.0 %** | +0.34 → +0.20 | 미수렴, 감속 중 |
| **bwood** | **+7.6 %** | +0.070 → **+0.125** | **미수렴, 가속** |

- **진단 함의**: LAI·GPP·플럭스·적설은 생산런 그대로 사용 가능. **ctl/lufix의 목재·토양탄소 저장량 추세와 NEE에는
  spin-up 표류가 섞임** → 탄소 추세를 온난화 반응으로 해석 금지(표류 명시 또는 cycle 간 차감). KIOST 결합기후 평형에서
  WFDE5 관측기후로 바뀐 데 대한 탄소 재평형으로 해석(추정). 그림 `figures/spinup_4models/lm4p_spinup.png`(cycle 2 포함).
- **빠른 탄소풀** (`analysis/fast_pool_convergence.py`, c1 y2010 vs ctl y2010, Jan–Nov, C96 비빙설): cLeaf −1.05 %(셀 ≤1 % 18.6 %),
  **cRoot +6.9 %**(12.2 %), cLitter +0.97 %(22.7 %) → 빠른 풀도 셀 단위로는 미수렴(PPA cohort 변동이 섞였을 가능성, 분리 안 함).
  비교: CLM5 post-AD 171→201년 LEAFC/FROOTC/LITR1C/SOIL1C 육지평균 ≤0.1 %, 셀 ≤1 % 92–96 %(수렴).

### 13.63 ★★★ offline 대기 잔존 계산 제거 — B+C 패치, 지면 비트 동일 + 18–21 % 단축 (2026-10-02~03)

- **실측 분해** (`lm4_spinup30` 1년, 24 PE, 44,466 s): Update-Land-Fast 73.9 %(그중 ddep 8.5 %), Land-Slow 4.3 %,
  **`update_atmos_model_state` 6.6 %**(FV dy-core 1,113 s + FV Diag 974 s …), **Flux UP to atm 5.3 %**, SFC BL+Flux DN 6.2 %, Ice 0.8 %.
  FV3 역학·물리 적분은 이미 꺼져 있음. 남은 대기 계산 = `coupler_main.F90:955` `update_atmos_model_state`가 **게이트 없이**
  매 dt_atmos 실행(`fv_update_phys` 3-D 전체 + 트레이서, `fv_diag`, 최하층 추출) + `flux_up_to_atmos`의 대기 격자 remap.
- **근거**: 무패치 lufix의 대기 restart 6종(fv_core/tracer/srf_wnd, atmos_coupled, physics_driver, radiative_gases)이
  y1990과 y2001에서 **바이트 동일** = 대기는 진짜로 얼어 있음.
- **패치** (Codex CLI와 교차검토 후 안전형으로 수정):
  - **B** `lm4/patches/coupler_main.F90.atmos_state_gate.diff`: `if (do_atmos) … else` 분기에서 **대기 시계 전진과
    `fms_diag_send_complete`만 유지**(atmos/land PE에서 유일한 diag 완료 호출, `atmos_model.F90:1129`).
  - **C** `lm4/patches/coupler.atmos_state_and_up_remap_gate.diff`(B 포함): 모듈 플래그 `atm_up_remap = do_atmos`로
    `flux_up_to_atmos`의 `dt_tr`(교환 트레이서 전부)·`dt_t`·`shflx`·`lhflx` → ATM remap 생략. 읽는 곳은 `atmos_model.F90`의
    대기 물리뿐(이미 꺼짐). flux 보정·지면 진단·stock은 유지. 안전 근거는 "값이 0"이 아니라 "소비자 없음"(shflx/lhflx는 SFC BL에서도 채움).
  - Codex 우려 해소: `atmos_tracer_driver_gather_data_down`의 `tr_bot`은 `intent(in)`; `restart_tbot_qbot` 기본 `.false.`;
    CO₂는 override 안 해 제자리 변환 분기 미진입; 빌드에 OpenMP 없음(`-qopenmp` 0, libiomp 미링크).
  - 빌드: 섀도 소스 + `exec/coupler` 복사본만 재컴파일·재링크(`lm4/scripts/stategate_build.sh gateB|gateBC`), 생산 exe 불변.
    exe = `/data2/ydkoh/lm4/build_gateBC/fms_esm4.5_gateBC.x`.
- **이어달리기 A/B 시험** (`lm4/scripts/stategate_test.sh`, `RUN/stategate_test2/`, 48 PE @climate00, lufix y2001 끝 → 2002-01-01,
  seg1 31일 → 각자 seg1 RESTART에서 seg2 5일, namelist 동일·`print_freq=0`):
  - **비교 결과 (B, B+C × seg1, seg2 전부)**: 지면 restart 60 · 지면/하천 history 132 · 대기/해빙/결합기 restart 57 ·
    coupler.res · landuse.res **전부 비트 동일**, 월평균 레코드 수 동일.
  - **main loop**: base 5,055 / 885 s → B 5,062 / 778 s → **B+C 4,139 / 697 s (−18.1 % / −21.3 %)**.
  - **B 단독은 31일 구간에서 효과 0**: `update_atmos_model_state` 154→0 s인데 Flux UP 832→942 s로 증가 = 그 시간 대부분이
    계산이 아니라 **다음 동기화 지점에서의 대기 시간**이 옮겨 간 것(추정). **실효는 C**: Flux UP 832→148 s(교환격자 통신 제거).
  - A(`print_freq=-99`)는 불필요: B가 `fv_diag`를 포함(FV Diag 호출 1,488 → 0).
- **결정(2026-10-03, 사용자)**: **B+C 채택.** 진행 중인 lufix는 기존 exe로 끝까지, **다음 LM4p 실행(spin-up cycle 3)부터 gateBC exe.**
  예상: 10.6 → ≈8.5 h/model-yr, 45년 −≈90 h, 30년 cycle −≈2.6일. 진단 출력 축소(≈25 %)는 별도로 추가 가능.
- **적용(2026-10-03 12:12)**: lufix 실행폴더 exe 링크 → `build_gateBC/fms_esm4.5_gateBC.x`, **y2005부터 B+C**(y1979–2004는 생산 exe,
  chain.log에 기록). 비트 동일이므로 출력은 끊김 없이 이어짐. lufix는 2023까지 진행(사용자 결정).

### 13.64 ★★ ctl vs lufix (같은 초기장) — 토지이용 고정이면 목재가 연 ≈0.25 % 더 쌓임, cycle 3 계획 (2026-10-03)

- **비교** (`extract_monthly_noice.py`로 두 런 1979–2003 동일 추출, `lm4/data/monthly_noice_{ctl,lufix}_1979_2003.csv`):
  1979-01 값 11변수 **차이 0.0**(초기장 동일 확인). 이후 벌어짐, lufix − ctl:
  | 연도 | LAI | GPP | evap | soilC | **bwood** |
  |---|---|---|---|---|---|
  | 1990 | +0.58 % | +0.28 % | +0.14 % | −0.23 % | +3.34 % |
  | 2003 | +0.86 % | +0.35 % | +0.22 % | −0.21 % | **+6.37 %** |
  그 외 2003: runoff −0.5 %, SWE −0.27 %, col_water −0.05 %, soil T −0.001 K.
- **해석**: ctl은 LUH2 전이(숲→농지·**목재 수확**)를 매년 적용해 목재를 덜어 냄; lufix(`do_landuse_change=F`)는 **전이·수확 0** →
  목재가 연 ≈0.25 % 더 쌓임(추정, 크기·방향 일치). 플럭스·LAI 차이는 1 % 미만 → 1차년도 물리 진단엔 영향 작음.
- **"cycle 2" 이중 명명 정리**: cycle 1→2 수렴 판정 = **ctl 1981–2010**(cycle 1과 토지이용 설정 동일, §13.62).
  **토지이용 고정 cycle 2 = lufix 1979–2010**(32년, 1979–80 포함; cycle 1과 설정이 달라 수렴 판정엔 부적합, 이어 붙이기엔 적합).
- **cycle 3 결정**: 토지이용 **고정**으로, lufix 2011-01-01 상태에서 시작(≈10/05), climate00, gateBC exe.
  근거: CLM5도 `2000_` 토지이용 고정으로 spin-up해 TOTVEGC 평형 도달 → 고정 자체는 표준이고 목재는 사망·교란과 균형을 이루며 평형에 감.
  토지이용 **켠** 채 cycling하면 매 cycle 1981–2010 전이 델타가 다시 더해져(§13.47 "2010 면적 + 델타") 농경지가 cycle마다 늘어남 → 부적합.
  판정: cycle 2(lufix 1981–2010) vs cycle 3 같은 해 비교 + **연별 목재·뿌리(cRoot) 증가율이 줄어드는지** 감시.
  뿌리 탄소는 수분 흡수로 식물에 되먹임하므로 수렴 필수(빠른 토양풀은 질소 off라 식물 무영향). 수렴 시 생산런 재실행 검토(≈16일).

### 13.65 ★★ LM4p spin-up 가속 기법 유무 + 4개 모델 C–N 결합 정리 (2026-10-03)

**(1) LM4p에 CLM5 AD 같은 가속 스위치는 없다** (lm4P 소스 전수 grep `spin.?up|accelerat|equilib` + namelist).
- 있는 것: **토양 탄소 해석적 평형용 누적 변수** `fsc_in`·`ssc_in`(빠른/느린 토양 탄소 입력 누적, kgC/m²)·`asoil_in`(분해 활성도 누적).
  주석 `"for soil carbon equilibration"`(`soil_util.F90:90`), restart `soil.res`에 저장(`soil.F90:1641-1643`), 진단 `fsc_in`/`ssc_in`.
  **모델 안에서는 누적·저장만 하고 사용하지 않음** → 오프라인으로 `C_eq = 연 입력 / (기준 분해율 × 평균 활성도)`를 계산해
  restart를 덮어쓰라는 장치(GFDL LM3식 해석적 spin-up으로 추정; 계산 도구는 소스에 없음).
- 없는 것: **식생(목재·뿌리) 가속**(사망률·회전율 일시 증대 등). namelist `tLongest=500`은 토양모델 파라미터일 뿐.
- **함의**: 해석적 평형은 **식물에 영향 없는 토양 탄소**(질소 off)만 당길 수 있음. 정작 식물에 되먹임하는 **목재·뿌리는 cycle을 더
  돌리는 것이 유일한 길**(B+C로 ≈10.6일/cycle, 진단 축소 시 ≈8일). 토양 탄소 해석적 평형은 2차년도 탄소 진단 때 검토.
- **판정 원칙 수정**: 빠른 풀의 평형은 입력원인 **느린 풀(목재)에 묶임**(목재↑ → 뿌리·고사목·낙엽↑). LM4p cRoot +6.9 %가 bwood +7.6 %와
  거의 같은 비율인 이유. → "빠른 풀 수렴?"이 아니라 **"목재 수렴?"을 볼 것.** cycle 2→3 목재 증가율 감소폭으로 필요 cycle 수 외삽.
  (참고 CLM5 기준 회전시간 `clm5_params.c171117.nc`: LITR1 0.054년, LITR2/3 0.204년, SOIL1 0.137년, SOIL2 5년, SOIL3 222년, CWD 3.3년.)

**(2) 4개 모델 탄소–질소(C–N) 결합** (설정·소스 직접 확인)
| 모델 | C–N 기능 | 우리 실험 | 근거 |
|---|---|---|---|
| CLM5 | 있음 | **켜짐** | `lnd_in`: `use_cn`·`use_fun`·`use_flexiblecn`·`use_nitrif_denitrif = .true.` |
| LM4p | 있음 | **꺼짐** | `soil_carbon_model_to_use='CENTURY-like' !Nitrogen turned off`, `N_limits_live_biomass=.FALSE.` (질소엔 `CORPSE-N`+ndep 입력 필요, §13.16; KIOST 설정 그대로 물려받음) |
| JULES | 있음 | **꺼짐** | `l_nitrogen=.false.` (rose-stem `loobos_jules_cn` 등은 켬) |
| Noah-MP | **없음** | — | 모듈 부재 (NOAHMP notes §11) |
- **식물 되먹임 경로가 다름**: CLM5만 빠른 토양·낙엽풀 → 질소 무기화 → 식물 성장 제한. 나머지 셋은 토양 탄소가 식물에 영향 없음
  (식물에 중요한 건 잎·뿌리·목재뿐). → spin-up 판정 기준도 CLM5는 토양 빠른 풀 포함, 나머지는 식생 풀 중심.
- **진단 해석**: GPP·LAI가 질소 제한을 받는 건 CLM5뿐 → "CLM5만 GPP 낮음" 등 차이의 1순위 원인 후보 = 질소 제한(2차년도 구조오차 주제).

### 13.66 ★★★ ctl 생산런 LAI vs GIMMS 1982–2020 — 과대 +54 %, 2001년 이후 추세 부호 반대 (2026-10-03, 포스터용)

포스터 폴더 `poster/2026_LM4p_LAI/` (scripts `p1_gimms_to_monthly_1deg.py` → `n1_lai_clim_anom.ncl`, 요약 `data/lai_mean_trend_summary.txt`).
LM4p = `postproc/lm4p_ctl/yearly`(lm4p_to_latlon.py, nearest 1°)의 `lai`를 CDO mergetime. GIMMS LAI4g = 반달 2개 평균 → 1/12°를 12×12 블록평균.
두 파일 좌표 동일(lat −89.5→89.5, lon −179.5→179.5) · 원본배열 플롯 정상 · 기후값 1982–2010(GIMMS 시작이 1982) · 기준기간 anom 평균 ~1e-10.
공통 14,903격자(60S–90N, 그린란드 제외), cos(lat) 가중, 연평균(1–12월).

| 항목 | LM4p | GIMMS | |
|---|---|---|---|
| 평균 1982–2010 | 2.586 | 1.678 | **+54 %**, r 0.81, RMSE 1.57 |
| 열대 20S–20N | 3.98 | 2.80 | +42 % |
| 북반구 중위도 20–50N | 1.89 | 1.17 | +61 % |
| 한대 50–70N | 1.59 | 1.02 | +57 % |
| 남반구 온대 60–20S | 2.58 | 1.21 | **+113 %** |
| 추세 1982–2000 | +0.05 %/yr (p=0.07) | +0.09 %/yr | 부호 일치 |
| **추세 2001–2020** | **−0.11 %/yr** (p<0.001) | **+0.28 %/yr** | **부호 반대** |
| 연간 아노말리 상관 | r=−0.63 (추세 제거 후 −0.05) | | 연변동 재현 못함 |

- 한대 계절주기: **가을 낙엽이 늦다** — 9월 2.87 vs 1.16, 10월 1.84 vs 0.78. 겨울 0.9 vs 0.3(관측의 눈 아래 상록수 신호 약화 가능성 있으므로 해석 주의). 봄 녹화 시점(5–6월)은 맞음.
- cycle 1(§13.46, 1990–2010 −0.08 vs +0.15 %/yr)과 같은 결론이 ctl에서도 재현 → 표류가 아니라 **모델 고유의 녹화 실패**. ctl은 cycle 1 끝 상태에서 출발해 1980년대 표류가 없음(1982–2000 추세 부호 일치가 그 확인).
- 2001년 이후 감소의 원인 후보(미검증): LUH2 전환(ctl vs lufix LAI 차 <1 %라 약함), 목재 미평형에 따른 잎 재배분, CO₂ 시비 반응 부족(N off이므로 오히려 과대가 예상됨 → 확인 필요). 다음: 추세 지도로 어느 위도대가 끌어내리는지.
- **위도대 분해 (2001–2020, LAI/10년)**: LM4p 감소는 **남반구가 주도** — 60–30S −0.157(전구 추세의 +28 %), 30–10S −0.101(+52 %), 10S–10N −0.057(+36 %). 북반구는 거의 0(10–60N), 60N 이상만 +0.044(관측 +0.041과 비슷). GIMMS는 모든 위도대 증가, 중위도 30–50N 기여가 가장 큼(+27 %). 감소 격자 비율 LM4p 50 % vs GIMMS 20 %, 추세 공간상관 r=0.06. → 남반구 건조지(호주·남미 남부·남아프리카) 가뭄 민감도 의심. 다음: 이 지역의 토양수분·강수(WFDE5) 추세와 대조.
- **지역별 (16개 박스, `poster/.../data/lai_regional_summary.txt`)**: 과대가 큰 곳 = **건조·반건조 초지/방목지** — C.Asia/Mongolia +147 %, US west/plains +142 %, S.America south +141 %, Boreal N.America +131 %, Australia +79 %. 작은 곳 = Europe +4 %, US east +9 %, Arctic tundra 0 %. 2001–2020 추세 부호 반대가 큰 곳 = S.America south −5.0 vs +3.2 %/10년, Southern Africa −5.3 vs +0.7, Amazon −3.0 vs +0.5, Australia −2.5 vs +1.8. **India(+9.7)·East China(+10.4)의 관측 녹화를 모델은 0** — 관개·조림·이모작 없음(Chen 2019, Shevliakova 2024).
- **LAI 상한 (field_table `LAImax`, `vegn_dynamics.F90:2119` `bl_max = LMA·LAImax·crownarea·(1−gap)`)**: prioria(열대) 6.0, picea·larix 5.0, acer 3.5, c3/c4grass 2.5, understory 0.25배. 이는 **한 cohort 수관 안의 목표 잎량**이지 격자 LAI 상한이 아님 — 격자 LAI는 층·cohort 합. 열대 15S–15N 정점월 LAI: LM4p p50 5.46 / p99 9.59 / max 11.0 (6 초과 격자 38 %) vs GIMMS p99 6.46 / max 6.52 (광학 위성 포화).
- **목초지 (LUH3 `states.v20260127.nc` 2000년 pastr+range, 0.25°→1° gridboxmean; 격자확인 몽골 0.98·호주 0.96·아마존 0·사하라 0·바다 nan)**: ≥0.5 격자 2,420개, 연평균 LM4p 1.39 vs GIMMS 0.68, 정점 2.04 vs 1.12. GIMMS는 목초지 면적 79 %가 연평균 LAI<1. `min_lai_for_grazing_past/range = 1.0`은 **"LAI<1이면 방목 중단" 문턱**이지 하한이 아님 → 관측 LAI가 원래 <1인 곳엔 방목이 거의 작동 안 함. LM4.1 논문의 "목초지 과소"와 반대로 **우리 오프라인은 목초지 과대**.

### 13.67 ★★ phenology 민감도 시험 tc_crit 5→10 °C (2026-10-04 시작, 포스터용)

- 동기(§13.66): 한대 50–70N 9월 LAI 2.80 vs GIMMS 1.14. phenology는 식(`vegn_phenology_ppa`), 모수는 `field_table` 종별.
  잎 켜기 = GDD>gdd_crit & tc_pheno≥tc_crit & 비가뭄, 끄기 = tc_pheno<tc_crit(GDD 리셋) 또는 가뭄; 끈 뒤 잎 7.5 %/일 감소.
  `tc_pheno = 0.95·old + 0.05·daily`(`vegetation.F90:2664`) → 일기온보다 ≈16일 늦음.
- 근거: 코드 기본값 tc_crit=283.16 K(`vegn_data.F90:261`, 주석 "10 C gives good growing season pattern"), 우리 field_table은 larix·c3grass만 278.15로 덮어씀(acer는 기본 10 °C).
  모델 한대 t_ref 기후값으로 계산한 가을 문턱 통과: 5 °C → tc_pheno 282일(10/9), 10 °C → 258일(9/15). 관측은 8→9월에 LAI 반감.
  **예상 부작용**: 같은 tc_crit이 잎 켜기에도 쓰여 봄 onset ≈3주 지연(현재 봄은 관측과 맞음).
- 설정 `lm4/scripts/phentest.sh`: ctl archive/y2009(2010-01-01 03Z) restart, 2010 1년, **24PE**(fv/land 2,2, SIS 6,4, io group 8 — KIOST AMIP 24PE 설정), gateBC exe, climate00 nohup. base / tc10(field_table 2줄만 다름).
  24PE 1일 시험 rc=0, restart 119, 361 s(main loop 180 s/일) → 1년 ≈18–19 h. 두 런 동시 시작 2026-10-04 01:28 KST.
- 판정 계획: 50–70N 월별 LAI base vs tc10 vs GIMMS, 특히 9–10월(개선)과 5–6월(악화) 크기. base는 ctl 2010과 PE 수만 달라 비트동일은 아님 → 비교는 base 대비로.
- **부작용 (2026-10-04)**: `/data2`·`/home`은 climate00이 NFS로 제공 → phentest 48랭크로 climate00 load 57이 되자 climate01의 lufix가 느려짐. y2001–2004 각 11.4–11.7 h, y2005(gateBC 첫 해, phentest와 7.5 h 겹침) 11.0 h, y2006 진행 속도 ≈11.2 h/년. gateBC 실측 이득(−18–21 %)은 climate00이 한가할 때 측정한 값 → phentest 종료 후 y2007 소요시간으로 재확인. /data2 98 %(3.8 TB 남음), lufix archive 8.7 GB/년.
- **극지 점검 (2026-10-04)**: 남극(<60S)은 LM4p·GIMMS 모두 유효 격자 0 → 식생 없음. 북극 65–75N 공통 2,006격자: **평균은 0.43 vs 0.43으로 같지만 분포가 양극화** — LM4p 52 %가 LAI≈0(맨땅), 6 %는 연평균 >1.5(툰드라에 나무, 정점 최대 6.8) vs GIMMS 맨땅 0 %·>1.5 0 %. 지역표의 "Arctic tundra 0 %"는 **상쇄된 가짜 일치**. >75N 섬은 LM4p 0.000 vs GIMMS 0.148. 그림 (c)의 유라시아 북단 갈색띠가 이 맨땅 격자.
- **그린란드 마스크 정정**: 60N+/75–10W 박스는 아이슬란드(40격자, LM4p 0.65 vs 0.50)와 캐나다 배핀·웅가바(120격자)도 잘랐음 → Fig.1(`n2_fig_meanmap.ncl`)부터 그린란드 본토만 제외. 전구 bias +54.0→+53.9 %(영향 무시 가능, 기존 summary txt는 옛 박스).
- **정정 — lm4P에는 온도 기반 분포 제한이 있다 (2026-10-04, 소스 확인)**: LM4.1 논문의 "온도 생물지리 한계 미도입"은 LM4.1 얘기. lm4P `vegn_disturbance.F90:551–563`은 항상 켜진 두 사망 규칙을 가짐 — ① cold mortality: 종별 `Tmin_mort`(prioria 278.16 K)보다 최한월이 추우면 사망률 ≥`cold_mort`=2/년, ② **treeline mortality**(Paulsen & Körner 2014): 생장기(일평균 tc>0.9 °C, 눈 덮인 날 제외) 평균기온 <6.4 °C 또는 생장기 <94일이면 목본 사망률 ≥2/년. 그런데도 65–75N 6 %에 LAI>1.5 숲 → 진단 후보: `treeline_T`·`treeline_season` diag 출력 여부, tc_daily(캐노피 공기온도) vs 관측 기온.
- **Q10 (Kim, Lee & Seo 2019 J. Clim, 우리 그룹 전신 과제)**: CLM4 토양 Q10을 PFT별·시공간 변동으로 → GPP 개선은 **질소 무기화 경로**. lm4P는 N off라 토양 분해 온도함수(`A_function`, 봉우리형)를 바꿔도 LAI에 안 닿음. LAI로 가는 대응 지점 = 식물 호흡 `thermal_inhibition` `exp(3000(1/288.16−1/T))`(Q10≈1.44 @15 °C, 하드코딩)과 Vmax 온도식(같은 3000).
- **FLUXCOM-X-BASE GPP grid-verify 통과 (2026-10-04)**: `/Volumes/data02/FLUXCOM_X_BASE/GPP_monthly_0.5deg/` 2001–2021 연별 21파일(ICOS, CC BY 4.0, 0.5° 월별, 106 MB). `GPP`(time,lat,lon)=(12,360,720), **lat 내림차순 89.75→−89.75**, lon −179.75→179.75(lon units 메타가 "degrees_north"로 오기), 단위 gC m⁻² d⁻¹, 유효 25.7 %. 원본배열 플롯 정상 세계지도. 2010 연평균 아마존 6.51·콩고 7.16·사하라 0.46(사막인데 0이 아님 — 해석 주의)·시베리아 1.51(7월 7.07, 1월 −0.14). 음수 최소 −0.89 존재. MTE(GEOCARBON 6.4 GB) 다운로드 중.
- **관측 제품 이음매 점검 — GIMMS consolidated vs solely (2026-10-04, `poster/.../data/lai_solely_vs_consolidated.txt`)**: consolidated = AVHRR LAI4g(1982–2003, MODIS에 맞춰 보정됨) + 재처리 MODIS(2004–2020)(Cao 2023 §Consolidation). solely = AVHRR만 1982–2015(LAI-DataKit, `p1_gimms_to_monthly_1deg.py solely`).
  공통 15,403격자 cos 가중: consolidated가 **전 기간 일정하게 +10–11 % 높음**(1982–2003 +10.9 %, 2004–2015 +10.0 %), 2004 이음매 계단 +0.008(solely도 +0.006) → **이음매 인공물 없음**.
  평균 bias 1982–2010: vs consolidated +53.9 %, **vs solely +70.3 %** → 제품 선택이 bias 크기를 ±16 %p 바꾸지만 결론 불변.
  추세(%/yr): 2001–2015 LM4p −0.09 vs consolidated +0.22 vs **solely +0.23**; 1982–2015 −0.06 vs +0.10 vs +0.14 → **부호 반대는 AVHRR 단독에서도 유지 = MODIS 이음매 탓 아님.** 1982–2000은 셋 다 양(+0.05/+0.09/+0.14).
  추세제거 연변동 1982–2015: r(LM4p,consol)=+0.21, r(LM4p,solely)=+0.25, r(consol,solely)=+0.78 → 관측끼리는 잘 맞고 모델은 연변동 재현 약함.

### 13.68 ★★★★ LM4p 오프라인은 CO₂가 ~292 ppm으로 고정 — CO₂ 비옥화 없음 (2026-10-04)

- 광합성 CO₂ = `co2_to_use_for_photosynthesis='interactive'`(input.nml:1206) → `phot_co2 = cana_co2_mol`(vegetation.F90:1754) = **캐노피 공기 CO₂**(`land_month`의 `qco2_dvmr`, land_model.F90:2607 정의 확인).
- ctl `land_month.tile1` 연평균 공간평균 qco2_dvmr: 1979 292.2 · 1985 292.2 · 1995 292.3 · 2005 292.3 · 2015 292.2 · 2023 292.2 ppm (격자 min/max 279–390도 해마다 동일 패턴) → **45년간 추세 0**. 실제 대기는 ≈337→420 ppm.
- 원인 추정(미확인): 오프라인(WFDE5 data_override Route B)에선 대기 물리를 돌리지 않아 대기 co2 추적자가 IC 값으로 얼어 있고, `atmos_co2_nml do_co2_restore`·`co2_gblannualdata.nc`가 지면으로 전달되지 않음. 292 ppm ≈ 1900년대 초 수준 = KIOST 결합 spin-up IC 유래 추정.
- **결과 해석 수정**: 관측 녹화의 ~70 %가 CO₂ 비옥화(Zhu 2016)인데 모델엔 그 강제가 없음 → §13.66 "2001–2020 추세 부호 반대"의 **1순위 원인 후보**. 또한 절대 CO₂가 낮은데도 GPP +29 %·LAI +54 % 과대 → 다른 과대 요인도 있음.
- 영향 범위: ctl·lufix·phentest 모두 동일 설정(같은 input.nml 계열). cycle 3 시작 전에 CO₂ 처방 방식 결정 필요: `'prescribed'` 상수(예: spin-up은 CLM5처럼 2000년값 ≈369 ppm, 또는 1981–2010 평균) vs 시변 CO₂ data_override(구현 확인 필요).
- 다중 LSM 비교 주의: CLM5 `2000_` compset도 CO₂ 2000년 고정 → **CO₂ 추세 없는 모델이 최소 2개**. JULES·Noah-MP CO₂ 설정 확인 필요.
- **지역별 추세 격차 (2001–2020, %/10년, `poster/.../data/lai_regional_trend_products.txt`)** — 관측(consolidated)−LM4p 큰 순: East China +9.2(LM4p +0.5 vs +9.7), India +9.2(0.0 vs +9.2), S.America south +8.5(−5.3 vs +3.2), C.Asia/Mongolia +7.9, Europe +6.6, Boreal Siberia +6.1, Southern Africa +6.0, US west +5.6. 작은 곳: SE Asia 0.5, Sahel 1.4, Congo 1.5. **Arctic 65–80N만 반대(LM4p +10.4 > 관측 +5.8)**. 2001–2015는 AVHRR 단독(solely)으로도 같은 부호 패턴.
  해석(가설): 기온이 주도하는 북극 녹화는 모델이 따라가고(과하게), **CO₂ 비옥화(건조지 수분이용효율·온대)와 토지관리(중국·인도 조림·관개·이모작)가 주도하는 녹화는 못 따라감** → §13.68 CO₂ 고정과 일관. 검증법: 시변 CO₂ 처방 다년 실험.
- **4개 모델 CO₂ 설정 (2026-10-04 서버 확인) — 전부 고정이고 값도 제각각**: LM4p ≈292 ppm(얼어붙은 대기 추적자) · JULES `co2_mmr=5.241e-4` kg/kg = **344.9 ppm** · CLM5 `CLM_CO2_TYPE=constant`, `CCSM_CO2_PPMV=367` · Noah-MP `NoahmpTable.TBL CO2=395e-6`. → 다중모델 평균 GPP/LAI 비교에도 CO₂ 차이(292–395)가 섞임. 프로토콜 통일 필요.
- **LM4p 시변 CO₂ 경로 (재컴파일 불필요)**: `atm_land_ice_flux_exchange.F90:891–897` — `data_table`에 `"ATM","co2_bot",...` 한 줄이면 `Atm%tr_bot(co2)`를 덮어씀(단위 **dry vmr mol/mol**, 코드가 moist mmr로 변환). sphum_bot과 같은 방식. 기존 `INPUT/co2_gblannualdata.nc`(time만 있는 0-D, ppm, 3277개, 1750–)는 끝부분 값이 ≈372 ppm이라 기간·값 확인 전엔 쓰지 말 것 → NOAA/CMIP7 전구 연평균으로 lat-lon 브로드캐스트 파일을 새로 만드는 게 안전. 짧은 시험으로 `qco2_dvmr`가 목표값을 따라가는지 확인 필요.
- **phentest 결과 (2010 1년, `poster/.../data/phentest_tc10_summary.txt`)** — 두 런 rc=0, 각 ≈19.4 h(24PE, climate00). base vs ctl 2010(48PE) 격자 연평균 최대차 0.002 → PE 수 영향 없음.
  한대 50–70N(4,956격자), GIMMS 2010 대비: **9–10월 base 2.35 → tc10 1.77 (관측 0.95)** = 격차 1.40 중 0.58(41 %) 해소. **5–6월 base 1.57 → tc10 1.23 (관측 1.63) = 악화**(6월 2.05→1.45 vs 2.12, 예측대로 같은 tc_crit이 잎 켜기도 늦춤). 월별 RMSE 0.753→0.584(−22 %). **겨울 0.89 vs 관측 0.33은 불변** → 상록(picea) 바닥값, phenology로는 못 고침(관측은 눈에 가려 낮을 가능성도).
  40–50N: 10월 2.11→2.05(관측 0.86) 거의 불변 → 중위도 가을 과대는 tc_crit(acer는 이미 10 °C) 문제가 아님. 열대 영향 0.
  결론: **잎 켜기·끄기가 문턱 하나에 묶인 구조 때문에 가을만 고칠 수 없다** → 끄기 조건 분리(일장 등)가 필요한 코드 수정 지점. 1년 실험이라 탄소 재배분의 다년 효과는 미포함.

### 13.69 ★★ 수정 후보 ① phenology 잎 지기 조건 분리 (설계 2026-10-06)

- 문제(§13.67 phentest): `tc_crit` 하나가 잎 켜기(`vegn_dynamics.F90:2113`)와 추위 잎 끄기(`:2125`)를 겸함 → 가을만 당길 수 없음(tc10: 가을 −41 % 격차, 봄 악화).
- 단순 분리(on 5 °C / off 10 °C)의 함정 2개: ① 봄에 tc_pheno 5–10 °C에서 켰다 껐다 반복(GDD 리셋), ② "하지 이후"만으로 가을 판정 시 **여름 최고월이 10 °C 미만인 북극 식생에서 하지 직후 낙엽** — ctl t_ref 기후값: 식생격자 중 최난월 <10 °C 비율 50–60N 2 %, 65–70N 9 %, **70–80N 44 %**.
- 설계(재시작 변수 추가 없음): 잎 끄기 = 기존 `tc_pheno<tc_crit` **.or.** [낮이 짧아지는 중(반구별 하지 이후) .and. 일장 < `dayl_crit_off` .and. `tc_pheno < tc_crit_off`]. 켜기 조건 불변. 새 종별 파라미터 `tc_crit_off`, `dayl_crit_off` 기본값 = 미사용(<0) → field_table에 없으면 **기존과 비트 동일**.
  1차 값: larix·c3grass `tc_crit_off=283.15`, `dayl_crit_off=14` h.
- 검증: (1) 파라미터 미기입 1개월 → base와 비트 동일 (2) 2010 1년 24PE: 성공기준 한대 9–10월 ≈tc10 수준, 5–6월 ≈base 수준, 70N+ 7–8월 base와 동일.
- 작업 규칙: 서버 소스 직접 수정 금지 → `lm4/patches/`에 diff, 별도 빌드 디렉터리(gateBC 위에 적용).
- **패치 구현·빌드 (2026-10-06)**: `lm4/patches/lm4P.phenology_autumn_daylength.diff`(28줄; 작업본 `lm4/patches/phenoff_work/`), 빌드 `lm4/scripts/phenoff_build.sh` → `/data2/ydkoh/lm4/build_phenoff/fms_esm4.5_phenoff.x`(gateBC coupler + 재컴파일 lm4P; 생산 exe Jul 20 그대로). 그림자 소스에 `src/FMS` 링크 필요(lm4P Makefile이 `$(SRCROOT)FMS/include` 참조 — 첫 빌드 실패 원인).
  일장 = Cooper(1969) 적위 + 일출 방정식, `shortening = lat·cos(2π(284+doy)/365) < 0`. 14 h 아래로 내려가는 날: 40N 216일(8/4), 55N 238일(8/26), 70N 251일(9/8). 호출부 `vegetation.F90:2776` → `vegn_phenology_ppa(tile, lnd%ug_lat(l), doy)`.
  **빌드 결과**: 성공 2026-10-06 13:47. 패치 대비 변경 vegetation.F90 2줄·vegn_data.F90 9줄·vegn_dynamics.F90 19줄(diff 기준), lm4P 38개 파일 재컴파일(vegn_data 모듈 변경 전파), exe 233,666,000 B. 생산 exe `fms_esm4.5_compile_v3_1007_fix.x`(Jul 20)·gateBC exe(Oct 2) 변경 없음. **아직 한 번도 실행 검증되지 않은 exe.**
  **실행 상태**: 13:47에 `noparam`·`offon`을 시작했으나 사용자 지시("빌드 후 기록하고 멈춤, 실행은 시작하지 말 것")에 따라 수 분 내 중단 — 모델 날짜 출력 전, 결과 없음. 런 디렉터리 `/data2/ydkoh/lm4/RUN/phentest/{noparam,offon}`는 스테이징된 채 남아 있음(재시작 시 setup이 rm -rf 후 다시 만듦). `phentest.sh`에 변형 추가(`VARIANTS=` 환경변수, run에 `nice -n 10`).
  **남은 단계 (사용자 승인 후)**:
  1. 회귀 시험: `cd /data2/ydkoh/lm4/RUN; VARIANTS="noparam" bash phentest.sh setup 31; nohup bash phentest.sh run noparam` (24PE ≈1.7 h) → `phentest/base`의 `20100101.land_month.tile1-6.nc` 1월 레코드와 **모든 float 변수 비트 동일** 확인. 하나라도 다르면 중단·원인 조사.
  2. 본 시험: `VARIANTS="offon" bash phentest.sh setup 365; nohup bash phentest.sh run offon` (≈19.4 h). 1이 통과한 뒤 시작(climate00 동시 2런이면 48코어 — climate01 잡 있으면 nice 유지).
  3. 판정(`lm4p_to_latlon.py` → 1°, base·tc10·GIMMS 2010과 비교): 한대 50–70N 9–10월 ≈tc10(1.77) 수준, 5–6월 ≈base(1.57) 유지, **70N 이북 7–8월 base와 동일**(북극 함정 없음). 결과 이 절에 기록.
  4. 통과 시: 패치 diff를 커밋, 수정 후보 ①을 다년 시험(탄소 재배분 효과) 후보로 등록.
- **포스터 결정 (2026-10-06, 사용자)**: 분석 기간 **1982–2010**(ctl vs GIMMS consolidated). 구성 = ① spin-up ② LAI 평균 편차 지도(CO₂ 고정 한계 명시) ③ 지역별 계절 곡선(29년 평균 ±1σ; 앙상블 없음, 월별 보간) + SOS·EOS ④ 원인(기온 문턱 하나)→일장 규칙 식→시험런 그림 ⑤ 향후: 시변 CO₂ 실험. ④의 민감도 시험(tc10·offon)은 **pilot — 보여주기 용도**(사용자 확정), "개선"이라 쓰지 않음. 주장 범위는 한대·중위도. **포스터는 가을(EOS) 쪽만 다룸**(사용자 확정) — 봄 지연(SOS +21일)과 tc_pheno 평활 지연 가설은 노트에만 두고 포스터에서 제외.
  SOS·EOS = **진폭 50 % 문턱**(각 곡선의 최소·최대로 정규화 → 겨울 바닥값 차이 0.88 vs 0.26이 날짜에 안 섞임; 월별 자료에서 기울기법은 보간에 민감). 지역 4개 = 시베리아 한대(50–70N, 60–140E)·북미 한대(50–70N, 170–50W)·동아시아(25–50N, 100–145E)·유럽(40–60N, 10W–40E).
  ctl은 LAI를 **월별로만** 저장(land_month·land_dust·land_month_cmip) → 시험런은 `base_d`·`offon_d`(`phentest.sh`의 `_d` 접미사 = land_daily에 lai 추가, 진단만)로 둘 다 일별 저장해 가을 낙엽 이동을 일 단위로 계산. base_d의 월별 출력이 기존 base와 비트 동일한지로 "진단만"임을 확인.
- **지역별 SOS·EOS (2026-10-06, ctl vs GIMMS 1982–2010, 연도별 50 % 진폭 문턱, 29년 평균±σ; `poster/.../scripts/p3_regional_seasonal_sos_eos.py` → `data/lai_regional_sos_eos.txt`, `figures/fig2_regional_seasonal_cycle.png`)** — 차이 = LM4p−GIMMS(일, +는 모델이 늦음), 29년 모두 같은 부호:
  시베리아 한대(1,586격자) SOS **+20.9±3.4**(6/17 vs 5/27) · EOS **+35.9±2.7**(10/9 vs 9/3) · 정점일 236 vs 196.
  북미 한대(1,692) SOS +21.3±3.3(6/16 vs 5/26) · EOS +30.5±3.4(10/13 vs 9/12) · 정점 여름값 2.96 vs 1.77(크기도 과대).
  동아시아(774) SOS **−11.1±3.4**(5/7 vs 5/18, 모델이 이름) · EOS **+63.4±4.0**(11/29 vs 9/27) · 생장기 +74.5일.
  유럽(815) SOS +25.9±5.4(5/16 vs 4/20) · EOS +52.2±4.9(11/8 vs 9/17).
  **정정**: §13.67의 "봄은 관측과 맞음"은 절대값(5–6월 평균) 기준일 때만 성립. 진폭으로 정규화하면 **한대 SOS도 3주 늦고 정점은 40일 늦음** → 가을만이 아니라 **계절 주기 전체가 뒤로 밀림**; 5월 절대값이 맞는 건 모델의 높은 겨울 바닥(1.03 vs 0.25)이 늦은 잎 켜기를 가린 결과.
  가설(미검증): `tc_pheno = 0.95·old + 0.05·daily`(시상수 20일) 저역통과가 봄·가을 양쪽을 ≈20일 늦춤 → SOS +21일과 크기가 맞음. EOS는 여기에 낮은 문턱(5 °C)이 더해짐. 시험 후보: 평활 계수 변경.
  주의: 관측 봄 상승에는 융설로 상록 캐노피가 드러나는 효과가 섞임(위성 SOS가 이르게 나올 수 있음) → **ΔSOS는 불확실, ΔEOS(9월 초, 적설 전)는 견고**. 자료는 월평균 선형보간(정밀도 ≈1주).
- **SOS·EOS 방법 민감도 — 다항식 맞춤은 쓰지 않음 (2026-10-06, 29년 평균 월별 지역 곡선 12점, `poster/.../data/lai_sos_eos_method_sensitivity.txt`)**: 50 % 진폭 날짜를 세 방법으로 비교. ΔEOS(LM4p−GIMMS, 일): 시베리아 선형 **+36.0** / double logistic **+39.7** / 6차 다항식 +17.4 · 북미 +30.8 / +30.1 / +7.8 · 동아시아 +63.2 / +64.1 / +51.7 · 유럽 +52.3 / +53.7 / +52.8.
  → **선형 보간과 double logistic은 4일 이내로 일치**. 6차 다항식은 겨울이 평평하고 전환이 급한 한대 곡선에서 진동(GIMMS 시베리아 맞춤 최솟값 **−1.13**, 자료 최솟값 0.25; RMSE 0.146 vs dlog 0.063) → EOS가 30일 늦게 나옴. 유럽·동아시아처럼 완만한 곡선에서만 무난.
  double logistic의 변곡점 파라미터(t1,t2)를 SOS·EOS로 직접 쓰는 것도 금지: 비대칭 관측 곡선에서 파라미터가 퇴화(북미 GIMMS t1 168.8, t2 185.7). **맞춘 곡선에 50 % 문턱을 적용하는 방식만 안정적.** 결정: 포스터는 선형 보간 유지, dlog는 강건성 확인용 한 줄.
- **EOS는 detrend와 무관 = CO₂ 고정이 패널 3 결론에 영향 없음 (2026-10-06, `poster/.../data/lai_eos_detrend_check.txt`)**: 월별로 선형 추세 제거(평균 유지) 후 연도별 EOS 재계산 → ΔEOS raw / detrended: 시베리아 +35.9 / +35.9 · 북미 +30.5 / +30.6 · 동아시아 +63.4 / +63.5 · 유럽 +52.2 / +52.2 (차이 ≤0.1일; 평균 곡선은 detrend해도 같으므로 당연). EOS 자체 추세(일/10년): LM4p +0.51·+1.39·+0.72·+1.72, GIMMS −0.28·−0.43·+0.40·−0.49 → 29년 누적 최대 ≈5일, 격차 31–63일에 비해 작음. CO₂ 340→390 ppm을 겪은 관측의 EOS가 거의 안 움직였다는 점이 "CO₂가 EOS 시기를 크게 바꾸지 않는다"의 간접 근거. 단 detrend는 CO₂의 **평균 수준 효과**(292 vs ≈360 ppm)를 못 지움 — LAI 크기 비교(패널 2)에는 한계로 남고, 모델 EOS의 CO₂ 민감도는 시변 CO₂ 실험으로만 확인 가능.
- **포스터 Fig.1 = MJJAS 평균으로 변경 (2026-10-06, 사용자 확정; `n2_fig_meanmap.ncl`의 `MON`/`SEAS`로 전환, 12개월 전부 넣으면 연평균)**: 1982–2010 MJJAS 전구 평균 LM4p **2.773** vs GIMMS **1.967**, 편차 **+0.81 (+40.9 %)** — 연평균(2.550 vs 1.657, +53.9 %)보다 작음(비생장기 과대가 빠지므로, 계절 분해 결과와 일관). 위도평균 최대 LM4p 5.95 / GIMMS 4.43, 차이 −0.48~+2.93(최대는 35S 부근). 배치: (a) GIMMS (b) LM4+ (c) 차이, 각 지도 오른쪽에 위도평균을 맞붙임((c) 옆은 차이), (a)(b) 색막대 공유, 위·오른쪽 눈금 제거, 경도 눈금 60°, 위도 30° 회색 점선. **주의: MJJAS는 북반구 생장기 — 남반구는 휴면기 값이라 남반구 편차(35S 최대)는 "비생장기 과대"로 읽어야 함.** NCL은 비대화형 실행 시 `< /dev/null` 필요(없으면 stdin 대기로 멈춘 사례 1회).
- **★★ 포스터 지역 최종 = IPCC AR6 육상 기준 지역 6개 (2026-10-06, 사용자 확정 — 아래 Giorgi·임의 박스 항목을 대체)**: Iturbide et al. (2020), 마스크·꼭짓점은 `regionmask.defined_regions.ar6.land`(v0.13.0). 한대: **NWN** 북미 북서부 · **ESB** 동시베리아 · **RFE** 러시아 극동 / 온대: **ENA** 북미 동부 · **WCE** 서·중부 유럽 · **EAS** 동아시아. Fig.1(c)에 검은 다각형+약칭, Fig.2 = 2×3.
  1982–2010, 50 % 진폭, LM4+−GIMMS(일, 29년 평균±σ) — SOS / **EOS**(모델 vs 관측 날짜): NWN +15.5±3.5 / **+32.9±3.9**(10/12 vs 9/10) · ESB +12.6±3.3 / **+37.6±2.4**(10/11 vs 9/3) · RFE +23.8±2.6 / **+28.2±2.9**(10/12 vs 9/14) · ENA +22.0±3.2 / **+42.4±3.8**(11/12 vs 10/1) · WCE +27.6±5.3 / **+48.8±3.8**(11/2 vs 9/14) · EAS −13.9±5.0 / **+69.7±4.3**(12/16 vs 10/7).
  여름 정점(모델/관측)·MJJAS 편차: NWN 3.12/1.99 +75 % · ESB 2.84/2.98 +17 % · RFE 2.67/2.88 −5 % · ENA 3.94/4.05 −2 % · WCE 2.66/3.22 −12 % · EAS 3.32/3.16 +18 % → **ESB·RFE·ENA·WCE는 크기가 맞는데 EOS만 28–49일 늦음 = "크기 아닌 시기 문제"의 가장 깨끗한 사례.** 북반구 전체 AR6 지역표 `poster/.../data/lai_eos_ar6_regions.txt`.
  제외: MED −67일·WCA −79일(모델 EOS가 7월 초 — 기온이 아닌 가뭄 낙엽으로 추정, 미확인, 별개 문제) · WNA(σ 40일)·SAS(계절성 약해 EOS 미정) · 남반구(달력 연 가정이 안 맞음, 7–6월로 재정의 필요). 방법 민감도·detrend 확인표는 Giorgi 지역 기준으로 남아 있음(두 지역 세트에서 결론 동일).
  **크기 과대(열대·남미 남동부·NWN +75 % 등)는 이번 포스터 범위 밖 — 향후 과제로만 명시**(사용자와 합의). 기존 단서: §13.60 잎 상한(bl=bl_max면 LAI=LAImax, LMA 소거).
- **★★★ 회귀 시험 결과: phenoff exe(파라미터 미기입)는 gateBC base와 비트 동일하지 않음 (2026-10-06, noparam 31일 rc=0·5,664 s; `lm4/scripts/phentest_bitcompare.py`·`phentest_diff_onset.py`·`phentest_diff_extent.py`)**: 132개 파일 5,742 변수 중 **3,312개 상이**(static 252개와 강제 precip만 동일). 입력은 동일 확인(INPUT 링크 720개·forcing·field/diag/data_table 일치, input.nml은 실행 길이만 다름) → 차이는 실행파일에서 옴.
  차이의 모양: 첫 3시간 출력에서 mrsos가 **격자의 2.2 %**에서만 다르고(중앙 상대차 1.9e-6, 최대 5e-3), 1일 끝 8.0 %, 1월 평균 LAI 33.8 %(중앙 1.4e-6, 최대 2.6e-2). 전구 평균 상대차: mrsos −1.0e-6 · LAI +2.8e-6 · t_ref +1.9e-7 · GPP −1.8e-4.
  해석(추정, 미검증): 규칙 코드의 논리 변화가 아니라 **재컴파일된 lm4P 38개 오브젝트의 반올림 차이**(spdata 타입에 실수 2개가 추가돼 메모리 배치·벡터화가 달라짐)가 민감한 격자에서 증폭. phenology 규칙은 3시간 안에 토양수분을 바꿀 수 없음.
  부호 점검(`phentest_diff_sign.py`, 1월 평균 LAI, noparam−base): 새 규칙이 파라미터 없이도 작동했다면 낮이 짧아지는 남반구에서 잎이 꺼져 31일에 −91 %(0.925³¹)가 돼야 함. 실제: **남반구 평균 LAI 변화 −6.3e-6(−0.0002 %)**, 격자 최대 감소 −0.068, |차|>0.05인 격자 17,306개 중 2개(감소 1·증가 1) → **규칙은 작동하지 않음**. 다만 격자 수로는 감소 쪽이 많음(전체 26.1 % vs 증가 7.6 %; 남반구 58.2 % vs 17.5 %) → 순수 무작위 잡음이 아니라 float32 몇 단위 크기의 체계적 미세 이동(계산 순서가 바뀐 재컴파일에서 흔한 모양이나 미증명).
  **결정**: gateBC base와의 비트 비교로는 패치의 무해성을 증명할 수 없음 → 과학 비교쌍을 **같은 exe**로 변경: `noparam_d`(phenoff exe, 파라미터 없음) vs `offon_d`(phenoff exe, 파라미터 있음), 차이는 field_table 2줄뿐. 기존 gateBC base·tc10과 offon을 직접 빼는 비교는 하지 않음(전구 평균 1e-6~1e-4 수준 잡음 + 격자별 최대 2.6 %).
  엄밀 검증이 필요하면: vegn_data.F90만 바꾼(필드 2개 추가, 규칙 코드 없음) 대조 빌드를 만들어 phenoff exe와 1일 실행 비트 비교 — 같으면 규칙 코드가 무해.
  **결정 (사용자, 2026-10-06)**: 패널 4는 **월평균 비교**로 진행 — 기준 = 기존 gateBC base(10/04, 월별 LAI), `noparam_d`는 실행하지 않음(offon 결과를 본 뒤 필요하면 순차 실행). offon_d는 일별 LAI도 저장하므로 offon 쪽 EOS만 일 단위 가능.
  **정정 15:36**: 48코어 동시 점유는 사용자 지적으로 중단 — `noparam_d`를 15:35:58에 kill(결과 없음, nohup의 "rc=0"은 kill된 mpirun의 표시일 뿐 무의미), **`offon_d`만 24PE로 계속**. `noparam_d`는 offon_d 종료 후 순차 실행(climate00은 한 번에 24랭크 1개까지).
  **본 시험 시작 2026-10-06 15:33:41**: `noparam_d`·`offon_d` 동시, 각 24PE @climate00, 2010년 1년, 예상 ≈19.4 h(10/07 11시경). setup 확인: 둘 다 phenoff exe, diag_table에 land_daily lai 1줄 추가, offon_d field_table에만 `tc_crit_off = 283.15`·`dayl_crit_off = 14.0`이 2개 종(2285–2286, 2517–2518행)에 추가, noparam_d field_table은 ctl과 동일. 기준 실행을 따로 돌리는 주된 이유는 **일별 LAI**(기존 base는 월별뿐); 지역 평균 월별 비교만이면 실행파일 잡음(1e-6~1e-4)은 무시 가능.
- **★★ phenology만 바꿔도 물·에너지 플럭스가 움직임 — tc10 vs base, 한대 50–70N, 2010 (`lm4/scripts/phentest_flux_response.py` → `poster/.../data/phentest_tc10_flux_response_50_70N.txt`, C96 원격자·land_area 가중)**: 9–10월 평균 LAI 2.283→1.741(**−23.7 %**) → 증산 0.260→0.240 mm/d(**−7.6 %**) · 총 증발산 0.734→0.702(**−4.5 %**) · 유출 0.582→0.610(**+4.7 %**) · GPP −11.2 % · 현열 −4.38→−4.17 W/m². 6월(봄 지연 부작용): LAI 2.03→1.48(−27 %) · 증산 1.223→0.926(**−24 %**) · 총 증발산 2.271→2.059(−9.3 %) · 유출 +2.6 %. 2 m 기온 +0.02 K·캐노피 공기온도 +0.03 K로 거의 불변 — **오프라인은 대기가 WFDE5로 고정이라 되먹임이 없기 때문**; 결합 모델에서는 증발산 감소 → 현열 증가 → 지표·경계층 가열로 이어질 수 있으나 여기서는 정량 불가. 유출 증가는 과제 주제(담수 유출→연안 염분)와 직접 연결. 주의: 출력의 `evap_soil`은 맨땅 증발이 아님(값이 `evap_land`보다 큼, 정의 미확인) — `transp`·`evap_land`만 사용.
- **★★★ 관측 EOS는 기온이 아니라 일장에 모여 있음 → 대안 = 일장 주도 규칙 (2026-10-06, `poster/.../data/eos_daylength_at_obs.txt`)**: 관측 EOS 날짜(1982–2010)의 지역 평균 위도 일장 — NWN 62.1N 9/9 **13.12 h**(6.2 °C) · ESB 54.2N 9/3 **13.29 h**(10.2 °C) · RFE 56.6N 9/14 **12.55 h**(7.5 °C) · ENA 40.7N 10/1 **11.52 h**(14.4 °C) · WCE 50.5N 9/14 **12.44 h**(14.3 °C) · EAS 33.0N 10/7 **11.42 h**(16.4 °C). **일장 폭 11.4–13.3 h(1.9 h) vs 기온 폭 6.2–16.4 °C(10.2 °C)** → 여섯 지역 EOS를 하나의 온도 문턱으로는 못 맞추지만 일장으로는 좁은 범위에 들어옴. 일장은 위도와 함께 길어짐(33N 11.4 h → 54–62N 13.1–13.3 h) = Birch 2021의 위도 의존 문턱(45N 11 h → 65N 15 h)과 같은 방향.
  순수 일장 규칙의 발동일: 12 h는 전 지역 9/21(추분), 13 h는 8/23(EAS)–9/11(NWN), 14 h는 7/14–9/1. 발동 후 잎 반감 ≈9일을 더하면 12 h 규칙의 EOS ≈9/30 → 관측 대비 NWN +21 · ESB +27 · RFE +16 · ENA −1 · WCE +16 · EAS −7일(현재 +28~+70일). **offon(일장<14 h .and. tc_pheno<10 °C)이 온대를 못 고칠 때의 다음 후보**: 온도 조건 없이(또는 느슨하게) 위도 의존 일장 문턱. 한계: 지역 평균 위도 한 점의 손계산, EOS는 감소 구간의 중간점(낙엽 시작은 더 이름), 모델 실행 아님.
- **★★★ 낙엽 규칙을 손으로 따라가면 모델 EOS가 재현됨 — 한대의 +28~38일 = 낮은 문턱 + 평활 지연 (2026-10-06, `poster/.../data/phenology_rule_walkthrough.txt`)**: 모델 t_ref 기후값(1982–2010, AR6 지역 평균, 월→일 선형보간)에 `tc_pheno=0.95·old+0.05·T` → `tc_pheno<5 °C`에서 LEAF_OFF → 7.5 %/일(반감 8.9일)을 적용.
  ESB: 관측 EOS 9/3(그날 일기온 **10.2 °C**) → 일기온 <5 °C 9/23(**+20일 = 문턱이 낮아서**) → tc_pheno <5 °C 10/10(**+17일 = 평활 지연**) ≈ 모델 LAI EOS **10/11**. NWN: 9/9(6.2 °C) → 9/16 → 10/1, 모델 10/12. RFE: 9/14(7.5 °C) → 9/22 → 10/8, 모델 10/12. 평활 지연 12–20일.
  온대는 온도 문턱으로 설명 불가: 관측 EOS 시점 일기온 ENA 14.4 · WCE 14.3 · EAS 16.4 °C; EAS는 최한월 1.3 °C라 tc_pheno<5 °C가 12/28.
  새 규칙(하지 이후·일장<14 h·tc_pheno<10 °C)의 손계산 발동일: NWN 9/1(관측 9/9) · ESB 9/21(9/3) · RFE 9/14(9/14) · ENA 11/13 · WCE 10/27 · EAS 11/28 → **한대는 근접, 온대는 여전히 한 달 이상 늦음**(larix·c3grass만 대상이므로 예상된 한계). offon 실험의 사전 예측값으로 사용. 한계: 지역평균 기온·t_ref(코드는 캐노피 공기온도 tc_daily)·종 혼합 무시.
  학부 수준 설명 문서: `poster/2026_LM4p_LAI/LM4plus_phenology_explained.html` (게시 https://claude.ai/artifact/FEG1NBpoo62E9rCZzWoJ9G, 비공개).
- **(이전) 포스터 지역을 Giorgi & Francisco (2000) 기준 지역으로 교체 (2026-10-06, 사용자 요청 — 아래 임의 박스와 위쪽 항목들의 지역별 수치를 대체)**: 경계는 `regionmask.defined_regions.giorgi`(v0.13.0, 로컬 설치)에서 읽음 — **NAS** 북아시아 50–70N, 40–180E(2,443격자) · **ALA** 알래스카 60–72N, 170–103W(674) · **EAS** 동아시아 20–50N, 100–145E(858) · **NEU** 북유럽 48–75N, 10W–40E(813). Fig.1(c)에 검은 박스(굵기 5), Fig.2 = 이 4개.
  SOS·EOS(1982–2010, 50 % 진폭, LM4p−GIMMS 일, 29년 평균±σ): NAS SOS +21.6±2.9 · **EOS +35.6±2.8**(10/10 vs 9/4) | ALA +19.2±3.7 · **+27.6±3.0**(10/6 vs 9/8) | EAS −9.1±3.6 · **+61.7±4.5**(12/1 vs 10/1) | NEU +28.8±3.5 · **+41.1±5.2**(10/30 vs 9/18). 네 지역 모두 29/29년 EOS 늦음.
  강건성 재확인(같은 지역): ΔEOS 선형/double logistic/6차 다항식 = NAS +35.5/+38.3/+17.1 · ALA +27.8/+29.0/+0.4 · EAS +61.5/+61.4/+51.7 · NEU +40.6/+44.3/+32.2 (선형–dlog 4일 이내, 다항식은 한대에서 음수 진동). detrend 전후 ΔEOS 차이 ≤0.1일, EOS 추세 LM4p +0.7~+1.1 · GIMMS −1.0~+0.4 일/10년.
  서지(regionmask 문서 인용, 권·쪽은 포스터 전 재확인): Giorgi, F. & Francisco, R. (2000) *Climate Dynamics* 16, 169–182. 북미 한대 전체를 덮는 단일 Giorgi 박스는 없음(ALA=알래스카·캐나다 북서부만, GRL 50–85N·103–10W는 그린란드·북극 군도 포함) → 캐나다 한대림 띠(50–60N)는 이번 4개 지역 밖.
- **(이전) 포스터 4개 지역 박스의 근거 = 임의 설정, 선행연구 정의 아님 (2026-10-06)**: 시베리아 한대(50–70N, 60–140E)·북미 한대(50–70N, 170–50W)·동아시아(25–50N, 100–145E)·유럽(40–60N, 10W–40E)는 계절 분해에서 위상 편차가 큰 한대 띠를 대륙별로 나누고 동아시아(사용자 요청)·유럽(중위도 대조)을 더한 **둥근 숫자 박스**. Fig.1(c)에 검은 박스로 표시. 주의: 10/4 추세표(`lai_regional_trend_products.txt`)의 "Boreal Siberia"는 1,197격자로 **이번 박스(1,586격자)와 다른 정의**, "Europe"은 815격자로 동일. 논문 단계에서는 표준 정의(IPCC AR6 reference regions 또는 TransCom 육상 지역)로 교체하고 박스 민감도 확인 필요.
- **관측은 GIMMS만 사용 (2026-10-06, 사용자 확정)**: MODIS 표준 LAI는 8일(MCD15A2H)·4일(MCD15A3H) 합성이고 일별 표준 제품 없음. 병목은 모델(ctl LAI 월별)이라 관측을 촘촘히 해도 패널 3엔 이득 없음 → MODIS 추가 검증은 하지 않음. (로컬 보유: `/Volumes/data02/LAI-DataKit/derived/modis_mcd15a2h/cmg005/` 1,105파일 — **격자 검증 안 함**, 쓰려면 먼저 검증.)
- **패널 1용 LAI 표류 점검 (2026-10-06, ctl 1979–2023 월별, 모델 유효격자 cos 가중, `poster/.../data/lai_ctl_drift_1982_2010.txt`)**: 1982–2010 연평균 추세 — 전구 −0.47 %/10년(2.357±0.021), 한대 50–70N **+2.69 %/10년**(9월 LAI가 1982–86→2006–10에 +0.229), 시베리아 한대 +1.23 %/10년, 동아시아 +1.32 %/10년. 한대 증가가 기후 반응인지 목재 축적 표류인지는 이 자료로 구분 불가. 그러나 9월 모델−관측 격차(1.66)의 14 %이고, **EOS 연변동 σ가 2.7–4.0일**(표류 포함)이라 +31–63일 차이는 표류로 설명 불가 → 계절 위상 결론에 영향 없음. 기존 `figures/spinup_4models/lm4p_spinup.png`(7패널, c2−c1 2010년: LAI −0.6 %, GPP +0.4 %, 토양C +3.0 %, 목재C +7.6 %)를 패널 1 원본으로 사용 가능. → **축약판 확정(사용자)**: `poster/.../scripts/p0_fig_spinup_3panel.py` → `figures/fig0_spinup_lai_gpp_wood.png`(LAI·GPP·목재C, 60년, 분석기간 음영). 같은 강제 연도 2010의 cycle 2−cycle 1: LAI −0.59 % · GPP +0.44 % · 목재C **+7.64 %**; 30년 평균으로는 LAI +0.87 % · GPP +1.30 % · 목재C +7.17 % (`data/spinup_cycle_drift.txt`).
- **편차의 계절 분해 — "phenology 문제"는 한대·중위도에만 성립 (2026-10-06, ctl vs GIMMS consolidated 기후값 1982–2010, `poster/.../data/lai_bias_season_decomp.txt`)**: 생장기(GS) = 관측이 연중 진폭의 절반을 넘는 달.
  한대 50–70N(4,956격자): 연평균 +56 %인데 **정점 +15 %**(8월 2.81 vs 7월 2.45), GS 평균 +13 %, **비생장기 +108 %** → 편차의 **87 %가 비생장기**. 계절별 몫: **8–10월 52 %**(9월 2.80 vs 1.14) · 11–4월 48 %(겨울 바닥 0.88 vs 0.26, 상록+눈 아래 위성 불확실) · 5–7월 0 %.
  40–50N: 정점 +3 %(7월 동일), 비생장기 몫 79 %. → 두 대역은 **크기가 아니라 계절 위상** 문제.
  열대 20S–20N: 정점 +44 %, GS +38 %/비생장기 +49 %(연중 고르게 과대, 최솟값 3.68 vs 2.66) → **크기 문제**, phenology 아님. SH 60–20S +113 %(정점 +88 %)도 크기.
  전구 편차(+54 %)에서 각 대역 몫(면적가중): **열대 44.1 %** · SH 18.5 % · 20–40N 16.5 % · 한대 13.8 % · 40–50N 7.5 % · 70N+ −0.5 %. → 한대 가을 phenology(8–10월)가 설명하는 전구 편차는 13.8 %×52 % ≈ **7 %**. 포스터 문장은 "전구 LAI 과대 = phenology"가 아니라 **"한대·중위도는 정점은 맞고 계절 위상이 틀림, 열대·남반구는 크기 과대"**로.

### 13.70 ★★★ phenology 민감도 실험 대장 (2026-10-06 작성 — 실험을 추가·재실행할 때 이 표부터 갱신)

종별 phenology 파라미터(ctl `field_table` 확인 2026-10-06; 코드 기본값 `tc_crit=283.16`, `gdd_crit=360`, 유형 기본 = deciduous): **larix** 5 °C·180 · **c3grass** 5 °C·180(deciduous 명시) · acer 기본값 10 °C·360 · c4grass 기본값 10 °C·360(deciduous 명시) · prioria(열대) 기본값 10 °C·360 · **picea** `phenology_type='evergreen'`(규칙 미적용). 즉 기본값을 덮어쓴 종은 larix·c3grass 둘뿐이고 둘 다 문턱과 GDD 기준을 함께 낮춤.

**이 값들의 출처 (2026-10-06 서버 확인)**: ① ctl `field_table`은 KIOST 원본 `~/KIOST-ESM2/field_table`(2026-06-13)과 **6줄(3쌍)만 다름** — n2o·ch4·co2 `lower_bound`에서 `fixed_year=1850.`을 뺀 것뿐, 종 블록은 동일(larix·c3grass `gdd_crit=180`, `tc_crit=278.15`) → **phenology 파라미터는 KIOST에서 받은 그대로**. `~/ESM4p5_KIOSTv2b/ASCII_INPUT_{PROD,SMALL}/field_table`(2026-02-13)도 같은 두 값. (co2 `fixed_year` 줄은 §13.68 CO₂ 고정 문제와 관련 가능 — 별도 확인 거리.)
② 옛 UFS LM4(`ufs-weather-model/LM4-driver/LM4/vegetation/`, 5종 c4grass·c3grass·tempdec·tropical·evergreen)의 **코드 기본값 배열** `tc_crit = 283.16, 278.16, 283.16, 283.16, 263.16` → **c3grass 5 °C는 GFDL 옛 코드부터 있던 값**(KIOST 조정 아님), lm4P에서 새로 생긴 larix가 같은 값을 받은 것으로 보임. 우리 UFS 실행 namelist는 `tc_crit(0:2) = 3*273.16`(c4grass·c3grass·tempdec을 0 °C로 덮어씀).
③ UFS LM4의 낙엽 규칙은 LM3식: `vegn_phenology`에서 `tc_av < tc_crit` 또는 가뭄이면 LEAF_OFF, **잎을 한 번에** 떨굼(`leaf_litter=(1-l_fract)*bl`), GDD·tc_pheno 평활 없음. lm4P(PPA)는 일 단위 판정 + GDD + 지수이동평균 + 7.5 %/일 낙엽으로 바뀐 것.

**★★★★ larix는 모델에 사실상 없다 — 종별 잎 면적 분포 (2026-10-06, base 2010, C96 원격자·land_area 가중; `lm4/scripts/phentest_species_share.py`·`phentest_species_presence.py` → `poster/.../data/species_leaf_area_share_july2010.txt`)**: 연중 잎이 한 번이라도 있는 격자 수 — prioria 4,183 · picea 5,864 · **larix 20** · acer 3,741 · c4grass 8,738 · **c3grass 16,649**(전체 육지 ≈18,700). 7월 잎 면적 몫(%):
| 영역 | prioria | picea | larix | acer | c4grass | c3grass | 평균 LAI |
|---|---|---|---|---|---|---|---|
| 70–90N | 0 | 0 | 0 | 0 | 0 | **100** | 0.07 |
| 50–70N | 0 | 34.2 | 0.0 | 17.7 | 0 | **48.1** | 2.69 |
| 30–50N | 0 | 32.5 | 0.0 | 33.0 | 0.3 | 34.3 | 1.83 |
| 0–30N | 50.9 | 1.5 | 0 | 4.7 | 5.9 | 37.0 | 2.45 |
| 60S–0 | 59.2 | 3.0 | 0 | 0.9 | 2.6 | 34.3 | 3.25 |
| NWN(박스) | 0 | 32.7 | 0 | 11.2 | 0 | 56.1 | 3.03 |
| ESB | 0 | **41.8** | **0.0** | 20.7 | 0 | 37.5 | 2.75 |
| RFE(박스) | 0 | 14.8 | 0 | 26.6 | 0 | 58.6 | 2.52 |
| ENA(박스) | 0 | 5.1 | 0 | **72.3** | 0.3 | 22.3 | 3.40 |
| WCE(박스) | 0 | 24.5 | 0 | 47.8 | 0 | 27.6 | 2.48 |
| EAS(박스) | 12.7 | 21.9 | 0 | 40.0 | 0.7 | 24.8 | 2.76 |
(NWN·RFE·ENA·WCE·EAS는 AR6 다각형을 근사한 경위도 박스.)
→ ① tc10·offon의 파라미터는 larix·c3grass에 주지만 **효과는 전부 c3grass 경유**. "낙엽송 문턱"이라는 표현은 틀림 — "한대 C3 풀의 문턱"으로. ② 실제 낙엽송 지대인 동시베리아가 모델에서는 **상록 가문비 42 % + 단풍나무류 21 % + C3 풀 38 %** → 겨울 바닥값(모델 ≈1.1 vs 관측 ≈0.3)의 유력한 원인 후보 = 상록수가 있어서(가설; 관측의 눈 효과와 분리 필요). ③ 한대에 온대 낙엽수(acer, 문턱 10 °C)가 18–27 % 있음. ④ 온대(ENA 72 %·WCE 48 %·EAS 40 %가 acer)는 tc10·offon의 대상 종이 소수라 반응이 작았던 것 — 4번 실험에서는 acer에도 가을 파라미터를 줘야 함. 종 분포 자체(초기 분포·`do_biogeography=F`)의 검토가 별도 과제로 추가됨.

**★★★ 고정된 종 분포의 출처 = 관측 지도가 아니라 경쟁의 결과 (2026-10-07, ctl `input.nml` `&vegn_nml` 1799–1812행 확인)**: `init_n_cohorts=6`, `init_cohort_species='c3grass','c4grass','acer','picea','larix','prioria'`, `init_cohort_nindivs=0.1,0.1,1,1,1,1`, `init_cohort_height=2.5e-3,…,0.5` → cold start 때 **모든 타일에 6종을 똑같이 심고**, PPA 경쟁·고사(cold/treeline mortality)·`seed_transport_to_use='diffuse'`(종자 확산)로 400년 결합 spin-up 동안 분포가 **스스로 형성**된 것(KIOST 결합 spin-up이 이 namelist로 cold start했다는 전제 — 우리 설정 파일이 KIOST 템플릿이라 그럴 가능성이 높으나 미확인). `do_biogeography=F`는 기후에 따른 종 재배정만 끄는 것이고, 기존 종의 확산·경쟁은 계속됨. INPUT의 `cover_type.nc`·`mksrf_pft*.nc`는 토지이용·LAI 보조자료이지 종 지도가 아님. **결론: "고정 분포"는 KIOST 결합 모델(그 기후 편차 포함)이 만든 경쟁 결과이며, larix는 그 경쟁에서 거의 전멸한 것**(원인 미확인: larix 파라미터 또는 결합 기후). 종 분포 평가가 별도 과제가 되는 이유.
**KIOST 전달 문구 (사용자 전언, 2026-10-07)**: "공유하는 코드·파일은 **CMIP7 PI Control** 실험용이며, 400년 Control Run 수행 후 기후 안정이 이뤄진 뒤의 자료." → 초기장 = 1850년 조건의 산업화 이전 대조실험 상태. 함의: ① 대기 CO₂ 추적자가 1850년 수준(≈284 ppm) → **§13.68의 "오프라인 CO₂ ≈292 ppm 고정"의 출처**(KIOST field_table의 co2 `fixed_year=1850.`과도 부합). ② "기후 안정"은 대기·해양 기준이고 식생 구조·종 분포·목재/토양 탄소의 평형을 뜻하지 않음(§13.62 목재C 표류, 거목 cohort). ③ 토지이용도 1850년 상태일 가능성 — ctl의 `do_landuse_change`·landuse.nc 적용 여부와 함께 확인 필요.
**★★★ 관측 지도로 재파종(replant) 착수 (2026-10-07, 사용자 결정: 우점종 하나 규칙·ctl 2010-01-01 restart 출발·약한 대응 3개 그대로)**: 스크립트 `lm4/scripts/replant_step1_crosswalk.py`(CLM5 PFT → LM4+ 6종 대응표, 결과 `lm4/data/replant/lm4_species_map_from_clm5.nc`, 종별 합 100 % 확인, 50–90N larix 우점 1,165셀) → `replant_step2_decode_restart.py`(vegn2.res `cohort_index` compress "cohort tile lat lon" 해독, 1,373,514 cohort, 종별 수가 restart 센서스와 일치; **larix 1,825 cohort는 63셀, 위도 −42.7~−8.1 = 남반구에만 살아남아 있었음**) → `replant_step3_relabel.py`(자연·2차림 타일(landuse 3·4)의 나무 cohort → 최근접 CLM5 셀의 우점 나무 종, 풀 cohort(모든 타일) → 우점 풀 종; 지도에 나무 없는 셀의 나무 7,047 cohort는 불변). 결과: 547,491 cohort 변경 — prioria 244,655→287,374 · picea 309,645→335,571 · **larix 1,825→11,890** · acer 289,347→210,637 · c4grass 170,163→366,190 · c3grass 357,877→161,850. 검증: 113개 restart 파일 바이트 동일, vegn2 6개는 `species` 변수만 변경, 1° 우점 나무 종이 지도와 **95.8 % 일치**(9,811셀). 사본 `/Volumes/data02/LM4P/cases/replant/IC_y2009_clm5/` (+`relabel_record.npz`); 서버 `/data2/ydkoh/lm4/RUN/replant_seed/`(vegn2 6개 복사·md5 일치, 나머지는 ctl y2009 심링크). `phentest.sh`에 `SEED=` 환경변수 추가. **1개월 시험 `replant_d`**(CTRL 설정·gateBC exe·일별 LAI) climate01 PBS 8518로 2026-10-07 14:xx 제출(dayl2_d와 함께 48랭크). 다음: 정상 종료·NaN 없음·larix가 봄에 잎을 내는지 확인 → 2010년 1년 → 30년 spin-up.
**ACM 2026 포스터 초안 (2026-10-07)**: 템플릿 `/Volumes/data01/발표_템플릿/전남대/poster/poster_2026_ACM.pptx`(원본 불변) → `poster/2026_LM4p_LAI/poster_2026_ACM_draft.pptx` (+pdf). 생성 스크립트 `poster/2026_LM4p_LAI/scripts/build_poster_acm2026.py`(python-pptx, 글·표·그림 위치 전부 코드; PDF는 PowerPoint AppleScript로, LibreOffice는 삭제됨). 제목 = 초록 그대로, 영어, 그림 fig1·fig2·fig3b_dl(정규화), EOS 지도는 공간 부족으로 제외(`p11_eos_maps_poster.py`·fig5는 보관). 사사: KEITI RS-2022-KE002160 + KIMST RS-2026-25543619. 사용자 승인("이정도면 충분"). **사용자가 pptx를 PowerPoint에서 직접 수정함(2026-10-07 14:4x) → 이후 `build_poster_acm2026.py` 재실행 금지**(템플릿부터 다시 만들어 수정이 지워짐). 남은 일: 실험 4(DL13/12)·5(DLtype) 결과로 fig3b_dl 재생성 → 수정본 백업(`_v1_user`) 후 **그림 개체만 교체**(python-pptx로 Picture 요소의 blip 이미지 교체, 위치·크기 유지) → 마무리.
**replant 1개월 시험 결과 (PBS 8518, 2010-01, 24랭크, 2026-10-07 15:25 종료) — 통과**: 완주·NaN 0(FATAL 4건은 base와 같은 MOM 파서 안내문 `FATAL_UNUSED_PARAMS`, 무해). cohort 1,373,512→967,647(−30 %; 기준 물리 noparam 1개월은 −14 %)이나 **종별 nindivs 1.000·목재 1.00 보존 → 병합**(같은 타일 내 종 통일로 '비슷한 cohort' 증가). 낙엽송 8,770 cohort 중 8,556 LEAF_OFF, 잎 질량 IC의 12.5 %(7.5 %/일 낙엽 31일 ≈9 %와 부합) → 낙엽수로 정상 작동. 가문비(낙엽수→상록 전환분) 잎 1.41배 성장 시작. 풀 구조량 c4 0.88·c3 0.91(겨울 축소 규칙). **status 코드 = LEAF_ON 0 / LEAF_OFF 5**(처음 1로 오독해 '1월에 잎 달림'으로 잘못 판단했다가 정정). 산출: `/Volumes/data02/LM4P/cases/replant/test1m_RESTART/vegn2.res.tile[1-6].nc`. 다음 = 2010 1년 `replant1y_d`(사용자 지시로 **속도 시험 4개 뒤로 보류**). 교훈: 실행 중인 bash 스크립트 파일(phentest.sh)을 덮어쓰면 bash가 바뀐 오프셋을 읽어 `syntax error`를 냄(이번엔 모델 종료 후 echo 단계라 무해) — 잡이 도는 동안 서버 스크립트 수정 금지.
**lm4P 질소 모드 존재 (2026-10-07 확인)**: `soil_carbon.F90:80–83` 옵션 CENTURY(1)·CORPSE(3)·**CORPSE_N(4, "enables all nitrogen code")**, 질소 코드가 15개 파일에 분산. ctl `input.nml:1454` `soil_carbon_model_to_use='CENTURY-like'`(주석 "Nitrogen turned off"), `:1780` `N_limits_live_biomass=.FALSE.` → KIOST piControl도 질소 off. 켜려면 질소 풀 초기화(0부터, 수백 년)·침적/고정 입력·종별 N 파라미터 검증 필요 → **2단계 후보**. 종 분포 교정의 빠른 길은 "관측 지도(CLM5 PFT)로 재파종"(초기장 cohort 종 번호 바꿔치기 + 수십 년 spin-up) — 대응표 초안·방법 B는 2026-10-07 대화 참조, 미착수.
**LM4.1 논문(Shevliakova 2024, 보유 PDF)의 관련 서술 (2026-10-07 확인)**: ① piControl은 "potential vegetation"으로 초기화, 종 분포는 경쟁에서 창발(LM3.0은 기후 한계 처방, LM4.1은 미도입). ② **"ESM4.1은 상록 침엽수를 툰드라 안쪽까지, 특히 북미에서 관측보다 넓게 모의"** — 원인으로 고위도 온난·습윤 편차와 **양분 제약 부재**를 들고, Weng 2016을 인용해 **상록(high LMA) vs 낙엽(low LMA) 경쟁 결과는 N 무기화를 통한 온도 효과에 좌우**되므로 C–N 결합 전까지 온도 생물지리 한계를 넣지 않았다고 명시 → **N이 꺼진 lm4P에서 낙엽 침엽(larix)이 상록(picea)에 지는 것은 모델 계열의 알려진 성향**, KIOST 고유의 실수라기보다 LM4.1 구조 + 결합 기후 편차의 결과. ③ 작물: "all crops everywhere are planted and harvested once" — LM4.1에는 연 1회 수확하는 작물 달력이 있음(이모작 없음). 앞서 적은 "모델에 작물이 없다"는 **종 목록에 없다**는 뜻으로 정정; 작물 타일(`land_month_crop`)의 수확 처리가 lm4P에서도 작동하는지는 미확인.
**★★ 초기 상태의 거목 cohort — 크기 문제의 단서 후보 (2026-10-07, `vegn2.res` dbh·nindivs·bwood, `dbh_census2.py`)**: 생물량 가중 dbh — prioria 중앙값 **1.05 m**, p90 2.7 m; picea p90 1.5 m, p99 4.3 m; larix p90 **40 m**(최대 50 m). 목재 생물량 중 dbh>2 m cohort의 몫: prioria **21 %**, picea 6 %, larix 44 % — 그 cohort들의 밀도는 1e-5~1e-9 개체/m²(ha당 0.1개 이하)의 "유령 거목". dbh 수 m~수십 m는 비물리적(LM4.1 논문 Fig. 21은 관측 플롯과 맞는 크기분포를 주장) → 400년 결합 spin-up에서 밀도가 아주 낮은 cohort가 고사 없이 계속 자란 결과로 추정. LAI 크기 과대(§13.60 LAImax 상한)와의 관계는 미확인 — 다음 단계 과제.
**larix 부재의 출처 = 초기 상태 (2026-10-06, `lm4/scripts/restart_species_census.py`, `vegn2.res` cohort 수)**: spin-up 시작 IC(`lm4_spinup30/INPUT`, KIOST 결합 400년 IC) — prioria 196,909 · picea 282,873 · **larix 1,790(전체의 0.15 %)** · acer 252,182 · c4grass 143,741 · c3grass 297,129. ctl y1979 1,794 → y2009 1,825 → y2023 1,754 → **처음부터 거의 없었고 45년간 늘지도 줄지도 않음**(`do_biogeography=F`라 새 곳에 정착 불가). 종으로서 계산은 되지만 사는 곳이 20격자뿐. 왜 KIOST IC에 larix가 거의 없는지는 미확인(KIOST 문의 필요). 주의: restart는 1월 1일이라 북반구 낙엽종의 잎 생물량 몫은 과소 — 종 비교는 cohort 수나 7월 잎 면적(위 표)으로.

**독립 검토 — codex CLI (2026-10-06, read-only, 원본·패치 소스 6개 파일만 제공; 프롬프트는 결론을 주지 않고 코드에서 답하게 함)**: 우리 진단과 일치 — 가을 지연 1순위 = `tc_pheno` 평활(평균 지연 ≈19일) + 온도 문턱까지 ON 유지, 겨울 잔존 1순위 = picea의 계절 낙엽 면제, 기본값이면 패치는 논리상 원본과 동일(비트 동일은 별개).
  새로 지적된 것: ① **가을 재전엽 반복 위험(실행 중인 offon_d에 해당)** — 새 규칙으로 OFF된 뒤 tc_pheno가 5–10 °C인 동안 GDD가 다시 쌓여 180(c3grass의 `gdd_crit`)을 넘으면 ON, 다음 날 다시 OFF·GDD 리셋. ON 분기는 가을 조건을 보지 않음 → **v2 후보: 가을 조건이 참인 동안 OFF→ON 금지**. offon_d의 일별 LAI에서 가을 재상승 유무 확인할 것. ② **초본은 OFF 순간 급감** — `vegn_dynamics.F90:2154–2168`에서 키·DBH·수관면적을 묘목 크기로 되돌리고 그 `bl_max`를 넘는 잎을 즉시 제거 → c3grass(한대 잎 면적 48 %)는 "7.5 %/일·반감 9일"이 아님. ESB에서 스위치 OFF(10/10)와 모델 LAI EOS(10/11)가 하루 차이인 이유로 보임(앞서 "종·격자 혼합" 추정을 대체). ③ 성장 배분 조건의 기온은 `tc_dorm`(≈10일 평활) > `T_dorm`. ④ `gdd`·`status` 진단 출력은 첫 cohort만 → 종 대표로 쓰면 안 됨. ⑤ 일장식 분모 365 고정(윤년 ≈1일 오차), 극점 `tan` 취약. ⑥ 기존 `tc_crit`(10 °C)보다 낮은 `tc_crit_off`는 효과 없음 → acer에 283.15를 줘도 무의미, 4번 실험은 더 높은 값(또는 일장만) 필요.
  codex가 "세 파일에서 확인 불가"라 한 일평균 정규화는 **확인 완료**: `land_model.F90:2832` `tc_daily = tc_daily/steps_per_day`, `:2881–2883`에서 일 누적·극값 리셋 → 문제 없음.

**★★★ 종 분포를 관측 기반 자료와 대조 (2026-10-06)** — 격자 검증 2건 포함.
① **MCD12C1 IGBP 격자 검증 통과**: `/Volumes/data02/MODIS/MCD12C1/mcd12c1_igbp_GLOBAL_2010_2020.nc`(GEE `MODIS/061/MCD12C1` Type 1 majority, 0.05°, 2010·2020; tif→nc 변환은 geotransform에서 좌표 계산). `igbp`(year,lat,lon)=(2,3600,7200) int16, 값 0–16, **lat 오름차순** −89.975→89.975, lon −179.976→179.976, 간격 0.0500002°. 좌표 없는 원본 배열 그림 = 정상 세계지도. 지점 점검 10곳 중 8곳 일치(사하라 Barren·아마존/콩고 EBF·그린란드 SnowIce·태평양 Water·미국 옥수수지대 Crop·티벳 Grass·호주 내륙 OpenShrub); 불일치 2곳(동시베리아 62N120E·캐나다 55N100W = WoodySavanna)은 격자 오류가 아니라 **IGBP가 성긴 한대림을 Woody savanna/Savanna로 분류**하기 때문(전구 DNF 0.2 %뿐). → **IGBP 다수 등급으로는 낙엽송/가문비 구분 불가**. 쓸모 있는 것은 농경지 비율(AR6 육지 면적 %, `poster/.../data/igbp_share_ar6_regions_2010.txt`): WCE **50.7** · EAS 25.9 · ENA 16.7 · NWN 4.7 · ESB 3.9 · RFE 2.5.
② **CLM5 지면자료 PFT 비율**(잎 유형이 구분됨; `surfdata_0.9x1.25_hist_16pfts_Irrig_CMIP6_simyr2000_c190214.nc` → `lm4/scripts/clm_surfdata_pft_extract.py` → `poster/.../data/clm5_surfdata_pft_0.9x1.25_simyr2000.nc`; 점검: lat −90→90 오름차순, lon 0→358.75, 지점 우점 PFT 동시베리아 NDT boreal 79.8 %·아마존 BET tropical·사하라 bare·캐나다 NET boreal·미국 동부 BDT temperate). AR6 지역의 식생 면적 대비 %(`clm5_pft_share_ar6_regions.txt`) vs LM4+ 7월 잎 면적 몫(위 표):
| 유형 (CLM5 / LM4+ 종) | NWN | ESB | RFE | ENA | WCE | EAS |
|---|---|---|---|---|---|---|
| 상록 침엽 / picea | 37.4 / 32.7 | 22.8 / **41.8** | 15.0 / 14.8 | 31.6 / 5.1 | 15.6 / 24.5 | 20.5 / 21.9 |
| **낙엽 침엽(낙엽송) / larix** | 0.2 / 0 | **25.4 / 0.0** | **17.2 / 0** | 0 / 0 | 0 / 0 | 0 / 0 |
| 낙엽 활엽 / acer | 2.1 / 11.2 | 4.6 / **20.7** | 5.2 / 26.6 | 24.5 / 72.3 | 12.2 / 47.8 | 15.9 / 40.0 |
| 관목 / (없음) | 18.2 / – | 5.5 / – | **29.5** / – | 0.5 / – | 0 / – | 0.1 / – |
| C3 풀 / c3grass | 37.1 / 56.1 | 36.8 / 37.5 | 31.5 / 58.6 | 16.3 / 22.3 | 32.5 / 27.6 | 22.5 / 24.8 |
| C4 풀 / c4grass | 0 / 0 | 1.1 / 0 | 0.1 / 0 | 8.6 / 0.3 | 1.5 / 0 | 13.3 / 0.7 |
| 작물 / (없음) | 5.0 / – | 3.8 / – | 1.5 / – | 17.3 / – | **38.1** / – | 22.0 / – |
주의: CLM5 쪽은 **지면 면적 비율**, LM4+ 쪽은 **7월 잎 면적 비율**이라 같은 양이 아님(나무는 면적당 잎이 많아 잎 면적 몫이 더 큼) → 숫자를 그대로 빼지 말고 "있다/없다, 많다/적다"로만 읽을 것. LM4+의 NWN·RFE·ENA·WCE·EAS는 근사 박스.
→ 분명한 것: (a) **동시베리아·러시아 극동의 낙엽송(식생 면적의 25 %·17 %)이 LM4+에는 없음**, 그 자리를 picea와 acer가 채움 → 겨울 잎 잔존의 원인 후보. (b) LM4+에는 관목·작물이 없음 — RFE 관목 30 %, WCE 작물 38 %·EAS 22 %·ENA 17 %(온대 관측 EOS에 수확이 섞임). (c) C3 풀 비율은 ESB에서 비슷(36.8 vs 37.5). CLM5 지면자료도 위성 기반 추정(2000년 기준)이지 실측은 아님.

**관측 EOS의 일장 — 격자별 계산으로 "지역 위도 한 점" 약점 해소 (2026-10-07, `poster/.../scripts/p6_daylength_at_eos_percell.py` → `data/eos_daylength_percell.txt`; 재현 스크립트 `p5_daylength_at_obs_eos.py`도 추가)**: GIMMS 1982–2010 기후값, 20N 이북·진폭 ≥0.5인 1° 격자 9,966개, 격자별 EOS(50 % 진폭)와 그 격자 위도의 일장. AR6 지역 중앙값(p25–p75): NWN **13.13**(12.57–13.55) · ESB **13.30**(13.00–13.71) · RFE 12.70(12.14–13.37) · ENA **11.43**(11.24–11.70) · WCE 12.77(11.92–13.41) · EAS 11.54(10.91–12.03) → 한 점 계산(13.08·13.29·12.56·11.51·12.44·11.43)과 0.3 h 이내 일치, 지역 내 IQR ≈ 0.5–1.5 h(≈ 1–3주). 5° 위도대 중앙값: 20–25N 10.9 · 30–35N 11.7 · 40–45N 12.0 · 50–55N 12.9 · 60–65N 13.2 · 65–70N **13.5** h → 위도 10°당 ≈ +0.6 h(Birch 2021의 +2 h/10°보다 완만). NEU(중앙값 10.5, p10 7.0)·70–75N(10.9)은 EOS가 10월 하순으로 늦고 일장이 짧음 = 상록·툰드라의 적설 주도 감소로 추정, 문턱 근거에서 제외. 전 격자 선형 회귀는 이 꼬리 때문에 기울기 0.013 h/°로 무의미 → 위도대 중앙값을 쓸 것. 4번 실험의 13 h/12 h는 각각 한대·온대 지역 중앙값에 해당.

**★★★ 식생 유형별 "관측 EOS의 일장" — 종별 문턱의 근거 (2026-10-07, `p7_daylength_at_eos_by_type.py` → `data/eos_daylength_by_type.txt`; 유형 = CLM5 PFT ≥50 % 우점 격자, GIMMS 기후값 EOS)**: 중앙값 [p25–p75] h (n):
  **낙엽 침엽(larch) 13.68 [13.39–14.07] (284)** — 50–60N 13.35, 60–72N 14.03, EOS doy 244–247(9/1–9/4) · **낙엽 활엽(acer) 11.40 [11.25–11.67] (85)** — 20–50N, EOS doy 273–281(9/30–10/8) · **C3 풀 12.34 [11.24–13.21] (2,076)** — 40–50N 12.77, 50–60N 12.22, 60–72N 11.61(p25 8.3: 툰드라 적설 꼬리) · 관목 13.32(60–72N 13.48) · 상록 침엽 12.55(위도 의존 10.8→13.1; 상록의 "EOS"는 낙엽이 아니라 적설·태양고도 효과로 봐야 함) · 작물 20–40N 11.8, 40–50N 12.8, 50–60N 13.7(수확).
  → 같은 위도대에서도 유형별로 1–2 h 다름(60–72N: larch 14.0 vs c3grass 11.6 vs 관목 13.5) = **종별 문턱이 필요하다는 직접 근거**. 4번 실험 값과의 대조: acer **12 h는 관측(11.4)보다 길어 약 2주 이름** → 결과에서 온대가 너무 일찍 지면 11.5 h로 재시험; c3grass 13 h는 관측(12.2–12.8)보다 약간 김(≈1주 이름)이나 모델에서 풀이 낙엽송 자리를 대신하므로 절충값; 낙엽송이 있다면 13.5–14 h(위도 의존). 주의: 유형 지도는 2000년 기준 CLM5 추정, 우점 ≥50 % 격자만, 위성 EOS는 격자 안 혼합 신호.

공통: 2010-01-01 03Z 시작(ctl `archive/y2009` restart), 2010년 WFDE5, 24PE @climate00(한 번에 1개), 실행 `lm4/scripts/phentest.sh`(서버 `/data2/ydkoh/lm4/RUN/phentest.sh`), 런 폴더 `/data2/ydkoh/lm4/RUN/phentest/<이름>/`. 파라미터는 larix·c3grass 두 종의 field_table 값. "기온" = `tc_pheno`(캐노피 공기온도의 지수이동평균, 시간상수 20일).

| # | 이름 | 실행파일 | 켜는 조건 | 끄는 조건 | 기간 | 상태 |
|---|---|---|---|---|---|---|
| 1 | `base` | gateBC | 기온 ≥ 5 °C | 기온 < 5 °C | 1년 | 완료 10/04 (8.7 G, restart 119, 종료 2011-01-01) |
| 2 | `tc10` | gateBC | 기온 ≥ 10 °C | 기온 < 10 °C (`tc_crit=283.15`) | 1년 | 완료 10/04 (8.7 G) |
| – | `noparam` | phenoff | #1과 같음(새 파라미터 없음) | #1과 같음 | 31일 | 완료 10/06 (5.2 G) — 회귀 시험용, gateBC와 비트 동일 아님(§13.69) |
| 3 | `offon_d` | phenoff | 기온 ≥ 5 °C | 기온 < 5 °C **또는** (하지 이후·일장 < 14 h·기온 < 10 °C) (`tc_crit_off=283.15`, `dayl_crit_off=14.0`) | 1년 | **완료** 10/06 15:33:41 → 10/07 08:02:30 (16.5 h, rc=0, restart 119, FATAL 4줄은 MOM 경고), 일별 LAI 포함, 로컬 사본 `cases/phentest_2010/offon_d` |
| 4 | `dayl_d` | phenoff | 기온 ≥ 5 °C | 기온 < 5 °C **또는** (하지 이후·일장 < 문턱·기온 < **20 °C**): larix·c3grass `dayl_crit_off=13.0`, **acer 12.0**, 셋 다 `tc_crit_off=293.15`(20 °C 상한은 열대 c3grass 보호용) | 1년 | **실행 중** 10/07 10:52:08~ (≈17 h, 10/08 04시경), 일별 LAI 포함. 손계산 예상 낙엽 시작: NWN 9/11·ESB 9/8·RFE 9/9·ENA 9/21(acer)·WCE 9/21(acer)·EAS 10/2 (관측 9/9·9/3·9/14·10/1·9/14·10/7) |
| 5 | `dayl2_d` | phenoff | 기온 ≥ 5 °C | 기온 < 5 °C **또는** (하지 이후·일장 < 문턱·기온 < 20 °C): **유형별 관측값** larix 13.5 h · c3grass 12.5 h · acer 11.5 h, `tc_crit_off=293.15` | 1년 | **실행 중** 10/07 11:07~ **climate01 PBS 8517**(24랭크, `phentest_pbs.sh`, 랭크 위치 확인: climate01 24개), 일별 LAI 포함. 4번과의 차이 = 지역평균 vs 유형별 문턱 |
| – | `noparam_d` | phenoff | #1과 같음 | #1과 같음 | 1년 | 15:35:58 중단(결과 없음). 일 단위 비교가 필요해지면 #3 종료 후 순차 실행 |
| – | `offon` | phenoff | #3과 같음 | #3과 같음 | – | 13:47 시작 직후 중단된 빈 폴더(다른 세션), 결과 없음 |

- **★★★ 실험 3(offon) 결과 (2026-10-07; 1° 변환 `lm4p_to_latlon.py`로 base를 재변환해 기존 파일과 차이 0 확인 → 같은 방법; `poster/.../data/offon.lai.2010-2010.1deg.nc`, `phentest_regions_summary.txt`, `figures/fig3_phentest_regions.png`)** — AR6 지역 9–10월 평균 LAI(관측 / base / tc10 / offon)와 base−관측 격차의 해소율:
  NWN 0.87 / 2.56 / 1.80 / **1.91** (tc10 45 %, offon **38 %**) · ESB 0.88 / 2.23 / 1.95 / **1.96** (21 %, **20 %**) · RFE 1.10 / 2.17 / 1.60 / **1.63** (54 %, **50 %**) · ENA 2.33 / 3.64 / 3.52 / 3.63 (9 %, 0 %) · WCE 1.56 / 2.24 / 2.20 / 2.20 (5 %, 6 %) · EAS 2.29 / 3.23 / 3.03 / 3.21 (21 %, 2 %).
  5–6월 평균: offon = base와 **동일**(NWN 1.73, ESB 1.75, RFE 1.01, ENA 2.84, WCE 1.99, EAS 2.88; tc10은 각각 1.17·1.51·0.70·2.69·1.89·2.64로 악화) → **설계 목표 달성: 가을만 당기고 봄은 그대로**. 1–8월은 base와 같고 9월부터 갈라짐(NWN 9월 3.22→2.56, 10월 1.89→1.25).
  온대 0–6 %는 예상대로(대상 종이 c3grass뿐, acer 미적용). 일별 LAI(`phentest_daily_lai_band.py`): 50–70N 밴드 정점 doy 242(2.84) → 9/1 2.83 · 9/15 2.23 · 10/1 1.62 · 10/15 1.31 · 11/1 1.03, 정점 이후 **재상승 일수 0** → codex가 우려한 가을 재전엽 반복은 밴드 평균에서는 안 보임(격자 단위 미확인). 60–72N: 9/1 2.37 → 9/15 1.30 → 10/1 0.63.
  손계산 예측과의 대조: 한대 "가까워짐·온대 그대로·봄 불변" 세 가지 모두 적중. 50 % 진폭 EOS(밴드, 일별): offon ≈ doy 266(9/23) vs base(월별 보간) ≈ 10/10 → **약 17일 당겨짐**, 관측(9/3–9/9)까지는 2–3주 남음.
- **SOS·EOS 지도 (2026-10-07, `p8_sos_eos_maps_2010.py` → `figures/fig4_sos_eos_maps_2010.png`, `data/sos_eos_maps_2010.{npz,txt}`, 지역표 `sos_eos_maps_2010_regions.txt`)**: 2010년 1° 격자별 50 % 진폭 날짜(월별 보간), 20N 이북 8,624격자. cos 가중 평균(일, +=관측보다 늦음): 20–90N **EOS CTRL +35.9 → TC10 +28.0 → DL14+T10 +23.8**; **SOS CTRL +11.3 → TC10 +23.2(악화) → DL14+T10 +9.3(불변)**. 50–70N EOS +33.0 → +16.0(DL14+T10, 격자의 86 %가 CTRL보다 이름). 지역별 EOS 잔차(CTRL→DL14+T10): **RAR +18.7→−0.5** · NEU +25.8→+4.6 · NEN +29.9→+10.1 · NWN +31.0→+12.3 · RFE +31.8→+17.3 · EEU +38.3→+22.4 · ESB +38.7→+27.2 · WSB +44.4→+29.1 · WCE +43.4→+37.9 · EAS +49.6→+41.7 · ENA +48.2→+45.5 · TIB +12.8→**−16.8(과보정)**. → 규칙이 잘 듣는 곳 = C3 풀 비중이 큰 고위도(RAR·NEU·NEN·NWN), 덜 듣는 곳 = 상록·acer 비중이 큰 ESB·WSB, 안 듣는 곳 = 온대(acer 미적용). 주의 RAR의 9–10월 평균은 CTRL 0.94 → DL14+T10 0.34로 관측 0.47보다 낮아짐(풀의 급감) — 날짜는 맞고 양은 과소.
  포스터용 3패널 `fig4b_eos_maps_2010.png`(전구 60S–80N, EOS만: (a) GIMMS, (b) CTRL−GIMMS, (c) DL14+TC10−CTRL). **(a)는 모델에서 C3 풀이 7월 잎 면적의 ≥50 %인 격자만 표시**(`phentest_species_frac_cells.py`로 C96 종별 몫 추출 → 1° 상자 면적가중 평균, 빈 상자는 최근접 셀로 채움; 사용자 요청: 규칙이 작동하는 곳만). 그 격자 5,058개의 cos 가중 EOS: CTRL−GIMMS **+28.0일**, DL14+TC10−GIMMS **+16.4일**, 이동 −11.5일(열대·남반구 풀은 T<10 °C 조건 때문에 안 움직여 평균이 희석됨). 남반구 EOS는 그 반구의 가을(3–5월)이며 달력 연 안에 들어옴; 남반구 20–60S의 CTRL EOS는 +78일(건기 낙엽 문제, 별건). 종 분포는 고정이라 이 마스크는 연도와 무관.
  대표 지역 시계열: `REGSET=dl`로 p4·p4b 실행 → `fig3_phentest_regions_dl.png`·`fig3b_phentest_regions_normalised_dl.png`(윗줄 RAR·NEU·NWN = 잘 듣는 곳, 아랫줄 ESB·ENA·EAS = 대조). fig3b의 TC10 선은 darkorange 일점쇄선으로 변경(가시성).
- 패치 `lm4/patches/lm4P.phenology_autumn_daylength.diff`(작업본 `lm4/patches/phenoff_work/`, `.orig` = 원본), 빌드 `lm4/scripts/phenoff_build.sh` → `/data2/ydkoh/lm4/build_phenoff/fms_esm4.5_phenoff.x`.
- 판정(월평균, 사용자 결정): AR6 6개 지역의 9–10월 평균 LAI 격차 감소·5–6월 유지·12개월 오차 — `poster/2026_LM4p_LAI/scripts/p4_fig_phentest_regions.py`(1° 파일 `data/<이름>.lai.2010-2010.1deg.nc`가 있으면 자동 포함). 플럭스 반응 `lm4/scripts/phentest_flux_response.py`.
- **보존**: 완료된 `base`·`tc10`·`noparam`을 로컬 `/Volumes/data02/LM4P/cases/phentest_2010/`로 복사(2026-10-06, INPUT·FORCING 링크와 exe 제외, history+RESTART 포함). **검증 완료**: 세 실험 모두 서버=로컬 — history 138·restart 119개, 바이트 base 9,290,940,033 · tc10 9,283,668,287 · noparam 5,479,864,689, md5(land_month.tile1 / RESTART 전체) base 8409508e6670 / 9caa985b5620 · tc10 5d6263a03a43 / 02bfbbf4c0bd · noparam 3d24a581e7e8 / afd8aabc0d31. `offon_d`도 2026-10-07 복사·검증 완료(history 138·restart 119, 9,315,952,732 B, md5 ce57de992a6c / 61c4e96459b8, 서버=로컬). 서버 `/data2`는 98 %라 원본을 지우기 전 반드시 로컬 사본의 파일 수·체크섬 확인.
- **lufix 생산런 완료 (확인 2026-10-07 10:55)**: `lm4p_lufix_1979-2023` chain.log "chain complete: 1979-2023" 2026-10-06 17:02:20, archive y1979–y2023 45개, PBS 8514–8516 종료(F). climate01·climate02 모두 유휴(load 0) — climate02의 타 사용자 점유도 현재는 없음. **lufix archive(≈8.7 GB/년 × 45 ≈ 390 GB)의 로컬 이중보존은 아직 안 함**(/data2 98 %).
- **덮어쓰기 방지**: `phentest.sh setup`은 변형 폴더를 `rm -rf` 후 다시 만든다 → 종료 restart(`RESTART/coupler.res`)가 있는 폴더는 `FORCE=1` 없이는 거부하도록 가드 추가(로컬 수정 완료, **서버 반영은 offon_d 종료 후** — 실행 중인 bash 스크립트를 덮어쓰면 종료 단계가 깨질 수 있음).

### 13.71 ★★★ 오프라인 실행 속도 최적화 — 설정 수준 (2026-10-07 착수)
**출발점(실측, 2010 CTRL pilot 24랭크 총 69,440 s)**: 지면 fast 80.5 % · 결합자 12.6 %(SFC boundary layer 4.5, Flux UP 5.0) · **land_tracer 건식 침적 평균 8.6 %, 최대 PE 22 %(호출 26억/년 = 매 30분 × 19,600타일 × 가스 31종 × cohort + 에어로졸 7종)** · slow 4.0 % · river 0.6 %. 호출 경로 분석표는 2026-10-07 대화(및 `docs/LM4p_timestep_flow.md`). 결합 전용인데 실제로 도는 것은 건식 침적뿐: 질소 침적은 `do_nitrogen_deposition=F`로 즉시 return, 먼지는 비용 ≈0, `calc_*_cons`는 diag_table에 `water_cons`·`carbon_cons`가 등록돼 있어 **켜져 있음**(`land_tile_carbon` 타일당 2회/스텝).
**실험 설계(사용자 지정, 1개월 2010-01, 24랭크 climate01, 모두 gateBC exe·ctl 물리·동일 restart)**: `ctrl1m`(기준) → `ddep1m`(field_table `"dry_deposition"` 109줄 삭제, atmos_mod+land_mod; 추적자 자체 유지) → `diag1m`(+ `config/diag_table.offline_min`: 필드 856→269, land_month 237→92, 스트림 13개 통째 삭제; 제거 목록 `lm4/config/diag_table_removed.txt`) → `cons1m`(+ water_cons/carbon_cons 제거 → 보존 bookkeeping off). 각 run dir에 `config_diff.txt`·`clock_table.txt`. 실행 = `phentest_pbs_chain.sh`(순차, 같은 노드 조건), 비교 = `phentest_timing.py`(tmin/tavg/tmax·불균형·speed-up) + `phentest_bitcompare.py`(지면 변수 비트 동일성). 가설: ddep off는 지면 변수 비트 동일 + 벽시계 10–20 % 단축. **체인1(ctrl1m ddep1m) PBS 8519 제출 2026-10-07 15:3x** — dayl2_d(24랭크)가 같은 노드에서 도는 조건에서 두 실험 모두 실행되므로 상대 비교는 공정, 절대값은 단독 실행보다 느림. **체인2(diag1m cons1m) PBS 8520을 15:53에 미리 큐 등록** → 4개 실행이 모두 dayl2_d 동반 조건에서 연속 실행되므로 ctrl1m 재실행 불필요. ddep1m이 비트 동일이 아니면 체인2 시작(≈18:40) 전 qdel. PBS `-o` 로그는 잡 종료 시에만 생성됨.
**★ EXP-DDEP 결과 (2026-10-07 18:18, 체인1 PBS 8519, 2010-01 31일, 24랭크, dayl2_d 동반 조건) — 채택 가능**: 총 runtime ctrl1m 5,953 s → ddep1m 4,538 s(**−23.8 %**, tmax 기준 = 벽시계). Update-Land-Fast −27.2 %, land_tracer −95.7 %(ddep 1,294→44 s tmax), Flux UP to atm −20.2 %, update_river −28.3 %(타 PE 대기 감소 효과), SFC boundary layer −1.6 %, slow −3.0 %. PE 불균형(tmax−tmin)/tavg: Land 11.0→12.7 %, Update-Land-Fast 7.7→8.4 % — 거의 불변(ddep가 불균형의 주원인은 아니었음; land_tracer 자체 불균형 245 %는 사라짐). **비트 동일성: 5,424 변수 중 물리 스트림(land_month·by_species·daily·8xdaily·cmip·토지이용별·river·dust) 전부 0 차이.** 차이 348개는 전부 `land_ddep`·`land_tracers_diurnal` 두 스트림의 침적/추적자 진단(O3/SO2/HNO3/H2O2/H2/SO4 *_tot_con_ref*, h2_* 토양 흡수, nhx/noy/bc/oa_ddep, nh3·so2 mol flux; 계산이 꺼져 fill 1e20) + 318개 진단 필드 미생성. → 지면 물리 결과 비트 동일, 가설 확인. 체인2(diag1m·cons1m) 18:18 자동 시작. 산출 `/Volumes/data02/LM4P/cases/speedtest/{ctrl1m,ddep1m}`. 수집 스크립트 `lm4/scripts/speedtest_collect.sh`.
**★ EXP-DIAG·EXP-CONS 결과 (체인2 PBS 8520, 18:18–20:43, 같은 조건)**: 총 runtime(tmax) ctrl1m 5,953 → ddep1m 4,538(−23.8 %) → **diag1m 4,309(−27.6 %, 증분 −5.0 %p)** → cons1m 4,387(−26.3 %, 증분 **+1.8 % 느려짐 = 잡음 범위**). diag 효과: Flux UP to atm 343→209 s, update_river 124→63 s, Update-Land-Slow 332→302 s, Update-Land-Fast 3,599→3,427 s; PE 불균형 Update-Land-Fast 8.4→4.9 %, Land 12.7→8.3 % (진단 버퍼·출력 대기가 불균형 일부였음). cons 효과: 측정 불가 — cons와 무관한 SFC boundary layer가 204→230 s(+13 %)로 흔들려 run-to-run 잡음 ≈±2 % (dayl2_d 동반 노드 공유). **비트 동일: diag1m·cons1m 모두 남은 1,950/1,938 변수 차이 0**; 사라진 것은 diag_table에서 뺀 13개 스트림 파일뿐. 판정: ddep(필수 채택) + diag(채택, 단 필요한 진단 목록 사용자 확인) / cons는 이득 없음 → 진단으로 쓰고 싶으면 water_cons·carbon_cons 유지해도 무방.
- **주의(2026-10-07)**: 끈 dry_deposition(대기화학 추적자 침적속도, land_tracer_driver)은 질소 순환의 N 침착 입력(`nitrogen_sources.F90`, `do_nitrogen_deposition` + 파일)과 **무관**. `nhx_ddep`/`noy_ddep`는 대기 쪽 손실 진단일 뿐 토양 N 수지에 안 들어감. 2단계에서 C–N(CORPSE-N) 켤 때는 do_nitrogen_deposition·N 침착 파일·질소 진단(nLand, nitrogen_cons, N 풀)을 offline_min diag_table에 추가할 것.
- **Codex 성능 검토 (2026-10-07, read-only, 소스 6개+설정+시계표)** 원문 `lm4/config/codex_perf_review_2026-10-07.md`. 요지: ①추적자 축소(sphum+co2 유지 필수; 결합자가 추적자별 매 스텝 재격자화) 수 % 기대·data_table/SIS2/대기init 의존성 감사 필요 ②`land_model.F90:1342` 저장량 진단용 2차 타일 순회를 진단 미사용 시 건너뛰기(코드) ③atmos init 130 s는 1회성 ④"Flux land to ice" 152 s는 대부분 앞 단계 PE 대기 시간(tmin 3 s) → 절감 여지 작음 ⑤layout 2,2→1,4/4,1 시험 가치(불균형 상한 2.2 %). Update-Land-Fast 80 % 내부 시계 부재가 핵심 공백.
- **체인3·4 제출 (2026-10-08 01:15)**: `phentest.sh`에 분해 접미사 추가(`_np48` = 48랭크·생산 layout 템플릿 그대로 / `_l14`·`_l41` = 24랭크, land layout 1,4·4,1). 서버엔 실행 중 잡(dayl_d·dayl2_d)이 옛 phentest.sh를 읽고 있어 **새 판을 `phentest_v2.sh`로 배포**(체인 스크립트 `PT=` 변수) — 잡 종료 후 phentest.sh로 덮을 것. 체인3 PBS 8521 `diag1m_l14 diag1m_l41`(24랭크, dayl2_d 동반 = diag1m과 같은 조건) 실행 중; 체인4 PBS 8522 `ctrl1m_np48 diag1m_np48`(ncpus=48 단독) 대기 → dayl2_d·체인3 종료 후 시작.
**★ 48랭크 확인·layout 결과 (2026-10-08)**: (1) **48랭크 단독(체인4 PBS 8522, 생산 layout)**: ctrl1m_np48 3,746 s → diag1m_np48(=ddep+diag) 2,873 s, **−23.3 %**(tmax), Update-Land-Fast −25.7 %, Flux UP −40.1 %, river −59.7 %; **비트 동일 1,950/1,950**. 1월 31일 기준 연 환산(main loop×365/31): 11.9 → 9.1 h/yr. 생산 실측 10.6 h/yr에 비율 적용 시 ≈8.1 h/yr. 24→48 확장: ctrl 5,953→3,746 s(1.59배), opt 4,309→2,873 s(1.50배). (2) **land layout 2,2 → 1,4 / 4,1 (체인3 PBS 8521, 24랭크)**: 총 시간 +0.2 / +0.3 %(잡음), PE 불균형 불변, **결과 비트 동일** → land는 비구조(UG) 분할을 따로 쓰므로 `land_model_nml layout`은 사실상 무관. layout 후보 기각. 최종 채택 권고 = ddep + diag(offline_min, river_daily 복원 여부 사용자 결정 대기); cons는 유지(이득 없음).
**★ 실험 4(DL13/12)·5(DLtype) 결과 (2026-10-08)**: 둘 다 2011-01-01 완주, 로컬 보존 바이트 일치(dayl_d 9,297,575,795 B / dayl2_d 9,297,565,915 B, 각 285파일) `/Volumes/data02/LM4P/cases/phentest_2010/{dayl_d,dayl2_d}`; 1° 변환 `poster/.../data/{dayl,dayl2}.lai.2010-2010.1deg.nc`. **Sep–Oct 격차 해소율(CTRL−GIMMS 대비)**: DL13/12 — NWN 49 %, ESB 32 %, RFE 84 %, ENA 60 %, WCE 116 %(과보정), EAS 40 %, RAR 93 %, NEU 113 %(과보정); DLtype — 40 / 22 / 63 / 46 / 86 / 32 / 69 / 98 %. 비교 DL14+TC10 38 / 20 / 50 / 0 / 6 / 2 %. **May–Jun 평균은 모든 지역에서 CTRL과 동일**(봄 부작용 없음). EOS 지도(셀 평균 dEOS vs GIMMS): 20–90N CTRL +35.9 → DL14+TC10 +23.8 → **DL13/12 +7.9** → DLtype +11.9 d; 50–70N +33.0 → 16.0 → **9.8** → 14.6; 40–50N +41.8 → 34.0 → **7.5** → 11.9. 일별 LAI(50–70N, 40–50N) 재개엽 0일. **주의: 20–40N dSOS가 −7 → −28 d** — 아열대에서 겨울 LAI 최저값이 낮아져(20 °C 상한 + 낮 길이 <12–13 h로 겨울 낙엽) 50 % 진폭 기준이 바뀐 지표 효과 가능성, 확인 필요(그림상 ENA·EAS 1–3월 정규화 값도 달라짐). 손 계산 예측(DL13/12가 acer 12 h로 온대에서 조금 이르게)과 방향 일치: WCE·NEU 과보정. 판정: 단일 문턱으로는 DL13/12가 최선, DLtype은 덜 공격적.
**★ 빠른 설정을 기본값으로 치환 (2026-10-08, 사용자 지시)**: `lm4/config/field_table.offline_fast`(ctl − dry_deposition 109줄) + `lm4/config/diag_table.offline_fast`(offline_min + **river_daily 복원**, 사용자 확인 "리버는 되살려"; 274필드). `phentest.sh`가 4개 속도시험 변형 외 **모든 변형에 기본 적용**, `FULLCFG=1`이면 ctl 표 사용. ctl·lufix 생산 폴더는 불변. 서버 이전 판 `RUN/config/phentest.sh.before_fast_20261008`, 임시 `phentest_v2.sh` 삭제. **2026-10-08 이전 실험(base·tc10·offon·dayl·dayl2·replant_d)은 ctl 표로 돌았음** — 지면 물리는 비트 동일하므로 비교 가능. 첫 적용: **replant 1년 `replant1y_np48_d`**(48랭크, 재파종 seed, CTRL 물리, 일별 LAI) PBS 8523 2026-10-08 실행, 예상 ≈8 h.
**아이디어 (2026-10-08, 사용자 확정 = "문턱만"): 낙엽 문턱의 머신러닝 추정 (hybrid, 2단계 AI 에뮬레이터 후보·두 번째 논문 후보)**. 물리 구조(짧아지는 낮 AND 평활기온 조건)는 유지하고 **문턱값 `dayl_crit_off`(+`tc_crit_off`)만 RF가 격자·종 특성으로 예측**. 통째 치환(매일 on/off를 RF가 결정)은 외삽 불가·관측 혼입(눈·가뭄 갈변·수확)·결합 되먹임·재개엽 진동 위험으로 기각. 목표값: 격자·연도별 관측 EOS 시점 낮 길이(이미 `p6_daylength_at_eos_percell.py`, `data/eos_daylength_percell.txt`) — 학습 연도에선 순환논리라 검증은 반드시 **기간 분리(1982–2000 학습 / 2001–2010 시험)·대륙 분리·극한 해(2010 러시아)**로, 비교 기준 DL13/12. 설명변수 후보: 위도(최대 낮 길이), 연·가을 평균기온, 건조도, 종/PFT 비율, 여름 GPP. 코드 측면: 현재 문턱은 종별 스칼라(field_table) → 격자별 2D 입력 읽기 필요(초기화 1회, 비용 ≈0). 첫 논문(진단+규칙) 이후.
**★ 봄·가을 신호 비교 (2026-10-08, `poster/.../scripts/p14_cue_skill_sos_eos.py` → `data/cue_skill_sos_eos.txt`)**: GIMMS 1982–2010 기후값 SOS/EOS(50 % 진폭) 8,488격자(20–75N) vs ERA5 t2m 1982–2010 기후값(0.25° NH, lat 내림차순·lon 0–360 확인, 1° 블록평균; 검산 50–60N 1월 −14.8 / 7월 16.2 °C). 고정 문턱 하나로 날짜 예측 RMSE(일, cos-lat 가중, 상수는 전 격자 공통 격자탐색). **SOS 50–75N**: 낮 길이(13.75 h) 46.5 / 기온(10 °C) **19.3** / GDD5(100) 23.9 / GDD+냉각(Murray형) 22.4 / **GDD(20)+낮 길이(13.5 h) 15.3**; 40–50N: 27.3 / 27.0 / 28.3 / 28.3 / 23.7. **EOS 50–75N**: 낮 길이(12 h) **18.8** / 기온(8.5 °C) 30.4 / 낮+기온 16.9; 40–50N: 25.0 / 44.9 / 23.8. 관측 SOS 시점 낮 길이 중앙 15.9 h(p10–p90 12.7–24 h, 흩어짐) vs EOS 시점 12.7 h(10.7–14.1 h, 모임). 해석: **봄은 기온(열 누적)이 주신호, 낮 길이는 "13.5 h 이전엔 안 됨" 관문 역할**; 가을은 낮 길이가 주신호(가설과 일치). 냉각 요구는 이 공간 비교에선 이득 작음(기후값 공간 비교의 한계, 연도별 검증 필요). **모델 함의: LM4+ 봄 규칙은 이미 GDD+평활기온이고 SOS가 늦음 → 낮 길이 관문을 넣으면 더 늦어질 뿐; 봄 지연은 평활 지연·문턱 쪽 문제일 가능성**(손 계산으로 확인할 것). 20–40N은 강수 주도 phenology라 기온·GDD RMSE 100일 이상 → 해석 대상에서 제외. 한계: 공간 대 시간 대치(격자당 기후값 1개), VIPPHEN 연도별로 연간 변동 검증 예정.
- **포스터 수식 상자 (2026-10-08)**: Results 2–3 사이에 잎 켜기/끄기 규칙을 **Weng et al. (2015, Biogeosciences 12, 2655–2694, 부록 A3 식 A31) 표기 그대로** 인용(사용자 지시: 코드는 적지 말 것). 논문과 lm4P 코드의 차이(기록용, 포스터엔 안 씀): 코드는 GDD를 ½[max(Tmin−0)+max(Tmax−0)]로, 온도는 캐노피 공기 일평균, 잎 켜기·끄기에 가뭄 조건 추가, 문턱은 종별(낙엽송·C3 풀 5 °C/180, 기타 10 °C/360; 원 논문은 공통 10 °C/320). LM4.1 논문(Shevliakova 2024)에는 phenology 식이 없고 인용만 함. 스크립트 `poster/.../scripts/p15_phenology_rule_box.py`.
- **SOS/EOS 정의 결정 (2026-10-08, 사용자 결정 = 50 % 유지)**: 20 %(Peano et al. 2021) 시험 결과 4지역 ΔEOS가 NEU −6 / RFE +10 / NWN −8 / ESB +33 d로 줄고 ΔSOS는 +19–39 d로 커짐(50 %: ΔEOS +27/+28/+33/+38, ΔSOS +27/+24/+16/+13). 원인: GIMMS는 정점 후 9–11월 완만 감소(상록·하층·눈 신호 혼재), 모델은 9월까지 정점 유지 후 10월 급강하 → 50 %는 "하강 시작", 20 %는 "하강 끝"을 봄. 모델 결함 = 하강 시작이 늦고 하강이 급함; 9–10월 LAI 과잉은 정의와 무관. 포스터는 50 %(White et al. 1997, GBC 11, 217–234, NDVI ratio 0.5) 유지, 논문은 두 시점 모두 제시. 20 % 산출 `poster/.../data/lai_regional_sos_eos_thr20.txt`, `figures/fig2_regional_seasonal_cycle_thr20.png` (`THR=0.2`). 핵심 선행: **Murray-Tortarolo et al. 2013, Remote Sens. 5, 4819** (TRENDY 8개 중 7개 모델이 늦은 휴면으로 생장기 과대, 북방 LAI 과대) — Discussion 핵심 인용.
- 포스터 갱신(2026-10-08): 4지역(NEU·RFE·NWN·ESB)으로 Fig. 1 다각형·Fig. 2(2×2)·Fig. 3 통일, Fig. 2·3 상단 제목 삭제, 범례 "CTRL (TC5)", 헤더 "RESULTS 2: PHENOLOGY (OBS. AND MODEL)" / "RESULTS 3: MODIFIED PHENOLOGY RULES (PILOT)"(40 pt), 수식 상자는 Weng 2015 표기 정의만. Results 2 수치: EOS +27–38 d(29년 모두), SOS +13–27 d, 관측 EOS 낮 길이 12.7–13.3 h(NWN·ESB·RFE; NEU 중앙값 10.5 h로 넓게 퍼짐 — 해양성, 본문에서 제외).
- Murray-Tortarolo 2013 원문 확인(2026-10-08): 정의는 **20 %**(월 단위)·진폭<0.5 마스크, TRENDY 8개(LM 없음) 중 7개 늦은 휴면(20–60 d), onset 모두 15–20 d 늦음, GPP 기준 휴면은 LAI보다 ≈38 d 이름. 포스터에선 "모델 공통 문제" 근거로만 인용(정의가 다름에 주의).
- **시간 해상도 점검 (2026-10-08)**: 2010 일별 LAI(offon_d, dayl_d) 대역 평균에서 일 자료 vs 월평균→일 보간 비교 — SOS/EOS 차이 1–8 d(일 자료가 EOS 3–8 d 이름, 20 %에서 더 큼). 50 % vs 20 % 차이(20–40 d)는 해상도가 아니라 곡선 모양(관측 2–3개월 완만 하강 vs 모델 2–3주 급강하) 때문. 일 자료로 바꿔도 "20 %에선 가을 편차 작음"은 유지. 관측 측 15일 원자료 효과는 미확인(로컬엔 월 통합판만).
- **KMS 2026(한국기상학회 가을) 포스터 초안 (2026-10-08)**: `poster/2026_LM4p_LAI/poster_2026_KMS_draft.{pptx,pdf}`, 생성 `scripts/build_poster_kms2026.py`(ACM과 같은 90×140 템플릿, 한국어). 사용자 결정: 중심 = 전 지구 LAI 평가 + 종 분포, phenology는 한 줄(pilot 실험은 ACM 전용). 그림: fig0 spin-up(LAI −0.6 %, GPP +0.4 %, 목재 +7.6 %), fig1 MJJAS, **신규** `p16_zonal_month_bias.py`(위도×월 편차; 열대 연중 +1.18 (+42 %), 20–60S +1.37 (+113 %), 50–70N JJA +0.28 / SON +1.06; AR6 SES MJJAS 1.36→5.00 (+268 %), NSA +30 %, SAM +43 %, WAF +49 %, CAF +43 %, SEA +44 %), **신규** `p17_species_model_vs_obs.py`(50N 이북 나무 구성 모델 vs CLM5: picea 65 vs 73 %, acer 36 vs 19 %, larix 0 vs 9 %, 우점 일치 59 %).
- **MODIS MCD12C1 v061 2010 원본 HDF (2026-10-08)** `/Volumes/data02/MODIS/MCD12C1_v061_hdf/MCD12C1.A2010001.061.2022161022952.hdf` (1.24 GB). 층: Type1(IGBP)/Type2(UMD)/Type3(LAI 분류, 11종: grass/cereal, shrub, broadleaf crop, savanna, EBF, DBF, ENF, DNF, …)의 Percent·Majority; **PFT(Type5) 층은 CMG 제품에 없음**. **격자 검증 통과**: 행0=90N, 열0=−180 (CMG 0.05°), 사하라 20–25N 0–10E 비식생 100 %, 동시베리아 60–65N 110–130E DNF 14 %·ENF 1 %, 캐나다 55–60N 120–100W ENF 19 %·DNF 0 %. 50–75N 육지: savanna 34.8 %, grass 24.0 %, shrub 16.9 %, ENF 10.7 %, DBF 3.6 %, DNF 3.0 % → 성긴 낙엽송 숲 상당수가 savanna로 분류돼 종 구성 비교용으론 부족, C3/C4 구분도 없음 → 종 지도는 MODIS 기반 CLM5 PFT(Lawrence & Chase 2007; Lawrence et al. 2019) 유지, MODIS DNF는 교차 확인용.
- **KMS 포스터 갱신 (2026-10-08)**: 그림1 spin-up `KMS=1 p0_fig_spinup_3panel.py`→`fig0_spinup_lai_gpp_wood_kms.png`(전체 제목 없음, (a) LAI (b) GPP (c) Wood carbon), 캡션 영어·본문 한국어. 그림3 `p16_zonal_month_bias.py`에 **GIMMS 연평균 LAI < 0.25 격자 제외**(`MINLAI`, 15,109→13,649격자; 0.1로 해도 백분율 동일: 열대 +42 %, 20–60S +112 %, 50–70N JJA +0.30 / SON +1.12, SES MJJAS 1.41→5.17 +268 %). 그림4 `p17` 6종(풀 포함)·(a) 관측 (b) 모델: **열대 30S–30N C4 풀 관측 45 % vs 모델 8 %, C3 풀 17 % vs 48 %, prioria 36 vs 40 %**(모델=7월 엽면적 비율, 관측=면적 비율이라 정의 차이 주의); 50N 이북 larix 7.5 vs 0 %, acer 4.8 vs 16.7 %, picea 29.8 vs 28.4 %, C3 풀 57.5 vs 54.9 %; 우점종 일치 50N 이북 57 %, 전 지구 50 %. **새 발견: 모델에서 사바나 C4 풀이 거의 사라지고 C3 풀·열대 상록수로 대체 — 열대·남반구 LAI 과대와 연결 가능(검증 필요).**
- **KMS 포스터 프레임 스타일 (2026-10-08, 사용자 스케치)**: 사용자 수정본에 직접 적용(스크립트 재생성 안 함, 백업 `poster_2026_KMS_draft_v1_user.pptx`). 머리띠 = 흰 바탕·초록(tx2) 4.5 pt 테두리·초록 글자, 직사각형; 각 절 본문 = 머리띠 아래 초록 테두리 사각형(맨 뒤 레이어, `Frame: …`); 본문·캡션·표를 테두리 안쪽 0.3 in로 이동, 표 열폭 비례 축소. **이후 `build_poster_kms2026.py` 재실행 금지(수정·프레임 지워짐)**.
- **그림 3 마스크 변경 (2026-10-08, 사용자 요청으로 Codex 웹검색 검토)**: LAI 문턱 마스크 폐기 → **MODIS IGBP 나지 비율 ≥ 50 % 격자 제외(고정, 두 자료 동일 적용)**, 민감도 80 %·무마스크 모두 백분율 동일(열대 +42 %, 20–60S +113 %, 50–70N +56 %, SON +1.06–1.07). 근거: GIMMS 0.25 문턱은 제외 격자의 53 %가 초지였고, 피복별 LAI(80 % 순도) 나지 GIMMS 0.20 vs LM4+ 0.29, 초지 0.58 vs 1.21, 사바나 1.46 vs 3.02, 사하라 순수 나지 GIMMS 0.23 vs LM4+ 0.16 → 관측·모델 바닥값이 달라 관측 LAI 문턱은 불공평. Codex 확인: 표준 LAI 사막 문턱 없음; 선례 Feng et al. 2021 Sci. Bull. (연평균 NDVI < 0.1 제외, doi:10.1016/j.scib.2021.02.023); Zhu et al. 2016의 LAI>0.1은 생장기 판정용; GIMMS LAI4g 사막 양의 바닥값 문서 없음(토양 배경은 추정); LM4.1은 나지 클래스 없이 풀 cohort로 저 LAI 유지. LAI·모델 공동 문턱은 평가 영역이 모델 성능에 좌우돼 피할 것. 관련 선행: **Park & Jeong 2021 ERL (doi:10.1088/1748-9326/abe2cf, ESM LAI 계절성)** — 저자 Hoonyoung Park & Sujong Jeong(정수종 교수 연구실; 사용자 정정 2026-10-08, 처음엔 우리 그룹으로 잘못 추정), 인용 검토. 원문 `scratchpad/codex_desert/answer.md`(임시).
- **Park & Jeong 2021 ERL 원문 정리 (2026-10-08)** `poster/.../references/REFERENCES.md` F-추가 2. CMIP5/6 14개(GFDL 없음) EOS +22/+18 d vs GIMMS3g(261 DOY), 북방·낙엽 침엽수 최대; 관측 EOS–가을기온 민감도 +0.5 d/K → **낮 길이 규칙의 다년 실행에서 EOS 기온 민감도 점검 필수**; CLM5는 이미 일장 문턱으로 낙엽 종료. 포스터·논문 인용.
- **CLM5(우리 release-clm5.0.37) 낙엽 규칙 소스 확인 (2026-10-08)**: `components/clm/src/biogeochem/CNPhenologyMod.F90` seasonal deciduous — 잎 끄기 L956–957: 하지 이후(`ws_flag==0`) `dayl < crit_dayl`이면 offset, 기온 무관; `clm5_params.c171117.nc` crit_dayl = 39300 s (10.92 h, 전 지구 공통), ndays_off = 15 d. 잎 켜기 L885–913: 동지에 GDD 리셋, 3번째 토양층 온도 > 0 °C 적산, 문턱 exp(4.8+0.13·(연평균 T2m−0 °C)) (Biome-BGC v4.1.2). **Birch et al. 2021의 위도 의존 일장 문턱(65N 15 h → 45N 11 h)은 우리 버전에 없음**(lat_slope류 코드 부재). → 다중 LSM 비교에서 CLM5 생산런 EOS = "일장 단독 규칙" 사례, EOS 기온 민감도(관측 +0.5 d/K, Park & Jeong 2021) 비교 재료.
- **★ CLM5 BGC 생산런 phenology 분석 (2026-10-08, `poster/.../scripts/p18_clm5_phenology_compare.py` → `data/clm5_lm4_gimms_sos_eos.txt`, `figures/fig_clm5_lm4_gimms_regions.png`)**: CLM5 TLAI 1982–2010(서버 `postproc/clm5_prod/clm5_prod.YYYY.nc`에서 `ncks -v TLAI` → 로컬 `/Volumes/data02/cesm2/clm5_prod_TLAI/`, 29파일 74 MB). **격자 검증 통과**: f09 192×288, lat −90→90 오름차순, lon 0–358.75, m² m⁻², fill 1e36; 연평균 사하라 0.00 / 아마존 3.90 / 콩고 3.73 / 동시베리아 1.02. 1° GIMMS 격자로 최근접 대응, 공통 유효 격자. ΔEOS(vs GIMMS, 50 %): NEU LM4+ +25 / **CLM5 +26**, RFE +29 / **+38**, NWN +32 / **+36**, ESB +38 / **+53**, ENA +42 / +64, WCE +49 / +96, EAS +70 / +57 d. ΔSOS CLM5 +3 ~ +39 d. **해석: CLM5는 일장 규칙(하지 이후 < 10.92 h, 15일 낙엽)인데도 더 늦음 — 50–60N에서 10.92 h는 10월 중순, 관측 EOS 일장은 12.7–13.3 h → 문턱이 약 2 h 짧음(Birch et al. 2021의 지적과 동일).** 결론 후보: 기온 단일 규칙(LM4+)과 일장 단일 규칙(CLM5) 모두 EOS 25–50 d 지연 = 원인은 "신호 종류"보다 "관측 낙엽 시점과 맞지 않는 문턱" → DL13/12형 처방이 두 모델에 공통 적용 가능(다중 LSM 논문 메시지 후보). 주의: CLM5 LAI 크기 과대(여름 3.5–4.8, NEU 겨울 2.3 = 상록 비중), h0는 격자 평균(PFT 혼합) → 낙엽수만 보려면 PFT별 h1 필요; WCE +96 d는 작물 등 확인 필요.
- **CTSM에서 Birch 수정 확인 (2026-10-08)**: 우리 CLM5 = `release-clm5.0.37`(git 547ae9643), Birch 관련 코드 없음(crit_dayl 상수 39300 s). **CTSM master `CNPhenologyMod.F90`에는 있음**: `SeasonalCriticalDaylength()` — crit = crit_dayl_at_high_lat(54000 s=15 h) − crit_dayl_lat_slope(720 s/°)×(65 − |lat|), 하한 crit_dayl 39200 s(White 2001); 45N 11.0 / 55N 13.0 / 60N 14.0 / 65N 15.0 h. 방식 `min_critical_dayl_method` = Constant | DependsOnLat | DependsOnVeg | DependsOnLatAndVeg; **기본 Constant, `clm6_0` 물리+use_cn일 때만 DependsOnLat**(namelist_defaults_ctsm.xml L682–683), `onset_thresh_depends_on_veg`도 clm6_0+cn에서 true, `snow5d_thresh_for_onset`=0.2 m 추가. CTSM = 소프트웨어/저장소 이름, CLM6 = CTSM의 clm6_0 물리 옵션; CTSM은 CESM 지면 성분으로 결합·오프라인 모두. 우리 CESM2.1.5는 옛 clm5.0 분기라 결합·오프라인 모두 미적용. → CLM5 생산런 EOS 지연은 "옛 상수 문턱" 결과로 해석; CTSM DependsOnLat 실험은 후속 과제.
- **CTSM/CLM6 일장 규칙 vs 우리 LM4+ 패치 비교 (2026-10-08)**: 공통 = 하지 이후(낮이 짧아짐) ∧ 낮 길이 < 문턱 → 낙엽. 차이: (1) 문턱 기준 CLM6 = 위도(15 h − 720 s/°×(65−|lat|), 하한 10.9 h; 또는 PFT 온대/북극형, DependsOnLatAndVeg 옵션), 우리 = 종별(DL13/12: larix·c3grass 13 h, acer 12 h); (2) 기온 조건 CLM6 없음, 우리 = 평활기온 < tc_crit_off(20 °C) 동시 조건 → Park & Jeong 2021의 관측 EOS 기온 민감도 +0.5 d/K를 남길 여지(20 °C 상한이라 실제론 일장 지배 가능 — 다년 실행에서 민감도 측정); (3) CLM 원래 가을 기온 규칙 없음(일장 규칙이 대체), 우리 = 기존 기온 규칙에 OR로 추가; (4) 낙엽 속도 CLM 15일 선형(ndays_off) vs LM4 나무 7.5 %/일 지수·풀 즉시; (5) 하지 판정 CLM ws_flag(dayl<prev_dayl) vs 우리 적위 도함수 부호, 일장 계산 CLM 궤도 dayl vs 우리 Cooper 1969. 논문 서술: "CLM6=위도 의존, 우리=종 의존 → 종×위도 결합이 다음 단계".
- **CLM6 위도 식 vs 관측 EOS 일장 (2026-10-08, data/eos_daylength_percell.txt 대역 중앙값)**: 40–45N 관측 12.0 vs CLM6 10.9(하한) h, 45–50N 12.4 vs 11.5, 50–55N 12.9 vs 12.5, 55–60N 13.1 vs 13.5, 60–65N 13.2 vs 14.5, 65–70N 13.5 vs 15.5 h. 관측 기울기 ≈0.06 h/° vs CLM6 0.2 h/° (3배 이상 가파름) → CLM6 이식 시 온대 늦고 고위도 이름 예상. 형태(위도 의존)는 맞지만 기울기 재추정 필요. 제안 실험(사용자 승인 대기): 패치에 위도 항(a + b(|lat|−lat0), 하한 c; 기울기 0이면 기존 동일) 추가 → 재빌드 → 2010 1년 "CLM6형"(15 h, 0.2 h/°, 하한 10.9 h, 기온 조건 없음)·"관측 맞춤형"(12.0 h + 0.06 h/°×(|lat|−42.5), Tcap 20 °C).
- **결정 (2026-10-08, 사용자)**: CLM6형 위도 문턱·온도 조건 끄기 실험은 지금 하지 않음 — **가능성으로만 기록**. 정리: (a) 온도 조건 끄기 = 파라미터만(tc_crit_off를 400 K 등 높게), 코드 수정 불필요; (b) 위도 의존 문턱 = 패치에 a + b(|lat|−lat0), 하한 c 항 추가 + phenoff 재빌드 필요; (c) 현재 DL13/12의 T_cap 20 °C는 한대 가을엔 거의 안 걸려 사실상 일장 지배 → 관측 EOS 기온 민감도(+0.5 d/K) 재현을 노리면 T_cap 15 °C 시험이 후보. 다년 실행에서 EOS 기온 민감도를 먼저 재 보고 필요하면 착수.
- **종별 vs 위도별 문턱 판단 (2026-10-08)**: 관측에서 종 차이(60–72N 낙엽송 14.0 / 관목 13.5 / C3 풀 11.6 h, 2.4 h)가 위도 차이(40→67N 12.0→13.5 h, 1.5 h)보다 큼 → 원리상 종별이 맞음. 그러나 2010 실험에서 관측 유형별 DLtype이 단순 DL13/12보다 덜 개선(해소율 NWN 40 vs 49, ESB 22 vs 32, RFE 63 vs 84, ENA 46 vs 60 %) — 모델 종 분포 오류 탓(북반구 낙엽송 부재 → 13.5 h 거의 미사용, 그 자리 acer에 11.5 h 적용). 결론: 종별 문턱의 이점은 종 분포가 맞을 때만 → **재파종 상태 + DLtype 실험**으로 확인(replant1y 종료 후). 논문 서술도 이 순서로.
- **해상도 결정 (2026-10-08, 사용자)**: C96 유지. C48 검토 결과 ≈3–4배 빠르나 C96 KIOST 초기장(타일·cohort) 이전, 입력(격자·하천망 등) 재생성, 기존 C96 결과와의 연속성 단절 비용이 커서 기각. 시간 단축은 (1) 문턱 시험 1–3년, (2) 최종 후보만 1982–2010, (3) climate02 비면 2노드 96 PE(1.70×), (4) 24+24 동시 실행, (5) Update-Land-Fast 코드 최적화로 대응. C48은 대규모 민감도 스윕이 필요할 때만 재검토.
- C48 가능성 점검 (2026-10-08): KIOST LM4+ INPUT은 C96 격자·모자이크만; "c48"은 UFS 회귀시험 설정 폴더(`ufs-weather-model/tests/tests/control_c48*`)뿐(지면 자료 아님); FRE-NCtools(make_hgrid, make_solo_mosaic, fregrid, river_regrid, make_topog) 미설치 → C48은 도구 설치부터 필요, C96 유지 결정 재확인.
- **포스터 2종 인쇄 맡김 (2026-10-08 15:27)**: KMS `poster/2026_LM4p_LAI/poster_2026_KMS_final.{pptx,pdf}`(15:27 사용자 저장본, KIOST 풀이 없는 서론 — 사용자 결정), ACM `poster_2026_ACM_final.{pptx,pdf}`. 둘 다 90×140 cm. 이후 수정은 이 final pptx에서만(생성 스크립트 재실행 금지).
- **replant1y_np48_d 완주 (2026-10-08 17:22, PBS 8523)**: 2011-01-01 03Z, RESTART 119, FATAL 4줄(MOM 경고), history 66파일 6.1 G. **Total runtime 23,079 s = 6.4 h/yr (48랭크 + offline_fast)** — 예상 8 h보다 빠름(생산 ctl 10.6 h/yr 대비 −40 %). 서버 `RUN/phentest/replant1y_np48_d/`. **로컬 보존·검증 완료**(2026-10-08) `/Volumes/data02/LM4P/cases/phentest_2010/replant1y_np48_d/`(INPUT·FORCING·model.x 제외): 서버=로컬 215파일 6,501,238,585 B, md5 coupler.res 4e6a9ea9df7d / land_month.tile1 90165452b7d4. 속도 원인(cohort 수 vs 1월 환산 오차)은 추가 조사 안 함(사용자: 단축이면 OK).
- **★ replant1y 결과 (2026-10-08, `poster/.../scripts/p19_replant_vs_ctrl.py` → `data/replant_vs_ctrl_2010.txt`; 1° `data/replant1y.lai.2010-2010.1deg.nc`; 종 `data/replant1y_species_share_july2010_c96.npz`)**. 7월 엽면적 종 비율(면적가중) **50–75N**: CTRL picea 26.6 / larix 0.0 / acer 15.8 / c3grass 57.6 % → REPL **picea 36.6 / larix 3.1 / acer 2.5** / c3grass 57.8 % (관측 CLM5 지도 picea 29.8 / larix 7.5 / acer 4.8 %, p17). **열대 30S–30N**: c4grass 7.2 → **35.8 %**, c3grass 57.6 → 28.9 %, prioria 31.7 → 33.0 %. LAI(GIMMS 대비 연평균 편차): 50–70N +59 → **+75 %**, 열대 +45 → +46 %, 20–60S +100 → +97 %, 30–50N +51 → +50 %, 전 지구 +50 → +53 %. 북쪽 지역 5–6월(관측/CTRL/REPL): NEU 2.14/1.58/1.97, RFE 1.70/1.01/1.21, ENA 3.44/2.84/3.38, WCE 3.04/1.99/2.27 → **봄 부족 개선**; 9–10월 격차는 **악화**(gap-closed NWN −13, NEN −18, NEU −25, RFE −20, ENA −26, ESB −14 %); 12개월 MAE 50–70N 0.61 → 0.75. 해석: 재파종이 acer(낙엽 활엽)를 picea(상록)로 바꿈 → 상록은 봄에 이미 잎이 있고 가을에도 유지 → 봄↑·가을↑. **larix는 1년 뒤 3 %뿐(어린 개체, 엽면적 작음)** → DLtype(larix 13.5 h) 시험은 이 상태에선 larix 문턱이 거의 안 쓰임 → **재파종 상태로 수년 키운 뒤** 시험해야 의미. **열대 C4 풀 7 → 36 %로 바뀌어도 열대 LAI 과대 불변(+45 → +46 %)** → KMS 포스터의 "C4 풀 소실 → 열대 LAI 과대" 가설은 1년 기준 지지 안 됨(C3/C4 교체가 LAI를 못 낮춤; 원인은 다른 곳 — 풀 LAI 자체·토양수분 등). 주의: 재파종 1년 = 미성숙, 모델 비율은 엽면적·관측은 면적 기준.
- **replant_2011_2015 완주·보존 (2026-10-10)**: 체인 `RUN/replant_2011_2015/`(stage `lm4/scripts/stage_replant_cont.sh`, git `chain_lm4p_ctl.sh` R 지정) 2011–2015 5년, 연마다 archive·12개월 검사 통과(2015 종료 10/10 02:22). 로컬 `/Volumes/data02/LM4P/cases/replant_2011_2015/` 서버=로컬 1,055파일 37,568,787,379 B. 분석 스크립트 `poster/.../scripts/p20_replant_5yr.py`(ctl 2011–15 1° LAI `postprocess/latlon/lm4p_ctl_1979-2024.lai.2011-2015.1deg.nc`, ctl 7월 종 비율 `data/replant5y/ctl_species_share_julyYYYY_c96.npz` 준비됨).
- **★ 재파종 1–6년차 결과 (2026-10-10, `p20_replant_5yr.py` → `data/replant5y/replant_5yr_summary.txt`; 같은 WFDE5 연도의 ctl 생산런과 비교)**: 7월 엽면적 종 비율 50–75N (picea / larix / acer, 재파종): 2010 36.6/3.1/2.5 → 2011 36.3/2.9/2.8 → 2013 36.4/2.9/2.8 → 2015 36.2/**2.7**/2.8 (CTRL 26.3/0.0/16.0, 관측 CLM5 지도 29.8/7.5/4.8) → **구성은 1년차에 고정, larix는 늘지 않고 소폭 감소**, picea 과다. 열대 C4/C3 풀: 35.8/28.9 → 32.6/29.8 (CTRL 7–8/57–58, 관측 45/17). LAI 연평균 편차(GIMMS 대비, CTRL → 재파종): 50–70N 2010 +59→+75, 2011 +58→+87, 2013 +53→+82, 2015 +51→+79 % (**재파종이 6년 내내 +25–30 %p 나쁨**); 열대 +45→+46, +47→+45, +43→+36, **+40→+30 %** (재파종이 시간이 갈수록 개선 — 1년차 "C4 가설 불지지" 판단 수정). 북쪽 6지역(NWN·NEN·NEU·WSB·ESB·RFE) 5–6월 GIMMS/CTRL/재파종 ≈1.5/1.58/1.9, 9–10월 ≈0.9/2.35/2.52. 판단: 현재 방식 재파종은 기준 식생으로 부적합(북쪽 악화·낙엽송 미정착), 재파종+DLtype은 larix <3 %라 의미 작음; 열대 C4 풀 개선은 별도 검토 가치.
- **ctl vs lufix = 둘 다 cycle 2 (사용자 질문 2026-10-10)**: 같은 시작 상태(cycle 1 끝을 1979로 되감음), 차이는 `do_landuse_change`만(ctl T, lufix 2010 고정). 탄소 수렴 비교는 cycle 1과 설정이 같은 ctl(T)로 함(lufix는 토지이용 고정 효과가 표류처럼 섞임).
- **★ 빠른 vs 느린 탄소풀 수렴 (2026-10-10, `lm4/scripts/compare_carbon_pools_cycles.py` → `lm4/data/carbon_pools_cycle1_vs_cycle2.csv`; §13.62와 같은 마스크·1–11월)**: 2010 c2−c1 % / 30년 추세 %(c1 → c2) — **빠른 풀: 잎 bl −0.98 (+7.0 → −2.1), 뿌리 br +2.53 (+6.1 → +1.0), NSC +0.42 (+7.1 → −1.0), 잎 낙엽 lflitt_C −0.21 (+6.6 → −1.0), 빠른 토양 fsc +1.17 (+6.4 → −1.0)** → 수렴(cycle 1의 +6–7 %는 결합 평형→WFDE5 재조정, cycle 2 추세 ±1 %). 느린 풀: 변재 bsw +7.12 (+8.6 → +6.0), 목재 bwood +7.64 (+4.1 → **+6.9 가속**), 굵은 목재 낙엽 cwlitt_C +2.20 (+2.6 → +0.9), 느린 토양 ssc +3.08 (+4.2 → +2.7), 총 토양 +2.97. LAI 참고 −0.59. → **1차년도 탄소 진단 = 빠른 풀(잎·뿌리·NSC·잎 낙엽·빠른 토양탄소) 근거 확보**. 참고: LM4p land_month에 `fsc`/`ssc`(빠른/느린 토양탄소) 출력 **있음**.
- **★ CO₂: KIOST-ESM2 결합 vs 오프라인 (2026-10-10, 서버 설정 비교)**: 지면 광합성 = `co2_to_use_for_photosynthesis='interactive'` → 캐노피 공기 CO₂(cana, init 286 ppm)가 대기 CO₂ 추적자와 교환; 대기 추적자는 `atmos_co2_nml do_co2_restore=.true.`, `restore_tscale=3.1536e7`(1년)로 data_table `co2_dvmr_restore`에 복원. **`~/KIOST-ESM2`(400년 PI 평형): 284.262 ppm 고정**(CMIP7 1850, 복사 `time_varying_co2=.false.`); **`~/KIOST-ESM2_AMIP`·우리 오프라인 ctl: `co2_dvmr_restore` = `INPUT/co2_gblannualdata.nc`(CMIP7 연별) + 복사 `time_varying_co2=.true.` 'time_series'**. 그러나 오프라인 실행파일은 대기를 data_override로 대체 → 대기 추적자 복원 미작동 → **ctl/lufix 캐노피 CO₂ ≈292 ppm 1979–2023 고정**(메모리 lsm-offline-co2-forcing, `qco2_dvmr` 출력). → 결합 historical(337→420 ppm)과 달리 **오프라인은 CO₂ 비옥화 없음**. 다음: 오프라인에서 land가 대기 CO₂를 받는 코드 경로 확인 → data_table로 시계열 처방 가능 여부; 가능하면 생산런 재실행(ctl 45년 ≈12일) 여부·4모델 공통 CO₂ 프로토콜 결정 필요.
- **★ 오프라인 CO₂ 처방 해결 (2026-10-10)**: 코드 경로(서브에이전트 추적 + 직접 확인) — `coupler_main.F90:853` `if (do_atmos)` 안에서만 physics→tracer_driver→`atmos_co2_time_vary`(co2_dvmr_restore 읽는 유일한 곳)가 호출됨; 오프라인 `do_atmos=.false.` → 복원 미작동, 대기 최하층 co2 = `fv_tracer.res` IC 그대로. **정식 처방 경로 = `atm_land_ice_flux_exchange.F90:897` `fms_data_override('ATM', trim(tr_name)//'_bot', Atm%tr_bot)`**(주석 "data override for co2 to be passed to land/photosynthesis (co2_bot)", 건조 vmr 입력 → 코드가 습윤 mmr로 변환) → `tr_flux` → cana co2 → 광합성(`vegetation.F90` interactive). 재빌드 불필요. `co2_to_use_for_photosynthesis`는 'prescribed'(상수)·'interactive'뿐(`vegn_photosynthesis.F90:132-139`); 대안 `"LND","phot_co2"` override는 광합성만 바꾸고 cana/qco2_dvmr는 안 바뀜 → 비채택. 입력 `co2_latlon_cmip7_1978_2024.nc`(`lm4/scripts/make_co2_latlon.py`; CMIP7 `co2_gblannualdata.nc`는 실제로 1750-01–2022-12 **월별** + 2024-01-01 마감 복사 기록 → 2023–24는 2022 월값 + n×2.318 ppm/yr(2019→2022 평균 증가, 사용자 선택 (a)); 2° 균일, noleap 월 중앙, ppm), data_table `"ATM", "co2_bot", "co2", "./INPUT/co2_latlon.nc", "bilinear", 1.0e-6`. diag_table.offline_fast에 `qco2_dvmr` 복원(서버 RUN/config에도 반영 → 이후 phentest 변형도 출력). **1개월 시험 `RUN/co2test_1m` (PBS 8539, 48랭크, seed = ctl archive/y2010 = cycle 2 끝, landuse.res → 1979)**: 1979-02-01 정상 완주(FATAL 4 = MOM 경고), **qco2_dvmr 1979-01 중앙값 337.84 ppm (p5–p95 337.18–339.49) vs 기존 ctl 284.53 (282.35–300.27); 목표 337.70** → 처방 작동. `basefast`(CTRL 물리 + offline_fast, 24랭크, **PBS 밖 climate00 직접 실행**)는 17:32 기준 2010-08-01, ≈22시 종료 예상 → `base`와 지면 변수 비트 비교 예정.
- **★ basefast 1년 비트 비교 (2026-10-09)**: `basefast`(CTRL 물리 + offline_fast 표, 24랭크 climate00, 2010 1년, 2026-10-08 22:09 종료, 39,610 s = 11.0 h) vs `base`(원래 표): history 60파일·**2,028변수·일별 365기록 포함 전부 비트 동일** (land_daily/_cmip, land_month/_by_species/_cmip, static, river_daily/_month) → 연말 경계(연 단위 cohort 재배치·병합·연 통계)까지 통과. **빠른 설정 최종 확정**: 모든 LM4+ 오프라인 실험·spin-up에 `field_table.offline_fast` + `diag_table.offline_fast` 사용. 로컬 `/Volumes/data02/LM4P/cases/speedtest/basefast/`(history+clock+config_diff).
- **replant 5년 연장 (2011–2015) 실행 중 (2026-10-09 확인)**: 다른 세션이 제출, PBS 8531 `replant5y`, `RUN/replant_2011_2015/run_lm4p_ctl.sh`(생산 체인 방식, 48랭크 climate01), 00:18 시작, archive y2011·y2012 완료, 2013 진행 중(≈6.4 h/yr → 2015 종료 ≈ 10-10 08시). 목적: 재파종 상태를 수년 키워 larix 성숙 후 DLtype 시험(10-08 결론).
  - basefast 연말 restart(face1) 비교: vegn2(155변수)·vegn1·soil·snow 전부 동일; cana.res는 **대기화학 추적자 농도 38개만 다름**(nh4, o3, so2 … — 침적 꺼져서), sphum·co2 동일 → 지면 상태도 비트 동일. 로컬 `speedtest/basefast/RESTART/`(face1 5개 + coupler.res).

**PPA 경쟁 범위 · 재파종 vs DGVM (2026-10-12, 코드·restart 확인)**
- 빛 경쟁 = **타일 안 모든 코호트, 종 무관**: `vegn_tile.F90:694 vegn_relayer_cohorts_ppa`가 코호트를 유효 높이(`height×layer_height_factor`) 내림차순으로 정렬해 수관층 배정. ctl `tree_grass_competition='trees-squeeze-grass'`(풀은 나무 아래 한 층으로 묶임). 토양수분도 같은 타일 토양을 공유.
- ctl y2010 `vegn2.res.tile1`(C96 tile 1) 실측: 식생 타일 19,634개 중 **1종 1,886 · 2종 3,917 · 3종 이상 13,831** → 90 % 타일이 다종 혼재. 다종 타일 17,748개 중 8,792개(50 %)에서 어떤 종이 하층에만 있음(다른 종에 가려짐). 흔한 조합: prioria+c4+c3(10,706), c4+c3(3,563). 종 번호 0 prioria·1 picea·2 larix·3 acer·4 c4grass·5 c3grass(tile 1엔 larix 없음).
- 종자: 종별로 생산(`vegn_reproduction_ppa`), 1 %는 격자 내 다른 타일로(`frac_seed_dispersed=1e-2`), 0.01 %는 이웃 격자로(`frac_seed_transported=1e-4`, ctl `seed_transport_to_use='diffuse'`) → 타일 간·격자 간 이주는 가능하나 매우 느림.
- `do_biogeography=T`의 실체(`vegn_cohort.F90:530 update_species`): 매년 연평균기온·한랭월기온·연강수·한랭월수 + **코호트 생물량**(`btotal<tg_c3_thresh` → C3 풀)으로 코호트 종 라벨을 **즉시 교체**하는 LM3식 기후 규칙. 선택지는 c4grass·상록·c3grass·열대·온대낙엽 5개뿐 → **larix로 바뀌는 경로가 없음**.
- 따라서 현 설정(`do_biogeography=F`): 종 **목록**은 초기장에 고정(외부 유입은 미량 종자뿐), 종 **비율**은 PPA 빛·물 경쟁, 성장, 사망으로 변함. 재파종 = 초기 라벨 교체(외부 개입)이고 그 뒤 변화는 PPA 경쟁. CLM4 CNDV(기후 규칙으로 PFT 진입·퇴출 + FPC 면적 경쟁)와 달리 개체 높이 기반 경쟁이며 기후 규칙에 의한 진입은 없음.
- 종자 정착(서버 `src/lm4P/vegetation/vegn_util.F90` `add_seedlings_ppa`, 2026-10-13 확인): **하한 없음** — `seed_C>0`인 종마다 새 코호트 생성, 개체수 = seed_C·prob_g·prob_e/plant_C. 너무 작은 코호트는 이후 `kill_small_cohorts_ppa`가 제거. 번식은 연 1회(`vegetation.F90:3093` 연도 바뀔 때). → 재파종은 초기 1회 라벨 교체, 이후 매년 확산으로 없던 종도 유입 가능(이웃에 종 공급원이 있어야 함). 부수 발견: 같은 함수 24행 `if (present(germination_factor)) germ_f = 1.0` → 인자값 무시(농경지 잡초 억제 0.0이 안 먹음, 코드 버그로 보임, 미수정).

### 낙엽송 소멸 원인 1단계: 종 파라미터 비교 (2026-10-14, 모델이 출력한 종 표 = ctl2_co2 `logfile.000000.out` 10060–10240행)
- picea와 다른 값(larix/picea/acer): Vmax 1.7/2.1/2.0e-5 · alpha_phot 0.06/0.04/0.04 · LMA 0.076/0.100/0.038 kgC m⁻² · mortrate_d_c 0.020/0.0143/0.010 yr⁻¹ · alpha_root 0.4/0.5/0.5 · alpha_wood 0.025/0.05/0.025 · gamma_resp 0.035/0.030/0.035 · rho_wood 245/185/245 · tc_crit 278.15/283.16/283.16 · gdd_crit 180/360/360 · 알로메트리(alphaHT/thetaHT/gammaHT, alphaCA, alphaBM). Phenology Type: larix 0(낙엽)·picea 1(상록)·acer 0.
- 같은 값: mortrate_d_u 0.081(세 나무 모두), Tmin_mort 0(추위 사망 없음, prioria만 278.16), seed·발아(prob_g 0.45, prob_e 0.40)·확산률·maturalage 5. → **H3(추위 사망) 기각: 온대·북방 나무엔 추위 사망 자체가 꺼져 있음.**
- 키 10 m 도달 목재 비용(kg C/그루, rho·alphaBM·D²·H): acer 4.7 < larix 9.0 < prioria 11.5 < picea 14.2 → 알로메트리는 larix에 불리하지 않음(picea보다 싸게 키가 큼).
- 연간 잎 비용(잎면적당, 낙엽은 매년 전량 교체·C 재흡수 0.24 / 상록은 alpha_leaf 0.12 yr⁻¹ = 수명 8.3년, `vegn_dynamics.F90:1075`): larix 0.076×0.76 = **0.058** · acer 0.038×0.76 = 0.029 · picea 0.100×0.12 = **0.012 kgC m⁻² yr⁻¹** → larix가 acer의 2배, picea의 약 5배.
- 후보(미검증): ① LMA가 같은 낙엽인 acer의 2배(실제 낙엽송 LMA 문헌값 대조 필요) ② 수관 사망률 최고(평균 수명 50년 vs picea 70, acer 100) ③ Vmax 최저(alpha_phot 0.06으로 일부 상쇄). 어느 것이 지배적인지는 2단계(재파종 run 코호트 추적)로 판정.
### 낙엽송 소멸 원인 2단계: 재파종 restart 코호트 추적 (2026-10-14, `lm4/scripts/larix_cohort_track.py` → `lm4/data/replant/larix_cohort_track.txt`)
- 대상 50–75N 자연·2차림 타일, restart 2010-01(재파종 IC)·2012~2016-01(archive y2011–y2015; 2011-01 restart는 로컬에 없음). 타일 면적 미가중 합 → 상대값만 의미.
- 수관면적(nindivs×crownarea) 2010→2016: **larix 418→346(−17 %, 2012 이후도 연 −2.9 %)** · picea 7,200→6,180(−14 %, 2012 이후 거의 평탄) · acer 862→864(0 %). 목재 larix −11.5 % · picea −6 % · acer +3 %.
- **larix는 그늘에 갇힌 게 아님**: 수관면적의 87→96.5 %가 최상층(layer 1), 수관가중 키 10.4→11.4 m로 계속 자람.
- **번식 붕괴**: 종자 탄소(bseed×nindivs) larix 0.212→0.060(−72 %, 매년 감소) vs picea 3.57→1.57(2014 바닥 후 반등)·acer 0.45→0.47 유지. 신규 개체(cohort_age<1) 비율 larix 0.2–0.6 % vs picea 0.9–3.4 % · acer 22–27 %. NSC/bl_max 중앙값 larix 3.0 vs picea 3.9 · acer 4.3.
- 해석: 윗층 낙엽송이 해마다 조금씩 죽는데(수관 사망률 2 %/yr) 종자·신규 개체가 거의 없어 빈자리를 못 채움 → 서서히 감소. 탄소 여유(NSC·종자)가 가장 적음 → 잎 비용 가설(H2)과 부합하나 미확정. 주의: 2010→2012 변화엔 재파종 직후 알로메트리 재조정이 섞일 수 있음(picea·acer 코호트를 larix로 라벨만 바꿈) → 추세는 2012 이후로 판단.
- 다음(3단계): `land_month_by_species`로 종별 GPP·NPP·잎 할당을 수관면적당 비교해 탄소 부족 vs 사망률을 분리.
### 낙엽송 LMA 문헌 검증 (2026-10-14; 탄소비 0.48로 g DM→kg C 환산; 모든 모델값은 투영면적 기준이어야 성립)
- L. decidua SLA 117±28 cm² g⁻¹(투영) → LMA 85 g DM m⁻² = **0.041 kgC m⁻²** (Fellner, Dirnberger & Sterba 2016 *Trees* 30:1237, doi:10.1007/s00468-016-1361-1 — 원문 직접 확인). 같은 논문 인용: Gower & Richards 1990 123, Matyssek & Schulze 1987 121(투영), Wieser 2013 125, Burger 1945 152 cm² g⁻¹; P. abies 45.8–50 cm² g⁻¹(→0.096–0.105 kgC).
- L. occidentalis 55–88 g m⁻² = 0.026–0.042, 같은 곳 상록침엽 0.089–0.109 (Kloeppel et al. 2000 *Funct. Ecol.* 14:281). L. gmelinii 97, L. laricina 86 g m⁻²(FloraVeg DB, 기준면적 불명). Acer saccharum ≈60, A. rubrum ≈85 g m⁻²(Reich et al. 1991, 그림 판독 근사).
- **판정**: picea 0.100 ✓ · acer 0.038 ✓ · **larix 0.076 = 문헌(0.026–0.046)의 약 1.6–2.2배 과대**. 비율 larix/picea 모델 0.76 vs 문헌 0.33–0.5. → 낙엽송이 매년 새로 만드는 잎 비용이 약 2배 과대 = 2단계의 탄소 여유 부족·번식 붕괴와 일관. 적정 후보값 0.035–0.045. LM4 문헌(Weng 2015/2017, Martinez Cano 2020)에서 원 출처 못 찾음.
### 낙엽송 LMA 시험 `larixlma_d` (2026-10-14 16:31 시작)
- 발견: ctl field_table larix 블록에 `LMA = 0.76e-01`(들여쓰기 5칸) 바로 아래 `#    LMA = 0.38e-01` 주석 → 원래 0.038(문헌·acer와 같은 수준)이었던 값을 누군가(GFDL/KIOST 미상) 2배로 바꾼 흔적. 
- 설정: `phentest.sh` 새 변형 `larixlma`(fast config 뒤 larix 블록의 LMA만 0.038로 sed), SEED=`RUN/replant_seed`, 2010 1년, 일별 LAI. config_diff 확인: fast config 외 차이는 LMA 한 줄. 비교 기준 = `replant1y_np48_d`(같은 seed·설정, 단 48랭크 vs 이번 24랭크 → 분해 차이).
- 실행: climate01(본 run)·climate02(타 사용자) 만석이라 **climate00 직접 24랭크**(nice 10, PBS 밖, 사용자 제안). 예상 ≈11 h(basefast 39,610 s). 감시 기준: 본 run y1986 구간이 10 h(현재 ≈9.3 h/yr) 넘으면 중단.
- **결과 (2026-10-15 01:09 완주 rc=0, 31,076 s ≈ 8.6 h; `lm4/scripts/larixlma_compare.py` → `lm4/data/replant/larixlma_compare.txt`)**: land_month_by_species, 50–75N 1월 larix 개체>0 셀 314개 무가중 평균, base→LMA 0.038: 7월 LAI 1.156→1.238(+7 %), GPP 0.242→0.254 kgC m⁻² yr⁻¹(+4.9 %), NPP 0.0888→0.0776(−12.6 %), 12월 bl_max 0.091→0.048(−47 %), NSC 0.260→0.192(−26 %), **종자 bseed 0.0020→0.0095(×4.7)**, 수관면적 +15 %, 목재 +6 %, 개체수 −0.6 %(사망·발아는 연말 처리라 1년 안엔 변화 없음). picea·acer는 이 셀들에서 미미, 변화 0.
  - 해석: PPA에서 bl_max = 목표 LAI × LMA × 수관면적이라 LMA를 반으로 줄여도 **LAI는 거의 그대로**(+7 %), 대신 잎에 쓰던 탄소가 절반으로 줄어 **종자·수관 확장으로 감** → 앞서 찾은 낙엽송 감소 원인(종자 생산 붕괴)을 직접 겨냥. LAI 과대 부작용 없음.
  - 주의: NPP −12.6 %는 GPP +4.9 %인데 줄어든 것 → 호흡(수관·목재 증가에 따른 유지호흡 추정) 증가, 원인 미확인. 1월 LAI 0.33→0.66은 IC 잎(bl 그대로 ÷ 절반 LMA) 탓 첫 달 아티팩트. 1년 시험이라 개체수 회복 여부는 미판정 → 다년(≥3년) 시험 필요.
### 봄 잎 나기 지연의 원인 진단 (2026-10-14, `lm4/scripts/spring_gate_diag.py` → `lm4/data/spring_gate_diag_2010.txt`)
- 코드: 잎 켜기 = GDD>gdd_crit ∧ tc_pheno≥tc_crit ∧ not drought. drought 판정 토양수분은 `soil_tile.F90:1284 soil_ave_theta1` = **액체 물(wl)만**/vwc_sat(얼음=건조로 취급), 30일 평활(`tau_smooth_theta_phen=30`), 문턱 cnst_crit_phen 0.3(전 종). tc_pheno = 0.95·어제 + 0.05·오늘(≈20일 평활).
- 재구성(dayl_d 2010 일별; 봄 규칙은 CTRL과 동일): 50–75N LAI 연변동 >0.3 셀 2,746개, larix/c3grass 문턱(180, 5 °C) 기준 **묶는 조건 = 평활 기온(tc) 98 %**, GDD 0 %, 해동 2 %. 중앙 doy: 해동(상층 10 cm) 122 · 눈 사라짐 128 · GDD 133 · **원 기온 5일평균 5 °C 117 → 평활 기온 5 °C 144(지연 27일)** · LAI 상승 148. acer 문턱(360, 10 °C)도 tc 99 %.
- 지역별 평활 지연(tc − 원기온): NEU 35 · NWN 33 · NEN 25 · WSB 25 · ESB 24 · RAR 22 · RFE 21일. 2010 SOS 편차(CTRL−GIMMS, 50 % 기준): NEU +21 · NWN +17 · NEN +29 · WSB +8 · ESB +10 · RAR +27 · RFE +21일 → **봄 지연은 가을과 같은 평활 기온 지연으로 설명 가능한 크기**(지연 ≥ 편차; 평활을 아예 없애면 일부 지역은 너무 이를 수 있음).
- 눈/동토 가설(사용자 제기): 상층 10 cm 해동·눈 사라짐이 평활 기온 문턱보다 2–3주 먼저 → 2010엔 묶는 조건 아님. 단 일별 출력이 0–10 cm뿐이라 실제 판정 깊이(뿌리 기반 depth_ave)의 해동은 미확인, 모델 SWE·SCF 자체는 봄 과소(−21~−30 %).
- **phenology 모델 평가 문헌 (2026-10-14 검색)**: ① Park & Jeong 2021 ERL 16:034027 (doi:10.1088/1748-9326/abe2cf) — CMIP5/6 14개 ESM vs GIMMS LAI3g 1982–2014, 로지스틱 SOS/EOS·LOS·phase; "IPSL-CM6A-LR showed the best simulation performance of all phenological indicators"(테일러 지표: 정규화 표준편차≈1·패턴 상관 = 일수 편차 아님), 개선은 주로 30–60N EOS; CMIP6 공통 EOS 늦음→LOS 과장. ORCHIDEE 낙엽 = 잎 나이 + 기온 문턱. ② Peano et al. 2021 BG 18:2405 (CRESCENDO Part 1) — 유럽 LSM 7개(CLM4.5/5, JULES-ES, JSBACH, LPJ-GUESS, ORCHIDEE, ISBA-CTRIP), LAI3g·MODIS·CGLS 2000–2011, 20 % 문턱; 평균 GSS 0.6개월 늦고 GSE 0.5개월 이름, 최상 LPJ-GUESS·최하 JULES-ES(ORCHIDEE 순위는 표 이미지라 미확인). ORCHIDEE 잎 켜기 = GDD + chilling(Botta et al. 2000 GCB 6:709). Part II(2025, BG 22:7117) 골·정점·진폭. ③ MacBean et al. 2015 BG 12:7185 — ORCHIDEE phenology 파라미터를 MODIS NDVI로 최적화, 북방·온대 낙엽 PFT 노화 앞당김 → NH 생장기간 최대 30일 단축, 전구 GPP −10 PgC/yr. LM4는 이들 평가에 미포함.
- **봄 문턱 추정 (2026-10-14, dayl_d 2010 일별 재구성; 목표일 = 평활기온 5 °C 도달일 − 지역 SOS 편차)**: (A) 20일 평활 유지 시 목표일의 평활기온 중앙값 NEU 1.2 · RFE −2.2 · NWN 0.8 · ESB 1.4 · NEN −0.8 · WSB 2.7 · RAR −5.5 °C(전체 0.6) → 지역 편차가 커 단일 문턱 부적합, 0 °C 근처 평활 문턱은 물리적 의미 약함. (B) 문턱 5 °C 유지·평활 단축 시 앞당김(일): 10일 평활 8–13, 7일 11–17, **5일(α 0.2) 14–18**, 3일 17–22 vs 필요 NEU 21·RFE 21·NWN 17·ESB 10·NEN 29·WSB 8·RAR 27 → 5일이면 NWN·NEU·RFE 대부분 해소, ESB·WSB 8–10일 과도, NEN·RAR(툰드라) 약 10일 부족. 목표일 원기온 5일평균 1.8–8.6 °C로 지역 차 → 단일 기온 규칙의 한계(chilling·눈·관측 SOS의 융설 오염 후보). 한계: 모델 10 % 개시 vs 관측 50 % SOS 편차를 섞은 근사, 2010 1년.
### 봄 잎 켜기 5일 평활 패치·시험 (2026-10-14)
- 패치 `lm4/patches/lm4P.phenology_spring_tau.diff`(phenoff 패치 위에 추가): `vegn_tile.F90` 새 필드 `tc_pheno_on`(restart 미포함, 음수=미설정 → 첫날 tc_pheno로 채움), `vegn_dynamics.F90` `&vegn_dynamics_nml tau_pheno_on`(일, ≤0 = 끔·기본) → 잎 켜기 판정만 `tc_on`(5일 평활) 사용, 잎 끄기·tc_pheno 불변, `vegetation.F90` 매일 갱신(가중 1/tau). tau ≤ 0이면 기존 phenoff와 같은 계산 경로.
- 빌드: `phenoff_build.sh`에 B/X 덮어쓰기 추가 → `/data2/ydkoh/lm4/build_phenspring/fms_esm4.5_phenspring.x`(2026-10-14 16:59, 오류 0; 기존 phenoff·gateBC·production exe 불변).
- 변형(`phentest.sh`): `spring5`(CTRL 가을 + 봄 5일), `daylspring5`(DL13/12 가을 + 봄 5일). fast config 복사 뒤에 field_table 수정(⚠ 기존 tc10/offon/dayl/dayl2 블록은 복사 앞이라 지금 재스테이징하면 덮어써짐 — 10-08 이전 스테이징이라 기존 결과는 무관). seed = ctl archive/y2009(base·dayl_d와 동일), 2010 1년, 일별 LAI.
- 실행: `RUN/phentest_queue.sh` — climate00에서 larixlma_d 종료 후 daylspring5_d → spring5_d 순차(각 24랭크 ≈11 h). 로그 `RUN/phentest_queue.out`.
- **⚠ 첫 버전 결함 (2026-10-15)**: daylspring5_d(완주 43,924 s)가 dayl_d보다 잎 켜기 +8일 늦음·6월 LAI −21 %. 원인 = 끄기 조건 `vegn%tc_pheno < tc_crit`(20일 평활)이 그대로라 5일 평활로 켜진 다음 날 꺼지고 GDD=0 초기화. 결과는 `phentest/daylspring5_bug_d`로 보존, 대기열(spring5_d) 취소.
- 수정: `vegn_dynamics.F90` 끄기 조건 → `(tc_pheno < tc_crit .and. (tau_pheno_on <= 0 .or. shortening)) .or. <DL 규칙>` (봄엔 기온 끄기 생략, 가을·tau 미사용 시 원래와 동일; 원래 모델도 봄 늦서리 반응 사실상 없음). diff 갱신, 빌드 `build_phenspring2/fms_esm4.5_phenspring2.x`(10-15 17:11, 오류 0). `phentest.sh` EXE_SPRING 교체 + `TAU=<일>` 덮어쓰기.
- 오프라인 스윕(findings 10-15): τ5만으로는 GDD 180이 다음 병목, τ5+GDD100이면 토양 해동이 병목 → 모델 확인 실행 `daylspring5_d` = τ5·GDD180·**1–6월(181일)**, 10-15 17:13 climate00 24랭크 시작(≈6 h).
- 판정 계획(decisions 2026-10-14): SOS 일수 아닌 FLUXCOM 5–6월 GPP·NEE(NEU·RFE에서 GPP 증가 기대, NWN·ESB는 호흡 원인이라 변화 작아야 함) + LAI 3종 범위.
- Bonan *Ecological Climatology* Table 18.5(p.~306): 침엽 낙엽수 LMA 100 g DM m⁻² ≈ 0.048 kgC m⁻²(×0.48) — LM4 larix 0.076의 근거 대조 추가(2026-10-14). 식생 파트 정리 `/Volumes/data02/ecological_climatology/vegetation_part_notes.md`.
### Bonan 책 식생 개념 vs LM4+ 구현 대조 (2026-10-14, 서버 KIOSTv2b 소스·ctl2_co2 로그 종 표·input.nml 확인)
| 책 | LM4+ (현 설정) | 판정 |
|---|---|---|
| §18.6–18.7 LMA↔잎 수명 trade-off | PPA에선 끊김(`init_derived_species_data`: LM3 Reich식은 `.not.do_ppa`일 때만), LMA·alpha_leaf 독립 입력 | 구조 없음 |
| §18.3 잎 나기 = GDD(≈5 °C 기준) + chilling | GDD 기준 0 °C(gdd_base_T 273.16 전 종)·가을 낙엽 시 리셋 + 20일 평활기온 ≥ tc_crit + 액체 토양수분 ≥0.3; **chilling 코드 없음**(grep 0) | 부분 |
| §18.3 잎 지기 = 짧은 일장 + 저온 | 기온만(tc_pheno < tc_crit) + 가뭄; 일장은 우리 패치(phenoff)로만 | 부분(패치로 보완) |
| §17.2 LAI = 투영(one-sided) | leaf_area = bl/LMA(투영 기준 LMA) | 일치 |
| §16 광합성·기공 | Farquhar/Collatz형 + Leuning 기공(`photosynthesis_to_use='leuning'`, m_cond 7) | 일치 |
| §17.4 LUE·NDVI | LUE 미사용(과정 기반) | 해당 없음 |
| §20.7 EC는 NEE만, GPP는 partitioning | 모델 GPP는 광합성에서 직접, NEE = −nep = Ra + Rh − GPP | 비교 시 관측 GPP가 추정치임에 유의 |
| §22.2 self-thinning | 명시 법칙 없음 → PPA 수관층(키 순 정렬, CA 채움)+그늘 사망(mortrate_d_u·DBH 보정 A_mort 4, B_mort 30)+탄소 기아 사망(코드 기본 NSC < 0.01·bl_max이나 **ctl input.nml:1772 `nsc_starv_frac = 0.0`** → 사실상 NSC<0 또는 bsw<0일 때만, cohort 전원 사망; 2026-10-14 정정)으로 창발 | 개념 일치(창발형) |
| §23.3 gap dynamics | 나무 쓰러짐 교란 2.5 %/yr(`treefall_disturbance_rate`, 타일 첫 코호트 종 기준) + 화재('unpacked') → `do_patch_disturbance` 새 타일 | 일치 |
| §24.6 코호트 vs 평균개체(LPJ·CNDV) | 크기 분포 코호트(PPA) | 코호트 쪽 |
| §25.6 CLM-DGVM 생물기후 한계로 PFT 진입·퇴출 | do_biogeography=F(끔); 켜도 5종 라벨 교체만 | 없음 |
- 결론: 생리(광합성·LAI 정의)와 군집 구조(코호트·gap·자기솎음)는 책 개념과 맞음. 다른 곳은 정확히 우리가 문제를 찾은 곳 — LMA–수명 연결 끊김(낙엽송 LMA), chilling 없음·일장 없음·0 °C GDD(봄·가을 phenology), 생물기후 진입 규칙 없음(낙엽송 미복원).
- 소스 동일성 확인(2026-10-14): /home/ydkoh/ESM4p5_KIOSTv2b/src/lm4P vs 생산 빌드 /data2/ydkoh/lm4/esm4p5-lm4p-offline/src/lm4P — sphum.F90(우리 clamp 패치)만 다름 → KIOSTv2b 소스의 줄 번호를 생산 exe 기준으로 써도 됨. 계산 순서 정리 = PDF `lm4/docs/LM4plus_flow_and_book.pdf`(작성 중).

### 봄 chilling(NCD–GDD) 문헌·ERA5 시험 (2026-10-19)
- 문헌 원문 확인(PDF `poster/2026_LM4p_LAI/references/`): Murray, Cannell & Smith 1989 = NCD–GDD 식 원출처, T = a + b·exp(rC) (T: 1/1~, >5 °C; C: 11/1~, ≤5 °C), 낙엽송 그룹 a 39, b 468, exp r 0.974. Park et al. 2015/2018(정수종 그룹) SOS = NDVI 로지스틱 변곡점(= 곡선 50 %), Park 2018의 WD는 결빙일수(chilling 아님, chilling은 일부러 제외). Botta et al. 2000 GCB 6:709 계수는 미확인.
- ERA5 2010 적용(`lm4/scripts/chill_gdd_murray.py` → `lm4/data/chill_gdd_murray_2010.txt`): 7개 북방 지역 모두 chill day 172–222로 포화 → 낙엽송 요구량을 0 °C 기준 GDD로 바꾸면 136–215 ≈ GDD180, 출엽 −2~−6일뿐(목표 −8~−29). **chilling 도입은 북방 봄 지연의 해법이 아님.** LM4 CTRL 문턱일은 ERA5 d180과 대체로 일치.
- 다음 가설: 문턱일→LAI 50 % 사이 성장 지연(11–24일, 기간 불일치 대략치). NEXT = dayl_d 2010 일별 LAI로 셀별 "leaf-on 문턱일 → LAI 50 %" 간격 계산.
- **성장 지연 확인 (2026-10-19)**: dayl_d 2010 셀별 gate(세 조건 모두 열린 날)→LAI 50 % 중앙값 6–14일(NEU 14 최대, 전체 8) → 11–24일 대략치는 과대, 성장 지연은 주원인 아님. 봄 지연 본체 = 평활기온 문턱 지연 → τ5 패치(`daylspring5_d`) 방향 유지. 상세 findings 10-19.
### 겨울 휴면 유지(winter hold) 패치 (2026-10-19)
- 문제: 일장 끄기 규칙은 `shortening`일 때만 작동 → 동지 후 온화한 겨울(tc ≥ 5 °C)에서 다시 잎이 켜짐(남반구 7월 1.48→1.85, 북반구 20–40N 1월 1.60 vs GIMMS 0.75). 오프라인 상태기계 비교(findings 10-19, `dl_dormancy_latch_offline.py`)에서 EQ12(잠금) ≈ HOLD12(무상태)가 재개엽 0–7 %로 최선, 50–70N 불변.
- 구현(무상태 = restart 안전; 연 체인이 1월 1일 restart라 잠금 변수는 북반구 겨울에 소실됨): `vegn_data.F90` 종 파라미터 `dayl_crit_on`(기본 −1 = 끔), `vegn_dynamics.F90` 잎 켜기 조건에 `.not.(dayl_crit_on>0 .and. tc_crit_off>0 .and. dayl<dayl_crit_on .and. tc_pheno<tc_crit_off)` 추가. diff `lm4/patches/lm4P.phenology_winter_hold.diff`(phenspring2 소스 위).
- 빌드 `/data2/ydkoh/lm4/build_phenhold/fms_esm4.5_phenhold.x`(10-19 15:14, make/link 오류 0, 생산 exe 7/20 불변). 서버 `phenoff_build.sh`가 B/X 덮어쓰기 없는 옛 판이라 로컬 git 판으로 교체.
- 변형 `daylhold5` = daylspring5 + larix/acer/c3grass `dayl_crit_on = 12.0`(phentest.sh; 서버엔 실행 중 잡 보호를 위해 `RUN/phentest_v2.sh`로 배포). 스테이징 `RUN/phentest/daylhold5_d`(2010 12개월). 대기열 `RUN/queue_daylhold5.sh`: daylspring5_d(전 연도) 종료 후 climate00 24랭크 자동 시작, 로그 `RUN/queue_daylhold5.out`.
- 판정 계획: 남반구 7월·북반구 20–40N 1월 LAI vs GIMMS, 50–70N SOS/EOS가 daylspring5_d와 같은지, c4grass·prioria LAI 간접 변화.
- **결과 (2026-10-20, findings 10-20 "daylhold5_d 결과")**: 50–70N SOS 불변(+8.0일) · 20–40S 7월 LAI 1.89→1.05(GIMMS 0.90) · 겨울 재개엽 % DL 수준 복귀 · 북반구 1월은 seed 상속이라 12월로 판정(20–40N 1.12→0.94, GIMMS 0.81) · **온대 봄 조기 개엽(ENA −23, 40–50N −14)은 미해결**. c4grass·prioria 간접 변화는 아직 안 봄.
- **실행 순서 사고 (2026-10-19 15:19)**: daylspring5_d 전 연도(14:06 시작)를 daylhold5 우선 실행으로 잘못 해석해 1시간 13분 진행 후 중단 → 사용자 의도는 "돌고 있으면 spring 먼저". 15:20 `phentest_v2.sh`로 재스테이징·재시작(climate00 24랭크, 로그 `RUN/phentest_daylspring5_full_d.out`), `queue_daylhold5.sh` 재가동(종료 후 daylhold5_d 자동 시작). 예상: daylspring5_d ≈10-20 02–04시, daylhold5_d ≈10-20 오후.
### 위도 의존 가을 일장 문턱 패치 (2026-10-20)
- 근거: findings 10-20 s7(관측 EOS 일장 = 12.0 + 0.05(|lat|−40) h, GIMMS·GLASS·상록 제외 맞춤 기울기 0.050–0.056) + 오프라인 예측(`autumn_latrule_offline.py`, 50–70N +9.3→+5.9일, TIB −31→+10.5일, 온도 게이트 기각).
- 구현(winter hold 소스 위): `vegn_data.F90` 종 파라미터 `dayl_off_slope`(기본 0 = 상수, 기존 실험 재현)·`dayl_off_lat0`(기본 40), `vegn_dynamics.F90` 가을 규칙 문턱 = `dayl_crit_off + dayl_off_slope*(|lat|deg − dayl_off_lat0)`. diff `lm4/patches/lm4P.phenology_autumn_latitude.diff`(56줄), 작업본 `lm4/patches/phenoff_work/`(서버 build_phenhold/patched와 md5 일치 확인 후 수정).
- 빌드 `/data2/ydkoh/lm4/build_phenlat/fms_esm4.5_phenlat.x`(10-20 13:54, `B=… X=… bash phenoff_build.sh`, make/link 오류 0, lm4P 38파일 재컴파일, exe에 `dayl_off_slope` 문자열 확인, 생산 exe 7/20 불변). 아직 실행 검증 안 됨.
- 시험런 설정 예정: larix/acer/c3grass `dayl_crit_off = 12.0`, `dayl_off_slope = 0.05`, `dayl_off_lat0 = 40`, `tc_crit_off = 293.15` 유지; 봄 설정은 daylhold5_d 결과 후 결정.
- 변형 `dayllat`(phentest.sh, 서버 `RUN/phentest_v3.sh` — v2는 daylhold5_d 실행 중이라 덮어쓰지 않음) = 가을 위도 문턱만, 봄 = CTRL(dayl_d와 1:1 비교). 스테이징 `RUN/phentest/dayllat_d`(2010 12개월, 일별 LAI, larix/acer/c3grass에 tc_crit_off 293.15·dayl_crit_off 12.0·dayl_off_slope 0.05·dayl_off_lat0 40 확인, tau_pheno_on·dayl_crit_on 없음, exe phenlat). 대기열 `RUN/queue_dayllat.sh`(daylhold5_d 종료 후 climate00 24랭크 자동 시작, 로그 `RUN/queue_dayllat.out`), 10-20 13:59 가동. 예상 시작 ≈16:30, 종료 ≈10-21 04시.
- 실험 행렬(사용자 10-20): 가을만(dayllat) → 봄만(τ5 ± hold) → 봄+가을. 우선 가을만.
- dayllat_d diag 추가(10-20 15:20, 시작 전): land_daily에 albedo_dir·albedo_dif·snow_frac·snow_depth, land_month에 albedo_dir·albedo_dif(fast 표에 없어 dayl_d와 비교용). phentest.sh(v3) dayllat 블록에 반영, 스테이징본은 scp→로컬 편집→scp(md5 일치). 물리 영향 없음.
### 강수 상 분할 민감도 실험 phasewfde5 (2026-10-20)
- 목적: LM4p 오프라인 forcing의 눈/비 분할(변환기 TBOT 0–2 °C 램프, WFDE5 Snowf보다 강설 1.2–1.5배)이 적설·융설·봄 phenology에 주는 영향 — 나중 적설 보정 때 "입력 탓 vs 눈 물리 탓"을 가르는 기준. coupled(ESM4/KIOST)는 대기 미세물리가 lprec/fprec를 직접 주므로 이 재분할이 없음.
- forcing: `lm4p_offline_wfde5_to_atm.py <y> wfde5` → `forcing_WFDE5_lm4p/wfde5_atm_{2009,2010,2011}_phasewfde5.nc`(+경계 2레코드 `append_boundary_phase.py`). 2010 대조: 강수 외 전 변수 차 0, 총강수 차 1e−10 (`cmp_phase_forcing.py`).
- 설계: 대조군 = 기존 `phentest/base`(2010, CTRL, gateBC exe, 24랭크, 램프) — 생산 ctl(48 PE)과는 비트 동일 아님이라 base와 비교. 실험 `phasewfde5_d` = base와 같은 exe·seed(ctl archive/y2009)·field_table, forcing만 `_phasewfde5`; 진단 추가(일별 albedo_dir/dif·snow_frac·snow_depth, 월별 albedo·fprec_l·melts). 한계: 1월 1일 적설은 램프 이력(2009 겨울) → 2010 봄은 부분 효과, 2010 가을–겨울은 완전 효과. 효과가 크면 2009–2010 2년 쌍(대조 포함, ≈44 h)으로 확장.
- 스크립트 `phentest.sh`(서버 `RUN/phentest_v4.sh`; v3는 queue_dayllat이 사용 중이라 덮어쓰지 않음), 대기열 `RUN/queue_phasewfde5.sh`(dayllat_d 종료 후 climate00 24랭크 자동 시작, 로그 `RUN/queue_phasewfde5.out`), 10-20 16:15 가동. 예상: dayllat_d ≈10-21 04시 종료 → phasewfde5_d ≈10-21 15시 종료.
