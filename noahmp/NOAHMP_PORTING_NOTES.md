# Noah-MP v5.2.1 Offline Porting — 작업 로그 & 현황 (2026-06-25)

_climate00 서버. HRLDAS offline driver + Noah-MP v5.2.1 (intel21 serial). 동적식생(DGVM) LSM 3종(CLM5·LM4.1·Noah-MP) 중 마지막._
_**상태: cold-start spin-up 가동 중 (2026-07-06: climate02 job 2899 실행 중, 1982-09-23에서 재개, §8)** — 이후 평형까지 다년 + ERA5 실전 forcing (§6)._

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

## 8. Spin-up 실행 로그 (2026-07-03)

DVEG=4 static cold-start spin-up 본격 가동. run dir `~/HRLDAS/forcing_GSWP3/spinup/`.

### 8a. 진행 현황 (★ 현재 상태)
- **2026-07-06 재개: climate02에서 실행 중 (job 2899, 48코어, R).** spinup.log가 `Found restart file: 'RESTART.1982092300_DOMAIN1'` + `***DATE=1982-09-23` → 1982-09-23부터 정상 이어달리기 확인(cold-start 아님). tail의 `GLACIER HAS MELTED / ARE YOU SURE...`는 benign 정보성 경고(빙하격자 처리), 옛 `WATER AT A LAND-POINT` flood와 무관. KDAY=10326으로 2010말까지 적분, 완주 시 PBS가 자동 `spinup_raw/` 아카이빙. walltime 72h 초과 시 마지막 연 restart에서 재 `qsub`.
- (7-03) cold-start 1981-01-01 → 1982-09-23 도달 (~1.7 model-year), restart 21개 보존.
- 재개 준비 완료: namelist가 `RESTART_FILENAME_REQUESTED="RESTART.1982092300_DOMAIN1"`, START=1982-09-23, KDAY=10326(→2010말), **연 restart**로 세팅됨. **다음엔 `qsub noahmp_spinup.pbs`만** 하면 이어짐.
- PBS: `noahmp_spinup.pbs` = 48코어·**climate02**(7-06 climate01→02 변경)·walltime 72h, `mpirun ... > spinup.log 2>&1`.
- 백업: `namelist.hrldas.bak_coldstart`(원 cold-start), `.bak_resume30day`(30일 restart판).

### 8b. ★ 이전 "멈춤" 원인 규명 (오진 정정)
- `repro.log` 6.2GB flood(`SOIL TYPE ... WATER AT A LAND-POINT` ~5만회 → SIGNAL 9)는 **6-30 이전 옛 문제, 이미 setup 수정으로 해결**. setup 검증: land 87,710점 중 water 토양(ISLTYP==14) **0개**.
- 7-02 diag 런 죽음 = **20분 diag 잡에 30년 namelist 걸어서 PBS walltime kill**(진짜 버그 아님). diag.log는 flood 0, 64일 정상 적분.
- **교훈: 첫 그럴듯한 원인(flood)에서 멈추지 말 것. diag.log 재확인(flood 0)이 오진을 정정.**

### 8c. ★ 24 vs 48 코어 벤치마크 (검증, KDAY=60)
| 코어 | 60일 wall | → 1 model-year |
|---|---|---|
| 24 | 517초 | ~52분 |
| **48** | **423초** | **~43분** |
- **48이 1.22× 빠름** (병렬효율 61%, Amdahl). 2배 안 나는 이유 = init/`MPI_Bcast`·I/O·통신·부하불균형·메모리대역폭(비병렬 고정비용). Noah-MP는 **column-독립**이라 LM4(halo 교환 有, 48서 오히려 느림)와 달리 48서 병목 아님 → **48 채택**.
- 실제 spin-up은 ~65분/년이었음(30일 restart+상세로그 오버헤드). **연 restart 전환 시 벤치(43분/년) 근접 예상** → 30년 ~32h→~22h.

