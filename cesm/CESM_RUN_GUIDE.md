# CESM2.1.5 실행 가이드 — climate00 (CLM5 offline · CAM6/CLM5 · CAM4/CLM4)

다른 프로젝트에서 그대로 가져다 쓰기 위한 **자족적(self-contained) 실행 매뉴얼**.
MOF_LSM 과제(2026)에서 실제로 돌려 검증된 것만 적었다. 연구 판단·수렴 결과는 `CLM5_SPINUP_NOTES.md`에 있고, 여기엔 **"어떻게 돌리나"**만 있다.

마지막 갱신: 2026-09-15.

---

## 0. 한 페이지 요약

```
1. ssh climate                              # 로그인 노드 climate00 (tcsh)
2. csh ~/run_scripts/<case>.csh             # create_newcase → xmlchange → case.setup → namelist → case.build
3. qsub ~/run_scripts/<case>.pbs            # PBS 안에서 ./case.submit --no-batch
4. 성패 = 로그의 "MODEL EXECUTION HAS FINISHED" + run/rpointer.* 날짜 진행   (exit code 아님)
5. 장기 적분 = 외부 bash 체인(chain.sh)이 10년 청크 qsub 반복        (RESUBMIT 못 씀)
```

이 머신에서 CESM이 **표준과 다른 점 4개** — 이것만 알면 나머지는 공식 문서대로다.

| 다른 점 | 왜 | 대응 |
|---|---|---|
| `BATCH_SYSTEM=none` | 머신 정의에 PBS 연동 안 함 | `case.submit`을 PBS 스크립트 안에서 `--no-batch`로 |
| mpirun이 **고정 hostfile** 사용 | `config_machines.xml`에 `-hostfile ~/mvapich2.hosts` 하드코딩 | 케이스별 hostfile을 `$PBS_NODEFILE`로 생성 (§4.2) |
| 계산노드에 perl `bigint` 없음 | 시스템 perl 모듈이 climate00에만 설치 | `export PERL5LIB=~/perl5/lib/perl5` |
| 48코어 단일 노드가 상한 | climate00=로그인, 2노드 MPI 미검증 | `NTASKS=48`, 청크 체인으로 장기런 |

---

## 1. 환경

### 1.1 버전

| 항목 | 값 |
|---|---|
| CESM | `release-cesm2.1.5` (`~/CESM/`, git tag) |
| CLM | `release-clm5.0.37` (= ctsm1.0.dev025). **CLM6 아님** |
| CAM | `cam_cesm2_1_rel_60` (CAM6) |
| 컴파일러 / MPI | Intel oneAPI 21 (ifort 2021.5) / mvapich2-2.3.4 |
| NetCDF / HDF5 / PnetCDF | `/usr/local/netcdf/4.6.1_intel21` · `/usr/local/hdf5/1.10.5_intel21` · `/usr/local/pnetcdf/1.11.2_intel21_mvapich2-2.3.4` |
| 배치 | PBS, queue `workq`. 노드 climate00(로그인)·climate01·climate02, 각 48코어 257 GB |

### 1.2 경로

| 종류 | 경로 |
|---|---|
| CIME 스크립트 | `~/CESM/cime/scripts/` (`create_newcase`, `create_clone`) |
| 케이스 | `~/CESM/cases/<CASE>/` |
| 빌드·실행 출력 | `/data2/ydkoh/cesm2_output/<CASE>/{bld,run}/` (`CIME_OUTPUT_ROOT`) |
| 입력자료 루트 | `/data1/CESM2_INPUT/` (`DIN_LOC_ROOT`; 소유자 타인, 일부 하위폴더 쓰기불가) |
| GSWP3 강제장 | `/data1/CESM2_INPUT/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516/` (0.5°, 3h, 1901–2014) |
| WFDE5 강제장 (CLM 포맷) | `/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5/YYYY_wfde5.nc` + `domain.lnd.360x720_wfde5.nc` |
| raw restart 아카이브 | `~/CESM/spinup_raw/<tag>/` (rsync, `--delete` 절대 금지) |
| 케이스 생성 스크립트 | 서버 `~/run_scripts/*.csh`, 로컬 git `cesm/run_scripts/` |
| PBS·체인 스크립트 | 로컬 git `cesm/run_scripts/*.pbs`, `cesm/scripts/*_chain.sh`, `*_chunk.pbs` |

### 1.3 머신 정의 (`~/.cime/`) — 새 계정이면 이 두 파일만 복사하면 된다

