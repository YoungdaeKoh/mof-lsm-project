# KIOST-ESM2 (GFDL ESM4.5) — climate00 Porting Notes

**Model:** GFDL ESM4.5 coupled Earth-System Model, KIOST-ESM2 (v2b) configuration
**Origin cluster:** `tomo` (AMD EPYC Zen2, Intel19 + MVAPICH 4.0, SLURM/PBS)
**Target cluster:** `climate00` (Intel Xeon Gold 5418Y Sapphire Rapids, Intel oneAPI 21 + mvapich2-2.3.4, OpenPBS)
**Ported by:** ydkoh / 눈사람 — 2026-07-02 ~ 07-03 (coupled), 2026-07-06 (AMIP)
**Status:** ✅ **BUILD + SMOKE TEST 성공** — coupled(48-core, 1 model-day 결합적분) + **AMIP(24-core, 1 model-day, §11)** 둘 다 완주

> 목표 확정: climate00에서는 **빌드 + 동작·결합 검증(smoke test)까지**가 deliverable.
> 720-rank 생산 config는 climate00 자원(3노드×48=144코어)으로 불가 → 생산런은 별도 트랙.
> **AMIP 변형(§11): 동일 exe 재사용(재빌드 X), 해양 PE 0 + SPECIFIED_ICE로 SST 처방. 지면 진단엔 이쪽이 실용적.**

---

## 0. 한 줄 결론

GFDL ESM4.5(FV3-C96 대기 + AM4.5 물리 + MOM6 해양 + SIS2 해빙 + COBALT BGC + LM4 육상)를
climate00의 Intel oneAPI21 스택으로 **재빌드**하고, PE를 720→48로 축소한 config로
**1 model-day 결합적분을 conservation 정상(NaN 0, CFL~0.11, S 34.88, T 3.64)으로 완주**시킴.

---

## 1. 두 클러스터 환경 비교 (포팅 델타)

| 항목 | 원본 tomo | 타깃 climate00 | 조치 |
|---|---|---|---|
| CPU | AMD EPYC 7H12 (Zen2) | Intel Xeon Gold 5418Y (Sapphire Rapids, AVX2+AVX512) | ISA는 `-march=core-avx2` 유지(안전·이식성) |
| 컴파일러 | Intel 19 | Intel oneAPI 21 (`intel21/compiler-21`) | mk 컴파일러 경로 교체 |
| MPI | MVAPICH 4.0 | mvapich2-2.3.4 (`intel21/mvapich2-2.3.4`, Hydra 3.2.1) | wrapper 경로·MV2 env 교체 |
| netCDF | 4.9.2 | 4.6.1 (`intel21/netcdf-4.6.1`) | include/lib 경로 교체 |
| HDF5 | 1.12.2 | 1.10.5 (`intel21/hdf5-1.10.5`) | include/lib 경로 교체 |
| MKL | `/usr/local/intel/mkl` | oneAPI (`$MKLROOT=/usr/local/intel/oneapi/mkl/latest`) | lib 경로 교체, soname shim 삭제 |
| 배치 | SLURM(srun)/PBS | OpenPBS (`/opt/pbs/bin/qsub`, 큐 `workq`) | PBS `select` 헤더로 |
| 규모 | 6노드×120 = 720 rank | 3노드×48 = 144코어 (climate00/01/02) | **PE 대폭 축소** |
| 메모리 | — | climate01 ~503GB, climate02 ~251GB (넉넉) | OOM 문제 아님 |

**climate00 실측 경로 (핵심):**
- mvapich2 wrapper: `/usr/local/mpi/intel21/mvapich2-2.3.4/bin/mpif90` (`ifort` 기반)
- netCDF: `$NETCDF=/usr/local/netcdf/4.6.1_intel21` (nf-config/nc-config 제공, netcdf.mod 있음)
- HDF5: `/usr/local/hdf5/1.10.5_intel21`
- MKL: `$MKLROOT=/usr/local/intel/oneapi/mkl/latest` (F95 wrapper `libmkl_blas95_lp64.a`/`libmkl_lapack95_lp64.a` 존재)

---

## 2. 소스 수령 & 복호화

