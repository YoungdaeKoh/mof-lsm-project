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

### 핵심 경로

| 종류 | 경로 |
|---|---|
| JULES 소스 | `~/jules-vn7.4/` |
| JULES 실행파일 | `~/jules-vn7.4/build/bin/jules.exe` |
| JULES 실험 | `~/JULES_runs/` |
| JULES 포팅 작업물 | `~/JULES_porting/` |
| CESM 소스 | `~/CESM/` (release-cesm2.1.5) |
| CESM cases | `~/CESM/cases/` |
| FCM | `~/fcm/bin/fcm` (anaconda perl 5.32) |
| 입력자료 | `/data1/` |
| 동료 백업 (찬혁) | `/data1/backup/ChanhyukChoi/002.JULES_RUN/` |
| 출력자료 | `/data2/ydkoh/` |

## 4. Model status (2026.05 기준)

| 모델 | 상태 | 비고 |
|---|---|---|
| **JULES vn7.4** | 빌드·테스트런 완료, spinup_cy01 설정 중 | serial(nompi). MPI 빌드 실패 미해결. ERA5 forcing time coord 이슈 미해결 |
| **CESM2.1.5/CLM5** | 빌드·5일 테스트런 완료 | I2000Clm50Sp @ f09_g17, 48 tasks |
| **Noah-MP** | 미시작 | CLM5와 같은 모듈 스택 활용 예정 |
| **LM4+** | 미시작 | FMS 프레임워크 별도 빌드 필요 |

## 5. Notion (research hub)

진행 상황·문헌·실험 로그는 **Notion**에서 관리. 이 repo의 CLAUDE.md는 환경/구조 정보만 담고, 변동성 있는 정보는 Notion 우선.

- Hub page: `33ca128b-012a-817f-aa1b-d03320027a72`
- 모델 설치 로그 DB: `ff9d38a9-eab6-4f00-9fc8-81ed9657d859`
- 문헌 DB: `003a75ec-c467-490e-ba24-3ccd61df0e44`
- JULES log page: `33ca128b-012a-81de-93d7-d2caf9435195`
- CLM5 log page: `33ca128b-012a-8182-99d8-d87a4916e89f`

## 6. Repo layout (expected)

```
~/MOF_LSM_project/
├── CLAUDE.md                  # 이 파일
├── README.md
├── .gitignore
├── docs/                      # HTML 로드맵, 포팅 가이드, 보고서
├── jules/
│   ├── namelists/             # JULES namelist 사본
│   ├── build/                 # build_jules.sh 등
│   └── runs/                  # 실험 설정
├── cesm/
│   ├── config/                # ~/.cime/ 사본
│   └── cases/                 # case 스크립트
├── noahmp/                    # 추후
├── lm4/                       # 추후
└── analysis/                  # Python/NCL 분석 코드
```

대용량 파일(NetCDF, 빌드 산출물, 입력자료)은 git에 넣지 않음. `.gitignore`로 차단.

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

- **JULES MPI 빌드 실패**: `PMPI_Comm_size: Invalid communicator` (mvapich2-2.3.4 + intel21 / OpenMPI-5.0.0 + gcc85 둘 다). 현재 nompi(serial) 사용
- **JULES ERA5 forcing time coord 불일치**: `/data1/backup/ChanhyukChoi/.../92.GPCPobs_ERA5obs/`의 1978-12.nc는 `proleptic_gregorian`, 다른 파일은 `standard`. 1979-01.nc 첫 time value가 ~Jan 23. 찬혁님 확인 또는 재생성 필요
- **ifort 최적화 버그 (해결됨, 패치 필요)**: `src/control/standalone/parallel/parallel_mod.F90`의 local 변수 미초기화. `ntasks_x`, `ntasks_y`, `task_nx`, `task_ny`, `x_start`, `y_start`를 `= 0`으로 초기화하는 패치 적용 필수

## 9. Key learnings

- JULES vn6.0 → vn7.4 namelist 변경 6건: `l_coord_latlon=.true.` (JULES_LATLON), `model_grid.nml` 순서, 5개 PFT 인덱스, `confrac=0.3` (jules_soil), `ctile_orog_fix=2` (science_fixes), `&IMOGEN_ONOFF_SWITCH l_imogen=.false.` (imogen)
- CESM2.1.5 `config_compilers.xml`의 `<SLIBS>`는 반드시 `<append>` 태그로 감싸야 함. 외부 PIO 설정은 내부 PIO1과 충돌하므로 제거
- JULES spinup 우선순위: smc_tot/smcl (~0.1 kg/m²), t_soil (~0.01 K). 깊은 층 수렴은 layer-specific smcl로 확인
- 다중 모델 운용: 각 실행 스크립트 `module purge` + 모델별 모듈. 분석 도구(nco, cdo, ncview)는 `.cshrc`에 공통, 모델 모듈은 절대 .cshrc 금지