`~/.cime/config_machines.xml`:
```xml
<?xml version="1.0"?>
<config_machines>
  <machine MACH="climate00">
    <DESC>climate00 Linux server, Intel21 + mvapich2</DESC>
    <OS>LINUX</OS>
    <COMPILERS>intel</COMPILERS>
    <MPILIBS>mvapich2</MPILIBS>
    <PROJECT>none</PROJECT>
    <SAVE_TIMING_DIR/>
    <CIME_OUTPUT_ROOT>/data2/ydkoh/cesm2_output</CIME_OUTPUT_ROOT>
    <DIN_LOC_ROOT>/data1/CESM2_INPUT</DIN_LOC_ROOT>
    <DIN_LOC_ROOT_CLMFORC>/data1/CESM2_INPUT/atm/datm7</DIN_LOC_ROOT_CLMFORC>
    <DOUT_S_ROOT>$CIME_OUTPUT_ROOT/archive/$CASE</DOUT_S_ROOT>
    <BASELINE_ROOT/>
    <BATCH_SYSTEM>none</BATCH_SYSTEM>
    <SUPPORTED_BY>ydkoh</SUPPORTED_BY>
    <MAX_TASKS_PER_NODE>48</MAX_TASKS_PER_NODE>
    <MAX_MPITASKS_PER_NODE>48</MAX_MPITASKS_PER_NODE>
    <mpirun mpilib="mvapich2">
      <executable>mpirun</executable>
      <arguments>
        <arg name="num_tasks"> -hostfile /home/ydkoh/mvapich2.hosts -np {{ total_tasks }}</arg>
      </arguments>
    </mpirun>
    <module_system type="module">
      <init_path lang="sh">/usr/share/Modules/init/sh</init_path>
      <init_path lang="csh">/usr/share/Modules/init/csh</init_path>
      <init_path lang="python">/usr/share/Modules/init/python.py</init_path>
      <cmd_path lang="sh">/usr/bin/modulecmd sh</cmd_path>
      <cmd_path lang="csh">/usr/bin/modulecmd csh</cmd_path>
      <cmd_path lang="python">/usr/bin/modulecmd python</cmd_path>
      <modules>
        <command name="purge"/>
        <command name="load">intel21/compiler-21</command>
        <command name="load">intel21/mvapich2-2.3.4</command>
        <command name="load">intel21/hdf5-1.10.5</command>
        <command name="load">intel21/netcdf-4.6.1</command>
        <command name="load">intel21/mkl</command>
      </modules>
    </module_system>
    <environment_variables>
      <env name="NETCDF_PATH">/usr/local/netcdf/4.6.1_intel21</env>
      <env name="NETCDF_C_PATH">/usr/local/netcdf/4.6.1_intel21</env>
      <env name="NETCDF_FORTRAN_PATH">/usr/local/netcdf/4.6.1_intel21</env>
      <env name="HDF5_PATH">/usr/local/hdf5/1.10.5_intel21</env>
      <env name="PNETCDF_PATH">/usr/local/pnetcdf/1.11.2_intel21_mvapich2-2.3.4</env>
    </environment_variables>
  </machine>
</config_machines>
```

`~/.cime/config_compilers.xml`:
```xml
<?xml version="1.0"?>
<config_compilers>
  <compiler MACH="climate00" COMPILER="intel">
    <NETCDF_PATH>/usr/local/netcdf/4.6.1_intel21</NETCDF_PATH>
    <PNETCDF_PATH>/usr/local/pnetcdf/1.11.2_intel21_mvapich2-2.3.4</PNETCDF_PATH>
    <FFLAGS> -fp-model precise </FFLAGS>
    <SLIBS>
      <append> -L/usr/local/netcdf/4.6.1_intel21/lib -lnetcdff -lnetcdf -L/usr/local/hdf5/1.10.5_intel21/lib -lhdf5_hl -lhdf5 -lcurl -lz -mkl </append>
    </SLIBS>
    <LDFLAGS>
      <append> -L/usr/local/netcdf/4.6.1_intel21/lib -lnetcdff -lnetcdf -L/usr/local/hdf5/1.10.5_intel21/lib -lhdf5_hl -lhdf5 -lcurl -lz </append>
    </LDFLAGS>
  </compiler>
</config_compilers>
```

- **`<SLIBS>`는 반드시 `<append>`로 감쌀 것.** 안 감싸면 CIME 기본 링크 라인이 통째로 대체돼 링크 실패.
- 외부 PIO 설정은 넣지 말 것 — CESM2.1 내장 PIO1과 충돌.
- 모듈은 CIME이 `env_mach_specific.xml`을 통해 스스로 로드한다. `module load`를 셸에서 미리 할 필요 없음(해도 무해). 단 **`.cshrc`에 모델 모듈을 넣지 말 것** — 다른 모델(JULES gfortran, Noah-MP intelmpi)과 충돌.
- `~/mvapich2.hosts` 내용은 `climate01:48`. **공용 파일이므로 건드리지 말고** 케이스별 hostfile을 쓴다(§4.2).

### 1.4 perl 모듈 (한 번만)

`case.run`이 **실행 시점에** `build-namelist`(perl)를 부르는데 `bigint.pm` 등이 계산노드에 없다.
```
Can't locate bigint.pm in @INC ... clm_phys_vers.pm line 30
```
해결(이미 돼 있음, 새 계정이면 반복): climate00의 `bigint.pm bignum.pm bigrat.pm Math/BigRat.pm Math/BigFloat/`를 `~/perl5/lib/perl5/`로 복사. `/home`이 공유라 계산노드에서 보인다. PBS 스크립트마다 `export PERL5LIB=/home/ydkoh/perl5/lib/perl5` 명시.

---

## 2. 케이스 생성 — 공통 골격

모든 `.csh` 생성 스크립트는 이 골격이다. **생성·빌드까지만** 하고 실행은 PBS로 넘긴다.