로컬 `/Volumes/data01/MOF_LSM_project/KIOST-ESM2/`에 암호화 tarball 2개 + 매뉴얼 제공:

| 파일 | 크기 | 내용 |
|---|---|---|
| `ESM4p5_KIOSTv2b.tar.gz.enc` | 37 MB | **빌드 트리**(src/ 1645파일, exec/, build 드라이버) |
| `KIOST-ESM2.tar.gz.enc` | 18 GB | **실행 디렉토리**(INPUT 663파일, config, run 스크립트) |
| `PORTING_AND_RUN_MANUAL.md` | — | tomo 기준 원본 매뉴얼 |

**복호화** (OpenSSL `Salted__` 형식 → `-aes-256-cbc -md sha256`):
```bash
openssl enc -d -aes-256-cbc -md sha256 -in <파일>.tar.gz.enc -out <파일>.tar.gz -pass pass:<PW>
```
- pbkdf2 아님(`-md sha256`이 정답). 서버 openssl 1.1.1k, 로컬 3.6.2 둘 다 가능.
- 빌드는 37MB 소스만으로 시작 가능 → 18GB INPUT는 빌드와 병렬 전송.

**서버 배치:**
- 빌드 트리 → `/home/ydkoh/ESM4p5_KIOSTv2b/` (`/home` 111T 여유)
- 실행 디렉토리 → `/home/ydkoh/KIOST-ESM2/`

---

## 3. Part A — 빌드 포팅

### 3.1 수정 파일 (2개, 원본은 `*.tomo.orig` 백업)

**`exec/env.sh`** — 모듈 스택 교체:
```bash
module purge
module load intel21/compiler-21
module load intel21/mkl
module load intel21/hdf5-1.10.5
module load intel21/netcdf-4.6.1
module load intel21/mvapich2-2.3.4
ulimit -s unlimited
```

**`exec/intel_tomo.mk`** — 5곳 경로 교체 (파일명은 유지: top-level Makefile이 하드코딩 참조):

| 위치 | tomo | climate00 |
|---|---|---|
| FC/CC/CXX/LD | `.../intel19/mvapich-4.0/bin/mpif90` | `/usr/local/mpi/intel21/mvapich2-2.3.4/bin/mpif90` |
| CPPFLAGS include | `hdf5/1.12.2_intel19 · netcdf/4.9.2_intel19` | `hdf5/1.10.5_intel21 · netcdf/4.6.1_intel21` |
| LIBS 기본 -L | `netcdf/4.9.2_intel19 · hdf5/1.12.2_intel19` | `netcdf/4.6.1_intel21 · hdf5/1.10.5_intel21` |
| HDF5 -L | `hdf5/1.10.5_intel19` | `hdf5/1.10.5_intel21` |
| MKL -L | `/usr/local/intel/{lib,mkl/lib}/intel64` | `$MKLROOT/lib/intel64` (=`/usr/local/intel/oneapi/mkl/latest/lib/intel64`) |

- `build_esm4.5.sh`는 수정 불필요(경로 없음). ISA `-march=core-avx2` 그대로.
- netcdf lib/flags는 mk가 `nf-config`/`nc-config`를 호출해 자동 해결(모듈 로드 후).

### 3.2 빌드 실행

```bash
# 모듈 초기화가 확실한 셸에서 nohup 백그라운드
cd /home/ydkoh/ESM4p5_KIOSTv2b
bash build_esm4.5.sh   # = cd exec; source env.sh; make clean; make -j 8 BLD_TYPE=PROD ISA="-march=core-avx2"
```
- 컴포넌트 순서: fms → atmos_phys → atmos_dyn → atmos_drv → lm4P → mom6 → sis2 → coupler
- **빌드 시간 ~14분** (`make -j 8`, GNU Make 4.2.1)

### 3.3 빌드 검증 (전부 통과)

```
바이너리   exec/fms_esm4.5_compile_v3_1007_fix.x  →  223 MB ELF64
컴포넌트   libfms 44M · libatmos_phys 68M · libmom6 157M · libsis2 30M · liblm4P 29M ... (8개 전부)
AVX2 지문  vfmadd 56,118 / %ymm 571,486   (매뉴얼 기준 "수만/수십만" 충족)
ldd        모든 공유 라이브러리 resolved (netcdf.so.13, hdf5.so.103, mkl_*.so.2, libimf.so)
```

