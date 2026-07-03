# MOF KIMST LSM Diagnostic Framework

## 1. Project overview

해양수산부 KIMST 지원 과제 (2026–2030): **차세대 해양기후모델 지면-식생모델 진단 및 개선**.
세종대 산학협력단 수행, 1인 연구자(ydkoh / 눈사람) 기준.

- **Phase 1 (2026–2028)**: 진단 체계 구축 — JULES, CESM2/CLM5, Noah-MP, LM4+ offline 테스트베드, 관측·재분석 DB, 지면-식생-대기 진단 도구
- **Phase 2 (2029–2030)**: 물리과정 고도화 (수문, 담수 유출, 역학식생, AI 에뮬레이터) + 미래 해양기후 영향 예측
- **과학 키워드**: 다중 LSM 비교, land-atmosphere coupling (Mi, λ), FLUXNET / GLEAM / ERA5-Land / GRDC / GRACE, ILAMB / PLUMBER2, CMIP6 LS3MIP, 동아시아 연안 염분·성층화

## 2. Working environment

이 repo는 **두 대의 머신**에서 mirror 됨:

- **로컬 (Ubuntu PC, `YDKOH-ubuntu`)**: 편집·git·문서·분석 코드 작성. Claude Code가 여기서 실행됨.
- **원격 (climate00 HPC)**: 실제 모델 빌드·실행·출력 분석. 무거운 작업은 모두 여기서.

작업 패턴:
1. 로컬에서 namelist / 스크립트 / 분석 코드 편집 → `git commit && git push`
2. climate00에서 `git pull` → 실행
3. 출력은 climate00에만 (`/data2/ydkoh/`); 로컬은 가벼운 텍스트만 보유

### climate00 SSH

- alias: `ssh climate` (이미 `~/.ssh/config`에 등록됨, port 22, user ydkoh, host 223.195.55.50)
- 비밀번호 없이 key 인증으로 접속됨
- 원격 명령 실행 패턴: `ssh climate "<command>"`

## 3. climate00 environment

| 항목 | 값 |
|---|---|
| OS | RHEL 8 (Linux), 48 cores |
| Compiler | Intel oneAPI 21 (ifort 2021.5.0), gfortran 8.5.0 |
| MPI | mvapich2-2.3.4 (intel21), OpenMPI 5.0.0 (gcc85) |
| NetCDF | /usr/local/netcdf/4.6.1_intel21 (C + Fortran) |
| HDF5 | /usr/local/hdf5/1.10.5_intel21 |
| PnetCDF | /usr/local/pnetcdf/1.11.2_intel21_mvapich2-2.3.4 |
| MKL | Intel MKL (intel21/mkl) |
| Batch system | none (직접 실행) |
| Login shell | tcsh; 빌드/실행 스크립트는 bash |

### 핵심 경로 (climate00)

| 종류 | 경로 |
|---|---|
| JULES | 소스 `~/jules-vn7.4/` · exe `~/jules-vn7.4/build/bin/jules.exe` · 실험 `~/JULES_runs/` |
| CESM | 소스 `~/CESM/` (release-cesm2.1.5) · cases `~/CESM/cases/` |
| 입력 / 출력 | 입력 `/data1/` · 출력 `/data2/ydkoh/` |
| 동료 백업(찬혁) | `/data1/backup/ChanhyukChoi/002.JULES_RUN/` |

(FCM `~/fcm/bin/fcm`, JULES 포팅 `~/JULES_porting/` 등 부수 경로는 필요 시 참조)

## 4. Model status (2026.05 기준)

