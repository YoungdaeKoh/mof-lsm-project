# JULES vn7.4 Porting & Gridded/DGVM Run Notes (climate00)

**작성: 2026-06-30 (ydkoh).** JULES vn7.4를 climate00에서 **0.5° 전구 gridded** 로 돌리고
**DGVM(TRIFFID)** 까지 구동한 전 과정 기록. "porting 이후 안 됨"의 정체와 해결을 박제한다.

관련: 본 repo `CLAUDE.md` §8(Known issues), 서버 run dir `~/JULES_runs/test_gridded_gf/`,
working namelist 사본 `jules/runs/test_gridded_gf_dgvm/`(DGVM)·`_static/`(static-veg diff).

---

## 0. TL;DR (결론)

- **"porting 이후 안 됨"의 진짜 원인** = JULES 빌드 실패가 아니라 **Intel netcdf 런타임 깨짐**.
  `libnetcdf.so.13`이 `__libm_feature_flag` 심볼을 요구하는데, 시스템의 유일한 Intel 런타임
  (oneAPI 2022.0.1, "intel21" 모듈도 실제로는 이걸 가리킴)의 libimf에 그 심볼이 **없음**.
  → admin이 netcdf 빌드 후 컴파일러를 교체해 깨진 상태. LD_LIBRARY_PATH를 어떻게 바꿔도 해결 불가.
- **해결 = gfortran + netcdf-4.6.1_gcc85 로 재빌드** (LM4와 동일 경로). Intel 안 씀.
- 그 위에 namelist를 vn7.4 규격으로 고치니 **0.5° 전구 맵 런 + DGVM 둘 다 성공**.
- 빌드 ~15s, 1개월 전구 0.5° serial run ≈ **81분**.

---

## 1. 환경 / 경로

| 항목 | 값 |
|---|---|
| 소스 | `~/jules-vn7.4/` (vn7.4, svn checkout) |
| 빌드 exe | `~/jules-vn7.4/build/bin/jules.exe` (gfortran, ~54M) |
| FCM | `~/fcm/bin/fcm` |
| run dir (테스트) | `~/JULES_runs/test_gridded_gf/` |
| forcing | `/data1/backup/ChanhyukChoi/002.JULES_RUN/INPUT_DATA/monitoring/92.GPCPobs_ERA5obs/%y4-%m2.nc` (ERA5, 0.5°, 6-hourly, standard calendar) |
| ancil (grid/frac/soil) | `/data1/backup/ChanhyukChoi/002.JULES_RUN/JULES/ancil/` (grid_info.nc, frac.nc, soil.nc) |
| 컴파일러 | gfortran 8.5.0 (`/usr/bin/gfortran`, system) |
| netcdf | `/usr/local/netcdf/4.6.1_gcc85` (+ hdf5 `/usr/local/hdf5/1.10.5`, zlib `/usr/local/zlib/1.2.11`) |

---

## 2. 빌드 (gfortran)

스크립트: `jules/scripts/build_jules_gfortran.sh` → 서버에서 `bash build_jules_gfortran.sh`.

핵심 환경변수 (fcm-make의 `custom` 플랫폼이 이 env들을 읽음):
```bash
export PATH=$HOME/fcm/bin:$PATH
export JULES_PLATFORM=custom
export JULES_COMPILER=gfortran        # etc/fcm-make/compiler/gfortran.cfg 사용 (gcc8.5 → 10_plus 아님)
export JULES_BUILD=normal
export JULES_MPI=nompi                 # serial. (MPI 빌드는 미해결, §8)
export JULES_OMP=noomp
export JULES_NETCDF=netcdf
export JULES_NETCDF_PATH=/usr/local/netcdf/4.6.1_gcc85
export JULES_NETCDF_INC_PATH=/usr/local/netcdf/4.6.1_gcc85/include
export JULES_NETCDF_LIB_PATH=/usr/local/netcdf/4.6.1_gcc85/lib
export JULES_LDFLAGS_EXTRA="-L/usr/local/hdf5/1.10.5/lib -L/usr/local/zlib/1.2.11/lib -lhdf5_hl -lhdf5 -lz -lcurl"
export JULES_FFLAGS_EXTRA="-Wno-argument-mismatch"   # ★ gcc8.5: -fallow-argument-mismatch(10+) 는 없음!
cd $HOME/jules-vn7.4 && fcm make --new -j 4 -f etc/fcm-make/make.cfg
```

빌드 함정:
- **`-fallow-argument-mismatch`는 gfortran 10+ 전용** → gcc8.5에서 "unrecognized command line option"으로 전부 실패.
  gcc8.5에선 **`-Wno-argument-mismatch`** 사용 (`-Werror`가 켜져 있어 argument mismatch를 error에서 warning으로 강등).
