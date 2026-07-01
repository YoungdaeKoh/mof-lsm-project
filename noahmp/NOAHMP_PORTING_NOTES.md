# Noah-MP v5.2.1 Offline Porting — 작업 로그 & 현황 (2026-06-25)

_climate00 서버. HRLDAS offline driver + Noah-MP v5.2.1 (intel21 serial). 동적식생(DGVM) LSM 3종(CLM5·LM4.1·Noah-MP) 중 마지막._
_**상태: 빌드·smoke test 완료 ✓** — 다음 단계는 2-stage spin-up (§5) → ERA5 실전 forcing (§6)._

## 0. 목표
Noah-MP를 offline(강제) 모드로 climate00에 포팅 → 진단 테스트베드 가동. 최종적으로 ERA5 forcing으로 long spin-up → 평형 RESTART를 본 실험 IC로.

## 1. 모델 구조 — 왜 HRLDAS가 필요한가
`NCAR/noahmp` repo는 **소스 전용** (README 명시: *"only provides the Noah-MP source code... To run offline, users need the host model system"*). offline 실행엔 **HRLDAS** 드라이버 필요.

설치 구조 (`~/HRLDAS/`):
```
~/HRLDAS/                         # = NCAR/hrldas (master)
├── hrldas/                       # HRLDAS 시스템 (빌드 진입점)
│   ├── configure  arch/          # 컴파일러 옵션
│   ├── user_build_options        # ← netcdf 경로 패치본 (§3)
│   ├── run/                      # hrldas.exe, namelist.hrldas, NoahmpTable.TBL, snicar*.nc
│   ├── HRLDAS_forcing/           # GRIB→LDASIN 전처리 (jasper 미빌드, §4)
│   └── docs/                     # README.ERA5 등 forcing별 가이드
├── noahmp/                       # ← submodule, v5.2.1 (commit 17751dc)
│   └── docs/NoahMP_v5_technote.pdf   # 공식 기술문서 (= user guide)
└── build_noahmp_serial.sh        # 재빌드 스크립트 (모듈 로드 포함)
```
- HRLDAS의 `.gitmodules`가 noahmp submodule을 **commit `17751dc` = v5.2.1 태그**로 이미 고정. `git submodule update --init`만 하면 v5.2.1 받아짐.
- Makefile 경로 의존: `noahmp/drivers/hrldas/Makefile`이 `../../../hrldas/user_build_options`를 include → hrldas와 noahmp가 sibling이어야 함 (submodule 구조가 이를 만족).

## 2. 환경 (climate00, CLM5와 동일 intel21 스택)
| 항목 | 값 |
|---|---|
| 컴파일러 | `module load intel21/compiler-21` (ifort 2021.5) |
| NetCDF | `/usr/local/netcdf/4.6.1_intel21` (`module intel21/netcdf-4.6.1`) |
| HDF5 | `module intel21/hdf5-1.10.5` |
| CMake | 불필요 (HRLDAS는 configure+Makefile) |
| 빌드 | serial (MPI 아님 — JULES MPI 실패 전례) |

## 3. 빌드 절차
```bash
cd ~/HRLDAS/hrldas
./configure 3          # 3 = Linux intel serial → arch/user_build_options.ifort.serial 복사
# user_build_options 패치 (NCAR Cheyenne 경로 → climate00):
#   NETCDFMOD = -I/usr/local/netcdf/4.6.1_intel21/include
#   NETCDFLIB = -L/usr/local/netcdf/4.6.1_intel21/lib -lnetcdf -lnetcdff
make NoahMP            # Utility→noahmp/{utility,src,drivers}→urban→IO_code→run(hrldas.exe)
```
또는 `~/HRLDAS/build_noahmp_serial.sh` (module purge + load 3개 + make).
**산출물: `~/HRLDAS/hrldas/run/hrldas.exe`** (11MB, libnetcdf.so.13/libnetcdff.so.6 동적링크 OK).