| 모델 | 상태 | 비고 |
|---|---|---|
| **JULES vn7.4** | **gridded 전구 + DGVM 실행 완료** | **gfortran 재빌드**로 Intel netcdf 깨짐(`__libm_feature_flag`) 우회. 0.5° 전구 맵 런 ✓ + TRIFFID(4-pool RothC) DGVM ✓. serial(nompi), 81분/월. 상세 `jules/JULES_PORTING_NOTES.md`. 전면 areal 경쟁(frac 진화)·MPI는 미해결 |
| **CESM2.1.5 (CAM6/CLM5)** | 빌드 완료 | I2000Clm50Sp @ f09_g17. F2000climo timeaddmonths 에러 (PE layout 불일치) |
| **CESM2.1.5 (CAM4/CLM4)** | smoke test 완료, spin-up 중 | F2000C4L40 @ f19_f19. F_ctrl_smoke 1개월 ✓. F_spinup 10년 실행 중 (매월 restart). Snowfall sensitivity: 5년 perturbation (-25/-50/-75% from year 10-11) |
| **Noah-MP v5.2.1** | **gridded global 실행 완료** | HRLDAS offline(`~/HRLDAS/`, v5.2.1). intel21 serial. 단일격자 ✓ + **global 0.5° GSWP3 gridded 실행 ✓**(WRF/WPS geo_em, GSWP3→LDASIN 변환기). 다음: 2-stage spin-up(static DVEG=4 cold start → dynamic DVEG=2). 상세 `noahmp/NOAHMP_PORTING_NOTES.md` |
| **LM4+** | **300년 static-veg spin-up 완료** | UFS LND-LM4(CDEPS DATM), C96, gfortran. cold-start qscomp clamp 패치. GSWP3 cycling 300yr → 평형 IC. 다음: WFDE5 forcing 이어달리기 + dynamic veg 1200yr+. 상세 `lm4/LM4_SPINUP_NOTES.md` |
| **KIOST-ESM2 (GFDL ESM4.5)** | **빌드 + smoke test 완료** | 결합 ESM(FV3-C96+AM4.5+MOM6+SIS2+COBALT+LM4). tomo(Intel19/mvapich4.0/nc4.9.2)→climate00(intel21/mvapich2-2.3.4/nc4.6.1) 재빌드 ✓(223M, AVX2). netcdf `__libm_feature_flag`는 oneAPI 런타임이 해결(gfortran 불필요). 720→48 PE 축소 config(FV3 2,2/MOM 6,4, concurrent)로 **1 model-day 결합적분 완주**(ocean.stats NaN 0, RESTART 129). mvapich2 `MV2_ENABLE_AFFINITY=0` 필수. 1 model-day≈43분(48코어)→**생산런 불가, 검증용**. 상세 `kiost/KIOST_ESM2_PORTING_NOTES.md` |

## 5. Notion (research hub)

진행 상황·문헌·실험 로그는 **Notion**에서 관리. 이 repo의 CLAUDE.md는 환경/구조 정보만 담고, 변동성 있는 정보는 Notion 우선.

- Hub page: `33ca128b-012a-817f-aa1b-d03320027a72`
- 모델 설치 로그 DB: `ff9d38a9-eab6-4f00-9fc8-81ed9657d859`
- 문헌 DB: `003a75ec-c467-490e-ba24-3ccd61df0e44`
- JULES log page: `33ca128b-012a-81de-93d7-d2caf9435195`
- CLM5 log page: `33ca128b-012a-8182-99d8-d87a4916e89f`

## 6. Repo layout (current/evolving)

```
MOF_LSM_project/                # 로컬 = /Volumes/data01/MOF_LSM_project
├── CLAUDE.md                   # 이 파일 / README.md
├── 2026/                       # 해수부 마일스톤·착수보고·분기 보고 (docx/pdf/md/html)
├── jules/                      # JULES namelist·빌드·실험 설정 사본
├── kiost/                      # KIOST-ESM2 (GFDL ESM4.5) 포팅 노트
├── cesm/
│   ├── cases/                  # case 스크립트
│   ├── run_scripts/            # 실행 스크립트
│   ├── clm_output/             # 로컬 분석용 경량 CLM 출력
│   └── download_*.{sh,py}      # 입력자료 다운로드
├── analysis/                   # Python/NCL 분석 코드
├── data/ · figures/            # 경량 데이터·그림 (대용량 제외)
└── (docs/ — 계획만, 미생성)     # 로드맵·포팅가이드 예정, 아직 없음
```

- noahmp/(porting notes)·lm4/(spin-up notes) 생성됨.
- 대용량 파일(NetCDF, 빌드 산출물, 입력자료)은 git 제외(`.gitignore`).
- `CLAUDE-FABLE-5.md`는 시스템 프롬프트 사본 — 프로젝트 메모리 아님. `.claude/` 이동 또는 gitignore 권장(별도 확인 후).

## 7. Working rules (Claude Code 작업 규칙)