- `fcm make --new` 로 이전(Intel) 빌드 산출물 무시하고 새로.
- parallel_mod.F90 의 미초기화 local 패치(ntasks_x/y, task_nx/y, x/y_start = 0)는 이미 적용돼 있음
  (`grep -n "ntasks_x = 0" src/control/standalone/parallel/parallel_mod.F90`). gfortran에도 무해.

검증: `ldd ~/jules-vn7.4/build/bin/jules.exe | grep "not found"` → 없어야 정상.

---

## 3. 실행 (gridded)

스크립트: `jules/scripts/run_jules_gf.sh`. 런타임 라이브러리 경로가 핵심:
```bash
export LD_LIBRARY_PATH=/usr/local/netcdf/4.6.1_gcc85/lib:/usr/local/hdf5/1.10.5/lib:/usr/local/zlib/1.2.11/lib:$LD_LIBRARY_PATH
cd ~/JULES_runs/test_gridded_gf && time ~/jules-vn7.4/build/bin/jules.exe
```
- **Intel oneAPI는 절대 source 하지 말 것** (그게 `__libm_feature_flag` 깨짐의 원천).
- 백그라운드(81분): `nohup bash run_jules_gf.sh >& /tmp/jrun.log &` (tcsh 아닌 bash로).

격자 구성(`model_grid.nml`, 이미 찬혁님 설정 그대로 OK):
`grid_is_1d=.false.`, `nx=720, ny=360` (0.5° 전구), `l_coord_latlon=.true.`,
grid_info.nc 기반, `land_only=.true.`. 출력은 압축 land-vector(x=67209 land pts) + 2D `latitude(y,x)`/`longitude(y,x)`.

---

## 4. Namelist 수정 — vn7.4 규격 맞추기 (디버깅 순서대로)

찬혁님 namelist는 다른 JULES 버전/커스텀 기준이라 vn7.4 + gfortran(엄격한 namelist reader)에서 줄줄이 실패.
**모든 config 오류는 init에서 <1초 만에 fatal** → 빠르게 고치고 재시도 가능 (성공해야만 81분).

### 4-1. drive.nml (ERA5 forcing) — 전면 재작성
무효 항목 제거: `l_emdef_file`, `l_tfor_mean_file`, `l_var_latlon`, `tname`, `units`, `tinc`.
- `tinc=21600` → **`data_period=21600`** (6-hourly).
- **var 식별자**가 netCDF 변수명이 아니라 JULES 내부 식별자여야 함:
  `Tair→t, Qair→q, PSurf→pstar, Wind→wind, LWdown→lw_down, SWdown→sw_down, Rainf→precip`
  (`var_name`은 netCDF 변수명 그대로: Tair, Qair, ...).
- 필수 추가: `z1_uv_in=10.0`, `z1_tq_in=2.0` (풍속/기온 기준고도, 없으면 fatal),
  `diff_frac_const=0.4` (SW 직접 공급 시), `t_for_snow=274.0`, `t_for_con_rain=293.15` (총강수 분리).
- `interp` = smoke용 전부 `'nf'` (no-interpolation; look-ahead 불필요 → 안전). 정식 런은 상태변수 'i' 검토.

### 4-2. timesteps.nml
`main_run_start/end` 를 forcing 기간과 일치(테스트: 2010-01-01 → 2010-02-01). `timestep_len=1800`.

### 4-3. jules_vegetation.nml
- `can_rad_mod=6` 인데 **`ilayers` 누락** → init에서 imdi(-32768)로 albpft `rnet_dir(0:ilayers)` 배열 크래시.
  **`ilayers=10` 추가** 필수.
- DGVM 켤 때(§5): `l_phenol=.true., phenol_period=1`, `l_triffid=.true., triffid_period=10`.
  (`l_phenol`→phenol_period, `l_triffid`→triffid_period 음수면 fatal.)

---

## 5. DGVM(TRIFFID) 켜기 — 추가 요구사항

static-veg(`l_triffid=.false.`)는 §4까지만 하면 맵 런 OK.
DGVM은 아래를 추가로 요구 (역시 init에서 빠른 fatal로 하나씩 드러남):

1. **soil_bgc_model=2** (4-pool RothC). `soil_bgc_model=1`(단일풀)이면
   `CHECK_JULES_SOIL_BIOGEOCHEM: TRIFFID needs a prognostic soil model` fatal.
   - `jules_soil_biogeochem.nml` 추가: `kaps_4pool=3.22e-7, 9.65e-9, 2.12e-8, 6.43e-10`
     (각 1e-12~1e-4 범위), `n_inorg_turnover=1.0` (0.01~100), `bio_hum_cn=10.0` (1~301).
   - cs 초기값은 4-pool로 자동 broadcast (initial_conditions의 const_val=10.0).