### 8d. ★ Resumability 검증 (잡2897, climate02)
- `RESTART_FILENAME_REQUESTED`로 재개 실측: 로그 `Found restart file: 'RESTART.1982032700_DOMAIN1'`, **첫 date=1982-03-27**(1981 아님)→2일 정상 진행. **이어달리기 확정 YES.**
- 끝의 exit=255/SIGKILL은 KDAY 완주 시 Intel-MPI 종료 아티팩트(benign, 계산 정상). walltime kill 시엔 안 뜸 → resume 무관.

### 8e. restart/로그 규모 & 정책
- restart 개당 **83MB**. 30일 주기=~12개/년(~1GB/년, 30년 ~30GB) → **연 1회(8760h)로 전환**: 30개(~2.5GB), I/O 12배↓. 연 checkpoint면 spin-up 재개에 충분.
- 로그: 30일판 spinup.log ~200MB/년(30년 ~6GB). **속도 병목 아님**(rank0 stdout ~32KB/s)이라 모니터링 위해 유지; 원하면 `/dev/null` 가능.

### 8f. ★ Forcing = GSWP3 3-hourly 유지 (LM4 정합)
- 6시간 간격 검토했으나 **일변화(특히 SWDOWN 정오피크·야간0, T2D 일교차) 훼손**으로 기각. 속도 이득도 미미(주 오버헤드는 restart+로그, forcing읽기 아님).
- **LM4 spin-up도 GSWP3 3-hourly** + CDEPS DATM **coszen 보간**([[lm4 notes]] §2). 다중 LSM 비교 정합 위해 Noah-MP도 3시간 유지가 맞음.

### 8g. ★ 결과값 검증 (restart, land-mean, NaN 0)
| date | SMC 4층 [m³/m³] | SOIL_T 4층 [K] | SWE |
|---|---|---|---|
| 1981-01-31 | 0.51/0.52/0.53/0.54 | 269/271/271/272 | 16mm |
| 1981-08-29 | 0.48/0.52/0.52/0.53 | 274/276/276/275 | 54mm |
| 1982-03-27 | 0.50/0.52/0.52/0.53 | 270/271/272/272 | 139mm |
- SOIL_T 계절변화 정상(범위 224–312K), NaN 0. **토양수분 ~0.5로 다소 젖음**(최대 1.0 포화·빙하점 포함) — 젖은 초기값서 서서히 배수(drift L1 −0.014/14개월). **SWE는 cold-start 0서 축적 중** → 둘 다 **미수렴, 다년 필요**(1.7년치라 당연). 진단 py: `~/nmp_result.py`(land-mean SMC/SOIL_T), `~/nmp_setup_check.py`(land-soil 정합).

### 8h. ★ Restart 보존 (LM4 방식 그대로, [[lsm-spinup-raw-preservation]])
raw restart **절대 자동삭제 금지 + 이중 보존**. run dir 밖으로 아카이빙(run dir 재사용/rm 대비).
- **서버 아카이브**: `noahmp_spinup.pbs` 끝에 `rsync -a`(--delete 없음) 단계 추가 → `/home/ydkoh/HRLDAS/spinup_raw/noahmp_GSWP3_staticveg/`에 매 세그먼트 후 자동 누적 보존. (LM4는 /data2였으나 96%참 → Noah-MP는 /home 111T)
- **로컬 이중보존**: `noahmp/scripts/pull_noahmp_spinup.sh` = 서버 spinup_raw → Mac `/Volumes/data02/NOAHMP/spinup_raw/` rsync(--delete 없음). 주기 실행 권장(LM4 puller와 동일 개념).
- **삭제는 사용자가 수동으로만.** rsync 어디에도 `--delete` 없음 → 아카이브는 누적만.
- 2026-07-03 초기 보존 완료: 22 restart(1.9GB) 서버+로컬 양쪽 확보.