## 4. jasper 이슈 (✓ 해결됨 — gridded용 create_forcing.exe 빌드 위해)
- **증상**: `HRLDAS_forcing/lib decode_jpeg2000.c` → `jasper/jasper.h` 없음. (hrldas.exe 자체엔 무관하나 gridded forcing 전처리 `create_forcing.exe`엔 필요.)
- **해결**: user_build_options 패치 (jasper는 libjpeg 의존 → `-ljpeg`도 추가):
  - `INCJASPER = -I/usr/local/jasper/1.900.1_gcc85/include`
  - `LIBJASPER = -L/usr/local/jasper/1.900.1_gcc85/lib -ljasper -L/usr/local/jpeg/8d_gcc85/lib -ljpeg`
- **결과**: `HRLDAS_forcing/create_forcing.exe` (3.1M) 빌드 ✓. **런타임엔 `module load gcc/jasper-1.900.1 gcc/jpeg-8d`**(LD_LIBRARY_PATH) 필요.

## 4b. Smoke test (✓ 통과, 2026-06-25)
- 입력: `HRLDAS_forcing/run/examples/single_point/` — Bondville Ameriflux 관측 `bondville.dat` + `create_point_data.f90`(→ setup nc + LDASIN forcing 생성, 외부 다운로드 불요).
- create_point_data: 1998-01-02~1999-01-01 30분 forcing **17,473개** + `hrldas_setup_single_point.nc` 생성.
- 실행: `run/`에서 `namelist.hrldas`(START_DAY=02, KDAY=10) → `./hrldas.exe`.
- **결과: EXIT=0, 10일 적분, 481 LDASOUT + RESTART. 출력 NetCDF 유효** (LAI·FVEG·HFX·LH·FSA 등).
- ⚠ 이 테스트는 `DYNAMIC_VEG_OPTION=4`(처방 LAI) — **동적식생 아님**. 빌드 검증용일 뿐.

## 5. Spin-up 프로토콜 (2-stage) — LM4.1 static→dynamic과 동일 논리
setup 파일은 **물리 초기장만** 줌 (SMOIS, TSLB, TSK, SNOW, CANWAT, 초기 LAI, 식생/토양타입).
탄소풀은 안 줌 → cold start 시 코드가 **임의값**으로 채움 (`noahmp/drivers/hrldas/NoahmpInitMainMod.F90`: `RTMASS=WOOD=500`, `FASTCP=1000`, 주석 *"all arbitrary"*).
→ 동적식생은 반드시 spin-up 필요. RESTART 파일엔 물리상태 **+ 탄소풀(LFMASS/STMASS/RTMASS/WOOD/FASTCP) + LAI** 전부 포함 → warm-start 가능 (확인됨).

```
[1단계] cold start, DVEG=4(table LAI, static) + SPINUP_LOOPS=N
        → 물/에너지 평형: 토양수분(수개월~수년), 깊은 토양온도(수년) → RESTART 저장
[2단계] warm start (RESTART_FILENAME_REQUESTED) + DVEG=2(동적)
        → 탄소풀·LAI 평형: 잎/뿌리(수년), 목질부·토양탄소(수십 년)
```
- 뉘앙스: 1단계(static)에선 탄소 미진화 → 1단계 RESTART의 탄소는 여전히 임의값. 1단계 이득 = "동적식생이 *평형 토양수분/온도* 위에서 출발". 2단계는 그래도 길게(수십 년 forcing 반복).
- HRLDAS 수단: `SPINUP_LOOPS=N`(forcing 기간 N+1회 순환, `IO_code/module_NoahMP_hrldas_driver.F`) · `RESTART_FILENAME_REQUESTED`(이어달리기).

### DYNAMIC_VEG_OPTION 1–9 (src/PhenologyMainMod.F90 + run/README.namelist)
| Opt | on/off | LAI 출처 | FVEG 산출 |
|:--:|:--:|---|---|
| 1 | off | table | 입력 SHDFAC |
| **2** | **on** | 예측(dynamic) | LAI+SAI 계산 (OPT_CRS=1과) |
| 3 | off | table | LAI+SAI 계산 |
| **4** | off | table | 연 최대 ← default |
| **5** | **on** | 예측(dynamic) | 연 최대 |
| **6** | **on** | 예측(dynamic) | 입력 SHDFAC |
| 7 | off | 입력 LAI 시계열 | 입력 SHDFAC |
| 8 | off | 입력 LAI 시계열 | LAI+SAI 계산 |
| 9 | off | 입력 LAI 시계열 | 연 최대 |
- LAI 출처: table=`1,3,4` / 예측=`2,5,6` / 외부입력=`7,8,9`
- FVEG: 입력SHDFAC=`1,6,7` / LAI+SAI계산=`2,3,8` / 연최대=`4,5,9`
- **동적식생 ON(`FlagDynamicVeg=true`)= 2,5,6 뿐.** 본격 DGVM은 **2** 권장.

