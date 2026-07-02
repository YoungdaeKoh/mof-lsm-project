# WFDE5 forcing 다운로드 & 전처리

다중 LSM(CLM5·LM4·LIS·JULES·Noah-MP) 공통 forcing으로 WFDE5 v3.0 사용.
ERA5를 CRU 관측으로 bias 보정한 0.5° hourly 지면 forcing → **0.5° native라 regrid 불필요**
(ERA5 직접 변환의 +12 W/m² SW regrid bias 원천 차단).

## CDS 다운로드 (★ 파라미터)
- dataset: `derived-near-surface-meteorological-variables`
- **`product`: `"wfde5"`** (필수 — 누락 시 400)
- **`version`: `"3_0"`** (점 아니라 언더스코어! "2.1"은 400)
- `reference_dataset`: `"cru"` (전체 1979–2024) / `cru_and_gpcc`(2016까지, precip 정밀)
- `variable` 8개: surface_downwelling_shortwave_radiation, surface_downwelling_longwave_radiation,
  near_surface_air_temperature, near_surface_specific_humidity, surface_air_pressure,
  near_surface_wind_speed, rainfall_flux, snowfall_flux
- 월별 hourly nc, 0.5°, lon **−180~180** (CLM/GSWP3는 0~360 → 변환 시 정렬 필요)
- valid values 조회: `ecmwf.datastores.Client(url,key).get_collection(ds).form`

## 3대 분담 다운로드
- 서버 climate(anaconda py3.11): SWdown·LWdown — `dl_wfde5_download.py`
- ubuntu: Qair·PSurf(전반) — `dl_wfde5_ub3.py`  ⚠️ `loginctl enable-linger` 필수 ([[ubuntu-systemd-linger]])
- mac: rainfall·snowfall·Tair·Wind·PSurf(후반) — `dl_wfde5_mac_psurf.py` 등
- ⚠️ 서버 system python은 3.6(cdsapi 안 됨) → **anaconda python 사용**
- 통합: 전부 `climate:/data2/ydkoh/WFDE5/` (368 zip, 584 GB). 백업: mac `/Volumes/data02/WFDE5/`

## 6h 평균 전처리
- `wfde5_6h_parallel.sh`: zip 해제 → `cdo timselmean,6` (8병렬) → `/data2/ydkoh/WFDE5_6h/{var}/`
- **모든 변수 6h 평균** (강수 Rainf도 `kg m⁻² s⁻¹` **flux**라 평균이 맞음 — 누적 아님)
- nc는 float(packed 아님)이라 cdo OK

## CLM5 변환 (★ NCL, 검증된 ERA5 파이프라인 보존)
- `analysis/wfde5_to_clm5.ncl`: 서버 `1_CLM/era5_to_clm5.ncl`(연도별 단일파일 버전)의
  WFDE5 판. **연도별 1파일** `YYYY_wfde5.nc`에 7변수(TBOT/QBOT/PSRF/FSDS/FLDS/PRECTmms/WIND)
  + LONGXY/LATIXY/EDGE + noleap time 통합. 출력 `/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5/`
- 매핑: Tair→TBOT, Qair→QBOT, PSurf→**PSRF**, SWdown→FSDS, LWdown→FLDS, Wind→WIND
- `PRECTmms = Rainf + Snowf` (둘 다 kg m⁻² s⁻¹ = mm/s), 단위환산 불필요(이미 LSM-ready)
- lon −180~180 → `lonFlip` → 0~360 (GSWP3 셀과 셀단위 일치)
- **⚠️ area_conserve_remap 쓰면 안 됨**: WFDE5는 land-only(ocean=1e20 fill)라 remap이
  fill을 섞어 전 격자를 망침(ERA5는 전구 완전자료라 OK였음) → grid 일치하니 **remap 생략, 직접 대입**
- noleap: WFDE5는 proleptic_gregorian(2/29 존재) → `drop_feb29`로 제거 (연 1460 step)
- `_FillValue=1.e20` (ERA5는 1.e36; WFDE5 ocean missing 보존)
- **실행**: `setenv NCARG_ROOT /usr/local/ncl_ncarg/6.6.2_gcc485` 필수(비대화형 ssh),
  `$NCARG_ROOT/bin/ncl wfde5_to_clm5.ncl`
- **1980 1년치 검증 완료**: TBOT 197.9–321.3K, FSDS 0–1093, WIND 0.06–37.7, valid 35.8%(land) ✓
- (폐기: python 버전·monthly ncl 버전 — CLM5 datm 필수요소 누락으로 삭제)

## 6h 전처리 완료 상태
- 8변수 × 552(46년×12월) = **4416 완료**. 단 PSurf 1993은 소스 zip 손상(648MB) →
  CDS 재다운로드(1811MB) → 6h 재변환 완료

## 다음 (TODO)
1. `wfde5_to_clm5.ncl` 전체 실행 (1979–2024, 연 ~10.6GB × 46 ≈ 490GB, /data2 여유 확인)
2. datm stream 설정 → CLM5 offline 런
3. 다른 LSM 포맷 변환 (LM4·JULES·Noah-MP)