## 9. ★ 1°/3h static-veg spin-up 2 cycle — 수렴 판정 (2026-07-09~10)

### 9a. 실행 이력
| cycle | 노드 | 기간 | wall | 종료 |
|---|---|---|---|---|
| 1 | climate00 | 1981-01-01 → 2010-12-31 (KDAY=10956) | — | exit=255 (§8d benign) |
| 2 | climate01 (job 2920, np48) | 동일 forcing 재생 | 5h41m (14:50→20:31) | exit=255 (§8d benign) |

- cycle 2 seed = cycle 1 최종 restart를 `redate_restart.py`로 Times만 1981-01-01로 재기입 → **원본 forcing 재사용**(forcing 재생성 불필요).
- 속도 **≈11분/model-year** (48-rank intelmpi, 1°/3h). 30년 ≈ 5.7h. 8c의 0.5° 벤치(43분/년)와 별개 config.
- `RESTART_FREQUENCY_HOURS=8760`은 365일 고정 → 윤년마다 하루씩 밀려 **최종 restart가 12-25**에 찍힘(런은 12-31 종료). 마지막 6일 상태는 restart에 없음. spin-up seed로는 무해.
- 산출물: LDASOUT 30 + RESTART 32. **아카이브 rsync가 LDASOUT을 안 담고 있었음** → 수동 보강 완료 (`spinup_raw/noahmp_GSWP3_1deg_staticveg_cyc2/`, 2.5GB). pbs 스크립트의 rsync 패턴에 `*.LDASOUT_DOMAIN1` 추가 필요.

### 9b. ★★ 수렴 판정: 지표를 바꿔야 함
동일 forcing을 재생하므로 **cycle 간 같은 날짜(2010-12-25) restart 차이 = 순수 표류**. 반면 `|annual change|`는 GSWP3 경년변동이 지배 → 수렴 판별 불가.

**모든 평균은 cos(lat) 면적가중** (§9f 참조).

| 지표 (non-ice land, 14717격자) | cycle 1 순변화 | cycle 2 동일날짜 표류 | 비고 |
|---|---|---|---|
| 심층 토양온도 | +0.623 K | **+3.0e-6 K** | ⚠ TBOT=2가 고정 TMN으로 relax → 약한 증거 |
| 컬럼 토양수분 | −3.29 kg/m² | **−0.56 kg/m²** | 자유 예후변수 → **주 증거** |
| SWE | — | **+1.8e-5 mm** | |
| 연간 변화 노이즈 \|ΔT\| | — | 0.051 K | 표류의 **1.7만배** |

- **판정: 비빙설 전구 지면 수렴 완료.** cycle 3 static은 불필요 — 583 kg/m² 컬럼에서 얻을 게 ~0.5 kg/m²(0.1%)인데 비용 5.7h×48코어.
- ⚠ **전구 평균만 수렴.** 격자별 컬럼수분 표류는 mean\|d\|=0.51 kg/m²지만 **p99=18.1, max=53.7 kg/m²**. land-mean 진단엔 무해하나 **지역별 토양수분 진단 시 상위 1% 격자의 잔차 유의**.
- 잔여 표류는 최하층(1 m)에 집중, `SMC` mean\|d\| 1.9e-4 m³/m³.
- **seed 확정**: `forcing_GSWP3_1deg/spinup/RESTART.2010122500_DOMAIN1` (NaN/Inf 0, 헤더 정상).

### 9c. ★ 빙상은 제외해야 함 ([[lsm-spinup-ice-mask-convergence]])
- capped(≥4999mm) 격자는 cycle 1·2 모두 **100% IGBP 15 안**(off-ice = 0). 일반 지면으로의 "눈 폭주" 아님.
- 빙상(7477격자) 평균 SWE 10 → 4096 mm, 상한 도달 0 → 1652격자(22%). offline엔 빙하 역학 없어 **평형 자체가 존재하지 않음**.
- 전 지면 평균으로 보면 심층T 표류가 부풀려짐 → cycle 1 그림이 "미수렴"으로 보였던 원인.
- `IVGTYP` max=21 → **MODIS-IGBP**(ice=15, water=17). `ICE = 15 if max<=20 else 24` 식 휴리스틱은 IGBP를 USGS로 오판함.