## 6. Next steps
1. **2-stage spin-up 셋업** (Bondville 단일격자로 먼저 프로토콜 검증): 1단계 DVEG=4 + SPINUP_LOOPS → RESTART → 2단계 DVEG=2 warm-start → LAI 수렴 확인.
2. **ERA5 실전 forcing**: `hrldas/docs/README.ERA5` + `run/examples/ERA5/namelist.hrldas.ERA5` 참조. 프로젝트 ERA5 파이프라인 출력을 HRLDAS LDASIN 포맷으로 변환.

## 8. Gridded run — 진행 중 (2026-06-25~)
목표: global geo_em + **GSWP3 v1 0.5° forcing**으로 gridded HRLDAS.

**★ forcing 결정 (사용자, 2026-06-25): GSWP3 v1 0.5°** (ERA5-Land 아님).
- 이유: CMIP6 **LS3MIP/PLUMBER2 표준** offline forcing = CLM datm 기본 → 다중 LSM 비교진단에 표준성 최고. CLAUDE.md 과학키워드(LS3MIP/PLUMBER2) 직결.
- 위치: `/data1/CESM2_INPUT/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516/` (TPHWL/Solar/Precip, 월별, 1901~, 3-hourly, noleap, 720×360=0.5° global).
- ⚠ 주의: GSWP3 SW 아티팩트(>1360 W/m², 최대 ~1630; LM4는 못 견뎌 ERA5GPCP 사용). Noah-MP는 forcing 단계 truncate 또는 namelist에서 처리.
- 참고: LM4.1은 ERA5GPCP로 spin-up 중 → 세 모델 forcing 완전정합은 아님. (GSWP3는 CLM·LS3MIP 표준 우선 선택.)

**→ 이 결정으로 계획 대폭 단순화:** CDS ERA5-Land 다운로드 + `create_forcing.exe` 파이프라인 **전부 불필요**. GSWP3는 이미 깨끗한 0.5° global NetCDF → **NetCDF→LDASIN 변환기(cdo/Python) 하나면 됨**. (Phase 1의 create_forcing.exe·wgrib·eccodes는 GSWP3엔 사실상 미사용; cdo만 쓸 수도.)

**수정된 Phase 계획:**
| Phase | 내용 | 상태 |
|---|---|---|
| 1. 툴링 | conda env `hrldas`(cdo 2.6.1); create_forcing.exe도 빌드됨(GSWP3엔 불요) | **✓ 완료** |
| 2. 도메인 | WPS(geogrid)+WPS_GEOG → **global 0.5° `geo_em.d01.nc`** (GSWP3 격자에 정합) | **✓ 완료** |
| 3. forcing | **GSWP3→LDASIN 변환기** `noahmp/scripts/gswp3_to_ldasin.py` (서버 `~/HRLDAS/`) | **✓ 검증됨** |
| 4. 실행 | geo_em→setup 변환기 + namelist → hrldas.exe gridded | **✓ 완료** |

**Phase 4 완료 (2026-06-26) — gridded Noah-MP 실행 성공:**
- **geo_em → HRLDAS_SETUP 변환기** `noahmp/scripts/geoem_to_hrldas_setup.py` (cold start): geo_em rename(XLAT_M→XLAT, LU_INDEX→IVGTYP, SCT_DOM→ISLTYP, HGT_M→HGT, SOILTEMP→TMN, GREENFRAC월별→SHDMAX/MIN, LAI12M→LAI) + 초기상태(SMOIS=0.3, TSLB=TMN, TSK=TMN, SNOW/CANWAT=0) + 4층 soil(DZS 0.1/0.3/0.6/1.0, ZS 0.05/0.25/0.70/1.50). → `~/HRLDAS/forcing_GSWP3/init/HRLDAS_setup_GSWP3_d01.nc`.
  - ★ 함정1: HRLDAS read_hrldas_hdrinfo가 전역속성 **DX,DY,TRUELAT1,TRUELAT2,STAND_LON,MAP_PROJ,GRID_ID,ISWATER,ISURBAN,ISICE,MMINLU 전부 요구**. geo_em엔 GRID_ID 없음 → 변환기에서 `GRID_ID=1` 명시 + TRUELAT/STAND_LON 없으면 0.
  - ★ 함정2: LDASIN 파일명 — 3-hourly(정시) forcing은 HRLDAS가 **10자리 `YYYYMMDDHH`** 기대 (single_point 30분은 12자리였음). gswp3_to_ldasin.py 파일명 `%Y%m%d%H`로 수정.