2. **triffid_params.nml** 에 vn7.4 신규 PFT별(5개) 파라미터 추가 (없으면 init_triffid fatal):
   `alloc_fast_io=5*0.6, alloc_med_io=5*0.3, alloc_slow_io=5*0.1,`
   `dpm_rpm_ratio_io=0.25 0.25 0.67 0.67 0.33, retran_r_io=5*0.2, retran_l_io=5*0.5`.
3. **initial_conditions.nml** 에 `canht` 추가 (`const_val=1.0`).
   - JULES는 누락 prognostic을 default dict로 자동 채우지만 **canht/frac은 default가 없어** 명시 필요.
4. **areal 경쟁(frac 진화)** 은 `l_veg_compete=.true.` 시 `frac`을 prognostic IC로 요구
   (합=1 제약이라 const 불가) → **테스트는 `l_veg_compete=.false.`** 로 회피.
   이 모드에서도 TRIFFID의 탄소역학·phenology·LAI/수고 성장은 전부 가동(frac만 ancil 고정).
   **전면 경쟁은 frac IC를 frac.nc(use_file)로 끌어오는 별도 처리 필요 — 후속 TODO.**

출력 검증(`test_dgvm_gf.monthly.2010.nc`, 1개월):
차원 `scpool=4, pft=5` 확인. lai 0.31–2.33(PFT 분화), canht 0.33–**9.38 m**(수고 성장),
cv 0–3.12 kgC/m², gpp_gb max ~9.9e-8 kgC/m²/s(≈3 kgC/m²/yr), npp_gb 양/음 혼재 → **DGVM 정상 작동**.

---

## 6. 산출물 위치

| 위치 | 내용 |
|---|---|
| `~/JULES_runs/test_gridded_gf/` (서버) | working run dir (현재 DGVM 설정) |
| `~/JULES_runs/test_gridded_gf/output/test_gridded_gf.*` | static-veg 맵 런 출력 + restart |
| `~/JULES_runs/test_gridded_gf/output/test_dgvm_gf.*` | DGVM 맵 런 출력 + restart(4-pool) |
| `jules/runs/test_gridded_gf_dgvm/` (repo) | DGVM working namelist 전체 사본 |
| `jules/runs/test_gridded_gf_static/` (repo) | static-veg diff 파일(jules_vegetation/output/timesteps/drive) |
| `jules/scripts/build_jules_gfortran.sh` | gfortran 빌드 스크립트 |
| `jules/scripts/run_jules_gf.sh` | 실행 스크립트(LD_LIBRARY_PATH 포함) |

---

## 7. 재현 절차 (요약)

```bash
# 1) 빌드 (서버)
scp build/build_jules_gfortran.sh climate:/tmp/ ; ssh climate "bash /tmp/build_jules_gfortran.sh"
# 2) run dir 준비: namelist 세트(jules/runs/test_gridded_gf_dgvm/) 를 ~/JULES_runs/<case>/ 로
# 3) 실행 (서버, bash)
ssh climate "cd ~/JULES_runs/<case> && nohup bash run_jules_gf.sh >& /tmp/run.log &"
# 4) 완료 확인: output/*.monthly.YYYY.nc 생성, 'run 종료 (exit=0)'
```

---

## 8. Spin-up 로드맵 (2026-07 결정)

**3단계 전략** (LM4와 동일 철학, 각 단계가 다음의 warm-start IC(dump)를 넘김):
1. **static-veg + GSWP3 30년(1981-2010) cycling** — JULES **내장 spin-up**(`JULES_SPINUP`, §9) 사용,
   smcl+t_soil 수렴판정 자동 종료 → 평형 IC. climate01 단일 job.
2. **ERA5(WFDE5)로 스핀업 1회 더** — production forcing에 적응시킨 IC.
3. **그 IC로 warm-start → dynamic vegetation(TRIFFID) spin-up** (장기, 수백~1000+년).

- forcing: GSWP3 v1 `/data1/CESM2_INPUT/.../GSWP3.0.5d.v1.c170516/` → 심링크 팜
  `/data2/ydkoh/jules_gswp3_forcing/`(3그룹 flat) + drive.nml `%vv` 템플릿(§9). noleap.
- ★ **최적화 빌드 필수**: gfortran.cfg `$fflags_common`에 `-fbounds-check` 박혀 있어 normal/fast 모두 느림.
  spin-up 전 `-fbounds-check` 제거 + `-O3`(fast) 재빌드 → ~10-30× (현재 debug는 16 hr/model-yr).

## 9. GSWP3 forcing (JULES drive.nml, 심링크+%vv 방식)