### 9d. ★ 탄소풀은 60년 동안 한 번도 적분되지 않음
```
WOOD identical cold-start vs cyc2 end? True
LFMASS/STMASS/RTMASS/WOOD/FASTCP/STBLCP   cold->cyc2 |d| = 0.000000
```
- DVEG=4 → `FlagDynamicVeg = .false.` (`PhenologyMainMod.F90` L158: 2/5/6일 때만 true) → 탄소 모듈 미실행.
- **dynamic veg로 가면 탄소 spin-up은 0에서 시작.** WOOD 회전시간 수십~수백 년 → 30년 1 cycle로 불가, 4~10 cycle(23~57h) 예상.
- **DVEG=2 vs 5 결정 필요**: 옵션 4(현재)는 `VegFrac = VegFracAnnMax` 고정. 옵션 2는 `VegFrac = 1-exp(-0.52(LAI+SAI))`로 **피복률 산정식까지 바뀜**. 옵션 5는 dynamic이면서 VegFrac 연최대 유지 → 변수 하나만 바꿔 비교 가능(진단 목적엔 5가 깔끔할 수 있음).

### 9e. 재현 도구
- 추출: `noahmp/scripts/extract_spinup_cyc12.py` (서버 실행, ice/non-ice 분리 CSV)
- 데이터: `noahmp/data/spinup_cyc12.csv` (61 model-year)
- 그림: `noahmp/scripts/plot_spinup.py` → `figures/noahmp_spinup_convergence_2cyc.png` (4-panel; LM4 `lm4/scripts/plot_spinup.py` 구조 계승 + 빙상 패널·표류 지표 추가)

### 9f. ★ LM4와 그림 기준 정합 (2026-07-10 점검)
두 모델의 "land-mean"은 **같은 양이 아니었음**. 비교 전 반드시 맞출 것.

| | LM4 (`lm4_equil.py`) | Noah-MP (수정 전) | Noah-MP (수정 후) |
|---|---|---|---|
| 샘플링 시점 | `{year}0101.000000.soil.res.*` = **1월 1일 고정** | 8760h stride → **Jan-01 → Dec-25로 표류**(7일) | 동일(구조상 불가피), 그림에 명시 |
| 공간 평균 | cubed sphere C96 = **준등면적** → 무가중 ≈ 면적가중 | 1° 정규격자 **무가중 → 고위도 과대대표** | **cos(lat) 가중** |

- 무가중 → 가중 전환 시 비빙설 심층T **285.53 → 288.89 K (+3.36)**, SWE **34.50 → 22.54 mm (−35%)**. 컬럼수분만 −0.11로 둔감.
- **수렴 판정은 가중 여부와 무관하게 유지**(동일 날짜 차분이라 상쇄): 심층T 표류 3.0e-6 K, SWE 1.8e-5 mm.
- 샘플링 표류는 **cycle 간 동일날짜(2010-12-25) 차분에는 영향 없음**. cycle 내 시계열에만 ≤7일 계절 wobble.
- CSV 정밀도 함정: `%.4f`로 쓰면 심층T 표류(O(1e-6) K)가 0으로 반올림됨 → `%.6f` 사용.
- 향후: LM4도 면적×land-fraction 가중으로 맞추면 완전 정합.