- **namelist** `~/HRLDAS/hrldas/run/namelist.hrldas` (사본 `noahmp/`): SETUP=위파일, INDIR=GSWP3 LDASIN, FORCING_TIMESTEP=10800, NOAH=1800, DVEG=4, KDAY=1.
- **실행**: `~/HRLDAS/hrldas/run`에서 hrldas.exe → **exit 0, 1979-01-01→02 하루, LDASOUT 9개(각120M) + RESTART**. 출력 `~/HRLDAS/forcing_GSWP3/output/`.
- 검증(박제): 720×360, 해양=-1e33 fill, 육지 max값 정상 — TRAD 320K, HFX 472, LH 551 W/m², FSA 867, LAI 4.6, SOIL_T 314K, SNEQV 20.9mm.
- 경고 "SOIL TYPE WATER AT LAND-POINT → RESET to SANDY CLAY LOAM": 해안 몇 셀 자동보정, 무해.

**=== gridded Noah-MP 파이프라인 완성 ===** GSWP3(/data1) → `gswp3_to_ldasin.py` → LDASIN + geo_em(WPS) → `geoem_to_hrldas_setup.py` → setup → hrldas.exe → LDASOUT.

## 9. Spin-up forcing = GSWP3 1981-2010 (진행 중, 2026-06-26)
**결정 (사용자): spin-up forcing = GSWP3 v1 1981-2010** (CMIP6/LS3MIP 표준 30년 기후period, LM4 ERA5GPCP 1981-2010 cycling과 정합).
- ★ **noleap 윤일 처리 (확정·검증)**: GSWP3는 noleap(1980-02도 time=224=28일, calendar="noleap" — 2/29 없음). 그러나 **HRLDAS는 실제 Gregorian 달력**(`Utility_routines/module_date_utilities.F`의 `mday(2)=nfeb(yrold)`) → 윤년에 2/29 파일 없으면 멈춤. **해법: 2/29 = (2/28 + 3/1) 평균 삽입** (사용자 지정). 과학적으론 4년에 하루라 무의미하나 크래시 방지용으로 파일은 필요. 검증: 1984 테스트 Feb29=0.5×(Feb28+Mar1), max diff=0.0 ✓.
- `gswp3_to_ldasin.py` 개정: `range STARTYEAR ENDYEAR OUTDIR` 모드 + 윤년 Feb29 자동삽입.
- 변환 실행 중: `python gswp3_to_ldasin.py range 1981 2010 ~/HRLDAS/forcing_GSWP3/LDASIN` (백그라운드, ~27파일/s, ~1시간, ~87,600파일/~360GB, **/home**). 로그 `~/HRLDAS/forcing_GSWP3/convert_gswp3.log`.
- 다음: spin-up namelist (DVEG=4 cold start, KDAY=365×... 또는 SPINUP_LOOPS로 1981-2010 블록 cycling, 출력 최소화) → 토양수분/온도 평형 → RESTART → (2단계) DVEG=2 dynamic warm-start.