`jules/runs/test_gswp3_static/` 참조. GSWP3-CLM 3파일그룹을 심링크 팜에 flat하게 모아 `%vv` 템플릿으로 읽음:
```
data_period = 10800          # 3-hourly
file = "/data2/ydkoh/jules_gswp3_forcing/clmforc.GSWP3.c2011.0.5x0.5.%vv.%y4-%m2.nc"
var      = 't','q','pstar','wind','lw_down','sw_down','precip'
var_name = 'TBOT','QBOT','PSRF','WIND','FLDS','FSDS','PRECTmms'
tpl_name = 'TPQWL','TPQWL','TPQWL','TPQWL','TPQWL','Solr','Prec'   # %vv ← tpl_name (파일태그)
```
- timesteps.nml `&JULES_TIME`: `l_leap=.false.`(GSWP3 noleap), `l_360=.false.`.
- 내장 spin-up: `&JULES_SPINUP max_spinup_cycles, spinup_start, spinup_end, terminate_on_spinup_fail, nvars, var, use_percent, tolerance` (timesteps.nml에 jules_time 다음으로). var=smcl/t_soil.
- ★ 검증됨: JULES가 Solr/Prec/TPQWL 3그룹 다 열고 init 완료(2026-07). 심링크라 디스크 0.

## 10. 미해결 / TODO

- **MPI 빌드 → ✅ 해결됨 (§11, 2026-07-15)**: serial 최적화 throughput = **24.8분/model-month ≈ 5 hr/model-yr** (30년 cycle ~6일).
  장기 spin-up·dynamic veg엔 MPI 필수. 과거 실패(`PMPI_Comm_size: Invalid communicator`)는 Intel netcdf 시절.
  ★ **레퍼런스 발견(2026-07-02)**: 찬혁님이 이미 **MPI JULES vn7.7을 mpich 40코어로 구동 중**
  (`/home/ChanhyukChoi/JULES_MODEL_VERSIONS/jules-vn7.7/build/bin/jules.exe`,
  machinefile `/data1/backup/ChanhyukChoi/002.JULES_RUN/ANAL/mpich_1.hosts`).
  → 맨땅 디버깅 대신 찬혁님 빌드 config(mpich, JULES_MPI 설정)를 참고해 vn7.4 MPI 빌드 시도.
- **전면 areal 경쟁(frac 진화)**: §5-4, frac IC를 frac.nc에서 use_file로 끌어오는 처리 필요.
- **DGVM spin-up**: 위 로드맵 3단계. 현재 1개월 테스트만.
- ERA5 forcing 1979 파일 time coord 손상 이력(1978-12 proleptic, 1979-01 첫 time ~Jan23).
  2010·GSWP3는 정상. 1979부터 ERA5로 돌릴 땐 재확인.

## 11. ★★ MPI 빌드 성공 (2026-07-15) — Invalid communicator 해결

**한 줄:** gfortran + **mvapich2-2.3.4(gcc85)** clean 빌드로 `PMPI_Comm_size: Invalid communicator` 해결. JULES가 4-task 병렬로 init 완주 확인. 찬혁님 mpich 레퍼런스(§10)와 같은 계열(mvapich2=MPICH 파생).

### 11.1 근본 원인
`utils/mpi_dummy/mpi_mod.F90`의 **가짜 `mpi_comm_world = 1`(INTEGER PARAMETER)** 이 real MPI 빌드에 섞여 들어감. dummy 모드에선 `mpi_comm_size`가 stub이라 comm 무시 → 안 터짐. real MPI에선 정수 1이 유효 communicator 아님 → 즉시 `Invalid communicator`. (`jules.F90`: `USE mpi, ONLY: mpi_comm_world` → dummy값 1 → `mpi_local_comm=1` → `parallel_mod` `mpi_comm_size(1,...)` FATAL.)

### 11.2 수정 (4가지 조합)
1. **일관 스택**: gfortran(gcc8.5) + **mvapich2-2.3.4 gcc85**(`/usr/local/mpi/gcc85/mvapich2-2.3.4`) + netcdf-4.6.1_gcc85 + hdf5-1.10.5_gcc85. 과거 실패 조합(mvapich2+intel=netcdf깨짐, OpenMPI+gcc85)과 달리 **mvapich2+gcc는 미시도였고, Noah-MP가 쓰는 안정 MPI**. mpif90 `-show` = `gfortran ... -lmpifort -lmpi`(mvapich2) 확인 필수.
2. **`JULES_MPI=mpi` + clean 빌드(`fcm make --new`)** → `mpi/mpi.cfg`가 `$compiler=$compiler_mpi=mpif90`, mpi_dummy 제외. incremental 빌드는 옛 dummy 잔재 남으니 `--new` 필수.
3. **`JULES_COMPILER=gfortran`** (gnu 아님 — `compiler/gfortran.cfg`).
4. **netcdf static libs에서 curl 제거**: `ncdf/netcdf.cfg` `$ncdf_libs_static`에서 `curl` 삭제(백업 `.bak_curl`). MPI 빌드는 static netcdf 강제라 `-lcurl` 나오는데 `/usr/lib64/libcurl.so`가 링크 순서상 안 잡힘. offline 로컬파일엔 curl 불필요(serial은 dynamic이라 무관했음).