---

## 4. Part B — INPUT 데이터

- 18GB `.enc` → 서버 전송(~3.5분) → 서버에서 복호화(19G tar) → 해제
- **`/home/ydkoh/KIOST-ESM2/` 20G, INPUT 663파일** (매뉴얼과 일치)
- **INPUT restart는 combined(layout-독립) 형태** (per-PE `*.res.nc.0000` 0개) → 새 layout으로 warm start 가능 ← 축소 포팅의 전제

---

## 5. Part C — 실행(run) 포팅 & PE 축소

### 5.1 왜 축소가 필요한가

기본 config = **720 rank** (대기 384 + 해양 336, concurrent). climate00은 144코어뿐 → 물리적 불가.
FMS ESM4.5 MPMD 구조 확인(SMALL/PROD 템플릿 대조):
- **대기 pelist** = FV3 + AM4.5 물리 + LM4 육상 + **SIS2 해빙** → `atmos_npes`
- **해양 pelist** = MOM6 + COBALT → `ocean_npes`
- 관계: `FV3 layout ×6 = land layout ×6 = SIS layout(2D 곱) = atmos_npes`, `MOM layout = ocean_npes`

### 5.2 축소 layout (720 → 48, concurrent 유지)

| 컴포넌트 | 파일 / nml | 원본 | 축소 | PE |
|---|---|---|---|---|
| FV3 대기 | `input.nml &fv_core_nml` layout | 8,8 (io 2,2) | **2,2 (io 1,1)** | 6×4 = 24 |
| LM4 육상 | `input.nml &land_model_nml` layout | 8,8 (io 2,2) | **2,2 (io 1,1)** | 대기와 공유 |
| SIS 해빙 | `SIS_layout` LAYOUT | 24,16 | **6,4** | 24 (=atmos) |
| MOM 해양 | `MOM_layout` LAYOUT | 21,16 | **6,4** | 24 |
| coupler | `input.nml &coupler_nml` | atmos_npes 384 / ocean_npes 336 | **24 / 24** | **총 48** |
| 런 길이 | `&coupler_nml` | months 1 / days 0 | **months 0 / days 1** | 1 model-day |

제약: FV3 nx,ny는 96(=npx-1)의 약수, MOM/SIS nx,ny는 720·576의 약수. 6·4=24 만족.

### 5.3 run 스크립트 (`run_kiost-esm2.sh`, 신규 작성)

원본 대비 **단순화**(모듈 load만, 하드코딩 LD_LIBRARY_PATH·MKL shim 삭제):
```sh
#PBS -N KIOST_ESM2_smoke
#PBS -q workq
#PBS -l select=1:ncpus=48:mpiprocs=48
source /etc/profile.d/modules.sh
module purge
module load intel21/compiler-21 intel21/mkl intel21/hdf5-1.10.5 intel21/netcdf-4.6.1 intel21/mvapich2-2.3.4
ulimit -s unlimited
export work_dir=/home/ydkoh/KIOST-ESM2 ; cd $work_dir
export MV2_SMP_USE_CMA=1
export MV2_IBA_EAGER_THRESHOLD=131072
export MV2_ENABLE_AFFINITY=0          # ← 중요 (아래 이슈 참고)
NP=`cat $PBS_NODEFILE | wc -l`
mpirun -hostfile $PBS_NODEFILE -np $NP ./fms_esm4.5_compile_v3_1007_fix.x > esm4p5.log 2>&1
```

### 5.4 실행 디렉토리 셋업
```bash
cd /home/ydkoh/KIOST-ESM2
# run-dir 바이너리를 climate00 빌드로 심링크 교체 (기존은 tomo 바이너리였음)
ln -sf /home/ydkoh/ESM4p5_KIOSTv2b/exec/fms_esm4.5_compile_v3_1007_fix.x .
rm -f libmkl_*.so.1        # tomo soname shim 삭제 (우리 바이너리는 .so.2 네이티브)
mkdir -p RESTART
qsub run_kiost-esm2.sh
```
- 수정 config 원본은 `input.nml.tomo.orig`, `MOM_layout.tomo.orig`, `SIS_layout.tomo.orig`, `run_kiost-esm2.sh.tomo.orig`로 백업.