## 10. MPI(dmpar) 빌드 — spin-up 가속 (2026-06-27)
serial은 global 0.5° 30년이 ~12일로 비현실 → MPI 필수. **HRLDAS는 WRF 독립(자체 MPP 레이어)** 이라 HRLDAS만 MPI 재빌드.
- **빌드**: `./configure 4`(Linux intel MPI) → user_build_options 패치: **`COMPILERF90=mpiifort`**(★ 기본 `mpif90`는 gfortran 백엔드 → netcdf intel21 `.mod`와 ABI 충돌, 반드시 mpiifort) + netcdf 4.6.1_intel21 + jasper/jpeg 경로. 모듈 `intel21/compiler-21 intel21/intelmpi-21 intel21/netcdf-4.6.1 intel21/hdf5-1.10.5`. `make NoahMP` → MPP 포함 hrldas.exe(libmpi/libmpifort 링크).
- **실행**: `mpirun -np N ./hrldas.exe`. **24코어 검증**(LM4 검증값, 교착 없음): exit 0, 5일 wall 62s. compute serial 93→MPI8 23→**MPI24 11 s/일**(~8.5배). per-interval ~1.5s(I/O 지배라 24가 sweet spot, 더 늘려도 효과 작음).
- **정확성 검증**: MPI24 restart SMC 0.07–1.0(평0.53), SOIL_T 223–315K, NaN 0, PE경계 garbage 없음 ✓.
- 30년 1pass 추정: ~36h(24코어, I/O bound). ⚠ climate00 직접 mpirun으로 테스트함(LM4는 PBS climate01 사용) — 장시간 job은 nohup 또는 PBS 고려.
- 실행 모듈 4종 + `mpirun -np 24`. namelist는 §8/spinup과 동일(DVEG=4 cold start).

## 11. Spin-up Pass 1 제출 (2026-06-29) — 실행 중
- **PBS job 2886.climate00**, `noahmp_spin`, workq, **climate01 24코어**, walltime 72h. 스크립트 `~/HRLDAS/forcing_GSWP3/spinup/noahmp_spinup.pbs` (Intel MPI, LM4의 OpenMPI/hcoll/spack 우회 불필요).
- **설정**: cold start, **DVEG=4(static), 1981-2010 (KDAY=10956)**, OUTDIR=`~/HRLDAS/forcing_GSWP3/spinup/`, 연 단위 RESTART(RESTART_FREQUENCY_HOURS=8760)+LDASOUT → 연도별 토양수분/온도 수렴 모니터링용.
- run dir: hrldas.exe·NoahmpTable.TBL·snicar·URBPARM 심볼릭 + namelist.hrldas.
- 확인: exec_host=climate01/0*24, cpupercent~2005(활성), 초기 soil-type reset 경고(무해). 첫 RESTART(1981말)≈1~1.5h, 전체 30년≈36h 예상.
- ⚠ PBS `-o` 로그는 job 종료 시 복사됨 → 실행 중 모니터는 spool(`climate01:/var/spool/pbs/spool/2886.climate00.OU`) 또는 spinup 디렉토리의 RESTART 파일 생성으로.
- 다음: 완료 후 연도별 전구평균 SMC/SOIL_T로 평형 확인 → 부족시 Pass2(RESTART 체인) → 평형 후 2단계 DVEG=2 dynamic warm-start.

### Pass 1 실패·진단·재시도 (2026-06-30)
- **job 2886 실패** (Exit_status=1): 6년(1981-1986) 정상 후 **7년차 1987에서 죽음** (walltime 5.7h, 초과 아님). RESTART 1982~1986 6개 생성. pbs.log 미전달·spool 정리되어 원본 에러 유실.
- 진단: 1987 LDASIN 완전(누락 아님). **★ 원인 = 빌드 F90FLAGS의 `-fpe0`** (FP 예외 trap→abort). 30년 글로벌 런 7년차에 어떤 셀이 일시적 FP 예외 → `-fpe0`가 전체 abort. "수년 정상 후 급사"는 fpe trap 전형.
- (참고: restart에서 재현 시도 시 **무한 "Write restart" 루프(106M줄)→OOM SIGKILL** 발생 — restart-at-restart-date namelist artifact, 원본 버그 아님. restart 재시작은 회피, cold-start 재실행이 깔끔.)
- **수정**: HRLDAS MPI 재빌드, F90FLAGS `-fpe0` 제거 + `-ftz`(denormal flush)·`-traceback` 추가. (장기 기후 런 표준.)
- **job 2888 재제출**: cold-start, 수정 빌드, climate01 24코어. → **10초만에 또 죽음(Exit_status=1)**. fpe0 제거로 abort는 없앴지만 startup에서 즉사.

