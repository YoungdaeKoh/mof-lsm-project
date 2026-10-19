# LM4p boreal phenology paper (2026)

Title (2026-10-19, user): **Reducing the delayed phenology of boreal vegetation in the LM4.1 land model**
Model naming in the paper: LM4.1 (Shevliakova et al. 2024, JAMES) in title/abstract; "LM4p" (our offline
PPA build from KIOST-ESM2, ESM4.5 code) defined once in Methods, then used for run names.
Verb "Reducing": autumn bias mostly removed, spring bias partly; revisit after the 15-yr run.

## Experiments (names used in figures)
| name | run | autumn | spring | winter | CO2 | years |
|---|---|---|---|---|---|---|
| CTRL | lm4p_ctl_1979-2024 | tc_pheno < tc_crit | 20-d tc_pheno | - | 292 ppm fixed | 1979-2023 |
| HistCO2 | lm4p_ctl2_co2_1979-2023 | same | same | - | historical | 1979- (running) |
| DL | phentest dayl_d | + day length 13 h (acer 12 h), 20 C cap | same | - | 292 | 2010 |
| DL+SP | phentest daylspring5_d | DL | 5-d tc_pheno_on | - | 292 | 2010 |
| DL+SP+WH | phentest daylhold5_d | DL | 5-d | leaf-on blocked while dayl < 12 h and tc < 20 C | 292 | 2010 |
| (planned) | 15-yr run from HistCO2 1996 state | final rules | | | historical | 1996-2015, analysis 2001-2015 |

## Observations
GIMMS LAI4g consolidated, GIMMS AVHRR-only (to 2015), GLASS V61 MODIS (2001-), all monthly 1 deg
(poster/2026_LM4p_LAI/data/). FLUXCOM-X GPP 2001-2021. SOS/EOS = 50 % of the annual amplitude of
monthly LAI interpolated to days (p3 method).

## Figures
| fig | script | data | content |
|---|---|---|---|
| 1 | scripts/f1_ctrl_bias_regions.py | data/f1_*.txt | CTRL vs three obs: regional normalised seasonal cycle 2001-2015 + SOS/EOS bias |

Inputs are read from ../poster/2026_LM4p_LAI/data and /Volumes/data02/LM4P; nothing large is copied here.
Notes and decisions: ../../notes/findings.md, decisions.md (dated 2026-10-19 onwards).