```tcsh
#!/bin/tcsh -f
cd ~/CESM/cime/scripts

set CCSMROOT = /home/ydkoh/CESM
set CNAME    = <case name>
set COMPSET  = <alias or longname>
set RES      = <grid alias>

# disposable case only -- production cases must NOT rm -rf (see CLM5_prod_1979_2023.csh guard)
rm -rf $CCSMROOT/cases/$CNAME
rm -rf /data2/ydkoh/cesm2_output/$CNAME

./create_newcase --case $CCSMROOT/cases/$CNAME \
                 --compset $COMPSET --res $RES \
                 --machine climate00 --compiler intel --mpilib mvapich2 \
                 --run-unsupported
cd $CCSMROOT/cases/$CNAME

# PE layout: one node, every component on the same 48 ranks
./xmlchange NTASKS=48,NTHRDS=1,ROOTPE=0
./xmlchange MAX_TASKS_PER_NODE=48,MAX_MPITASKS_PER_NODE=48

./case.setup

# case-specific xmlchange (run length, restart, forcing years, spin-up switches)
./xmlchange STOP_OPTION=nyears,STOP_N=10
./xmlchange REST_OPTION=nyears,REST_N=1
./xmlchange CONTINUE_RUN=FALSE
./xmlchange RESUBMIT=0,DOUT_S=FALSE        # no self-resubmit (BATCH_SYSTEM=none), no short-term archive

# namelists
cat >> user_nl_clm << EOF
 hist_nhtfrq = 0
 hist_mfilt  = 1
EOF

./preview_namelists                        # ALWAYS: check run/lnd_in before spending a build
./check_input_data --download              # only if files may be missing (F cases at new res)
./case.build
echo "built. submit with: qsub ~/run_scripts/$CNAME.pbs"
```

**각 줄이 하는 일**
- `--run-unsupported`: 이 머신·격자 조합은 NCAR 지원 목록에 없으므로 필수.
- `NTASKS=48,ROOTPE=0`: 모든 컴포넌트를 같은 48 rank에 순차 배치. F compset 기본값이 96이라 반드시 덮어쓸 것(48코어에 96 rank면 2배 초과할당).
- `case.setup`: `env_mach_specific.xml`·`.case.run` 생성. 이후 `xmlchange`는 namelist 수준이면 재빌드 불필요.
- `RESUBMIT=0`: CESM 자체 재제출은 `BATCH_SYSTEM=none`에서 로그인 노드에 뜨므로 끔. 장기런은 §5 체인으로.
- `DOUT_S=FALSE`: short-term archive 끔. 출력은 `run/`에 남고 우리가 직접 rsync.
- `preview_namelists`: `run/lnd_in`·`atm_in`을 만들어 준다. **finidat·spinup_state·use_cn·use_crop을 여기서 눈으로 확인**한 뒤 빌드.

**케이스 복제**: `~/CESM/cime/scripts/create_clone --case <new> --clone <old> [--keepexe]`. `cases/`에는 없고 `cime/scripts/`에 있다. `--keepexe`면 빌드 공유(`EXEROOT`가 원본 bld를 가리킴).

---

## 3. 자주 쓰는 compset · 격자

| 용도 | compset | 격자 | 비고 |
|---|---|---|---|
| CLM5 offline, 위성 LAI 처방 | `I2000Clm50Sp` | `f09_g17` | = `2000_DATM%GSWP3v1_CLM50%SP_SICE_SOCN_MOSART_CISM2%NOEVOLVE_SWAV` |
| CLM5 offline, 탄소순환(crop 없음) | **longname만 가능**: `2000_DATM%GSWP3v1_CLM50%BGC_SICE_SOCN_MOSART_CISM2%NOEVOLVE_SWAV` | `f09_g17` | `I2000Clm50Bgc`+GSWP3 alias가 없음(비crop은 CRU만). crop 넣으면 `BGC-CROP`, 40% 느림 |
| CLM5 offline, 1850 BGC crop | `I1850Clm50BgcCropCru` | `f19_g17_gl4` | CRU-NCEP forcing |
| CAM6+CLM5 대기결합, SST 처방 | `F2000climo` | `f19_f19` / `f09_f09_mg17` | f09는 `_mg17` 접미 필수(맨 `f09_f09` alias 없음) |
| CAM4+CLM4 (구버전 물리) | `2000_CAM40_CLM40%SP_CICE%PRES_DOCN%DOM_RTM_SGLC_SWAV` | `f19_f19` | 적설 민감도 실험용 |

- **CESM에 정확한 1°×1° 전구 격자는 없다.** f09 = 0.9°×1.25°. 다른 모델과 격자를 억지로 맞추지 말고 진단 시 remap.
- `hcru_hcru`(0.5°)는 domain이 CRUNCEP land-mask라 GSWP3 mask와 불일치 위험 + 비용 4배 → 안 씀.
- `2000_`: CO2·에어로졸 2000년 고정. constant-forcing cycling과 정합. `IHist`는 transient라 spin-up엔 부적합.

---

## 4. 실행 — PBS 래핑

### 4.1 왜 래핑하나
`BATCH_SYSTEM=none`이라 `./case.submit`은 **호출한 자리에서** 48 rank를 띄운다. 로그인 노드에서 치면 로그인 노드에서 돈다. 그래서 PBS 잡 안에서 `./case.submit --no-batch`.

### 4.2 템플릿 (`cesm/run_scripts/F_2000climo_f09.pbs`가 최신 형태)

