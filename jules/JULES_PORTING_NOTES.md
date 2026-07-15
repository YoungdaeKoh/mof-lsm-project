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
