# KIOST-ESM2 (GFDL ESM4.5) — climate00 Porting Notes

**Model:** GFDL ESM4.5 coupled Earth-System Model, KIOST-ESM2 (v2b) configuration
**Origin cluster:** `tomo` (AMD EPYC Zen2, Intel19 + MVAPICH 4.0, SLURM/PBS)
**Target cluster:** `climate00` (Intel Xeon Gold 5418Y Sapphire Rapids, Intel oneAPI 21 + mvapich2-2.3.4, OpenPBS)
**Ported by:** ydkoh / 눈사람 — 2026-07-02 ~ 07-03
**Status:** ✅ **BUILD + SMOKE TEST 성공** (48-core 축소 config, 1 model-day 결합적분 완주)

> 목표 확정: climate00에서는 **빌드 + 동작·결합 검증(smoke test)까지**가 deliverable.
> 720-rank 생산 config는 climate00 자원(3노드×48=144코어)으로 불가 → 생산런은 별도 트랙.

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