```bash
#!/bin/bash
#PBS -N <name>
#PBS -q workq
#PBS -l select=1:ncpus=48:mpiprocs=48:host=climate01
#PBS -l walltime=30:00:00
#PBS -j oe
#PBS -o /home/ydkoh/CESM/cases/<CASE>/run.log
set -u
export PERL5LIB=/home/ydkoh/perl5/lib/perl5${PERL5LIB:+:$PERL5LIB}   # compute nodes lack bigint

CASE=/home/ydkoh/CESM/cases/<CASE>
RUN=/data2/ydkoh/cesm2_output/<CASE>/run
cd "$CASE" || exit 1

# hostfile from the PBS allocation -- the launch always goes where the allocation is
awk '{c[$1]++} END {for (h in c) print h":"c[h]}' "$PBS_NODEFILE" > "$CASE/mpi.hosts"
cat "$CASE/mpi.hosts"

echo "=== START $(date) on $(hostname) ==="
./case.submit --no-batch
echo "=== MODEL PHASE DONE $(date) ==="
cat "$RUN/rpointer.lnd" 2>/dev/null

# raw preservation: rsync WITHOUT --delete
ARCH=/home/ydkoh/CESM/spinup_raw/<tag>; mkdir -p "$ARCH"
shopt -s nullglob
rsync -a "$RUN"/*.clm2.r.*.nc "$RUN"/*.clm2.h0.*.nc "$RUN"/rpointer.* "$ARCH/"
echo "=== END $(date) ==="
```

hostfile을 케이스가 읽게 하려면 **케이스 생성 직후(case.setup 뒤) 한 번**:
```tcsh
sed -i "s|-hostfile /home/ydkoh/mvapich2.hosts|-hostfile $CCSMROOT/cases/$CNAME/mpi.hosts|" env_mach_specific.xml
```
이걸 안 하면 PBS가 어느 노드를 주든 rank는 `~/mvapich2.hosts`(=climate01)로 간다. 실제로 post-AD가 3주간 예약과 다른 노드에서 돌았다(노트 §7k). **노드를 바꿀 땐 PBS `host=`와 hostfile 두 곳을 같이** 고쳐야 한다.

### 4.3 성공 판정 (exit code 금지)

```
2026-07-10 14:56:11 MODEL EXECUTION HAS FINISHED
ERROR: No result from jobs [('case.run', None)]
=== END exit=1 ===
```
`--no-batch`에서 CIME이 배치 결과를 못 찾아 항상 `exit=1`을 낸다. **모델은 정상.** 판정은:
1. `run/cesm.log.*`에 `MODEL EXECUTION HAS FINISHED`
2. `run/rpointer.lnd`의 날짜가 진행
3. `run/*.clm2.r.YYYY-01-01-00000.nc` 존재

### 4.4 rank가 실제로 어디 있나 확인

`qstat -n`의 할당 노드는 예약일 뿐이다. 각 노드에서 직접 센다:
```
ssh climate01 pgrep -c -u ydkoh cesm.exe
ssh climate02 pgrep -c -u ydkoh cesm.exe
```
로그 파일명의 머신명(`climate00`)은 `--machine` 값이지 실행 노드가 아니다.

### 4.5 노드 선택

- climate00 = 로그인. 잡 금지.
- climate01 / climate02 = **동일 하드웨어**(48코어, 257 GB). 속도 차이는 없고 **타 사용자 경합**만 변수. 타 사용자 LIS가 PBS 밖에서 climate02를 점유할 때가 있어 `pbsnodes`가 free라고 해도 `ssh climate02 uptime`으로 load를 먼저 볼 것.
- 2노드 96 rank는 미검증. 48이 상한.

---

## 5. 장기 적분 — 외부 청크 체인

`RESUBMIT`을 못 쓰므로 bash 체인이 N년 청크를 `qsub`하고 끝나길 기다리기를 반복한다. 검증: 청크 경계에 TWS 단차 없음, 연속 적분과 동등(노트 §7m, `scripts/verify_chunk_continuity.py`).

구조 (`cesm/scripts/clm5_bgc_pad_chain.sh` + `clm5_bgc_pad_chunk.pbs`):

```
chain.sh <TARGET_YEAR>
  rpointer 있음? → FIRST=0 (CONTINUE_RUN=TRUE)   / 없음 → FIRST=1 (CONTINUE_RUN=FALSE, finidat 읽음)
  loop:
    y0 = rpointer 연도;  y0 >= TARGET → 끝
    JID = qsub -v CHUNK_N=10,FIRST=$FIRST chunk.pbs
    qstat $JID 가 사라질 때까지 sleep 300
    y1 = rpointer 연도;  y1 <= y0 → ABORT (stale restart, 무한루프 방지)
    FIRST=0
  MAXCHUNK 하드캡
```

chunk.pbs가 매번 하는 xmlchange:
```bash
./xmlchange CONTINUE_RUN=$( [ "$FIRST" = 1 ] && echo FALSE || echo TRUE )
./xmlchange STOP_OPTION=nyears,STOP_N=$CHUNK_N
./xmlchange REST_OPTION=nyears,REST_N=1
./xmlchange RESUBMIT=0,DOUT_S=FALSE
```