---

## 6. 도중 해결한 이슈 (Troubleshooting)

| 증상 | 원인 | 해결 |
|---|---|---|
| **netcdf `__libm_feature_flag` 미해결 우려** (JULES 교훈) | libnetcdf.so가 심볼을 U로 참조 | oneAPI 컴파일러 런타임(libimf)이 링크 경로에 있어 **자동 해결**. gfortran 불필요 (JULES와 상황 다름). 사전 링크테스트로 확인 후 진행 |
| **MPI_Init `Fatal error` + abort** | mvapich2-2.3.4 Hydra가 `MV2_ENABLE_AFFINITY=1`을 oversubscription으로 오판 | **`MV2_ENABLE_AFFINITY=0`** (매뉴얼의 tomo 기본값 1은 mvapich-4.0용) |
| MKL soname 불일치 우려 | tomo 바이너리는 `libmkl_*.so.1` 요구 | 우리 바이너리는 oneAPI `.so.2` 네이티브 링크 → **shim 불필요**, 삭제 |
| SIS layout(384) ≠ ocean(336) "불일치" | SIS는 해양 아닌 **대기 pelist**에서 구동 | 축소 시 SIS layout = atmos_npes로 맞춤 |
| `FATAL_UNUSED_PARAMS over-ridden` 경고 | `MOM_override`의 의도적 override | **benign** (매뉴얼 §5), 무시 |
| tcsh SSH 리다이렉트 깨짐 | 원격 로그인 셸 tcsh | 복잡 명령은 `ssh climate 'bash -s' < script.sh` 패턴 |

---

## 7. Smoke test 결과 (검증 통과)

**job 2893, 축소 48-core config, 1 model-day:**

```
Total runtime      2566.6 s   (완주)
 ├ Initialization    613.4 s   (~10분, AM4.5 화학/복사 테이블 로딩 — 24 PE라 느림)
 ├ Main loop        1777.1 s   (~30분, 1일 결합적분)
 └ Termination       175.5 s   (~3분, restart 기록)
RESTART            129 파일 기록 (atmos/ocean/ice/land/cobalt)
time_stamp         401-1-1 → 401-1-2 (1일 완료)
ocean.stats        NaN 0 · En 0.338 · CFL 0.115 · SL -0.10 · S 34.885 · T 3.641  (매뉴얼 §4 기준 일치)
seaice.stats       정상 적분(step 12→18→24) · CFL 0.055–0.060 · NH ice area ~1.66e13 m² · NaN 없음
에러 마커          없음
```

→ **build → run → 결합적분 → restart** 전 경로 climate00 검증 완료.

---

## 8. 한계 & 참고

- **성능**: 1 model-day ≈ 43분(48코어) → 1 model-year ≈ 7.5일. **climate00은 검증용, 생산런 불가**(실측 확인).
- 생산런은 (a) 원본 tomo, (b) KISTI 누리온 등 대형 HPC 별도 트랙 필요.
- init 613s 중 상당수가 AM4.5 상호작용 화학 + 장파 복사 CO2 전달함수 테이블(`lw_gases_stdtf`) 파일 로딩 — PE 수와 거의 무관(파일 I/O 위주).
- 더 큰 검증이 필요하면 `days`를 늘리거나(수일~1개월) 2노드(96코어)로 layout 상향(FV3 2,4=48 등) 가능.

---

## 9. 파일 인벤토리 (climate00)

```
/home/ydkoh/ESM4p5_KIOSTv2b/            # 빌드 트리
├── exec/env.sh              (+ env.sh.tomo.orig)
├── exec/intel_tomo.mk       (+ intel_tomo.mk.tomo.orig)   ← climate00용으로 수정됨(파일명 유지)
└── exec/fms_esm4.5_compile_v3_1007_fix.x   223M 바이너리

/home/ydkoh/KIOST-ESM2/                 # 실행 디렉토리 (20G, INPUT 663)
├── run_kiost-esm2.sh        (+ .tomo.orig)
├── input.nml                (+ .tomo.orig)   fv_core/land layout, coupler npes·런길이 수정
├── MOM_layout / SIS_layout  (+ .tomo.orig)   LAYOUT 6,4
├── fms_esm4.5_compile_v3_1007_fix.x → 빌드트리 심링크
├── INPUT/ (663, combined restart) · RESTART/ (129 written)
└── esm4p5.log · ocean.stats · seaice.stats · KIOST_ESM2_smoke.log

# 정리 대상(선택): /home/ydkoh/KIOST-ESM2.tar.gz(19G) + .enc(19G) — INPUT 해제 후 삭제 가능
```

