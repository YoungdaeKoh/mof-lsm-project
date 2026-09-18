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

## 7. ★★ Spin-up 수렴 기준 — 공식 가이드 (2026-07-12 조사)

### 7a. CLM5-SP 공식 기준 (우리 케이스 해당)
`doc/.../Spinning-up-the-Satellite-Phenology-Model-CLMSP-spinup.rst`:
> "run CLMSP for **about 50 simulation years** from arbitrary initial conditions."
> 대부분 상태변수(FSH, EFLX_LH_TOT, GPP, H2OSOI, TSOI)는 **10년 미만**에 평형. **TWS는 조금 더 걸림.**
- 진단도구 `tools/contrib/SpinupStability_SP.ncl`이 보는 변수: **FSH**(현열), **EFLX_LH_TOT**(잠열), **GPP**(광합성), **TWS**(총수분저장), **H2OSOI layer 8**(~0.80 m), **TSOI layer 10**(~1.36 m).
- ★ **층 주의**: 가이드는 TSOI **layer 10 = 1.36 m**를 봄. levgrnd 최하층(25층)은 **41.998 m** — 이걸 보면 열관성 탓에 영원히 미수렴으로 오판. (내가 처음 이 실수 함.)
- levgrnd node depth [m]: 0.01/0.04/0.09/0.16/0.26/0.40/0.58/0.80/1.06/**1.36**/1.70/2.08/2.50/2.99/3.58/4.27/5.06/5.95/6.94/8.03/9.80/13.33/19.48/28.87/**42.00**.

### 7b. CLM5-BGC 기준 (참고, 우리 SP엔 불필요)
- AD(accelerated decomposition) ~200년 → pAD(final) 수백 년.
- 판정: **"97% 격자에서 총생태계탄소(TOTECOSYSC) 변화 ≤ 1 gC/m²/yr"** (= 3% 미만이 disequilibrium). 고위도 TOTSOMC 회전 느려 1000년+ 걸릴 수 있음, 완화 허용.
- `SpinupStability.ncl` 변수: TOTECOSYSC, TOTSOMC, TOTVEGC, TLAI, GPP, TWS.

### 7c. ★ 우리 CLM5 cycle 1 (30년) 실측 vs 가이드 (area-weighted, 마지막 5년 |Δ/yr|)
| 가이드 변수 | 마지막 5년 |Δ/yr| | 판정 |
|---|---|---|
| H2OSOI layer 8 | 0.0014 mm³/mm³ | ✅ 수렴 |
| FSH (현열) | 0.25 W/m² | ✅ 수렴 |
| EFLX_LH_TOT (잠열) | 0.45 W/m² | ✅ 수렴 |
| TSOI layer 10 (1.36 m) | 0.11 K | ✅ 거의 수렴 |
| **TWS** | 12.8 mm | ⚠ 미수렴 (가이드가 "더 걸린다"고 예고한 그 변수) |
- 데이터: `cesm/clm_output/clm5_spinup_guide_cyc1.csv`, 추출 `~/extract_clm5_guide.py`.
- **판정: cycle 3 불필요.** 가이드 목표 50년을 이미 넘김(cycle 1+2=60년). 가이드가 보라는 변수는 TWS 하나 빼고 다 수렴, 그 TWS는 가이드가 "더 걸린다"고 명시한 변수. LM4 사하라 심층수와 동일 논리(global/flux 무영향).
- cycle 2 종료 후 `r.2041-01-01 − r.2011-01-01` 표류로 최종 확정.

### 7d. ★ 모델 간 수렴 기준 정합 판단
| 모델 | 공식 기준 | 판정 변수 | 격자 커버리지 |
|---|---|---|---|
| **CLM5-SP** | 가이드: ~50년, flux/soil 10년 내 평형 | FSH·LH·GPP·H2OSOI·TSOI(L10)·TWS | (도구 기본) |
| **CLM5-BGC** | 97% 격자 TOTECOSYSC ≤ 1 gC/m²/yr | 탄소풀 + TWS | 97% |
| **JULES** | **모델 내장** `&JULES_SPINUP`: 변수별 tolerance, **전 격자** `\|Δ\| ≤ tol` | `smcl`·`t_soil`·`c_soil`·`c_veg` | **100% (ALL)** — CLM보다 엄격 |
| **LM4/GFDL** | 정형 tolerance **없음**. carbon lifetime cap(500yr)+가속치환+장기적분(piControl 800년+) | (탄소 평형 중심) | — |
| **Noah-MP** | HRLDAS 공식 수렴 기준 문서 **없음** | 관행: soil moisture/temp 안정까지 | — |

### 7e. ★ BGC-AD 케이스 실제 셋업 + 실측 속도 (2026-07-20)
LM4 dynveg spin-up과 **공정비교**용 CLM5 탄소 spin-up. SP 다음 단계(동적 탄소).
- **케이스 `clm5_bgc_ad`** (crop 없음): compset **longname** `2000_DATM%GSWP3v1_CLM50%BGC_SICE_SOCN_MOSART_CISM2%NOEVOLVE_SWAV`로 생성. **주의: 2000+GSWP3 non-crop alias가 없음**(비-crop은 CRU forcing만; `I2000Clm50BgcCru`) → longname에서 `BGC-CROP`→`BGC`만 바꿔 GSWP3v1 DATM 템플릿 유지. `create_newcase --compset "<longname>" --res f09_g17 --machine climate00 --run-unsupported`.
- **config**: `CLM_ACCELERATED_SPINUP=on`(→ `spinup_state=2`, CLM5 AD), `CLM_FORCE_COLDSTART=on`, `CLM_BLDNML_OPTS=-bgc bgc`(crop 없음 → `use_cn=.true. use_crop=.false.`), NTASKS=48, NO_LEAP, RUN_STARTDATE=0001-01-01, DATM 1981/2010/align 1981. WFDE5는 crop 케이스의 `user_datm.streams.txt.CLMGSWP3v1.{Solar,Precip,TPQW}` 3개 복사(WFDE5 domain `domain.lnd.360x720_wfde5.nc` + 1981-2010 절대경로 내장; **LND_DOMAIN은 f09 기본 유지**, DATM이 WFDE5 0.5°→f09 매핑).
- **입력자료**: non-crop fsurdat = `surfdata_0.9x1.25_hist_16pfts_...c190214.nc`(16-pft, 동료 공유분 디스크에 존재). BGC 공통(ndep/lightning/popdens/finundated)은 crop용 다운로드분 재사용. `check_input_data` 0 누락. 빌드 474초.
- **★ 실측 속도 (climate01 48PE, 유휴, daily dt 안정)**:
  - BGC-**CROP**-AD: 41초/model-day = **249분/년** (200yr ≈ 35일)
  - **순수 BGC-AD: 24.6초/day = 150분/년** (200yr ≈ **21일**) — **crop 제거로 40% 절감**(추정 15-30%보다 큼)
  - SP는 35분/년 → BGC는 SP의 ~4.3배(CN순환+수직토양분해가 지배; crop은 그 위 40%만).
- **노드 정합(정정)**: climate01·climate02는 **동일 하드웨어**(48코어 257GB). 이전 "climate02가 4.4배 느리다"는 **잘못된 측정**(sample1 빈 model date로 progress 오산)이었음. 실제 느림은 **타 사용자 부하 경합**일 때만. [[climate01-only-for-jobs]]
- **다음**: 청킹 = walltime 24h ÷ 150분/년 ≈ 잡당 9년 → self-chaining PBS 또는 수동 청크. AD 200년(또는 TOTECOSYSC ≤1 수렴까지) → post-AD(`CLM_ACCELERATED_SPINUP=off`).

- **결론: CLM5-SP 가이드를 다중 LSM 공통 수렴 기준으로 채택.** 근거:
  1. 유일하게 **정량 threshold + 판정 변수 + 진단도구**를 문서화한 표준.
  2. JULES 내장 기준(smcl/t_soil, 전 격자)과 **변수·방향 일치**(오히려 JULES가 더 엄격 → CLM 통과하면 JULES 관점서도 안전 방향).
  3. LM4·Noah-MP는 정형 기준 부재 → CLM 프레임(표층 flux + soil T/moisture 층 + TWS-longer 예외) 적용이 타당.
- **공통 판정 규칙(채택)**: ① 표층 flux(현열·잠열)·표층 토양수분·soil T(≤1.5 m) 의 cycle 간 |Δ| 가 무시 가능 → 수렴. ② TWS/심층수/심층열은 "느린 저수지"로 별도 취급, global·flux 진단엔 무영향 시 완료로 간주(LM4 사하라 판례). ③ 각 모델은 자기 격자에서 돌리고 비교는 remap 후.

상세: `notes/lsm_spinup_criteria.html` ([[lsm-landmean-comparability]], [[lsm-spinup-ice-mask-convergence]])

### 7f. ★★ CESM mpirun이 PBS 노드 할당을 무시한다 (2026-07-20, job 8279)

**증상**: `#PBS -l select=1:...:host=climate02`로 제출했는데 **climate02는 load 0.00**, `cesm.exe`는 **climate01에서** 48랭크로 실행. 같은 시각 climate01에 LM4 잡(48랭크)이 돌고 있어 **96랭크가 48코어를 나눠 씀** → 둘 다 심각한 성능 저하(LM4 CPU 99% → 15%).

**원인**: `env_mach_specific.xml`의 mpirun 인자가 **고정 hostfile**을 참조.
```xml
<arg name="num_tasks"> -hostfile /home/ydkoh/mvapich2.hosts -np {{ total_tasks }}</arg>
```
`~/mvapich2.hosts` 내용이 `climate01:48` → PBS가 어느 노드를 주든 mpirun은 이 파일만 보고 climate01로 보냄. `BATCH_SYSTEM=none`(§8 기록)의 연장 부작용인데, **노드 할당까지 무시된다는 건 새로 발견**.

**해결**: 케이스 전용 hostfile을 PBS 할당에서 생성.
- `env_mach_specific.xml` → `-hostfile /home/ydkoh/CESM/cases/clm5_bgc_ad/mpi.hosts`
- PBS 스크립트 선두에 `sort -u "$PBS_NODEFILE" | awk '{print $1":48"}' > "$CASE/mpi.hosts"`
- **공용 `~/mvapich2.hosts`는 미변경**(타 CESM 케이스 영향 방지).
- 확인: `mpi.hosts` = `climate02:48`, climate02에 cesm.exe 48개 / climate01에 0개.

**★ 진단법**: 잡이 `R`이고 로그도 갱신되는데 지정 노드가 한가하면, **로그 파일명의 머신명은 CESM `--machine` 값일 뿐 실제 실행 노드가 아님**. 각 노드에서 `ps -u <user> -o args`로 `cesm.exe`를 직접 찾을 것. `pgrep -c -u ydkoh cesm.exe`가 빠름.

**교훈**: LM4(FMS) 실행 스크립트는 `mpirun -hostfile $PBS_NODEFILE`로 PBS를 따르는데 CESM만 고정 파일을 씀. **다중 모델을 병렬로 돌릴 때는 각 모델이 노드 할당을 어떻게 정하는지 먼저 확인할 것.** [[climate01-only-for-jobs]] (climate02는 2026-07-20 기준 유휴 — 상시 점유라는 기존 기록은 갱신 필요)

### 7g. AD 실행 확인 + post-AD 전환 시 `finidat` 함정 (2026-07-20, job 8281)

**AD 정상 가동 확인** (`run/lnd_in`, `lnd.log.8281`):
- `spinup_state = 2` (가속분해 활성) · `use_cn = .true.` · `use_crop = .false.`
- `CLM_ACCELERATED_SPINUP=on`, `CONTINUE_RUN=TRUE`, `STOP_N=9`(첫 청크만 9년, 이후 10년 — restart를 0011/0021/… 10년 경계에 정렬)
- 로그: `Reading restart pointer file....` → `Reading restart file clm5_bgc_ad.clm2.r.0002-01-01-00000.nc` = **warm start 정상**
- 노드: climate02 (§7f의 hostfile 수정 적용). 강제장: **WFDE5** (`user_datm.streams.txt.CLMGSWP3v1.*` → `/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5/{year}_wfde5.nc`, domain `domain.lnd.360x720_wfde5.nc`) = LM4 offline과 **동일 원자료**.

**★ 함정: `CLM_FORCE_COLDSTART=off`로 바꾸면 `finidat`에 기본값이 채워짐.**
- 현재 값: `/data1/CESM2_INPUT/.../clmi.I2000Clm50BgcCrop.2011-01-01.**1.9x2.5**_gx1v7_...nc`
- **격자(1.9×2.5 vs 우리 0.9×1.25)도 구성(BgcCrop vs Bgc)도 불일치** (§7의 기존 기록과 동일 문제).
- `CONTINUE_RUN=TRUE`인 동안은 rpointer를 읽으므로 **무해**. 하지만 **post-AD 전환 시 `CONTINUE_RUN=FALSE` + `finidat`으로 AD 최종 restart를 지정하게 되므로, 그때 이 기본값을 반드시 덮어쓸 것.** 안 덮으면 엉뚱한 격자 파일을 읽음.

**post-AD 전환 절차 (AD 완료 후)**
```bash
cd ~/CESM/cases && ./create_clone --case clm5_bgc_pad --clone clm5_bgc_ad
cd clm5_bgc_pad
./xmlchange CLM_ACCELERATED_SPINUP=off     # spinup_state=0; CLM이 restart 읽을 때 토양 C/N 풀을 정상 배율로 환산
./xmlchange CLM_FORCE_COLDSTART=off
./xmlchange CONTINUE_RUN=FALSE
./xmlchange RUN_STARTDATE=0001-01-01
echo "finidat = '/data2/ydkoh/cesm2_output/clm5_bgc_ad/run/clm5_bgc_ad.clm2.r.0201-01-01-00000.nc'" >> user_nl_clm
# ↑ 반드시 명시. 안 하면 위의 1.9x2.5 기본값이 남음
```
clone을 쓰는 이유: AD 케이스와 그 결과를 보존하기 위함.

**수렴 판정**: 97% 격자에서 `TOTECOSYSC` 표류 ≤ 1 gC/m²/yr (§7의 채택 기준). 200년을 채우는 게 목적이 아니라 수렴이 목적이므로, 조기 수렴 시 중단 가능.

### 7h. AD 출력 = 연별 확정 (2026-07-21)

**결정: AD spin-up은 연별 출력 유지** (`hist_nhtfrq=-8760`, `hist_mfilt=20`, `hist_empty_htapes=.true.`, `hist_fincl1='TOTECOSYSC','TOTECOSYSN','TOTSOMC','TOTSOMN','TOTVEGC','TOTVEGN','TLAI','GPP','CPOOL','NPP','TWS'`).
- 왜: AD 수렴 판정 기준이 "TOTECOSYSC **연간** 표류 ≤ 1 gC/m²/yr" → 연평균 비교가 자연스러움. 월별로 하면 200년×12로 12배 용량인데 계절변동은 수렴 판정에 미사용.
- **월별은 post-AD 생산런(WFDE5 1981-2010)에서** — 계절순환(유출·LAI·플럭스)을 LM4·관측과 비교할 때. LM4 offline이 지금 월별(`land_month`)인 건 그게 이미 생산런 성격이기 때문(위상이 다름).
- 검증(job 8281, year 0008): h0 1파일에 연별 8레코드 누적(mfilt=20 → 20년/파일). TOTECOSYSC 1224 · TOTSOMC 279 · TOTVEGC 621 · TLAI 1.32 gC/m². **값이 낮은 건 정상** — AD가 풀을 키우는 중, 상승 궤적이 곧 수렴 신호.

### 7i. ★★ AD 완료 → post-AD 전환 (2026-08-24)

**AD 완료**: 2026-08-23 17:16, **year 0211**(목표 202를 10년 chunk가 넘어섬).
최종 restart `clm5_bgc_ad.clm2.r.0211-01-01-00000.nc` (1.4 GB).

**전환 절차 실행** — §7g에 적어둔 그대로. 새 케이스 `clm5_bgc_pad`(clone, AD 케이스 보존):

```
CLM_ACCELERATED_SPINUP=off · CLM_FORCE_COLDSTART=off
CONTINUE_RUN=FALSE · RUN_STARTDATE=0001-01-01
user_nl_clm: finidat = '.../clm5_bgc_ad.clm2.r.0211-01-01-00000.nc'
```

- **★ finidat 함정을 실제로 확인**: 전환 전 `lnd_in`의 기본값이
  `clmi.I2000Clm50BgcCrop.2011-01-01.**1.9x2.5**_gx1v7_...nc` — 격자(우리 0.9×1.25)도
  구성(우리 Bgc)도 불일치. `CONTINUE_RUN=FALSE`라 이 값이 **실제로 읽히므로** 반드시 덮어써야 한다.
  `preview_namelists`로 `spinup_state=0` + finidat 교체를 제출 전에 검증했다.
- **재빌드 불필요**: `CLM_ACCELERATED_SPINUP`은 런타임 namelist 스위치(`spinup_state`)라
  AD의 exe를 그대로 쓴다. `EXEROOT`를 AD bld로 돌리고 `BUILD_COMPLETE=TRUE`.
- **create_clone 경로**: `~/CESM/cases/`에 없고 `~/CESM/cime/scripts/create_clone`.
- 스크립트 신규: `clm5_bgc_pad_chunk.pbs`(첫 chunk만 `FIRST=1`로 `CONTINUE_RUN=FALSE`,
  이후 자동 TRUE) · `clm5_bgc_pad_chain.sh`(목표 100년, 연도 미진행 시 중단).
- **실측 1.79 h/model-year** (AD 2.1보다 빠름 — 가속분해 계산이 빠짐).

### 7j. ★★ post-AD 수렴 판정 — 40년 시점 미수렴, 전지구 평균은 이미 기준 안 (2026-08-27)

판정 도구 `cesm/scripts/clm5_postad_convergence.py`. 기준 = **TOTECOSYSC 표류 ≤ 1 gC/m²/yr가
97 % 격자**(§7b). 표류는 마지막 N년 연평균의 최소제곱 기울기(첫해–마지막해 차이는 두 해에 좌우됨).

**year 1–40, 마지막 20년 창**:

| 변수 | 평균 | 전지구 표류 | 기준 통과 격자 |
|---|---|---|---|
| **TOTECOSYSC** | 21,442 | **−0.50** gC/m²/yr | **51.8 %** |
| TOTSOMC | 15,858 | +0.29 | 65.9 % |
| TOTVEGC | 4,171 | −0.09 | 52.7 % |
| TLAI | 1.78 | ~0 | — |
| TWS | 7,289 | +0.69 | — |

- **★ 전지구 평균 표류(−0.50)는 이미 기준 안에 있는데 격자별로는 절반이 미달이다.**
  격자들이 서로 반대 방향으로 움직여 평균에서 상쇄되기 때문. **평균만 봤으면 "수렴"으로
  오판했을 것** — CLM5-BGC 기준이 평균이 아니라 "97 % 격자"로 정의된 이유가 이것이다.
- 평균은 면적·육지분율 가중, 97 % 판정은 무가중(기준이 격자 단위 정의).
- **전망**: 40년에 51.8 %면 100년에도 97 %는 어려울 수 있다. 가이드도 고위도 토양탄소는
  1000년+ 걸릴 수 있고 완화가 허용된다고 명시(§7b). 100년 시점 값을 보고 미달이면
  **완화 기준 채택 + 근거 박제**가 현실적.
- **CLM5는 이미 offline이다**(COMPSET `2000_DATM%GSWP3v1_CLM50%BGC_...`, COMP_ATM=datm,
  ocn/ice는 stub). post-AD 다음은 추가 스핀업이 아니라 **1979–2024 생산 적분**이며,
  이는 아직 착수하지 않았다.

### 7k. ★★★ post-AD가 줄곧 climate02에서 돌고 있었다 — PBS 할당과 mpirun 목적지가 달랐다 (2026-09-10)

PBS는 `host=climate01`을 예약해 놓았는데 **실제 48 rank는 climate02에 떨어지고 있었다.**
climate01은 load 0.00으로 놀고, climate02는 타 사용자 load 53–88 위에 우리 잡이 겹쳐 올라갔다.

```
PBS 할당     climate01/0*48
mpi.hosts    climate02:48          <-- 실제 목적지
실제 rank    climate00 0 / climate01 0 / climate02 48
```

- 원인: `cases/clm5_bgc_pad/env_mach_specific.xml:44` 가
  `-hostfile /home/ydkoh/CESM/cases/clm5_bgc_ad/mpi.hosts` 를 **하드코딩**.
  그 파일 내용이 `climate02:48`(2026-08-22 AD 케이스 만들 때 박힘).
- **불일치가 생긴 시점**: 타 사용자 LIS가 climate02를 PBS 밖에서 점유하는 문제 때문에
  `clm5_bgc_pad_chunk.pbs` 의 `host=` 를 climate02 → climate01로 바꿨는데,
  **mpirun hostfile은 같이 안 바꿨다.** 노드를 옮길 때는 **PBS `host=` 와 hostfile
  두 곳을 같이** 고쳐야 한다 — 한 쪽만 고치면 조용히 갈라진다.
- 기본값 `~/.cime/config_machines.xml` → `/home/ydkoh/mvapich2.hosts` = `climate01:48`.
  **나머지 21개 케이스는 전부 기본값을 쓴다**. AD·post-AD 두 케이스만 예외였다.
- **증상은 성능으로만 드러났다**: 타 사용자 부하가 커지자 연별 소요가
  1h43m → 3h46m → 4h05m (**2.4배**). 크래시도 경고도 없다.
- **예전 "1.79 h/model-year" 벤치마크(§7i)도 climate02가 한가할 때 잰 값**이었다.
  climate01 실측은 **1.70–1.83 h/model-year**로 사실상 같다 — 노드 성능 차이가 아니라
  **경합 여부**가 변수였다.
- 조치: `mpi.hosts` → `climate01:48` (백업 `mpi.hosts.bak_climate02`). 수정 후 48 rank
  climate01 확인.
- **교훈**: `qstat -n`의 할당 노드를 믿지 말고 **`pgrep -u <user> -c cesm.exe`를 노드마다
  돌려 rank가 실제로 어디 있는지 확인**할 것. 두 정보가 다를 수 있다.
  [[climate01-only-for-jobs]]

### 7l. ★★ AD→post-AD 전환 때 탄소풀 역환산이 실제로 됐는지 숫자로 확인 (2026-09-11)

AD는 분해를 가속해 풀을 작게 유지하므로, 빠져나올 때 가속계수를 되돌리지 않으면
**탄소 고갈 상태에서 post-AD를 시작**하고 스핀업 전체가 헛일이 된다. 로그 메시지는
restart 경로에서 찍히므로 **산술이 실제로 먹었다는 증거가 아니다.** 도구
`cesm/scripts/verify_ad_exit_rescaling.py` (면적·육지분율 가중).

```
spinup_state = 0                      (namelist)
restart_file_spinup_state = 2         (AD restart에 박힌 값)
Multiplying stemc and crootc by 10 for exit spinup
CNRest: taking c12 SOM pools out of AD spinup mode
```

| 변수 | AD 마지막(0201) | post-AD 첫해(0001) | 배율 |
|---|---|---|---|
| **TOTSOMC** | 397 gC/m² | 15,834 | **×39.8** |
| **TOTECOSYSC** | 1,855 | 21,439 | **×11.6** |
| TOTVEGC | 905 | 4,164 | ×4.6 |

- TOTVEGC ×4.6은 **죽은목재(×10)가 TOTVEGC에 포함**되고 살아있는 풀은 AD가 안 건드리기
  때문. 1.0이면 역환산 실패 신호다.
- 절대값 검증: post-AD 첫해 토양탄소 **2,366 PgC** — 관측 추정 1,500–2,400 PgC와 같은 자리수.
- 로직 위치: `SoilBiogeochemCarbonStateType.F90:685-694` (`flag=='read'` 이고
  namelist와 restart의 spinup_state가 다를 때 분기).

### 7m. ★★ 쉘 청크 체인 ≡ 연속 적분인지 검증 — 청크 경계에 흔적 없음 (2026-09-11)

공식 CLM 레시피는 `RESUBMIT`으로 체인하는데 여기선 `BATCH_SYSTEM=none`이라 **쉘로 10년씩
끊어서** `CONTINUE_RUN=TRUE`로 이어붙인다. 같아야 하지만 **"같아야 한다"는 증거가 아니다** —
청크 경계가 깨져도 크래시하지 않고 조용히 시계열에 단차만 남긴다.

검증 도구 `cesm/scripts/verify_chunk_continuity.py`. 두 종류 경계를 **반드시 구분**해야 한다:

- **청크 경계** 0093·0102·0112 — 쉘이 멈추고 재제출한 해. 여기 단차 = 체인 고장.
- **강제장 되감기** 0091·0121 — GSWP3 cycling이 2010 넘어 1981로 돌아가는 해.
  여기 단차는 예상된 것이고 우리 탓이 아니다. [[lsm-cyclic-forcing-wrap-shock]]

검정량은 **TWS**(연내 반응할 만큼 빠르고, 날씨 잡음만은 아닐 만큼 깊게 적분된 양).
판정은 "그 해 점프가 주변 해들의 점프 산포에 비해 튀는가".

```
배경 연간 점프: 평균 +0.411, sd 3.923 mm (n=28, 경계 제외)

청크 0093:  -3.061 mm = 0.8 sd  -> 평범한 해와 구별 안 됨
청크 0102:  -6.761 mm = 1.7 sd  -> 평범한 해와 구별 안 됨
되감기 0091: +5.771 mm = 1.5 sd  (예상)
```

- **기록 전체 최대 점프는 0103년 +9.3 mm (2.4 sd)로, 경계가 아닌 해**에서 나왔다.
  즉 청크 경계는 배경 변동 안에 완전히 묻힌다 → **쉘 체인은 연속 적분과 동등**.
- 강제장 정렬도 성립: `YR_START=1981, YR_END=2010, YR_ALIGN=1981`에서 모델연도 1 → 1981
  (1980이 30으로 나누어떨어져 `ALIGN=1`과 동일하게 동작).
- 공식 예시와의 **의도적 차이 2건**(둘 다 무해):
  `RESUBMIT` → 외부 쉘 체인(BATCH_SYSTEM=none 때문, 위에서 동등성 검증),
  `RUN_TYPE=hybrid` → `startup` + `finidat`(I compset에서는 효과 동일).

### 7n. post-AD 111년 시점 수렴 — 여전히 미수렴, 목표를 200년으로 (2026-09-11)

| 변수 | 평균 | 전지구 표류 | 기준 통과 격자 | 40년 시점(§7j) |
|---|---|---|---|---|
| **TOTECOSYSC** | 21,456 | +0.77 gC/m²/yr | **53.0 %** | 51.8 % |
| TOTSOMC | 15,886 | +0.50 | 64.9 % | 65.9 % |
| TOTVEGC | 4,177 | +0.30 | 54.1 % | 52.7 % |
| TLAI | 1.79 | +0.0007 | — | — |
| TWS | 7,323 | +0.53 | — | — |

- **40년 → 111년에 51.8 % → 53.0 %.** 71년을 더 돌려 1.2 %p. §7j의 전망("100년에도
  97 %는 어려울 수 있다")이 그대로 맞았다.
- 전지구 평균 표류는 평균의 **연 0.0036 %**로 이미 무시할 수준 — §7j와 같은 함정이
  111년에도 유지된다.
- 체인 목표를 **200년**으로 재설정(`clm5_bgc_pad_chain.sh 200`). 2026-09-11 기준 0116년,
  climate01에서 1.83 h/yr → 남은 84년 ≈ **154 h (6.4일)**.
- 200년에도 97 % 미달이면 §7j가 예고한 **완화 기준 채택 + 근거 박제** 경로로 간다.
  판정에 쓸 값은 이미 다 모여 있다.

### 7o. ★★ post-AD 200년 완주 + 수렴 판정 — 여전히 97 % 미달, 완화 기준 경로 확정 (2026-09-17)

체인 종료: `chain.log` "post-AD complete at year 0202" (2026-09-17 17:32, chunk 10 = job 8454).
restart 0202-01-01 = **201 model-year 완주**, raw 201개 `~/CESM/spinup_raw/clm5_BGC_PAD`.
판정 = 같은 도구 `clm5_postad_convergence.py 20` (마지막 20년 창, 40년·111년과 동일 방법).

| 변수 | 평균 | 전지구 표류 | 기준 통과 격자 | 111년(§7n) | 40년(§7j) |
|---|---|---|---|---|---|
| **TOTECOSYSC** | 21,484 | +0.80 gC/m²/yr | **53.4 %** | 53.0 % | 51.8 % |
| TOTSOMC | 15,912 | +0.43 | 66.4 % | 64.9 % | 65.9 % |
| TOTVEGC | 4,184 | +0.21 | 54.5 % | 54.1 % | 52.7 % |
| TLAI | 1.79 | +0.0007 | — | — | — |
| TWS | 7,347 | +0.41 | — | — | — |

- **40 → 111 → 201년: 51.8 → 53.0 → 53.4 %.** 90년을 더 돌려 0.4 %p. 97 %는 이 속도로
  도달 불가(수천 년 규모) — 가이드가 말한 고위도 토양탄소 1000년+ 케이스.
- 전지구 평균 표류는 +0.80 gC/m²/yr = 평균의 연 0.0037 % → 이미 기준 안(§7j 함정 그대로).
- **결정: 추가 spin-up 중단, §7j 예고대로 완화 기준 채택.** 근거 정량(어느 threshold에서
  97 %가 되는지, 미달 격자의 위도·토양탄소 분포)은 다음 단계에서 박제.
- post-AD 최종 IC = `clm5_bgc_pad.clm2.r.0202-01-01-00000.nc`. 다음 = WFDE5 forcing
  I compset 생산 적분(LM4p WFDE5 실험과 동일 forcing).

### 7p. ★★ 생산런 착수 — `clm5_prod_1979_2023`, WFDE5 1979–2023, post-AD 0202 IC (2026-09-17)

- 케이스 생성·빌드 `run_scripts/CLM5_prod_1979_2023.csh`(climate00, ~10분). finidat =
  `clm5_bgc_pad.clm2.r.0202-01-01-00000.nc`. `RUN_STARTDATE=1979-01-01`, DATM 1979–2023 align 1979.
- **★ 스트림 파일 함정**: post-AD의 `user_datm.streams.txt.*`는 **1981–2010 30개 파일만** 나열
  (cycling용). 가이드 §7.3 "복사해서 그대로"로는 1979·2011+ forcing이 없어 죽는다. 스크립트가
  복사 후 연도 목록만 awk로 1979–2023으로 재작성(도메인·변수 매핑은 그대로). 결과 검사 줄
  ("forcing years in the streams")을 로그에서 반드시 확인 — 이번엔 `mv -i` alias 탓에 재작성이
  무시된 걸 이 줄이 잡았다([[climate-cshrc-interactive-aliases]]). 최종: 3스트림 모두 45년,
  CaseDocs 반영 확인.
- hostfile: 케이스별 `mpi.hosts`를 chunk.pbs가 `$PBS_NODEFILE`에서 생성(§7k 재발 방지).
- 실행: `run_scripts/run_F96_then_prod.sh`(nohup @climate00) → ① F2000climo f09 **96PE 2노드
  타이밍 1년**(`F_f09_96pe_cam6clm5.csh` + `F_2000climo_f09_96pe.pbs`) 완료 후 ② `clm5_prod_chain.sh 2023`
  (5년 청크 × 9, climate01, 1.8 h/yr → ≈81 h). 로그 `~/run_F96_then_prod.out`, `cases/clm5_prod_1979_2023/chain.log`.
- raw 보존 `~/CESM/spinup_raw/clm5_PROD/`(청크마다 rsync, --delete 없음).
- 설계 메모: LM4p WFDE5 ctl(1979–2023)과 forcing·기간 일치. CLM5 쪽은 `2000_` compset =
  토지이용 2000년 고정·crop 없음 — LM4p(LUH2 transient)와 비교할 때 land-use는 자유변수.

### 7q. 생산런 체인 가동 확인 + F 96PE 결과 (2026-09-18)

- F2000climo f09 96PE(2노드) 1년: **10.95 h/yr**, 1052 pe-hr/yr, 2.19 yr/day. 48PE(18.6 h/yr) 대비 1.70×, 효율 85 %.
  **2노드 MPI 작동 확인**(rank 48+48, CLAUDE.md "96PE 불가"는 미검증이었음 → 정정). 생산런은 여전히 climate01 단독.
- 생산 체인 chunk 1(1979–1983, job 8456) 07:04 시작 → 11:42 시점 1980-11 (≈2.4 h/yr, 초기화 포함). 5년 청크 ≈ 11 h,
  45년 ≈ 4일 예상. 로그 `cases/clm5_prod_1979_2023/chain.log`.
