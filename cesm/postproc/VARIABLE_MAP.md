# Multi-LSM variable map (1979–2023 production runs)

Common diagnostic set for CLM5 / Noah-MP / LM4p. Native names differ; this table is
the single place the mapping is written down. Extraction scripts per model:

| model | script | output |
|---|---|---|
| CLM5 | `cesm/postproc/clm5_mon2year_extrac.ncl` | `/data2/ydkoh/cesm2_output/postproc/clm5_prod/clm5_prod.YYYY.nc` |
| Noah-MP | `noahmp/postproc/ldasout_6h_to_daymon.py` + `pp_years.sh` | `~/HRLDAS/forcing_WFDE5_1deg/prod_1979_2023/postproc/noahmp_prod_{mon,day}_YYYYMM.nc` |
| LM4p | `lm4/scripts/` (C96 → 1° lat-lon regrid) | `/data2/ydkoh/lm4/.../latlon/` |

Grid convention: diagnostics are compared on **1° lat-lon**; only LM4p is regridded
(C96 → 1°, conservative). Absolute/global means are computed on each model's native
grid — see memory `grid-compare-on-model-grid`.

## Energy

| quantity | CLM5 | Noah-MP | LM4p | note |
|---|---|---|---|---|
| latent heat | `EFLX_LH_TOT` | `LH` | `levapg+levaps+levapv` (or `hevap`) | W/m² |
| sensible heat | `FSH` | `HFX` | `sens` / `shflx` | W/m² |
| ground heat flux | `FGR` | `GRDFLX` | `grnd_flux` | W/m² |
| absorbed shortwave | `FSA` | `FSA` | `swdn_dir+swdn_dif − swup_dir−swup_dif` | W/m² |
| net longwave | `FIRA` | `FIRA` | `lwdn − flw` | CLM/Noah are up−down |
| incoming SW / LW | `FSDS` / `FLDS` | `SWFORC` / `LWFORC` | `swdn_*` / `lwdn` | forcing check |

## Temperature

| quantity | CLM5 | Noah-MP | LM4p |
|---|---|---|---|
| 2 m air temperature | `TSA` | `T2MV`/`T2MB` (tiled) | `t_ref` |
| ground / skin | `TG`, `TSKIN` | `TG`, `TRAD` | `Tgrnd`, `Trad` |
| canopy | `TV` | `TV` | `vegn_T` |
| soil temperature | `TSOI` (levgrnd 25) | `SOIL_T` (4) | `soil_T` |
| top-10 cm soil T | `TSOI_10CM` | — (derive from `SOIL_T`) | — |

## Water

| quantity | CLM5 | Noah-MP | LM4p | note |
|---|---|---|---|---|
| total evapotranspiration | `QFLX_EVAP_TOT` | `ECAN+ETRAN+EDIR` | `evap_land` | mm/s vs mm |
| soil evaporation | `QSOIL` | `EDIR` | `evap_soil` | |
| canopy evap / transpiration | `QVEGE` / `QVEGT` | `ECAN` / `ETRAN` | `levapv` / `transp` | |
| total runoff | `QRUNOFF` | `UGDRNOFF+SFCRNOFF` (accumulated!) | `runf` (`frunf` liquid) | **Noah accumulates**; see memory `lsm-runoff-definition-mismatch` |
| surface / drainage runoff | `QOVER` / `QDRAI` | `SFCRNOFF` / `UGDRNOFF` | `frunf` / — | |
| soil moisture (profile) | `H2OSOI` | `SOIL_M` | `soil_liq`(+`soil_ice`) | volumetric vs mass |
| top-10 cm soil water | `SOILWATER_10CM` | derive | derive | |
| SWE | `H2OSNO` | `SNEQV` | `snow` | **ice sheets dominate** — mask IGBP 15 / LM4 glacier |
| snow depth | `SNOW_DEPTH` | `SNOWH` | — | |
| snow cover fraction | `FSNO` | `FSNO` | `snow_frac` | |
| water table depth | `ZWT` | `ZWT` | — | |
| rain / snowfall | `RAIN` / `SNOW` | `RAINRATE` / `ACSNOW` | `precip` / `fprec_l` | |

## Vegetation / carbon

| quantity | CLM5 | Noah-MP | LM4p | note |
|---|---|---|---|---|
| LAI | `TLAI` (total), `ELAI` (exposed) | `LAI` | `lai` | LM4 has a second CMIP stream, see memory `lm4-lai-native-vs-cmip` |
| GPP / NPP | `GPP` / `NPP` | `GPP` / `NPP` | `gpp` / `npp` | |
| NEE / NEP | `NEE` | `NEE` | `nep` (sign flips) | |
| vegetation carbon | `TOTVEGC` | `LFMASS+STMASS+RTMASS+WOOD` | `btot` (`bwood`,`bl`,`br`) | |
| soil carbon | `TOTSOMC` | `STBLCP+FASTCP` | `tot_soil_C` (`fsc`,`ssc`) | |

## Traps already paid for

- CLM5 h0 stamps a monthly mean at the **end** of its period → the extraction script
  shifts `time` by −15 days. Without it every month is off by one.
- Noah-MP runoff/snow variables are **accumulated since model start**, and the
  accumulators are inherited from the spin-up restart (~1e6 mm) → float32 quantises
  6-h increments; monthly means are exact, daily values are noisy in high-runoff cells.
- Noah-MP fill values are **two**: ocean −1e33 and N/A tile −9999 → mask `< -9998`.
- Land means must exclude ice (`IVGTYP` 15 in Noah-MP) and be cos(lat)-weighted;
  see memory `lsm-spinup-ice-mask-convergence`, `lsm-landmean-comparability`.