## 10. 재현 절차 (요약, A→Z)

```bash
# 1) 소스 복호화·전송
openssl enc -d -aes-256-cbc -md sha256 -in ESM4p5_KIOSTv2b.tar.gz.enc -out ESM4p5_KIOSTv2b.tar.gz -pass pass:<PW>
scp ESM4p5_KIOSTv2b.tar.gz climate:/home/ydkoh/ ; ssh climate 'cd /home/ydkoh && tar xzf ESM4p5_KIOSTv2b.tar.gz'
# 2) 빌드 스택 포팅: exec/env.sh + exec/intel_tomo.mk 를 §3.1대로 수정
# 3) 빌드
ssh climate 'cd /home/ydkoh/ESM4p5_KIOSTv2b && bash build_esm4.5.sh'   # ~14분, exec/*.x 확인
# 4) INPUT 복호화·전송·해제 (18GB)
scp KIOST-ESM2.tar.gz.enc climate:/home/ydkoh/
ssh climate 'cd /home/ydkoh && openssl enc -d -aes-256-cbc -md sha256 -in KIOST-ESM2.tar.gz.enc -out KIOST-ESM2.tar.gz -pass pass:<PW> && tar xzf KIOST-ESM2.tar.gz'
# 5) run 포팅: input.nml/MOM_layout/SIS_layout/run_kiost-esm2.sh 를 §5대로 수정 + 바이너리 심링크
# 6) smoke test
ssh climate 'cd /home/ydkoh/KIOST-ESM2 && qsub run_kiost-esm2.sh'
# 검증: grep "Total runtime" esm4p5.log ; tail ocean.stats seaice.stats ; ls RESTART | wc -l
```

---

## 11. AMIP 변형 포팅 (2026-07-06) ✅ SMOKE TEST 성공

**한 줄:** coupled와 **동일 실행파일**을 config만 바꿔(해양 PE 0 + SIS2 SPECIFIED_ICE로 SST/해빙 관측 처방) climate00에서 AMIP(대기 AM4.5 + 육상 LM4)를 구동. **재빌드 불필요**. 24-core 축소로 1 model-day(1979-01-01→02) `rc=0` 완주, RESTART 119개·atmos diag 생성·ocean diag 0.

### 11.1 AMIP이란 (coupled와의 차이)
- 소스: `KIOST-ESM2_AMIP.tar.gz.enc`(24GB, sha256 `6987e8d9…ce6e`). CMIP7 AMIP(1979–2022) 실험셋, base=historical config + PI IC.
- 메커니즘 (README_amip.md): `&coupler_nml do_ocean=.false., ocean_npes=0, concurrent=.false.` → **MOM6/COBALT 초기화조차 안 됨**. SIS2 `SPECIFIED_ICE=True` → slab ice(cat 1, 동역학 없음), 매 스텝 data_override로 `sst_obs/sic_obs/sit_obs` 강제.
- 경계자료: input4MIPs **CMIP7 PCMDI-AMIP-1-1-10** mid-month bcs (`amipbc_{sst,sic}_*.nc`, INPUT에 실파일). data_table 마지막 3줄에 `ICE sic_obs/sit_obs/sst_obs` 엔트리.
- IC: 대기·육지 = PI 평형 최종상태(1979 관측 아님) → **1979–80은 스핀업, 분석 제외 권장**. 개선: historical이 1979 도달 시 그 RESTART로 교체.
- **바이너리 동일**: `fms_esm4.5_compile_v3_1007_fix.x` (§3 빌드 그대로). 패키지 내장 .x는 tomo(intel19/mvapich4.0/nc4.9.2) 빌드라 climate00에서 불가 → climate00 exec로 심링크 교체.

