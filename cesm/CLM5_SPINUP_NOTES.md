# CLM5.0 offline (I2000Clm50Sp) GSWP3 spin-up — climate00 notes

_**진행 중 (2026-07-10)**: cold-start cycle 1 (1981–2010) 실행 중, job 2931 @ climate01 48PE, ~18.5h 예상._

다중 LSM 진단의 세 번째 모델. LM4(300년 완료)·Noah-MP(60년 완료)와 **같은 프로토콜**: static vegetation에서 토양수분·토양온도를 먼저 수렴시키고, 그 뒤 dynamic vegetation.

## 1. 구성

| 항목 | 값 |
|---|---|
| CLM 소스 | `release-clm5.0.37` (= `ctsm1.0.dev025`), CESM2.1.5 내장. **CLM6 아님** |
| compset | `2000_DATM%GSWP3v1_CLM50%SP_SICE_SOCN_MOSART_CISM2%NOEVOLVE_SWAV` (alias `I2000Clm50Sp`) |
| grid | `f09_g17` (0.9°×1.25°). **CESM에 정확한 전구 1°×1° 격자는 없음** |
| calendar | `NO_LEAP` |
| case | `~/CESM/cases/clm5_spinup_gswp3` (clone of `clm5_test01`, `--keepexe`) |
| exe | `/data2/ydkoh/cesm2_output/clm5_test01/bld/cesm.exe` (공유) |
| run dir | `/data2/ydkoh/cesm2_output/clm5_spinup_gswp3/run` |
| 아카이브 | `/home/ydkoh/CESM/spinup_raw/clm5_GSWP3_SP_cyc1/` (rsync, `--delete` 없음) |

### compset 선택 근거
- **`CLM50%SP`** = Satellite Phenology. LAI를 관측 기후값으로 처방 → Noah-MP `DVEG=4`, LM4 static veg와 같은 계열. BGC/탄소 예후변수 없음 → spin-up 대상이 토양수분·토양온도로 한정.
- **`2000`** = CO2·에어로졸 2000년 고정. constant-forcing cycling 프로토콜과 정합. `IHistClm50Sp`는 CO2·토지이용이 transient라 LM4/Noah-MP와 어긋남.
- **grid**: `f09_g17`(0.9×1.25) vs `hcru_hcru`(0.5°, GSWP3 원해상도). hcru는 domain이 **CRUNCEP land-mask**(`domain.lnd.360x720_cruncep`)라 GSWP3 mask(`domain.lnd.360x720_gswp3`)와 불일치 위험 + 비용 4배. **모델 격자를 억지로 맞출 필요 없음** — 진단 시 공통 격자로 remap. f09는 이미 빌드·검증됨.

### ★ cold start 결정
clone 직후 기본 `finidat`이 `clmi.I2000Clm50BgcCrop.2011-01-01.**1.9x2.5**_gx1v7_...nc` — 격자(1.9×2.5 vs 0.9×1.25)도 구성(BgcCrop vs SP)도 불일치.
→ `CLM_FORCE_COLDSTART=on`. LM4·Noah-MP 모두 cold start에서 수렴시켰으므로 출발선 정합.
로그 확인: `WARNING: CLM is starting up from a cold state` + `Model clm no file specified for finidat`. (이 WARNING은 의도한 것.)

## 2. ★ 벤치마크 (2026-07-10, climate01, 동일 조건 1개월 cold start)

| PE | s/mday | SYPD | 분/model-year | Model Cost (pe-hrs/yr) |
|---|---|---|---|---|
| 24 | 8.967 | 26.40 | 54.5 | 43.64 |
| **48** | **5.800** | **40.81** | **35.3** | **28.23** |

- **speedup 1.55× / 병렬효율 77%.** Noah-MP의 24→48(1.22×, 61%)보다 좋음 — CLM은 계산 비중이 커서(LND 86%) 코어를 잘 씀.
- **24 PE는 모든 면에서 손해.** 느린 데다 `Model Cost`가 더 비쌈 — CESM은 node 단위로 환산하는데 24 PE도 48코어 노드를 통째로 점유.
- 1년 런(48PE)은 6.302 s/mday, 38.3분/년 → 계절 변동·월별 출력 누적으로 1개월 런보다 8% 느림. **계획엔 38.3분/년(보수적)** 사용.
- 컴포넌트 비중(1년, 48PE): **LND 1976s (86%)**, CPL COMM 470s, ROF(MOSART) 152s, ATM(DATM) 138s, GLC(CISM) 0.7s. → MOSART/DATM 꺼도 무의미.
- **96PE(2노드) 불가**: climate00은 로그인 노드, climate02는 타 사용자 점유. **climate01 단일 노드 48PE가 상한.**