실행:
```
ssh climate "cd ~/CESM/cases/<CASE>; nohup bash <chain>.sh 200 >& ~/<chain>.out &"
```
- 로그인 노드에서 nohup으로 띄워도 된다. 체인 자체는 sleep만 하므로 부하 없음.
- **재개 시 FIRST를 하드코딩하지 말 것.** rpointer 유무로 판단하게 한 이유: 한 번 `FIRST=1` 고정으로 재시작해 post-AD 연도를 날려 먹은 적이 있다.
- 청크 길이 = walltime ÷ 연당 시간. BGC f09 48PE는 ~1.8 h/yr → 10년 청크 ≈ 18 h.
- GSWP3 30년 cycling과 10년 청크는 무관하다(강제장 되감기 연도 0091·0121…에 예상된 단차, 청크 경계 아님).

---

## 6. 레시피 A — CLM5 offline SP spin-up (GSWP3, cold start)

케이스 `clm5_spinup_gswp3`. 목적: 토양수분·토양온도 수렴. LAI는 위성 기후값 처방(BGC 없음).

```tcsh
set COMPSET = I2000Clm50Sp
set RES     = f09_g17
# ... 골격 §2 ...
./xmlchange CLM_FORCE_COLDSTART=on            # default finidat is 1.9x2.5 BgcCrop -> wrong grid, so start cold
./xmlchange DATM_CLMNCEP_YR_START=1981,DATM_CLMNCEP_YR_END=2010,DATM_CLMNCEP_YR_ALIGN=1981
./xmlchange CALENDAR=NO_LEAP                  # already default for this compset; restart lands on Jan-01
./xmlchange STOP_OPTION=nyears,STOP_N=30,REST_OPTION=nyears,REST_N=1
```

- 로그에 `WARNING: CLM is starting up from a cold state` + `Model clm no file specified for finidat` 나오면 **의도한 것**.
- `YR_ALIGN=1981`: 모델연도 1 → 강제장 1981. 30년 cycling이면 모델연도 31에 1981로 되감김.
- `CLM_FORCE_COLDSTART`·`NTASKS` 변경 후 `case.setup --reset`을 하면 `BUILD_COMPLETE`가 지워진다. 재빌드 불필요 → `./xmlchange BUILD_COMPLETE=TRUE`.
- 수렴 판정: cycle 간 같은 날짜(Jan-01) restart 비교. 면적가중은 history의 `area`·`landfrac`. 빙상 격자 제외.

## 7. 레시피 B — CLM5-BGC: AD → post-AD → 생산런 (WFDE5)

세 케이스가 한 사슬이다. 각각 clone으로 만들어 앞 단계 결과를 보존한다.

### 7.1 AD (accelerated decomposition) — `clm5_bgc_ad`

```tcsh
set COMPSET = "2000_DATM%GSWP3v1_CLM50%BGC_SICE_SOCN_MOSART_CISM2%NOEVOLVE_SWAV"   # longname, quoted
set RES     = f09_g17
# ... 골격 ...
./xmlchange CLM_BLDNML_OPTS="-bgc bgc"        # use_cn=.true., use_crop=.false.
./xmlchange CLM_ACCELERATED_SPINUP=on         # spinup_state=2
./xmlchange CLM_FORCE_COLDSTART=on
./xmlchange RUN_STARTDATE=0001-01-01
./xmlchange DATM_CLMNCEP_YR_START=1981,DATM_CLMNCEP_YR_END=2010,DATM_CLMNCEP_YR_ALIGN=1981
```
- 강제장을 WFDE5로 바꾸려면 §10.
- 입력: non-crop fsurdat `surfdata_0.9x1.25_hist_16pfts_...c190214.nc`(16-pft). ndep/lightning/popdens/finundated는 crop 케이스 다운로드분 재사용. `check_input_data` 누락 0이면 빌드(~8분).
- 첫 청크만 `STOP_N=9`로 잡아 restart를 0011/0021… 10년 경계에 정렬했다(선택사항).
- AD 종료 기준: 200년 또는 `TOTECOSYSC` 표류 수렴. 실제 0211년까지.

### 7.2 post-AD — `clm5_bgc_pad` (AD의 clone)

```bash
cd ~/CESM/cime/scripts && ./create_clone --case ~/CESM/cases/clm5_bgc_pad --clone ~/CESM/cases/clm5_bgc_ad
cd ~/CESM/cases/clm5_bgc_pad
./xmlchange CLM_ACCELERATED_SPINUP=off       # spinup_state=0: pools rescaled on first finidat read
./xmlchange CLM_FORCE_COLDSTART=off
./xmlchange CONTINUE_RUN=FALSE
./xmlchange RUN_STARTDATE=0001-01-01
./xmlchange EXEROOT=/data2/ydkoh/cesm2_output/clm5_bgc_ad/bld   # reuse AD exe
./xmlchange BUILD_COMPLETE=TRUE
echo "finidat = '/data2/ydkoh/cesm2_output/clm5_bgc_ad/run/clm5_bgc_ad.clm2.r.0211-01-01-00000.nc'" >> user_nl_clm
./preview_namelists && grep -E "finidat|spinup_state" /data2/ydkoh/cesm2_output/clm5_bgc_pad/run/lnd_in
```