### 11.2 climate00 셋업 (coupled와 다른 점만)
run dir `/home/ydkoh/KIOST-ESM2_AMIP/`. 3가지 조치:

1. **심볼릭링크 재연결 (핵심)**: 배포 INPUT의 **529개 링크가 tomo 경로 `/data3/noah/KIOST-ESM2/INPUT`을 가리켜 전부 깨짐**. climate00 coupled INPUT(`/home/ydkoh/KIOST-ESM2/INPUT`)로 재지정 → basename 100% 존재(missing 0)라 전부 해소. exec 링크·tomo MKL 심(`libmkl_*.so.1`, soname부터 틀림)도 정리. 스크립트 `amip_symlink_fix.sh`. 결과 broken link 0.
   - AMIP INPUT 자체는 실파일 ≈24GB(강제력 16G nc4압축 + 재시작 2.8G) + 529 링크(coupled INPUT 공유) 구조. 즉 **coupled INPUT이 먼저 있어야 AMIP이 돎**.
2. **PE 축소 (720 → 24)**: `input.nml` `atmos_npes 720→24`, `&fv_core_nml layout 12,10→2,2 · io_layout 2,2→1,1`, `&land_model_nml` 동일, `SIS_layout LAYOUT 30,24→6,4`(coupled 검증 분할 재사용). do_ocean/ocean_npes는 이미 F/0. **총 랭크=atmos_npes 불일치 시 coupler_init 즉시 FATAL**. 원본은 `*.bak_720` 백업.
   - AMIP은 해양 PE가 없어 전 코어가 대기 → coupled(atmos24+ocean24)보다 단순. 24랭크 = climate00 단일노드.
3. **run 스크립트** `run_amip_smoke.sh`: §5.3 coupled 스크립트 복제 + work_dir/PBS만 변경(`ncpus=24:mpiprocs=24`), 동일 모듈·`MV2_ENABLE_AFFINITY=0`. smoke는 `&coupler_nml months=0, days=1`.

### 11.3 Smoke test 결과 (job 2900, climate00 24코어, ~17.5분)
- `SIS Date 1979/01/02 00:00:00 (step 24)` 완주, PBS 로그 `END rc=0` (SIGKILL 아님).
- **SPECIFIED_ICE=True** (SIS_parameter_doc.short), `input_filename='F'` slab ice cold-start, ice mass/heat conservation Error ~1e-4, NaN 0.
- RESTART **119개**(atmos_coupled/cana/cg_drag/land…), diag `19790101.atmos_daily_cmip`·`atmos_month_aer` 생성, **ocean diag 0개**(정상). GHG co2=337ppm@1979(연도 정합).
- init(HITRAN LW gas transmission 등 forcing 다량 로딩)이 대부분 시간 차지. 적분은 6-hourly SIS diag로 진행 확인. **qstat "Time Use 00:00:00"은 PBS 미집계 아티팩트** — `ps`로 24 rank 전부 99% 확인이 진짜 상태.