### ★★ 진짜 원인 규명 (2026-07-01/02) — soil-type 로그 폭주
- 진단 실행(diag) 로그가 **9.7GB**! traceback = 토양수분 솔버(SoilHydraulicPropertyMod). 5GB 지점 샘플 → 지배 메시지 **"SOIL TYPE FOUND TO BE WATER AT A LAND-POINT / RESET SOIL type to SANDY CLAY LOAM"** (3MB에 25,852회).
- **근본 원인**: setup 파일의 **육지 87,710셀 중 27,653개(32%)가 ISLTYP=14(water soil)**. geogrid soiltype이 0.5° 거친 격자에서 육지 상당부(호수·해안·고위도)를 water로 판정. Noah-MP가 이를 매 timestep sandy clay loam으로 리셋하며 **경고 출력** → 로그 GB 폭주 → disk/메모리 채워 job 사망.
  - → **fpe0는 원인 아니었음** (red herring). 원본 2886의 "1987 급사"도 6년간 이 로그가 PBS spool 채워 죽은 것. 무한루프처럼 보인 것도 이 매-스텝 경고.
- **수정 (확정)**: `geoem_to_hrldas_setup.py`에 `sct = np.where((landmask>=0.5)&(sct==14), 7, sct)` — 육지 water-soil→7(sandy clay loam) 사전 재할당 (모델이 어차피 하는 것, 로그만 제거). setup 재생성 → **육지 ISLTYP=14: 27,653→0** 확인 ✓. (repo `noahmp/scripts/geoem_to_hrldas_setup.py`)
- 빌드 상태: 현재 `-fpe0` 제거 + `-ftz -traceback` (2888용). 원인이 fpe0 아니었으니 유지/복원 무관 — 그대로 두고 진행.

### ▶ 내일 재개 (RESUME) — climate01이 찬혁님 사용중이라 대기
1. **smoke test 먼저** (재빌드/재수정 후엔 반드시): KDAY=5 PBS(diag.pbs, 8코어, explicit log) → **diag.log가 MB급(GB 아님)이고 정상 완료 + 출력 NaN 없음** 확인. (namelist.hrldas는 현재 mpitest=KDAY5로 세팅돼 있음)
2. 통과하면 **spinup namelist(KDAY=10956) 복원 → noahmp_spinup.pbs 24코어 재제출** → 1987 통과 → 30년 완주.
3. 산출물: 연 RESTART로 SMC/SOIL_T 수렴 확인 → 2단계 DVEG=2 dynamic warm-start.
- ⚠ diag.pbs/smoke는 반드시 explicit `>& log` (PBS -o 미전달 이력). 거대 로그 재발 시 즉시 원인 재확인.

**Phase 3 검증 (박제, 2026-06-25):** `gswp3_to_ldasin.py 1979 1 OUTDIR 2` → 16개 LDASIN(720×360, Time=1) 생성. base env(netCDF4 1.7.4)로 실행. 값 범위 정상: T2D 190.7–319.4(평277.9)K, Q2D ~0.044, U2D 0–22.5(V2D=0), PSFC 50.8–105.4kPa, LWDOWN 89–480, **SWDOWN 0–1361**(아티팩트 경계), RAINRATE 0–0.0074 mm/s. 단위 전부 그대로 통과(변환 불요). 출력: `~/HRLDAS/forcing_GSWP3/LDASIN/`.
- 미해결: noleap(Feb 29) — 장기 cycling spin-up 때 윤일 갭 처리 필요. 단기 테스트는 무관.

**GSWP3 → LDASIN 변수 매핑 (단위 전부 일치, rename만):**
| GSWP3 | LDASIN | 단위 |
|---|---|---|
| TBOT | T2D | K |
| QBOT | Q2D | kg/kg |
| WIND | U2D (+ V2D=0) | m/s |
| PSRF | PSFC | Pa |
| FLDS | LWDOWN | W/m² |
| FSDS | SWDOWN | W/m² |
| PRECTmms | RAINRATE | mm/s |
- GSWP3 파일: `clmforc.GSWP3.c2011.0.5x0.5.{TPQWL,Solr,Prec}.YYYY-MM.nc`, 3-hourly. 좌표 LONGXY/LATIXY(2D), time "days since 1979-01-01" noleap.

