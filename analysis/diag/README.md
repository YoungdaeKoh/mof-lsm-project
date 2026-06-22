# CLM5 진단 분석 (diag) — ERA5-Land 비교 & forcing 검증

해수부 1.7 1차년도: CLM5 offline(ERA5 forcing) 출력을 ERA5-Land와 비교하고
forcing이 CLM에 제대로 전달됐는지 검증하는 분석 코드 모음.

## 데이터 위치 (로컬, data02 마운트 끊겨 data01에 보관)
| 데이터 | 경로 | 내용 |
|---|---|---|
| CLM 출력(lnd) | `cesm/clm_output/I2000_ERA5_spinup/lnd/hist/*.clm2.h0.*` | 월별 H2OSOI/TSOI/TSA/TBOT/FSDS/FLDS/RAIN/SNOW (f19, 모델 0001~ = 1979~) |
| CLM 출력(rof) | `cesm/clm_output/.../rof/hist/*.mosart.h0.*` | MOSART runoff/discharge (TOTAL_DISCHARGE_TO_OCEAN_LIQ 등) |
| ERA5-Land regrid | `data/era5land/era5land_swvl_clmgrid_YYYY.nc` | swvl1-4, CLM격자(f19)로 regrid, 1979-1987 |
| 그림 | `figures/*.png` | 결과 PNG |

서버 원본: CLM `climate:/data2/ydkoh/cesm2_output/archive/I2000_ERA5_spinup/`,
ERA5-Land 0.1° `climate:/data1/ERA5/land_level/monthly_0.1/`.

## 스크립트
| 파일 | 역할 | 입력 → 출력 |
|---|---|---|
| `regrid_era5land_swvl.ncl` | ERA5-Land swvl1-4 (0.1°) → CLM격자 regrid (area_hi2lores, missing 처리). **서버서 실행** | ERA5-Land → `era5land_swvl_clmgrid_YYYY.nc` |
| `compare_soilmoist.py` | 토양수분 층별 비교 (CLM H2OSOI 깊이가중 vs ERA5-Land 4층). 절대 + 아노말리 | → `soilmoist_seasonal_layered.png`, `soilmoist_seasonal_anomaly.png` |
| `check_forcing_temp.py` | forcing 검증: CLM TSA(2m) vs TBOT(받은 forcing) 계절순환 | → `forcing_temp_check.png` |
| `temp_timeseries_region.py` | 온도 108개월 시계열 + 동아시아 영역 | → `temp_timeseries_108mon.png`, `temp_seasonal_eastasia.png` |
| `forcing_4panel.py` | forcing 4구동력(기온·강수·단파·장파) CLM 전달 검증 | → `forcing_4panel_received.png` |
| `mosart_ocean_discharge.py` | 해양 유입 총담수 (MOSART TOTAL_DISCHARGE_TO_OCEAN) → km³/yr, 관측 ~40k 비교 | → `mosart_ocean_discharge.png` |
| `forcing_flowchart.py` | ERA5→CLM forcing 생성 파이프라인 도식 | → `forcing_flowchart.png` |

## 실행 (로컬)
```bash
/opt/homebrew/bin/python3 <script>.py
```
주의: CLM 시각이 모델 연도 0001~ (pandas 범위 밖) → `use_cftime=True, decode_timedelta=False` 필수.

## 핵심 발견 (1차 진단)
- **온도**: TSA가 TBOT를 −1.3°C offset으로 정확 추종 → **forcing 정상 구동 ✅**
- **토양수분**: CLM(~0.10) ≪ ERA5-Land(~0.27) m³/m³, 계절진폭도 CLM이 5-13%뿐
  → 절대값은 porosity 정의차(아노말리로 비교), 진폭약함은 spin-up 미완/모델 damping (구조오차 진단)
- **담수**: MOSART discharge ~100k km³/yr (관측 40k의 2.5배) → spin-up 전이 추정, 평형 후 재확인
- **층 매칭**: ERA5-Land 4층(0-7/7-28/28-100/100-289cm) ↔ CLM levsoi idx (0-1/2-4/5-7/8-12)

## 다음
- 45년 spin-up 후 재진단 (진폭 살아나나, discharge 40k 수렴하나)
- 동아시아 지역·복사 검증 확대
- 향후 ILAMB 종합 벤치마킹 + 다중모델(JULES/Noah-MP/LM4)
