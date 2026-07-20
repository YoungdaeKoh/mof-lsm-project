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