★ **빌드 래퍼 = 실행 mpirun 일치 필수**: 둘 다 mvapich2-gcc85. (ldd가 로그인노드서 Intel IMPI `libmpi.so.12` 잡는 건 MPICH ABI 호환일 뿐; `LD_LIBRARY_PATH`에 mvapich2 넣으면 mvapich2 링크 확인.)

### 11.3 검증 (잡 2943-2944, climate01 -np 4)
- **Invalid communicator 사라짐 ✓.** `{MPI Task 0..3}`으로 병렬 실행, JULES_DRIVE·OUTPUT_PROFILE·init_vars_tmp 전부 4-task 통과.
- 마지막 `file_ts_seek_to_datetime: No data for datetime`는 **serial도 동일하게 나는 forcing 시각 이슈**(§10, 1978-12 time coord)라 MPI 무관.
- exe: `build/bin/jules.exe.mpi_mvapich2`(45MB, mvapich2). serial은 `jules.exe.serial_bak` 보존.
- 부수: `drive.nml`의 `interp_wind = .true.`는 vn7.4에 없는 무효 변수 → 제거(per-변수 interp은 `interp(N)` 배열로 처리).

### 11.4 빌드 레시피 (재현)
`JULES_porting/build_jules_mpi.pbs` (climate01). 핵심 env: `PATH=$MV/bin:$PATH`(MV=mvapich2-gcc85), `JULES_COMPILER=gfortran`, `JULES_MPI=mpi`, netcdf/hdf5=gcc85, `JULES_LDFLAGS_EXTRA="-L/usr/lib64 -L.../hdf5.../lib -lhdf5_hl -lhdf5 -lz -L$MV/lib -lmpifort -lmpi"`, `fcm make --new`. 실행: mvapich2 mpirun + `LD_LIBRARY_PATH=$MV/lib:netcdf_gcc85/lib` + `MV2_ENABLE_AFFINITY=0`.

### 11.5 임팩트 / 다음
- JULES 48-rank MPI 가능 → **1° 전구가 serial 16h/년에서 대폭 단축**. 1차년도 "JULES 부분진단" 제약 해소.
- 다음: (1) forcing 시작날짜/time-coord 정리(1979부터 또는 GSWP3), (2) **1° JULES forcing 필요** — 현 JULES GSWP3는 0.5°만(§9), 1°는 regrid 필요, (3) 48-rank 1° spin-up.

## 12. ★ 1° GSWP3 forcing 생성 (JULES 1° 런용, 2026-07-15)

**배경:** JULES는 standalone이라 forcing을 모델격자로 자동 regrid 안 함(CLM5·LM4는 CDEPS가 regrid). 1° JULES 런엔 1° forcing 필수. 기존 JULES GSWP3는 0.5°만(§9). Noah-MP 1° forcing은 LDASIN 포맷이라 공유 불가.

**방법: CDO conservative remap (0.5°→1°).** GSWP3는 전구 완전자료(100% 유효, ocean fill 없음)라 conservative remap 안전.
- **★ NCL area_conserve_remap 폐기**: 적도 1개 위도행(lat 0.5°) 전체가 0 K 되는 버그 + Prec 그룹 dim 에러. CDO로 전환.
- **★ CDO의 LONGXY 2D좌표 거부** ("Unsupported generic coordinates") → **소스 grid 명시로 우회**: `src_grid_0.5.txt`(gridtype=lonlat, 720×360, xfirst=0.25 xinc=0.5, yfirst=-89.75 yinc=0.5) + `cdo remapcon,r360x180 -setgrid,src_grid -selname,VARS in out`.
- **★ climate01에 `libgfortran.so.3` 없음**(perl bigint 때와 같은 계산노드 패키지 부족) → 로그인노드 `/usr/lib64/libgfortran.so.3`를 `~/lib`에 복사 + `LD_LIBRARY_PATH`. (단 CDO는 netcdf_gcc85만 필요, NCL만 so.3 필요.)
- **★ partial-write 함정**: 쓰는 중 파일 읽으면 0 K/변수누락으로 오판(WFDE5 HDF와 동일). 완성본만 검증.

**구성:** 3그룹 CLM포맷 유지 — TPQWL(TBOT/QBOT/PSRF/WIND/FLDS)·Solr(FSDS)·Prec(PRECTmms). 출력 `/data2/ydkoh/jules_gswp3_1deg/clmforc.GSWP3.c2011.1x1.{grp}.YYYY-MM.nc`, 1° 전구 r360x180(360×180, lon 0~359, lat -89.5~89.5).
- 기간 1981-2010(cycling spin-up용, 30년×12×3=1080). 배치 `gswp3_cdo_batch.pbs`(climate01), ~1시간.
- 검증: TBOT 154~328 K, FSDS 0~1400, PRECTmms 0~0.015, 0 K 셀 0.

