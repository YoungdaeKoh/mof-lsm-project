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

## 다음 (TODO)
1. lon −180~180 → 0~360 정렬
2. LSM별 포맷 변환 (CLM5 clmforc 우선)
