# WFDE5 forcing — HTML 정리본 초안 (수집·구조화)

_2026-07-31. 출처: `cesm/wfde5/README.md`, `lm4/LM4_SPINUP_NOTES.md`, `cesm/CLM5_SPINUP_NOTES.md`,
`jules/JULES_PORTING_NOTES.md`, memory `mof-wfde5-forcing` · `lsm-wfde5-cold-instability-debug`.
ERA5판 정리본(`2026/작업요약_ERA5_CLM_forcing.html`)의 후속 = 이 문서가 그걸 대체함._

---

## 1. 왜 WFDE5인가 (배경·결정)

- 다중 LSM(**CLM5 · LM4+ · Noah-MP · JULES · LIS**) **공통 forcing**으로 채택.
- 정체: ERA5를 **CRU 관측으로 bias 보정**한 0.5° hourly 지면 forcing (v3.0, 1979–2024).
- **결정적 이유**: ERA5 직접 변환 파이프라인에서 `area_conserve_remap_Wrap` regrid로
  **+12 W/m² SW bias**가 생겼는데, WFDE5는 **0.5° native**라 regrid 자체가 불필요 → 원천 차단.
- 모델 간 비교가 과제 핵심이므로 **모든 LSM이 같은 원자료**를 먹는 것이 설계 요구사항.

## 2. 자료 사양

| 항목 | 값 |
|---|---|
| 버전 / 기간 | v3.0, 1979–2024 (46년) |
| 해상도 | 0.5° (360×720), **land-only** (유효격자 35.8 %) |
| 원본 시간 | hourly, 월별 파일 `Var_WFDE5_CRU_YYYYMM_v3.0.nc` |
| 좌표 | lon **−180~180** (CLM/GSWP3는 0–360 → 변환 시 flip) |
| 결측 | ocean = `1e20` fill (ERA5는 1e36) |
| 자료형 | float (packed 아님 → cdo 안전) |
| 용량 | 원본 368 zip = 8변수 × 46년, **584 GB** |
| 8변수 | SWdown · LWdown · Tair · Qair · PSurf · Wind · Rainf · Snowf |

## 3. 다운로드 (CDS 파라미터 — 400 에러 방지)

- dataset: `derived-near-surface-meteorological-variables`
- **`product = "wfde5"`** — 누락 시 400 "invalid combination"
- **`version = "3_0"`** — 언더스코어. `"3.0"`·`"2.1"`은 400
- `reference_dataset = "cru"` (1979–2024 전체) / `cru_and_gpcc` (2016까지, precip 정밀)
- valid values 조회: `ecmwf.datastores.Client(url, key).get_collection(ds).form`
- **3대 분담**: 서버(anaconda py3.11 — ★system py3.6은 cdsapi 불가) / ubuntu(`loginctl enable-linger` 필수) / mac
- 통합 위치 `climate:/data2/ydkoh/WFDE5/`, 백업 mac `/Volumes/data02/WFDE5/`
- ⚠️ **truncate 함정**: PSurf 1993 zip이 648 MB(정상 ~1810 MB)로 손상. `size > 1MB` skip guard로는 못 거름 → 재다운로드

## 4. 전처리 (6시간 평균)

- `cesm/wfde5/wfde5_6h_parallel.sh`: zip 해제 → `cdo timselmean,6` (8병렬) → `/data2/ydkoh/WFDE5_6h/{var}/`
- **모든 변수 평균이 맞음** — 강수 `Rainf`도 `kg m⁻² s⁻¹` = **flux**라 평균 (ERA5 `tp`는 누적이라 합산이었음)
- 완료 상태: 8변수 × 552개월 = **4416** ✓

## 5. 모델별 변환

### 5a. CLM5 / LM4 공통 중간포맷 (`analysis/wfde5_to_clm5.ncl`)