**★ finidat 함정.** `CLM_FORCE_COLDSTART=off`로 바꾸면 `finidat`에 compset 기본값 `clmi.I2000Clm50BgcCrop.2011-01-01.1.9x2.5_gx1v7...nc`가 채워진다. 격자(1.9×2.5 vs 0.9×1.25)도 구성(Crop vs 비crop)도 다르다. `CONTINUE_RUN=FALSE`인 첫 청크가 이걸 **실제로 읽으므로** 반드시 `user_nl_clm`에서 덮어쓴다. `preview_namelists`로 확인하기 전엔 제출하지 말 것.

- `CLM_ACCELERATED_SPINUP`은 런타임 namelist 스위치라 **재빌드 불필요**. AD→post-AD 탄소풀 역환산이 실제로 됐는지는 `scripts/verify_ad_exit_rescaling.py`로 숫자 확인(노트 §7l).
- 실측 1.70–1.83 h/model-year @ climate01 48PE (AD 2.1보다 빠름).
- 수렴 판정 `scripts/clm5_postad_convergence.py`: 97% 격자에서 `TOTECOSYSC` |Δ| ≤ 1 gC/m²/yr.

### 7.3 생산런 — `clm5_prod_1979_2023` (`run_scripts/CLM5_prod_1979_2023.csh`)

post-AD 마지막 restart를 finidat으로, 실제 달력 1979–2023 transient.
```tcsh
./xmlchange CLM_ACCELERATED_SPINUP=off,CLM_FORCE_COLDSTART=off
./xmlchange RUN_TYPE=startup,RUN_STARTDATE=1979-01-01,CONTINUE_RUN=FALSE
./xmlchange STOP_OPTION=nyears,STOP_N=5,REST_OPTION=nyears,REST_N=1
./xmlchange DATM_CLMNCEP_YR_START=1979,DATM_CLMNCEP_YR_END=2023,DATM_CLMNCEP_YR_ALIGN=1979
# finidat in user_nl_clm; WFDE5 streams copied from clm5_bgc_pad (do not rewrite -> no drift)
foreach s (Precip Solar TPQW)
  cp ~/CESM/cases/clm5_bgc_pad/user_datm.streams.txt.CLMGSWP3v1.$s .
end
```
- 이 스크립트는 **케이스가 이미 있으면 ABORT**한다(45년 출력을 `rm -rf`로 날리지 않기 위해). spin-up 스크립트의 `rm -rf` 습관을 생산런에 옮기지 말 것.
- `RUN_TYPE=hybrid` 대신 `startup`+`finidat`: I compset에선 동일 효과.
- 5년 청크 체인 `run_scripts/clm5_prod_chain.sh 2023`.

## 8. 레시피 C — CAM6 + CLM5 대기결합 (`F2000climo`)

f19: `run_scripts/F_spinup_cam6clm5.csh`(서버 `~/run_scripts/`) · f09: `run_scripts/F_f09_cam6clm5.csh` + `F_2000climo_f09.pbs`.

```tcsh
set COMPSET = F2000climo
set RES     = f19_f19            # or f09_f09_mg17
# ... 골격 (NTASKS=48 필수: default 96) ... case.setup 까지
# hostfile: PBS 할당을 따르게 (이 줄이 없으면 어느 노드를 예약하든 rank는 climate01로 간다)
sed -i "s|-hostfile /home/ydkoh/mvapich2.hosts|-hostfile $CCSMROOT/cases/$CNAME/mpi.hosts|" env_mach_specific.xml
./xmlchange STOP_N=2,STOP_OPTION=nyears,REST_N=1,REST_OPTION=nyears,CONTINUE_RUN=FALSE
cat >> user_nl_cam << EOF
 npr_yz = 24,2,2,24
 inithist = 'YEARLY'
 empty_htapes = .true.
 nhtfrq = 0
 mfilt  = 1
 ndens  = 2
 fincl1 = 'TREFHT:A','TS:A','PSL:A','PS:A','PRECT:A','PRECC:A','PRECL:A',
          'LHFLX:A','SHFLX:A','FLNS:A','FSNS:A','U:A','V:A','T:A','Z3:A','OMEGA:A','Q:A'
EOF
cat >> user_nl_clm << EOF
 hist_nhtfrq = 0
 hist_mfilt  = 1
 hist_empty_htapes = .false.
 hist_fincl2 = 'TLAI:A','TSAI:A','FSH:A','EFLX_LH_TOT:A',
               'H2OSOI:A','TSOI:A','SOILLIQ:A','H2OSNO:A','SNOWDP:A','FSNO:A',
               'TSA:A','RH2M:A','QSOIL:A','QVEGT:A','QVEGE:A','BTRAN2:A'
EOF
./preview_namelists
./check_input_data --download      # f09 CAM IC + topography are not on /data1
./case.build
```

- **`npr_yz`는 필수.** FV dycore 분할 `npr_y × npr_z = NTASKS`, y-서브도메인당 위도 ≥3. f19(96 lat): 24×2 → 4 lat/subdomain. 안 주면 CAM이 48×1로 쪼개 2 lat이 돼 거부. f09(192 lat): 24×2 → 8. CAM4 96 task 케이스는 `32,3,3,32`.
- **history 변수명은 반드시 마스터 목록 대조.** CLM은 모르는 이름이면 `htapes_fieldlist`에서 abort(무시 안 함). `HTOP`(CLM4 이름)·`BTRAN`(CLM5엔 `BTRAN2`만) 때문에 submit 한 번 날렸다.
- `empty_htapes=.true.`+`fincl1`: CAM 기본 수백 변수 대신 지정 변수만 월평균. `ndens=2` 압축.
- `check_input_data --download`는 climate00에서 인터넷 됨. `/data1/CESM2_INPUT` 일부 하위폴더는 소유자(타 사용자) 권한으로 쓰기 실패할 수 있음 → 그땐 `cesm/download_inputs.py`로 우회하거나 소유자에게 폴더 생성 요청.
- 실측: f19 48PE **4.29 h/model-year**. f09는 측정 중(케이스 `F_2000climo_f09`, 예상 30–34 h/yr).
- F2000climo `timeaddmonths` 에러가 났었다면 PE layout 불일치(96 default vs 48) 문제.

