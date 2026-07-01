# LM4 Offline Spin-up — 실행 가이드 (run scripts & workflow)

_2026-06-23. climate00 서버. 이 문서는 **무엇을 어떻게 돌렸는지**의 재현 가이드.
배경·시행착오·결과는 [`LM4_SPINUP_NOTES.md`](LM4_SPINUP_NOTES.md) 참조._

모든 경로는 `climate:/data2/ydkoh/lm4/` 기준. 서버 셸은 **tcsh**(인라인 python/heredoc 금지, scp→편집→scp).
무거운 건 전부 PBS 배치잡. 로컬 Mac은 편집·그림만.

---

## 0. 전체 워크플로 (한눈에)

```
[소스 패치] sphum.F90 qscomp clamp 적용
   └─> [재빌드] make_ufs.csh                         # incremental, ufs_model 생성
[런 구성] setup_lm4_spinup.sh <YEARS> 24 3600 gswp3  # run dir 재생성 (rm -rf 주의)
   └─> [warm-start 자료] static_veg tar → INPUT/
   └─> [설정 손보기] input.nml / model_configure / ufs.configure  (아래 §3)
[제출] qsub spinup24.pbs                              # 24코어, climate01, 24h walltime
[감시] scripts/mon_lm4.sh (백그라운드)                # 잡 종료/크래시까지 폴링
[검증] scripts/lm4_equil2.py                          # 연간 restart로 평형 진단
[보존] cp RESTART/<최종>.* → IC_*/                    # 평형 IC 아카이빙 (run dir 밖)
```

---

## 1. 빌드 스크립트 (소스 고친 뒤에만)

LM4 소스(예: `sphum.F90`)를 고치면 **incremental 재빌드**만 하면 됨. 풀 cmake 불필요.

| 스크립트 (`/data2/ydkoh/spack-stack/`) | 역할 |
|---|---|
| `ufs_cmake.csh` | cmake 재구성 (`rm -rf build` 후). spack load + `CC/CXX/FC=mpicc/mpicxx/mpif90` + `-DAPP=LND-LM4`. **최초/대규모 변경 때만** |
| **`make_ufs.csh`** | **incremental make**(`build` 유지). spack spec 7개 load + `LIBRARY_PATH`에 PIO·HDF5 lib 추가(`-lpioc` 누락 방지) + `make -j6`. **소스 한두 파일 고친 뒤 이거만** |
| `relink_ufs.csh` | 링크만 다시 (linker flag 포함) |

실행 (tcsh 스크립트, 백그라운드 권장):
```bash
ssh climate 'cd /data2/ydkoh/spack-stack; nohup tcsh make_ufs.csh >& /data2/ydkoh/lm4/rebuild.log &'
# 끝나면 ufs-weather-model/build/ufs_model 갱신. "=== END make (exit 0) ===" 확인.
```
⚠️ **함정**: 내 손수 만든 빌드 스크립트로 `spack load` 1개만 하면 `-lpioc` 못 찾고 링크 실패.
반드시 `make_ufs.csh`(LIBRARY_PATH 세팅됨)를 쓸 것.

### 적용한 소스 패치 — qscomp clamp
`LM4-driver/LM4/shared/sphum.F90` 의 `qscomp`에서 `escomp` 호출 전:
```fortran
real :: Tc
Tc = min(max(T, 173.16), 372.16)   ! es-table 범위로 캡 (로컬 복사본; 실제 T는 안 건드림)
call escomp(Tc, esat)              ! 원래 escomp(T,esat)
... call escomp(Tc+del_temp, esat) ! 미분항도 동일
```
- 효과: cold-start 단일셀 온도폭주 시 `lookup_es` 테이블 overflow FATAL 방지. 모든 qscomp caller(Tv·T_ca·grnd_T) 보호. 평형 후 무발동(no-op).
- 사본: `lm4/patches/sphum.F90.clamp`. 서버 원본 백업: `sphum.F90.orig`.
- **git submodule update 시 사라짐 → 재적용 후 `make_ufs.csh`.**

---

## 2. 런 디렉토리 구성 — `setup_lm4_spinup.sh`

```bash
ssh climate 'cd /data2/ydkoh/lm4 && bash setup_lm4_spinup.sh <YEARS> <CORES> <CPLSEC> <FORCING> |& tail -25'
#   YEARS  : 모델연수 (FHMAX=YEARS*8760h 로 환산)
#   CORES  : 24 (layout 2,2; 48은 land 분해 교착) 
#   CPLSEC : 3600 (LM4 fast timestep, 초)
#   FORCING: gswp3 | era5gpcp
```
- **⚠️ `rm -rf RUNDIR` 함** → 기존 run dir 산출물 전부 삭제. 평형 IC는 미리 `IC_*`로 빼둘 것.
- 하는 일: 회귀시험 템플릿으로 `input.nml`·`model_configure`·`ufs.configure`·`diag_table`·`field_table` 생성 + `INPUT/`에 격자·mesh·forcing 스테이징 + `datm.streams` 생성(gswp3: `gen_streams.py`, era5gpcp: `gen_streams_era5gpcp.py`, cycle 1981–2010).
- 산출 run dir: `/data2/ydkoh/lm4/RUN/lm4_spinup/`.