- 서버 `1_CLM/era5_to_clm5.ncl`(연도별 단일파일 버전)의 WFDE5 판
- 연 1파일 `YYYY_wfde5.nc`에 7변수 + `LONGXY/LATIXY/EDGE` + noleap time 통합
- 출력 `/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5/` — 연 10.6 GB × 46 ≈ 490 GB
- 매핑: Tair→TBOT · Qair→QBOT · **PSurf→PSRF**(PBOT 아님) · SWdown→FSDS · LWdown→FLDS · Wind→WIND
- `PRECTmms = Rainf + Snowf` (둘 다 mm/s, 단위환산 불필요 — 이미 LSM-ready)
- lon −180~180 → `lonFlip` → 0–360 (GSWP3 셀과 셀단위 일치)
- noleap: 원본 `proleptic_gregorian` → `drop_feb29` → **연 1460 step**
- **CLM5·LM4가 이 파일 하나를 공유** (둘 다 CDEPS DATM)

### 5b. LM4+ 전용 변환 (`lm4/scripts/lm4p_offline_wfde5_to_atm.py`)

- 위 CLM 포맷 → LM4 offline(FMS data_table) 대기 강제장으로
- 달력은 `v.calendar = tvar.calendar`로 **상속** → 모델도 NOLEAP (`:79`)

## 6. ★ 함정 모음 (이 문서의 핵심)

### 6a. `area_conserve_remap` 금지 — land-only fill 오염
WFDE5는 ocean = 1e20 fill이라 remap이 fill을 전 격자에 섞어 **결과가 전부 fill**이 됨.
ERA5는 전구 완전자료라 remap이 OK였던 것. WFDE5 grid == GSWP3 0.5°(lonFlip 후 셀 일치)이므로
**remap 생략, 직접 대입**이 정답.
⚠️ 서버 사본 `/data2/ydkoh/2026_MOF_LSM/wfde5_to_clm5.ncl`이 **옛 buggy 버전**(remap 씀).
**로컬 git `analysis/wfde5_to_clm5.ncl`이 검증본.**

### 6b. ★★ CDEPS DATM mesh — GSWP3 mesh 재사용 금지
GSWP3 ESMFmesh는 `elementMask`가 **전 격자 valid(100 %)** 인데 WFDE5는 valid 35.8 %.
이 mesh로 bilinear remap하면 **연안에서 fill(1e20)이 육지로 섞여** 모델 init read에서
**MPI_ABORT**(FP 트랩 없는 깨끗한 abort, UFS.F90 Initialize). `_FillValue` 있어도 mesh mask가
valid면 remap이 포함시킴.
**해결 = WFDE5 land-mask mesh**: GSWP3 mesh 복사 후 `elementMask`를 WFDE5 valid격자로 교체
(각 요소 `centerCoords`로 WFDE5 TBOT valid 직접조회 → flatten 순서 무관).
→ `/data2/ydkoh/2026_MOF_LSM/Atm_forc/wfde5_landmask_ESMFmesh.nc`.
지리검증(사하라 land · 중태평양 ocean · 아마존 land) 통과. **CLM5도 동일 mesh 필수.**

### 6c. 한랭 안정경계층 불안정 (GSWP3엔 없던 것)
WFDE5가 한랭 대륙점(몽골·티벳·시베리아)에서 지표를 불안정 임계로 몲 → `escomp` 크래시, t_ca NaN.
근본원인 = `&surface_flux_nml`의 **gustiness 하한 부재**(무풍·안정조건에서 난류교환→0,
지표-대기 decoupling → 복사냉각 런어웨이).
**FIX(namelist만)**: `alt_gustiness=.TRUE.` + `gust_const=3.0`.
→ **다른 LSM도 WFDE5로 갈아탈 때 같은 종류 주의.**

### 6d. 1년 테스트 통과 ≠ 다년 안전
gustiness fix 후 **연 전환(1982-01-01)에서 탄소보존 FATAL**(diff 6.6e-6 = roundoff).
GSWP3 1년 테스트는 run-end가 정확히 1982-01-01이라 그 체크를 **밟지 않았음**.
FIX: `carbon_cons_tol=1e-3`, `water_cons_tol=1e-3`.