- **언어**: 대화는 한국어, 코드 주석·논문·variable name은 영어
- **단계 분할**: 3단계 이상 작업은 계획 먼저 제시 → 확인 → 한 단계씩 진행. 한 번에 하나만, 10분 단위로 쪼갬
- **기초 설명 필수**: 명령어·패턴마다 "이게 무엇을 하는지" 짧게라도 설명
- **막연한 격려 금지**: "잘하셨어요" 류 대신 구체적 다음 행동만
- **climate00 작업**: 항상 `ssh climate "<command>"` 패턴으로. 무거운 작업은 nohup/screen/tmux로 백그라운드
- **파일 편집**: 로컬 우분투에서 git으로 관리되는 파일만 편집. climate00의 모델 소스(`~/jules-vn7.4/` 등)는 직접 편집 금지 (단, parallel_mod.F90 같은 검증된 패치는 예외, 별도 patches/에 기록)
- **commit 메시지**: 영어, 동사로 시작 (`Add JULES spinup_cy01 namelist`, `Fix CESM SLIBS append tag`)
- **Notion 업데이트**: Claude Code에서 Notion MCP 연결 시, 모델 설치 로그·문헌 추가는 Notion에 직접. CLAUDE.md는 안 건드림 (구조만 변하면 갱신)

## 8. Known issues

- **JULES Intel netcdf 깨짐 (해결됨 → gfortran)**: `libnetcdf.so.13`이 요구하는 `__libm_feature_flag` 심볼이 시스템 Intel 런타임(oneAPI 2022.0.1; "intel21" 모듈도 실제 이걸 가리킴) libimf에 없음. admin이 netcdf 빌드 후 컴파일러 교체로 깨진 상태. **해결 = gfortran + netcdf-4.6.1_gcc85 재빌드**(Intel 안 씀). 상세 `jules/JULES_PORTING_NOTES.md`
- **JULES MPI 빌드 실패 (미해결)**: `PMPI_Comm_size: Invalid communicator` (mvapich2-2.3.4 + intel21 / OpenMPI-5.0.0 + gcc85 둘 다). 현재 nompi(serial). 0.5° 전구 81분/월이라 장기 spin-up엔 MPI/영역축소 필요
- **JULES 전면 areal 경쟁 미해결**: DGVM은 `l_veg_compete=.false.`(탄소·phenology·LAI/수고만)로 구동. `=.true.`는 frac을 prognostic IC로 요구(합=1) → frac.nc를 use_file로 끌어오는 처리 필요
- **JULES ERA5 forcing time coord 불일치**: `/data1/backup/ChanhyukChoi/.../92.GPCPobs_ERA5obs/`의 1978-12.nc는 `proleptic_gregorian`, 다른 파일은 `standard`. 1979-01.nc 첫 time value가 ~Jan 23. (2010 파일은 정상.) 1979부터 돌릴 땐 재확인 필요
- **ifort 최적화 버그 (해결됨, 패치 적용됨)**: `src/control/standalone/parallel/parallel_mod.F90`의 local 변수 미초기화. `ntasks_x`, `ntasks_y`, `task_nx`, `task_ny`, `x_start`, `y_start`를 `= 0`으로 초기화하는 패치 적용됨 (gfortran에도 무해)

## 9. Key learnings

- JULES vn6.0 → vn7.4 namelist 변경 6건: `l_coord_latlon=.true.` (JULES_LATLON), `model_grid.nml` 순서, 5개 PFT 인덱스, `confrac=0.3` (jules_soil), `ctile_orog_fix=2` (science_fixes), `&IMOGEN_ONOFF_SWITCH l_imogen=.false.` (imogen)
- JULES gfortran 빌드: `-fallow-argument-mismatch`(gcc10+)는 gcc8.5에 없음 → `-Wno-argument-mismatch` 사용. fcm-make `custom` 플랫폼은 env(JULES_COMPILER/NETCDF_*/LDFLAGS_EXTRA)를 읽음
- JULES gridded run namelist 함정: drive.nml var은 JULES 식별자(t/q/pstar/wind/sw_down/lw_down/precip), `data_period`(≠tinc), `z1_uv_in/z1_tq_in` 필수. can_rad_mod=6엔 `ilayers=10`. DGVM은 soil_bgc_model=2(+kaps_4pool/n_inorg_turnover/bio_hum_cn), triffid_params 6종(alloc_*/dpm_rpm_ratio/retran_*), initial_conditions에 canht. 상세 `jules/JULES_PORTING_NOTES.md`
- CESM2.1.5 `config_compilers.xml`의 `<SLIBS>`는 반드시 `<append>` 태그로 감싸야 함. 외부 PIO 설정은 내부 PIO1과 충돌하므로 제거
- JULES spinup 우선순위: smc_tot/smcl (~0.1 kg/m²), t_soil (~0.01 K). 깊은 층 수렴은 layer-specific smcl로 확인
- 다중 모델 운용: 각 실행 스크립트 `module purge` + 모델별 모듈. 분석 도구(nco, cdo, ncview)는 `.cshrc`에 공통, 모델 모듈은 절대 .cshrc 금지