### setup 뒤 손보기 (warm-start 자료 + 설정)
```bash
# 1) static veg(규정식생) restart 풀기 → INPUT/
ssh climate 'cd RUN/lm4_spinup/INPUT && tar xf /data2/ydkoh/lm4/INPUTDATA/input-data-20251015/LM4_input_data/c96_LM4/19810101.static_veg_LM3p2sosn_HWSD5min_C96_OM4_025.v20150930.tar'
# 2) input.nml / model_configure / ufs.configure 편집 (scp→로컬 Edit→scp) — §3
```

---

## 3. 핵심 설정 노브 (run dir 안)

### `input.nml`
| 노브 | 값 | 뜻 |
|---|---|---|
| `&static_veg_nml use_static_veg` | `.TRUE.` | 규정(static)식생 사용 → 식생 cold-start 폭주 회피. 식생 = `INPUT/19810101.static_veg_out.nc`(매년 loop) |
| `&coupler... restart_interval` | `1,0,0,0,0,0` | FMS restart 주기 `[yr,mo,dy,hr,mn,sc]` = **연 1회**. (기본 `0,0,0,6,0,0`=6h면 디스크 폭발) |
| `&soil_nml geohydrology_to_use` | `'hill'` | hillslope(TOPMODEL식) 수문. groundwater는 soil column `wl` 안에서 표현(별도 배열 0) |

### `model_configure`
| 노브 | 값 | 뜻 |
|---|---|---|
| `calendar:` | `'NOLEAP'` | **JULES/CLM 정합 + leap drift 제거.** 없으면 기본 gregorian(leap)→30년이 12-25에 끝남. `lm4_cap.F90`이 이 값 읽음 |
| `nhours_fcst:` | `262800` | 런 길이(시간). NOLEAP이라 30yr=30×8760. **ESMF 시계 한계로 90yr(788400)는 init 즉사 → 한 잡 30년 이하** |
| `start_year/month/day` | `1981 01 01` | 시작일 |
| `dt_atmos:` | `900` | 커플링/모델 timestep(초) |

### `ufs.configure`
| 노브 | 값 | 뜻 |
|---|---|---|
| `start_type` | `startup`(cold) / `continue`(warm) | 신규 vs restart 이어돌리기 |
| `stop_n` / `stop_option` | `262800` / `nhours` | 정지 시점 (= nhours_fcst와 맞춤) |
| `restart_n` / `restart_option` | `8760` / `nhours` | CMEPS restart 주기(연 1회) |
| `case_name` | `ufs.cpld` | 커플러 출력 prefix(`ufs.cpld.cpl.hi.*`). restart엔 안 붙음(cosmetic) |

---

## 4. 제출 — `spinup24.pbs`

```bash
ssh climate 'cd /data2/ydkoh/lm4; qsub spinup24.pbs; qstat -u ydkoh'
```
PBS 잡: `select=1:ncpus=24:host=climate01`, walltime 24h, `-o spinup.log`.
spack 환경 load + HPCX(hcoll/ucx/ucc) LD_LIBRARY_PATH + `libnsl` symlink + `OMPI_MCA_coll=^hcoll`(단일노드 hcoll 비활성) + `ulimit -s unlimited` → `mpirun -np 24 ./ufs_model`.
- ⚠️ **PBS는 `spinup.log`(`-o`)를 잡 종료 시에만 갱신** → 실행 중 진행은 `logfile.000000.out`·`cpl.hi` 파일명·`warnfile`로 봐야 함.
- ⚠️ tcsh라 `>& file`(stdout+stderr), `2>&1` 금지.

throughput ≈ **8.5분/모델연** (np24) → 30년 ≈ 3.5h.

---

## 5. 감시 — `scripts/mon_lm4.sh`

잡번호만 바꿔 백그라운드로. 5~10분마다 폴링, 잡이 큐에서 빠지면 종료 보고.
```bash
# scripts/mon_lm4.sh 안의 2868을 현재 잡번호로 수정 후
bash scripts/mon_lm4.sh   # (로컬, run_in_background)
```
- alive 체크는 `qstat <JOBID> | grep -c "<JOBID>"` (공백 패턴 `" 2868 "`는 `2868.climate00` 못 잡음 — 함정).
- 진행도 = 최신 `ufs.cpld.cpl.hi.lnd.*` 파일명의 날짜.

---

## 6. 평형 검증 — `scripts/lm4_equil2.py`

연간 restart(`RESTART/YYYY0101.000000.{soil,snow}.res.tile*.nc`)에서 land-mean 시계열:
**층별 soil T, column soil water, groundwater, snow water**. drift(연변화)가 ~0이면 평형.
```bash
ssh climate 'bash -lc "source /home/ydkoh/anaconda3/etc/profile.d/conda.sh; conda activate; python /data2/ydkoh/lm4/lm4_equil2.py"'
```
(서버 python = **anaconda activate** 필요. `lm4_equil.py`는 deepT+water 약식판.)