### 9g. 아카이브 rsync 수정 (2026-07-10)
- 기존 rsync가 `RESTART.*` + namelist + log만 담고 **`*.LDASOUT_DOMAIN1` 누락** → `prep_*.sh`가 run dir을 `rm` 하면 출력 소실. cycle 2 출력(2.5GB)은 수동 보강함.
- 수정: `noahmp_spinup.pbs`, `run_pass1_c00.sh`, `run_spinup300_1deg.sh`, `run_cyc2b_c01.sh` 4개에 `*.LDASOUT_DOMAIN1` 추가 + `shopt -s nullglob`(짧은 런에서 glob 미매치 시 rsync 실패 방지). 원본은 `*.bak_noldasout`로 보존.

### 9h. ★ 모델비교용 Jan-01 스냅샷 생성 (2026-07-10, job 2923)
**두 모델 다 그레고리력(leap)이다. 차이는 달력이 아니라 restart 알람 방식이다.**
- **Noah-MP**: `RESTART_FREQUENCY_HOURS=8760` = **시간 기반** 알람 → 윤년마다 1일씩 밀림 (1981-01-01 → 2010-12-25).
- **LM4**: FMS **달력-연 기반** 알람 → leap이어도 매년 정확히 1월 1일 (`19820101` … `20100101`). `model_configure`의 `restart_fh`는 비어 있고 `soil.res`는 LM4 cap이 씀.
- 검증: LM4 `nhours_fcst=262800` = 10,950일. `1981-01-01 + 10950d = 2010-12-25`(leap), 2011-01-01 restart 부재 → leap 확정. LM4 노트 §9c·§9d(“NOLEAP 전환 실패 → leap 유지”)와 일치.
- GSWP3 원본은 `calendar=noleap`(1984-02 = 224스텝). Noah-MP는 2/29를 `0.5*(Feb28+Mar1)`로 **합성 주입**해 LDASIN에 넣었고, LM4는 CDEPS가 처리. 적분 일수: Noah-MP 10,957일(1981-01-01~2010-12-31) vs LM4 10,950일(~2010-12-25).

- **해법**: 밀린 restart에서 다음 1월 1일까지 1~7일만 이어달리기(동일 forcing·동일 옵션 → 연속 궤적 정확히 재현). 27개 tail, 총 105일, **6분**.
- 산출: `spinup_raw/noahmp_GSWP3_1deg_jan1snap_cyc2/JAN1.YYYY010100_DOMAIN1` **30개(1981–2010, 624MB)**, Times 전수 검증 + NaN 0.
- **2011-01-01은 생성 불가**: HRLDAS가 적분 종료 시각의 LDASIN을 반드시 염 → `Problem opening ... 2011010100.LDASIN_DOMAIN1`. LDASIN은 `2010123121`까지. LM4 시계열도 2010-01-01에서 끝나므로 무관.
- **함정 2개**:
  - HRLDAS는 런 종료 시 restart를 안 씀 → tail은 `RESTART_FREQUENCY_HOURS = 24*KDAY`로 끝점에 정확히 찍히게 해야 함.
  - `while read` 루프 안의 `mpirun`이 **stdin(here-string)을 삼켜** 첫 tail 후 루프가 조용히 종료됨 → `mpirun ... < /dev/null` 필수.

**제거된 계절 어긋남의 크기** (밀린 restart → 다음 1월 1일, 비빙설 cos(lat) 가중):

| 어긋남 | d(심층T) | d(SWE) |
|---|---|---|
| 1일 | −0.034 K | +0.27 mm |
| 7일 | **−0.272 K** | **+2.49 mm** |

- 일수에 거의 선형(−0.039 K/일). **수렴 표류(3e-6 K)보다 ~9만 배 큼** → 표류 판정엔 상쇄되어 무해했으나 **모델 간 절대값 비교엔 치명적**이었음. SWE는 평균 22.5 mm 대비 +11%.
- 진단 코드: `noahmp/scripts/extract_jan1_snapshots.py`, 데이터 `noahmp/data/jan1_snapshots.csv`, 실행 `jan1_snap/make_jan1.sh`.
- **원칙: 다중 LSM 비교는 반드시 Jan-01 스냅샷(`JAN1.*`)을 쓸 것. 수렴 판정만 밀린 restart(Dec-25) 사용.** [[lsm-landmean-comparability]]