**다음(JULES 1° 연결):** ① `model_grid.nml` nx=360 ny=180. ② **1° grid_info.nc**(land mask + 좌표) 필요 — 0.5° grid_info 재regrid 또는 표준 1° land mask. ③ drive.nml `%vv` 경로를 1° 파일로. ④ 48-rank MPI(§11) 1° spin-up.

## MPI 빌드 + 병렬 netCDF (2026-07-29, 해결)

**결론: `/usr/local/netcdf/4.6.1_intel21_mv234` + `/usr/local/hdf5/1.10.5_intel21_mv234` + mvapich2로 재빌드하면 된다.** 빌드 스크립트 `jules/scripts/build_jules_pnc.sh` (서버 `~/JULES_runs/build_jules_pnc.sh`).

**원인**: JULES는 출력 파일을 열 때 **무조건** MPI communicator를 넘긴다 — `internal_open_output_file.inc:130`이 `mpi_local_comm`을 `file_ts_open`에 전달하고, `file_ncdf_open.inc:87`이 `IOR(nf90_clobber, nf90_netcdf4, nf90_mpiio)`로 생성한다. **런타임 스위치가 없다.** 따라서 MPI 빌드는 병렬 지원 netCDF가 필수인데, 기존 빌드가 가리키던 `/usr/local/netcdf/4.6.1_intel21`은 `nc-config --has-parallel -> no`였다 → 첫 출력 쓰기에서 `"Parallel operation on file opened for non-parallel access"`로 사망.

**시스템에 이미 있는 병렬 스택** (직접 확인):

| | 경로 | 확인 |
|---|---|---|
| netCDF | `/usr/local/netcdf/4.6.1_intel21_mv234` | `--has-parallel -> yes` |
| HDF5 | `/usr/local/hdf5/1.10.5_intel21_mv234` | `libhdf5.settings`에 `Parallel HDF5: yes` |
| MPI | `/usr/local/mpi/intel21/mvapich2-2.3.4` | netCDF/HDF5가 이걸로 빌드됨 |

**★ 함정 1: `ldd`만 보고 판단하지 말 것.** 새 exe를 그냥 `ldd`하면 **비병렬** `4.6.1_intel21`과 oneAPI MPI를 가리킨다. 병렬/비병렬 netCDF가 **같은 soname**(`libnetcdf.so.13`)을 쓰고, mvapich2와 oneAPI MPI도 **둘 다 `libmpi.so.12`**(MPICH ABI)라서, **`LD_LIBRARY_PATH`에서 먼저 오는 쪽이 이긴다.** 실행 환경과 같은 `LD_LIBRARY_PATH`를 걸고 `ldd`해야 진짜 링크 대상이 보인다.

**★ 함정 2: `nc-config --flibs`가 틀렸다.** mv234 설치의 `--flibs`가 `-L/usr/local/netcdf/4.6.1_intel21/lib`(비병렬)를 가리킨다. gcc85 설치도 같은 문제(intel21 경로를 뱉음). **nc-config 출력을 그대로 빌드에 쓰면 안 되고 경로를 직접 지정할 것.**

**검증 (2일 시험 런, `~/JULES_runs/test_out36`, `mpirun -np 4`)**: rc=0, 22.7초 완주.
- 프로파일 4개 전부 생성(`monthly`·`daily`·`daily_max`·`daily_min`), 월별 파일에 **좌표 4 + 데이터 35 = 39 변수** 정확히.
- 값 정상: `ftl_gb` 평균 36.2 W/m²(−230~492), `latent_heat` 38.7(−84~344), `t1p5m_gb` 223~312 K, `snow_frac` 0~1, `frac` 평균 0.1111(=1/9, 지면타입 9개 합=1).
- **물수지 정합**: `runoff` 9.8135e-5 = `surf_roff` 1.1283e-6 + `sub_surf_roff` 9.7006e-5 → `extract_var.inc:978`의 정의가 출력에서 확인됨.
- 처리량 참고: 4랭크에서 2일 22.7초(초기화 포함) → 대략 70분/model-yr 수준. serial 81분/월(≈16 h/yr) 대비 크게 개선이나 **정식 벤치는 별도 필요**.

**미해결로 남긴 것**: `zw`(지하수면)는 TOPMODEL 전용이라 `l_top=.false.`인 현재 설정에선 출력 목록에서 제외했다. `l_top=.true.`로 바꾸면 되돌릴 것.

---

## (이력) MPI 재빌드 이후 출력 쓰기 실패 (2026-07-29, 위에서 해결됨)