### 6e. 03:00 앵커 — 시간축이 모델 달력을 지배
WFDE5 레코드가 **03/09/15/21 UTC**(6h 중점)라 세그먼트가 03:00에서만 시작 가능
(`current_date = Y,1,1,3,0,0` + `force_date_from_namelist=.true.`).
그 결과 **월평균 구간도 03:00에 앵커**되어, 세그먼트가 364d21h면 12월 구간이 3시간 모자라
**매년 11개월만 기록**되는 문제가 발생 → `days=365`로 수정해 해결(§13.31/13.36/13.38).

### 6f. partial-write
NCL이 파일 쓰는 중 읽으면 HDF error·0 K·변수누락으로 오판. **완성본만 검증.**
(`HDF5_USE_FILE_LOCKING=FALSE` 또는 완료 후 확인)

## 7. 모델별 적용 현황

| 모델 | 상태 |
|---|---|
| **LM4+** | WFDE5 land-mask mesh + gustiness fix로 구동. **1981–1996 완주, 1997 진행 중**(climate01 24 PE) |
| **CLM5** | `user_datm.streams.txt.CLMGSWP3v1.{Solar,Precip,TPQW}` 3개를 WFDE5로 교체, domain `domain.lnd.360x720_wfde5.nc`. **LM4와 동일 원자료** |
| **Noah-MP** | 현재 GSWP3 1° spin-up 완료 상태. WFDE5 전환 예정 |
| **JULES** | ERA5(WFDE5)로 spin-up 1회 추가 계획 |

## 8. 검증 현황

- ✅ CLM5 변환 1980 1년치: TBOT 197.9–321.3 K, FSDS 0–1093, WIND 0.06–37.7, valid 35.8 %(land)
- ✅ mesh 지리검증: 사하라 land · 중태평양 ocean · 아마존 land
- ✅ 46년 전체 변환 완료 (~4분/년, ~490 GB), lon 0.25–359.75로 GSWP3 일치
- ⬜ **미완: 모델이 실제로 받은 강제장 검증 맵** — `land_forcing` 스트림에 지면이 받은 값이
  그대로 기록되므로 WFDE5 원본과 격자별 비교 가능. **이 문서의 마지막 조각.**

## 9. 경로 요약

| 종류 | 경로 |
|---|---|
| 원본 zip | `climate:/data2/ydkoh/WFDE5/` (584 GB) · 백업 `mac:/Volumes/data02/WFDE5/` |
| 6h 평균 | `climate:/data2/ydkoh/WFDE5_6h/{var}/` |
| CLM 포맷(공통) | `climate:/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5/YYYY_wfde5.nc` |
| LM4 포맷 | `climate:/data2/ydkoh/lm4/forcing_WFDE5_lm4p/wfde5_atm_YYYY.nc` (연 3.8 GB) |
| land-mask mesh | `climate:/data2/ydkoh/2026_MOF_LSM/Atm_forc/wfde5_landmask_ESMFmesh.nc` |
| 변환 스크립트 | `analysis/wfde5_to_clm5.ncl` (★검증본) · `lm4/scripts/lm4p_offline_wfde5_to_atm.py` |
| 다운로드·전처리 | `cesm/wfde5/{dl_wfde5_*.py, wfde5_6h_parallel.sh}` |

## 10. 재현 체크리스트 (새 모델에 WFDE5 물릴 때)

1. 격자가 0.5°와 일치하는가 → 일치하면 **remap 금지, 직접 대입**
2. mesh/domain의 land mask가 **WFDE5 valid(35.8 %)** 를 반영하는가
3. 달력을 noleap으로 맞췄는가 (1460 step/년)
4. 시작시각이 **03:00**인가 (레코드 중점)
5. 무풍·한랭 조건에서 gustiness 하한이 있는가
6. **다년(≥2년)** 테스트로 연경계 체크를 밟았는가