비용: 30년 = 19.2h, 2 cycle = 38.3h. 파일 크기 restart 586MB, h0(월) 122MB → 30년 ≈ 62GB.

## 3. ★★ 함정 3개 (전부 실패로 겪음)

### 3a. compute node에 perl `bigint` 없음
`case.run`이 **실행 시점에** `build-namelist`(perl)를 호출 → 계산노드에서 필요.
```
Can't locate bigint.pm in @INC ... clm_phys_vers.pm line 30
```
- `bigint.pm`·`bignum.pm`·`bigrat.pm`·`Math/BigRat.pm`·`Math/BigFloat/`가 **climate00(로그인)에만** 존재, climate01·02엔 없음.
- **해결**: `/home` 공유 + `PERL5LIB`에 `~/perl5/lib/perl5` 이미 등록 → 그 5개를 거기로 복사. root 불필요. PBS 스크립트에도 `export PERL5LIB=...` 명시.

### 3b. `case.setup --reset` 이 `BUILD_COMPLETE`를 지움
```
ERROR: Build complete is not True please rebuild the model by calling case.build
```
- `CLM_FORCE_COLDSTART`·`NTASKS` 변경은 **namelist/decomp 수준**이라 재빌드 불필요.
- **해결**: `./xmlchange BUILD_COMPLETE=TRUE` (exe는 `--keepexe`로 `clm5_test01/bld` 공유).

### 3c. `case.submit --no-batch` 의 가짜 `exit=1`
```
2026-07-10 14:56:11 MODEL EXECUTION HAS FINISHED
ERROR: No result from jobs [('case.run', None)]
=== END exit=1 ===
```
- 모델은 **정상 완주**. CIME이 `--no-batch`에서 배치 결과를 못 찾아 뱉는 잡음.
- **성패는 `MODEL EXECUTION HAS FINISHED` + restart/history 파일로 판단.** (Noah-MP `exit=255`와 같은 성격.)

## 4. PBS 래핑 (BATCH_SYSTEM=none 이므로 필수)
CESM machine `climate00`은 `BATCH_SYSTEM: none` → `case.submit`이 **로그인 노드에서 48-rank를 그대로 띄움**. 반드시 PBS로 감싸고 `--no-batch`로 잡 안에서 `case.run` 실행. 스크립트 `cesm/run_scripts/clm5_cyc1.pbs`.

**climate02 사용 금지** ([[climate01-only-for-jobs]]).

## 5. 다음
1. cycle 1(30년) 완료 → 아카이브 확인
2. cycle 2(동일 forcing 재생) → **동일 날짜(1월 1일) cycle 간 표류**로 수렴 판정. `NO_LEAP`이라 restart가 자동으로 1월 1일 → Noah-MP에서 했던 Jan-1 스냅샷 수술 불필요.
3. 면적가중은 CLM history의 `area`·`landfrac` 사용(cos(lat) 근사보다 정확). 빙상 격자 분리는 Noah-MP와 동일 원칙 ([[lsm-spinup-ice-mask-convergence]]).
4. 수렴 후 dynamic vegetation.

## 6. 참고: 세 모델 spin-up 대조

| 모델 | static veg 설정 | 달력 | restart 알람 | spin-up |
|---|---|---|---|---|
| LM4 | static veg | leap (Gregorian) | FMS 달력-연 → 매년 Jan-01 | 300년 완료 |
| Noah-MP | `DVEG=4` | leap (2/29 합성 주입) | 시간 기반 8760h → Jan-01→Dec-25 표류 | 60년 완료 |
| **CLM5.0** | `CLM50%SP` | **NO_LEAP** | 달력-연 → 매년 Jan-01 | cycle 1 진행 중 |
| JULES | — | — | — | MPI 미해결로 장기적분 불가(81분/월 serial) |

"같은 연수"가 등가 기준이 아님. 각자의 표류 기준으로 수렴했는가가 기준 — 토양 깊이·하부경계가 다름(Noah-MP 2m + 고정 TMN relax, LM4 8.75m 자유, CLM5 ~50m 기반암 포함).
