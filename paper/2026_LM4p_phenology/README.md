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
| (planned) | 15-yr run from HistCO2 1996 state, daily LAI on | final rules | | | historical | 1996-2015, analysis 2001-2015 |

## Observations
GIMMS LAI4g consolidated, GIMMS AVHRR-only (to 2015), GLASS V61 MODIS (2001-), all monthly 1 deg
(poster/2026_LM4p_LAI/data/). FLUXCOM-X GPP 2001-2021. SOS/EOS = 50 % of the annual amplitude of
monthly LAI interpolated to days (p3 method).

## Planned main figures (2026-10-20, decisions.md "논문 범위 = 가을 중심")
Scope: autumn day-length rule is the main contribution; spring = diagnosis + partial fix (tau5) as discussion.
| fig | message | built from |
|---|---|---|
| 1 | problem: CTRL SOS/EOS bias | f1 (as is) |
| 2 | how the threshold was constrained: obs EOS/SOS day length vs latitude (3 products), onset slope 0.19 = Birch vs 50 % slope 0.05 | s6, s7, s4 txt (new script) |
| 3 | why CTRL is late (rule timing) + CTRL vs corrected SOS/EOS bias | f3 + f4 merged |
| 4 | LAI / GPP / NEE seasonal improvement (spring NEE bias = respiration, out of scope) | p21-type flux vs obs |
| 5 | why it improved: dGPP follows dfAPAR (GPP/fAPAR unchanged) | gpp_vs_fapar_dl |
Rule schematic (f2) -> equations in Methods; rule box (f2a) -> SI. Wording: "process-based bias reduction", not "bias correction".
Draft figures below are the 2010 versions; final = 15-yr CTRL/FULL pair.

## Figures
| fig | script | data | content |
|---|---|---|---|
| 1 | scripts/f1_ctrl_bias_regions.py | data/f1_sos_eos_bias.txt | (a) GLASS MJJAS LAI, (b) LM4.1 - obs, (c) boreal seasonal cycle vs 3 obs, (d,e) SOS/EOS bias by latitude band (monthly, 50 %) |
| 2 | scripts/f2_rules_schematic.py | - | (a) CTRL vs modified rules, (b) one-cell 2010 timeline (dayl_d) - draft, winter hold pending daylhold5_d |
| 3 | scripts/f3_rule_timing_maps.py | data/f3_rule_timing_bands.txt | rule timing reconstructed from daily T: spring smoothing delay, binding gate, photoperiod vs cold rule, cold rule vs obs EOS |
| 4 | scripts/f4_bias_change.py | data/f4_bias_change.txt | SOS/EOS bias maps CTRL vs EXP + latitude-band bars; CASE switch (2010 draft: CTRL = phentest base, EXP = dayl_d; 15-yr pair later) |
| 2a | scripts/f2a_rule_box.py | - | Weng et al. 2015 rule box with the added winter-hold and photoperiod terms in red (spring change not shown) |
| S1 | scripts/s1_daylength_formula.py, s1b_daylength_globe.py | - | day-length terms of the patch: declination / day-length curves (30-70N, 40S) and north-pole globe view on 21 Jun, 5 Sep (50N reaches 13 h), 21 Dec |
| SI | scripts/o1_obs_native_to_1deg.py, dlog.py, o2_regional_fit_native.py | data/obs_native/, data/o2_regional_fit_native.txt | native-sampling obs (8-day / half-monthly) and double-logistic dates: sampling moves dates <= 3 d |

Inputs are read from ../poster/2026_LM4p_LAI/data and /Volumes/data02/LM4P; nothing large is copied here.
Notes and decisions: ../../notes/findings.md, decisions.md (dated 2026-10-19 onwards).