### Phase 2 완료 기록 (2026-06-26) — WPS 빌드 + global 0.5° geo_em
- **WRF v4.6.1** 빌드: `~/WRF_WPS/WRF`, intel classic serial(configure opt 13, ifort/icc), `export NETCDF=/usr/local/netcdf/4.6.1_intel21` + intel21 모듈 3종. io libs(io_netcdf/io_int/io_grib1/io_grib_share) + main exe 생성. 스크립트 `~/WRF_WPS/build_wrf.sh`.
- **WPS v4.6.0** 빌드: `~/WRF_WPS/WPS`, intel classic **serial_NO_GRIB2(opt 22)** — WRF와 컴파일러 매칭 필수(io libs ABI). `WRF_DIR=~/WRF_WPS/WRF`. → `geogrid.exe` ✓ (ungrib 불요, forcing은 GSWP3).
- **WPS_GEOG**: `geog_high_res_mandatory.tar.gz`(2.77GB) → `~/WPS_GEOG/WPS_GEOG/` (landuse 20class 30s, soiltype top/bot 30s, topo 30s, greenfrac_fpar_modis, soiltemp_1deg 등).
- **namelist.wps** (`~/WRF_WPS/WPS/namelist.wps`): map_proj='lat-lon', e_we=721 e_sn=361, dx=dy=0.5, ref_lat=0 ref_lon=180 → mass점 lon 0.25..359.75 / lat −89.75..89.75 = **GSWP3 격자 정확 정합** (WPS는 lon을 −180..180으로 표기하나 인덱스·물리위치 동일).
- ★★ **핵심 함정 (geogrid global hang)**: 첫 실행이 field 10 GREENFRAC에서 **3시간 CPU 100% 무한 스핀**. 원인 = `geog_data_res='default'`가 GEOGRID.TBL의 `default:` 옵션 선택→끝의 **`+search` 보간 메소드가 글로벌 도메인에서 병리적 무한루프**. **해결: GEOGRID.TBL에서 모든 `+search`·`+search(N)` 제거** (`no_search` 태그는 보존). 글로벌 0.5°는 four_pt/average로 전 셀 채워져 search 불요. → 재실행 즉시 "Successful completion", `geo_em.d01.nc`(13M).
- 검증: 720×360, lat −89.75~89.75, LU_INDEX 1~21(MODIFIED_IGBP_MODIS_NOAH), SCT_DOM/SCB_DOM 1~16, GREENFRAC 0~0.98, 육지 87,710셀.

**▶ 재개 지점 (RESUME):** Phase 1·2·3(forcing 변환기) 완료. 남은 것 = **Phase 4**:
1. **geo_em → HRLDAS_SETUP_FILE 변환기** (cold start): geo_em 필드 rename(XLAT_M→XLAT, LU_INDEX→IVGTYP, SCT_DOM→ISLTYP, HGT_M→HGT, SOILTEMP→TMN, GREENFRAC→SHDMAX/MIN) + 초기상태 추가(SMOIS~0.3, TSLB←TMN, TSK, SNOW=0, CANWAT=0). single_point setup nc 변수목록이 템플릿(§4b의 ncdump 참조).
2. namelist.hrldas (HRLDAS_SETUP_FILE=위 파일, INDIR=GSWP3 LDASIN, DVEG=4 먼저, KDAY 작게) → hrldas.exe gridded 실행 → LDASOUT 검증.
- ⚠ `/data2` 잔여 9.2GB뿐 → 출력·LDASIN은 **/home(113T)**.

## 7. 문서 (서버 내)
- `~/HRLDAS/noahmp/docs/NoahMP_v5_technote.pdf` — 공식 기술문서 (He et al. 2023b, NCAR/TN-575+STR, doi:10.5065/ew8g-yr95) = user guide
- `~/HRLDAS/noahmp/docs/NoahMP_refactored_variable_name_glossary_Feb2023.xlsx` — 변수 사전
- `~/HRLDAS/hrldas/run/README.namelist` — 전 namelist 옵션 설명
- `~/HRLDAS/hrldas/docs/README.{ERA5,GLDAS,NARR,NLDAS,single_point,vector}` — forcing별 셋업
- 온라인: https://ral.ucar.edu/solutions/products/noah-multiparameterization-land-surface-model-noah-mp-lsm · He et al. 2023a, GMD 16, 5131