### 8.1 climate02에서 돌리기 — 순서 그대로

```
1. ssh climate02 uptime                      # load가 0 근처인지. pbsnodes "free"는 못 믿는다 (§4.5)
2. csh ~/run_scripts/F_f09_cam6clm5.csh      # 생성+빌드 (climate00에서; sed 줄이 들어 있는 스크립트)
                                             #   f19면 F_spinup_cam6clm5.csh에 위 sed 한 줄을 추가해서 쓸 것
3. PBS 스크립트에서 host=climate02 확인      # F_2000climo_f09.pbs 는 이미 climate02. 다른 케이스는 §4.2 템플릿 복사 후 CASE·host 수정
4. qsub ~/run_scripts/F_2000climo_f09.pbs
5. ssh climate02 pgrep -c -u ydkoh cesm.exe  # 48이어야 함. climate01에서 같은 명령이 0인지도 확인
```

- `F_f09_cam6clm5.csh` + `F_2000climo_f09.pbs` 조합은 이 순서로 climate02에서 실제 제출·실행된 것이다(2026-09-11).
- 2년 넘게 돌리려면 §5 체인을 케이스명만 바꿔 복사. F 케이스는 `rpointer.atm`·`rpointer.lnd` 둘 다 생기며 연도 파싱은 `rpointer.lnd`로 하면 된다.
- 실험 설계(SST 처방 변경, 강제장 섭동, branch)는 이 문서 범위 밖이다. branch는 `RUN_TYPE=branch, RUN_REFCASE, RUN_REFDATE`로 기준 케이스 restart에서 갈라진다(§9 CAM4 적설 실험이 그 예).

## 9. 레시피 D — CAM4 + CLM4 (`F_spinup.csh`)

```tcsh
set COMPSET = 2000_CAM40_CLM40%SP_CICE%PRES_DOCN%DOM_RTM_SGLC_SWAV
set RES     = f19_f19
./xmlchange STOP_N=11,STOP_OPTION=nyears,REST_N=1,REST_OPTION=nmonths,CONTINUE_RUN=FALSE
```
- 이 케이스는 NTASKS 96 기본값으로 만들어졌고 `~/mvapich2.hosts`가 당시 2노드였다. 지금 다시 만들면 §2 골격대로 48로.
- 적설 민감도 branch: F_spinup restart(year 0010-11-01)에서 `RUN_TYPE=branch`, 강수 중 snowfall −25/−50/−75%.

---

## 10. 사용자 강제장 물리기 (DATM `user_datm.streams.txt.*`)

`DATM_MODE=CLMGSWP3v1`은 3개 스트림(Solar / Precip / TPQW)을 쓴다. 다른 자료(WFDE5·ERA5)를 먹이려면 **CLM 포맷으로 변환한 파일**을 만들고, `preview_namelists`가 `CaseDocs/`에 만들어준 스트림 파일을 `user_` 접두로 복사해 경로만 바꾼다.

### 10.1 변환 파일 규격 (한 해 한 파일 `YYYY_wfde5.nc`)
- 변수: `TBOT`(K) `QBOT`(kg/kg) `PSRF`(Pa) `WIND`(m/s) `FLDS`(W/m²) `FSDS`(W/m²) `PRECTmms`(mm/s)
- 좌표: `LONGXY`·`LATIXY` 2D, `EDGEN/E/S/W`, lon **0–360**(WFDE5 원본은 −180–180 → roll), 달력 `noleap`
- domain: `domain.lnd.360x720_wfde5.nc`(xc/yc/area/mask). LND_DOMAIN은 f09 기본 유지 — DATM이 0.5°→f09 매핑.
- 변환기: 로컬 git `analysis/wfde5_to_clm5.ncl`(검증본). 서버에 있는 옛 사본은 remap 버그 → git 것을 배치해 쓸 것. NCL 비대화형 실행엔 `setenv NCARG_ROOT /usr/local/ncl_ncarg/6.6.2_gcc485` 필수.