### 11.4 알아둘 것
- 크래시 3건(landuse.res 날짜 1979, SIS `input_filename='F'`, `FATAL_UNUSED_PARAMS=False`)은 **배포 config에 이미 패치됨**(tomo에서 해결). climate00 재현 시 재현 안 됨.
- 다음: 생산런은 48/96랭크로 확대 + 다년(스핀업 1979–80 버림). 초기조건은 historical 1979 도달 시 교체가 정석.
- 정리(선택): `/home/ydkoh/KIOST-ESM2_AMIP.tar.gz.enc`(24GB) — 해제 완료라 삭제 가능(/home 111T).
```

### 11.5 CFC lbc 활성화 (협력기관 patch `amip_mod.tar.gz`, 2026-07-13)
협력기관(noah/`yhkimstar@gmail.com`)이 "AMIP 세팅 수정" 패치 `amip_mod.tar.gz`(로컬 `/Volumes/data03/`) 전달. **목적: 대류권 화학에서 CFC→오존 변화 모의** (배포본은 CFC 꺼져 있었음). 내용물 2개: `input.nml`, `chemlbf`.

- **입력 판정 (통째 교체 금지)**: 협력기관 `input.nml`은 **full production**(atmos_npes 720, `&coupler_nml months=12`, fv/land layout 12,10 · io 2,2)이고 내 서버본은 **축소 smoke**(npes 24, 1일, layout 2,2). diff하면 CFC 2줄 + PE/layout/기간이 다름 → **CFC 2줄만 이식**(1623-1624), 축소설정 유지. 통째 교체했으면 720 PE라 climate01 48코어서 안 돎.
  - `&tropchem_driver_nml`: `time_varying_cfc_lbc = .false.→.true.`, `cfc_lbc_dataset_entry = 1950,…→1979,1,1,0,0,0,`. (line 884 `do_generic_CFC=.false.`는 별개 메커니즘, 불변.)
- **chemlbf 교체 (AMIP만)**: `chemlbf`는 CFC lbc **ASCII 시계열**(26372줄, namelist에 경로 없음 = 모델이 고정 파일명 `chemlbf` 읽음). 새 CMIP7본은 구본과 **뒤 226줄(26146-26372)만 다름**(sha `51befd…` vs 구 `3cfbd5…`). AMIP `INPUT/chemlbf`가 **coupled INPUT 심링크 공유**였음 → 심링크 끊고 새 실파일 배치(AMIP만), **coupled INPUT은 불변**(구본 `3cfbd5…` 유지, 되돌리기 가능).
- **백업**: `input.nml.bak_precfc`, `chemlbf.symlink.bak_info`(원 심링크 기록).
- **검증 — smoke test 재확인 (job 2933, climate01 24코어, 17분)**: `time_varying_cfc_lbc=.true.`로 `tropchem_driver_init nt=145` 통과, 새 chemlbf 읽고 **1979/01/02 00:00 완주 rc=0**. RESTART 117 · atmos diag 103 · 실제 abort 0(FATAL 4건은 benign `FATAL_UNUSED_PARAMS over-ridden` 경고). CFC 켠 게 안정성 무해(구 CFC-off smoke RESTART 119와 대등).
- **주의**: 이 변경은 **서버에만** 존재(로컬 repo 미반영). coupled는 여전히 CFC-off + 구 chemlbf. 생산 AMIP 시 PE/기간은 production input.nml 참고하되 climate01 단일노드(48코어) 한계 고려.

## 12. ★★ AMIP SST 단위 버그 — `sst_degk=.true.`인데 입력은 degC (2026-07-20, 미수정)

**증상 아님(스모크는 통과) — 조용한 물리 오류.** 1 model-day 스모크는 rc=0·RESTART 119로 통과했으나 SST 필드 자체가 틀린 상태.

- 입력: `INPUT/amipbc_sst_PCMDI-AMIP-1-1-10.nc`의 `tosbcs:units = "degC"` (ncdump 확인).
- 설정: `input.nml &ice_spec_nml sst_degk = .true.` — 소스 정의는 `ice_spec.F90:30` "when sst_degk=true **the input sst data is in degrees Kelvin**".
- 결과: `ice_spec.F90:160` `SST_offset = 0.0 ; if (sst_degk) SST_offset = -T_0degC` → 이미 degC인 값에서 **273.15를 또 뺌**. 개빙면 SST가 −273 °C 부근으로 감. (해빙 격자는 `t_sw_freeze0 + T_0degC`로 채운 뒤 같은 offset이 걸려 우연히 맞음 → **개빙면만 망가져서 더 안 보임**.)
- **본인 data_table 주석이 이미 정답을 적어둠**: `# tosbcs in degC (ice_spec sst_degk=.false.)`. 즉 주석과 namelist가 불일치.
- **수정 = `sst_degk = .false.`** (한 줄). 서버 `~/KIOST-ESM2_AMIP/input.nml:949`. 아직 미적용 — 적용 시 백업 후 1일 스모크 재실행하고 SST min/max를 물리범위(−2~35 °C)로 검증할 것.
- **교훈**: rc=0 · RESTART 개수 · abort 0 은 **물리 검증이 아니다**. 처방 경계장은 반드시 min/max·영역평균을 찍어볼 것 (grid-safety 정신과 동일).