`~/jules-vn7.4/build/bin/jules.exe`는 **2026-07-15 MPI(gfortran+mvapich2) 재빌드본**이고, 그 뒤로 성공한 런이 없다. 마지막 정상 출력은 `test_gridded_gf/output/` 2026-06-30 (serial 빌드 시절).

**증상** (`~/JULES_runs/test_out36`, 2일 시험):
```
[INFO] init: Initialisation is complete
[INFO] file_ncdf_open: Opening .../out36test.monthly.2010.nc for writing
[FATAL ERROR] file_ncdf_open: NetCDF error - NetCDF: Parallel operation on file
              opened for non-parallel access
```
- exe를 직접 실행하면 같은 지점에서 죽고, `mpirun -np 1`로 띄워도 동일.
- 원인 추정: 링크된 netCDF(`4.6.1_gcc85`)가 **병렬 I/O 없이 빌드**됐는데 MPI 빌드 JULES가 병렬 접근 경로를 탄다.
- 후보 대응: ① serial(nompi) 빌드를 별도 exe로 복구 ② 병렬 netCDF(pnetcdf/HDF5 parallel) 링크로 재빌드 ③ JULES 쪽 병렬 I/O 스위치 확인.

**★ 단, 출력 변수명 검증은 이 실패와 무관하게 완료됐다.** JULES는 초기화 단계에서 출력 식별자를 검증한다 — `register_output_profile.inc:354`가 `get_var_id()`를 호출하고, 미등록 이름이면 `get_var_id.inc:49`에서 `"Unrecognised variable identifier"`로 즉사한다. **`init: Initialisation is complete`가 찍혔다 = 확장한 35변수 × 2 프로파일 + 일최고/최저 2개가 전부 유효**하다는 뜻(`jules/runs/test_gridded_gf_dgvm/output.nml`).

**함께 확인된 것**: `zw`(지하수면)는 TOPMODEL 전용이라 `l_top=.false.`인 현재 설정에선 사용 불가 → 목록에서 제외함. `l_top=.true.`로 바꾸면 되돌릴 것.

## 13. ★★ 1° ancillary 생성 — grid_info / soil / frac (2026-09-28)

§12에서 1° GSWP3 forcing만 만들어 두고 **1° ancil이 없어 두 달 멈춰 있던 지점**을 해소.
스크립트 `jules/scripts/make_grid_info_1deg.py` (서버 산출물 `~/JULES_runs/ancil/global_1deg/`):
`grid_info_1deg.nc`, `soil_1deg.nc`(9필드), `frac_1deg.nc`(9타일).

- **JULES는 index로 맞춘다 — 좌표로 안 맞춘다.** forcing과 ancil의 배열 순서가 같아야 함.
  1° forcing 격자는 **lon 0..359 / lat −89.5..89.5**, 0.5° ancil은 **lon −179.75..179.75** →
  집계 전에 0–360으로 roll. 안 하면 사하라가 태평양에 놓이는데 **조용히** 돌아감.
- **land mask 규칙**: 0.5° land_fraction은 이미 0/1 마스크(67,209셀). JULES는 `land_fraction > 0`이면
  **그 박스를 100% 육지로 간주**(User Guide model_grid.nml) → 2×2를 "any"로 모으면 해안선이 1° 부풀음.
  **다수결(4칸 중 2칸 이상)** 채택 → 1° 육지 **17,295셀**(기대치 67,209/4 = 16,802과 정합).
- **grid-verify 통과 (2026-09-28)**: ① 좌표 lat 오름차순·lon 0–359, forcing 격자와 **배열 동일**(np.array_equal True)
  ② 원본배열 index-space 플롯 = 정상 세계지도(lon 0 시작, 아프리카 좌측) ③ soil/frac 유효셀이 육지마스크와 **정확히 일치**(17,295),
  육지 밖 유효값 0, **frac 9타일 합이 모든 육지셀에서 1.000** ④ 박스검정 사하라 1.00 / 태평양 0.00 / 아마존 1.00
  ⑤ 값·결측(-1e20) 정상.
- **★ 남극이 없다**: 0.5° 원본 ancil(찬혁님)에 남극 육지가 아예 없음(60S 이남 0셀). Noah-MP의 비빙설 육지와 대조하면
  60S 이남 양쪽 다 0이라 **정합**(Noah 남극은 전부 IGBP 15 = ice). 다중 LSM 비교는 어차피 빙상 제외이므로 문제 없으나,
  JULES 단독 전지구 수지에는 남극이 빠진다는 점 기록.
- Noah-MP 1° 비빙설 육지(14,717)와 셀단위 불일치 2,740(4.2%): 대부분 **JULES-only**이고 60–90N에 1,413 집중
  = 그린란드·북극 도서(Noah는 ice로 분류) + 해안 1셀. 설명되는 차이.