## 10. ★★ WFDE5 forcing 전환 + DVEG=5 탄소 spin-up 설계 (2026-09-17, 실행은 보류)

**결정(사용자)**: forcing을 LM4p·CLM5와 같은 **WFDE5**로 통일, **1° 도메인 유지**(물리 restart 재사용), **DVEG=5**.
Noah-MP 실험 자체는 다른 실험(F 96PE 타이밍·CLM5 생산런)이 끝난 뒤 실행.

- **층위 정합**: Noah-MP "dynamic veg"(2/5/6)는 탄소·LAI phenology이지 타입 변화가 아님 → CLM5-BGC(PFT 면적 고정,
  LAI 예후)와 같은 층위. LM4p(cohort 경쟁+LUH2)는 한 층 위. DVEG=5는 FVEG를 연최대로 고정해 "탄소 켠 효과"만
  분리(옵션 2는 FVEG=f(LAI) 되먹임이 추가돼 CLM5에 없는 항). §9d 결정 종결.
- **변환기** `noahmp/scripts/wfde5_to_ldasin_1deg6h.py`(서버 `~/HRLDAS/`): `YYYY_wfde5.nc`(0.5°, 6h 평균 1460/yr,
  noleap, 중점 stamp 0.125d=03Z) → stride-2 부표본 → LDASIN. **grid-verify 통과**(`chk_wfde5_grid_1deg.py`):
  WFDE5 LATIXY/LONGXY == GSWP3 완전 일치, 부표본 == 1° setup(XLONG 360 차는 −180/180 표기). 1° 육지 22,003셀 중
  WFDE5 fill 18셀(빙상 15) → 최근접 유효값 fill(lon 주기, lm4p 변환기와 동일). Feb 29 = avg(2/28, 3/1) 삽입.
- **★ 시각 stamp 결정**: 6h **평균**이므로 창 중점 **03/09/15/21Z**에 파일을 찍고 `START_HOUR=3`. 창 시작(00Z)에
  찍으면 일변화가 3h 앞당겨짐(SWDOWN 피크 09Z). HRLDAS는 forcing 사이를 선형보간 → LM4p(FMS data_override
  선형보간)와 같은 처리. restart도 03Z에 찍힘. GSWP3 6h 변환기는 순간값이라 00Z stamp가 맞았던 것.
- 첫 2일 검증: 8파일, NaN 0, 육지평균 T2D 266.0 K, 1.4 mm/d. GSWP3 LDASIN 1981-01-01 대조(육지 무가중 평균, 스냅샷
  1개라 참고용): T2D 268.2 vs 265.4 K, Q2D 3.94e-3 vs 3.96e-3, U 2.9 vs 3.7 m/s, PSFC 884.8 vs 882.7 hPa,
  LW 240 vs 233, SW 210 vs 202 W/m², P 1.42 vs 1.35 mm/d. 자료 차이지 변환 오류 신호는 아님(격자·단위·부호 정상).
- **성능 함정**: 스텝마다 `[t, ::2, ::2]` 읽기 → ~1파일/s(45년 16h). 80스텝(20일) 블록 캐시로 수정.
- 실행 스크립트(한 파일에 설정 전부): `noahmp/run_scripts/NoahMP_WFDE5_dveg5_spinup.sh` — `setup`(링크·seed redate
  03Z·namelist·PBS 생성) / `next`(cycle N+1 스테이징). namelist 차이 5개: DVEG 4→5, INDIR, START_HOUR 00→03,
  FORCING_TIMESTEP 10800→21600, KDAY 10956→10957(윤일 포함). 수렴 판정은 non-ice land·cos(lat) 가중, WOOD·STBLCP 표류.
- 탄소 IC 없음: seed의 탄소풀은 cold-start 임의값 그대로(§9d). 4~10 cycle 예상.