### 10.2 스트림 파일 편집 지점 (3개 파일 공통)
```xml
<domainInfo>
  <filePath> /data2/ydkoh/2026_MOF_LSM/Atm_forc </filePath>
  <fileNames> domain.lnd.360x720_wfde5.nc </fileNames>
</domainInfo>
<fieldInfo>
  <variableNames>              <!-- file var  ->  datm internal name -->
     TBOT     tbot
     WIND     wind
     QBOT     shum
     PSRF     pbot
     FLDS     lwdn              <!-- TPQW stream; Solar: FSDS swdn ; Precip: PRECTmms precn -->
  </variableNames>
  <filePath> /data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5 </filePath>
  <fileNames>
    1981_wfde5.nc
    ...
    2010_wfde5.nc
  </fileNames>
</fieldInfo>
```
- 파일 목록은 `DATM_CLMNCEP_YR_START/END`와 일치시킬 것. 케이스 간 스트림 파일은 **복사**해서 쓴다(다시 쓰면 조용히 어긋남).
- `preview_namelists` 뒤 `chmod u+w user_datm.streams.txt.*`가 필요할 때가 있다.
- WFDE5는 land-only(바다 1e20). CDEPS mesh를 쓰는 모델(LM4)에선 land-mask mesh가 별도로 필요했지만(`wfde5_landmask_ESMFmesh.nc`), CESM2.1 DATM(MCT)은 domain mask로 처리해 그대로 동작했다.

---

## 11. 실측 비용 (climate01, 48 PE, 유휴 노드)

| 구성 | 격자 | 시간 / model-year | 비고 |
|---|---|---|---|
| CLM5-SP offline | f09 | 35–38 min | 24PE는 54 min(효율 77%, 손해) |
| CLM5-BGC offline, AD | f09 | ~2.1 h | 150 min/yr 벤치 |
| CLM5-BGC offline, post-AD·생산 | f09 | 1.70–1.83 h | 경합 시 2.4× 느려짐 |
| CLM5-BGC-CROP AD | f09 | ~4.1 h | crop이 +40% |
| CAM6+CLM5 F2000climo | f19 | 4.29 h | |
| CAM6+CLM5 F2000climo | f09 | 측정 중 | 예상 30–34 h |

디스크: CLM5 f09 restart 586 MB(SP)~1.4 GB(BGC), h0 월 122 MB → 30년 ≈ 62 GB. 컴포넌트 비중(SP): LND 86%, CPL 통신 ~20%, MOSART·DATM 각 5% 내외(꺼도 이득 없음).

---

## 12. 함정 체크리스트 (제출 전 30초)

- [ ] `./preview_namelists` 후 `run/lnd_in`에서 `finidat`·`spinup_state`·`use_cn`·`use_crop` 확인했나
- [ ] `CONTINUE_RUN=FALSE`인데 `finidat`이 compset 기본값(1.9x2.5 BgcCrop)으로 남아 있진 않나
- [ ] `NTASKS=48`인가 (F compset default 96)
- [ ] PBS `host=`와 `env_mach_specific.xml`의 hostfile이 같은 노드를 가리키나 (또는 `$PBS_NODEFILE`로 생성하나)
- [ ] `PERL5LIB` export 했나
- [ ] `RESUBMIT=0` 인가 (아니면 로그인 노드에서 다음 청크가 뜬다)
- [ ] `case.setup --reset` 했으면 `BUILD_COMPLETE=TRUE` 복구했나
- [ ] CAM: `npr_yz` 줬나 / CLM history 변수명 마스터 목록에 있나
- [ ] 생산 케이스에 `rm -rf` 골격을 쓰고 있진 않나
- [ ] 아카이브 rsync에 `--delete` 없나
- [ ] `ssh climate "..."` 안에서 `2>&1`·`&&` 쓰지 않았나 (tcsh: "Ambiguous output redirect")

---

## 13. 파일 인덱스

| 파일 (로컬 git `cesm/`) | 역할 |
|---|---|
| `run_scripts/f2000_clm5_test.csh` | 최소 골격 (F2000Nuopc f19) |
| `run_scripts/F_spinup_cam6clm5.csh` (서버 `~/run_scripts/`) | CAM6/CLM5 f19, history 목록 검증본 |
| `run_scripts/F_f09_cam6clm5.csh` + `F_2000climo_f09.pbs` | CAM6/CLM5 f09, hostfile 자동생성 최신 패턴 |
| `run_scripts/clm5_cyc1.pbs` | SP spin-up PBS 래퍼 + rsync 아카이브 |
| `scripts/clm5_bgc_pad_chunk.pbs` + `clm5_bgc_pad_chain.sh` | 10년 청크 체인 (FIRST 로직 포함) |
| `run_scripts/CLM5_prod_1979_2023.csh` + `clm5_prod_chunk.pbs` + `clm5_prod_chain.sh` | 생산런 (rm -rf 가드, 스트림 복사) |
| `scripts/clm5_postad_convergence.py` | 97% 격자 TOTECOSYSC 수렴 판정 |
| `scripts/verify_ad_exit_rescaling.py` · `verify_chunk_continuity.py` | AD→post-AD 역환산 확인 · 청크 경계 단차 검정 |
| `scripts/extract_clm5_annual.py` · `plot_clm5_spinup*.py` | history → 연평균 npz → 그림 |
| `analysis/wfde5_to_clm5.ncl` | WFDE5 → CLM DATM 포맷 변환 (검증본) |
| `download_inputs.py` · `download_f2000_inputs.sh` | 입력자료 수동 다운로드 (권한 문제 우회) |
| `CLM5_SPINUP_NOTES.md` | 실험 이력·판단·수렴 결과 (§3 함정, §7f/7k hostfile, §7g finidat, §7m 청크 검증) |
| 서버 `~/.cime/config_machines.xml` · `config_compilers.xml` | 머신 정의 (§1.3에 전문) |
| 서버 `~/CESM2.module.sh` | 대화형 셸용 모듈 로드 (CIME 빌드엔 불필요) |