평형 판정 후 → 본 실험은 그 restart에서 warm-start (미평형 상태로 warm-start 금지).

---

## 7. 평형 IC 아카이빙 (데이터 안전)

run dir는 재실행마다 덮어쓰임 → **평형 restart는 run dir 밖으로 복사**:
```bash
ssh climate 'mkdir -p /data2/ydkoh/lm4/IC_<name>; cp RUN/lm4_spinup/RESTART/<YYYY>0101.000000.* RUN/lm4_spinup/RESTART/coupler.res /data2/ydkoh/lm4/IC_<name>/'
```
보존된 IC: `IC_GSWP3_staticveg_spin30/`(leap 30년판, FMS 9종×6타일).

---

## 8. continue로 세그먼트 이어돌리기 (★검증됨 2026-06-23, 잡2871)

ESMF 한계로 한 잡 30년 → **30년씩 끊어 continue**. 자동화: `scripts/spinup_loop.sh`. 수동 레시피:
```bash
# ① 이전 cycle 최종 RESTART의 land 9종을 INPUT/에 ★날짜 prefix 떼고 복사
#    (FMS는 INPUT/soil.res.tile1.nc 식 무날짜 이름으로 읽음. 날짜 붙이면 못 찾고 cold-start!)
for f in RESTART/<YYYYMMDD>.000000.*.res*; do
  cp "$f" "INPUT/$(basename $f | sed -E 's/^[0-9]{8}\.[0-9]{6}\.//')"   # → INPUT/soil.res.tile1.nc ...
done
# ② ufs.configure: start_type = continue
# ③ 출력 정리: rm -f RESTART/* ufs.cpld.cpl.hi.lnd.*  →  qsub
```
- mediator restart(`ufs.cpld.cpl.r.*`) **불필요** — `read_restart=.false.`(mediator cold-init). LM4 land 9종만 있으면 됨.
- 물리 restart는 **calendar 독립**. branch 방식: 시계 1981 리셋, land 상태만 누적(forcing 1981–2010 안에서).
- **★ 반드시 warm-start 검증**: 첫 해(1982) restart의 deep soil T 확인(`scripts/check_warm.py`). **~272.5K=warm OK, 287K=cold(실패, 또 헛돔)**. 2870이 이 검증 없이 cold로 3.5h 헛돌았음 → 항상 초반 검증.
- 스테이징 스크립트: `scripts/stage_restart.sh`.

### 함정 정리 (이 세션에서 깨진 것)
- ❌ INPUT restart에 날짜 prefix(`19810101.000000.soil.res.tile1.nc`) → cold-start. ✅ 무날짜(`soil.res.tile1.nc`).
- `warm_start` namelist 플래그는 **FV3 atm용** — DATM+LM4엔 무관. 순전히 INPUT 파일 존재/이름 문제.

---

## 9. 출력 변수 → 그림용 NC 변환 — `lm4_to_latlon.py`

LM4 land 진단(`*.land_annual.tile*.nc` 등)은 변수를 **압축 cubed-sphere**(grid_index)로 저장 →
규칙 lat-lon NC로 변환해야 ncview/cdo/xarray로 열림.
```bash
ssh climate 'bash -lc "source /home/ydkoh/anaconda3/etc/profile.d/conda.sh; conda activate; cd /data2/ydkoh/lm4; \
  python lm4_to_latlon.py --prefix 19810101.land_annual --rundir RUN/lm4_spinup \
    --coords auto --vars LAI --res 1.0 --rec all --out land_annual_latlon.nc"'
```
- 좌표는 `cpl.hi.lnd`의 `lndExp_lon/lat`에서 복원(파일 내 geolon_t는 이 run에서 0/fill) + grid_index 분해 + binning.
- `--vars all` 가능. 3D(z) 변수는 `--level N`(기본 표층). 자세한 건 스크립트 docstring.
- ⚠️ land_annual은 **연말에야 레코드 기록** → 실행 중엔 0 레코드일 수 있음(land_static로 먼저 검증 가능).

---

## 10. 잡 이력 (이 세션)

| 잡 | 내용 | 결과 |
|---|---|---|
| 2865 | GSWP3 static clamp **30년 (leap)** | exit=0, 1981→2010-12-25(leap drift). 평형 미달(deepT/water drift) → `IC_GSWP3_staticveg_spin30/` |
| 2866 | 90년 한방 (leap) | **init 즉사**: ESMF_ClockSet Value out of range (90년 길이 한계) |
| 2867 | NOLEAP 1년 테스트 | exit=0, 1982-01-01에 정확히 끝남. **NOLEAP 검증 OK** |
| 2868 | **NOLEAP static clamp 30년 (segment 1)** | 진행중. 완료 후 평형검증→`IC_GSWP3_staticveg_noleap_spin30/`→segment 2·3 |