- **★ 검증 중 잡은 함정(내 실수)**: Noah-MP `XLONG`은 **0.25..179.25 다음 −179.75..−0.75**로 이미 0–360 순서로 감겨 있다.
  음수 개수만 보고 roll을 한 번 더 걸었더니 불일치가 2,740 → 24,269로 폭증. **"음수가 있으니 −180–180"은 증거가 아니다.**

**다음 (1° 런 착수)**: ① `model_grid.nml` nx=360 ny=180 + ancil 경로를 `global_1deg/`로 ② `ancillaries.nml`의 soil/frac 경로 교체
③ `drive.nml` `%vv`를 `/data2/ydkoh/jules_gswp3_1deg/`로 ④ initial_conditions 확인 ⑤ 48-rank MPI(§11) 1° spin-up.

## 14. ★★★ 1° 런 성공 — 1개월 smoke (2026-09-28, job 8495 @climate02)

`~/JULES_runs/prod_1deg_test` (repo `jules/runs/prod_1deg_test/`). base = `test_out36`(MPI+병렬netCDF 검증본, TRIFFID on, cold start).
**1981-01 1개월, 8랭크, 50초 완주(rc=0, FATAL 0)**. 출력 4프로파일 + dump.

**바꾼 파일 6개**: `model_grid.nml`(nx=360/ny=180, grid_info 2곳) · `ancillaries.nml`(soil/frac → global_1deg) ·
`drive.nml`(GSWP3 1° 템플릿, **data_period 21600→10800**, 1981) · `timesteps.nml`(1981-01) · **`output.nml`(run_id/output_dir)** ·
실행 스크립트. `initial_conditions.nml`은 cold start(상수)라 그대로 — 0.5° dump 재사용 금지 경고는 애초에 해당 없음.

**막혔던 4단계 (전부 환경·자료 문제, 코드 아님)**
1. PBS 스크립트에 **shebang 없음** → 로그인셸 tcsh로 실행돼 `> log 2>&1`이 `Ambiguous output redirect`. `#!/bin/bash` 필수.
2. **`libifport.so.5` 없음(rc=127)**: mv234 netCDF/HDF5가 Intel 빌드라 exe가 ifort 런타임을 요구하는데, 비대화형 셸에서 제출한
   PBS 잡엔 oneAPI 환경이 없음 → `LD_LIBRARY_PATH`에 `/usr/local/intel/oneapi/compiler/2022.0.1/linux/compiler/lib/intel64_lin` 추가.
3. **★ `init_ic: Land ice points and soil points are mutually exclusive`** — 1° ancil 재격자화의 부작용. `init_ic.inc:906`은
   `frac(ice) > 0`이면 즉시 빙하점으로 보고, `frac(ice) ≠ 1`이면 또 에러. 2×2 평균이 빙하 가장자리에 0.25/0.5/0.75를 만듦.
   → **다수결**: ≥0.5면 순수빙하(ice=1, 나머지 0), <0.5면 빙하 조각 제거 후 8타일 합=1 재정규화. (834 순수빙하, 61셀 정리)
4. **★ 그것만으론 부족했다 — 토양 판정은 `sm_sat > 0`으로 따로 한다**(`init_ic.inc:932`). 0.5° 원본은 빙하셀에서
   b·sathh·satcon·sm_sat·sm_crit·sm_wilt=**0**, hcap=6.3e5·hcon=0.265·albsoil=0.75(얼음값) 규약인데 평균이 이걸 뭉갬.
   → 순수빙하 셀의 토양 수리특성을 0으로, 열특성을 얼음값으로 복원. **빙하 마스크는 실제로 파일에 쓰이는 배열에서 뽑을 것**
   (원본에서 따로 계산했더니 결측처리 차이로 16셀이 어긋남).

**검증**: x = **17,295** 육지점으로 1° 마스크와 정확히 일치. lat −55.5..83.5(남극 없음, §13 그대로), lon 0..359.
daily 31 records. 육지평균 `latent_heat` 35.1 W/m²(−102~303), `ftl_gb` 36.6, `t1p5m_gb` 273.2 K(211~311), `snow_frac` 0.38,
`frac` 평균 0.1111(=1/9, 9타일 합=1). **물수지 `runoff = surf_roff + sub_surf_roff` 최대오차 4.1e-10** — §MPI 검증과 동일한 정합.
처리량 8랭크 50초/월 → **≈10분/model-yr**, 48랭크면 더 빠름. 30년 cycle이 현실적.

**다음**: ① 1년 런으로 계절순환 확인 ② 48랭크 벤치 ③ GSWP3 1981–2010 cycling spin-up ④ 생산런 1979–2023(단 1° GSWP3 forcing은
현재 1981–2010만 — 1979–80·2011–23 추가 변환 필요).
