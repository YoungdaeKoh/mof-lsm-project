# 데이터 다운로드 & ERA5 forcing 현황

> 마지막 갱신: **2026-06-22** (Claude Code)
> 모든 다운로드·변환은 백그라운드(nohup) — 맥미니 꺼도 서버/ubuntu는 계속 돔.

---

## 1. ERA5 → CLM forcing (★ monthly 전환으로 datm 버그 해결)

- **문제였던 것**: yearly 1파일/년(`{year}_era5.nc`)은 datm이 multi-year로 이을 때 1980+ 시간 매핑이 깨짐 (1979만 정상). forcing 값·time은 정상인데 CLM이 받은 FSDS가 계절 뒤집히고 ~106 상수.
- **해결**: GSWP3식 **monthly + 표준 파일명**으로 변환. 1980 검증 RMSE 108→**13.75**(FSDS), TBOT 0.04, PRECT 0.0007. 상세는 메모리 `mof-era5-forcing-pipeline`.
- **코드**: `analysis/era5_to_clm5_monthly.ncl` (출력만 monthly 3그룹)
- **출력**: `/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM/monthly/{Solar,Precip,TPHWL}/clmforc.ERA5.0.5x0.5.{Solr,Prec,TPQWL}.YYYY-MM.nc`
- **현재**: **1979~2025 전체 변환 백그라운드 실행 중** (서버, ~2-4시간). 로그 `/data2/ydkoh/monthly_all.log`
- 검증 그림: `figures/forcing_{FSDS,TBOT,PRECT}_1980_monthly_fix.png`
- 확인:
  ```
  ssh climate "tail -3 /data2/ydkoh/monthly_all.log; ls /data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM/monthly/Solar/ | wc -l"
  ```

## 2. GSWP3 0.5° datm forcing — 3대 분담 (1901–2014, 변수당 1368)

| 머신 | 담당 | 저장 위치 | 소스 |
|---|---|---|---|
| **서버** climate | Precip | `/data1/CESM2_INPUT/atm/datm7/...GSWP3.../Precip` | UCAR https |
| **ubuntu** | Solar | `/mnt/data2/GSWP3_ERA5testbed/Solar` | UCAR https |
| **mac** mini | TPHWL | `/Volumes/data02/GSWP3_ERA5testbed/TPHWL` | UCAR https |

- UCAR 속도: ubuntu 실측 5.1 MB/s (서버 단독 1.4 MB/s보다 빠름) → 3대 병렬이 훨씬 빠름
- 다 받으면 ubuntu·mac → 서버 `/data1`로 rsync 통합
- 확인:
  ```
  ssh climate "ls /data1/CESM2_INPUT/atm/datm7/*GSWP3*/Precip/*.nc | wc -l"
  ssh ubuntu "tail -2 /mnt/data2/gswp3_solar.log"
  tail -2 /Volumes/data02/gswp3_tphwl.log
  ```

## 3. CMFD daily (v2.0) — 서버 + 로컬 분담 (8변수×74년=592)

| 위치 | 받은 것 (대략) | 스크립트 |
|---|---|---|
| **서버** `/data2/ydkoh/CMFD_daily` | lrad~69, prec14, temp46 | `download_cmfd_daily_resume.sh` (전체 -c) |
| **로컬** `/Volumes/data02/CMFD/daily` | prec14, wind~26 | `dl_cmfd_local.sh wind srad shum` |

- TPDC FTP 느림·자주 끊김 → resume 루프. monthly(1951–2024)는 로컬에 완비
- 확인: `ssh climate "ls /data2/ydkoh/CMFD_daily/*.nc | sed 's#.*/##;s/_CMFD.*//' | sort | uniq -c"`

## 4. Sheffield(PGF)·ISIMIP3b — 미시작 (testbed forcing 후보)
- PGF: soton 아카이브, 1948–2016. 미래는 ISIMIP3b(SSP). 필요 시 받기.

---

## 다음 액션
1. ERA5 monthly 변환(1979–2025) 완료 → stream/케이스 전체기간 → CLM spinup 재실행
2. GSWP3 3대 완료 → 서버 통합 rsync
3. CMFD 완료 → 서버/로컬 한 곳 통합
4. (미해결) cdo monmean이 FLDS만 1 step으로 깨짐 — input FLDS 검증 그림 필요 시 NCL/python으로
