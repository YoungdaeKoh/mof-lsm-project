# Briefing for external review — LM4p offline phenology bias (2026-10-20)

You are reviewing a PhD student's research direction. Please read this brief, then (read-only) look at the
repo files listed at the end as needed. Answer in Korean; keep technical terms in English.

## 1. Context
- Project: KIMST (Korea, 2026–2030) "diagnose & improve land-surface models (LSMs) of a next-gen ocean-climate
  ESM". Year-1 deliverable = multi-LSM diagnostic framework (JULES, CLM5, Noah-MP, LM4p). Target ESM = KIOST-ESM2
  (GFDL ESM4.5), whose land model is **LM4p** (LM4.1 + PPA cohort vegetation).
- All 4 LSMs run offline with WFDE5 forcing 1979–2023 (spin-up on 1981–2010). LM4p: species distribution fixed
  (`do_biogeography=F`), N off, **CO2 fixed ≈292 ppm** in offline mode.
- One researcher, one 48-core node; one LM4p test year (2010, 24 ranks) costs ≈11–13 h wall. So each
  sensitivity experiment = 1 year, seeded from ctl restart y2009.
- Intended outputs: (a) a paper on LM4p phenology bias & fix (`paper/2026_LM4p_phenology/`), (b) a KMS 2026
  poster on LAI, (c) the improved scheme feeding back to KIOST-ESM2 (coupled), (d) later snow-physics work.

## 2. The CTRL bias (vs GIMMS / AVHRR / GLASS LAI, 2010 and 1982–2010 clim)
- **Autumn (EOS) far too late everywhere**: +20 to +55 days (50–70N +34, ENA +48, EAS +55). Leaves stay on
  until temperature drops below tc_crit; no day-length control in LM4p leaf-off.
- **Spring (SOS) late in boreal**: 50–70N +16, NEU +17, RFE +19, NEN +27, RAR +28 days.
- Winter LAI too high in mild climates (20–40N Jan 1.60 vs GIMMS 0.75; SH July 3.47 vs 2.05) — leaves re-open
  after the solstice when 20-day smoothed T ≥ threshold.
- Species leaf area: larix is essentially absent; boreal leaf area = picea (evergreen) + acer + c3grass.
  So "deciduous needleleaf" parameters barely matter; c3grass and acer carry the phenology.

## 3. Observational analyses done (obs only)
- Obs EOS sits at a near-constant day length that rises with latitude: DL_EOS ≈ 12.0 + 0.05(|lat| − 40) h
  (GIMMS/GLASS, evergreen-dominated cells excluded; slope 0.050–0.056). Obs SOS tracks temperature instead.
- Chilling (Murray 1989 NCD–GDD) with ERA5 2010: chill saturated in all boreal regions → would advance SOS only
  2–6 days (need 8–29). Rejected as the fix.
- Growth delay (gate open → LAI 50 %) in model: median 6–14 days → not the main cause of late spring.
  Main cause = 20-day smoothed temperature gate (tc_pheno) is slow.

## 4. Code patches & 1-year experiments (all 2010, same seed)
| run | change | key result |
|---|---|---|
| base (CTRL) | — | biases above |
| dayl (DL13/12) | leaf-off also when day length < 13 h (larix/acer/c3grass) / 12 h | EOS bias 50–70N +34→+11, ENA +48→+12; SOS unchanged |
| daylspring5 (DLS5) | DL + leaf-ON uses 5-day smoothed T (τ5) instead of 20-day; spring T-based leaf-off skipped | boreal SOS halved (50–70N +14.7→+7.9, NEU +15→+6) **but temperate too early**: 40–50N +1→−15, ENA 0→−23, EAS −41→−59 (real early leaf-out, Mar LAI ENA 1.43 vs 1.11) |
| daylhold5 (DLH5) | DLS5 + "winter hold": no leaf-on while day length < 12 h AND tc_pheno < tc_crit_off (stateless, restart-safe) | boreal SOS kept (+8.0); SH 20–40S July LAI 1.89→1.05 (GIMMS 0.90); NH 20–40N Dec 1.12→0.94 (GIMMS 0.81); Jan unchanged only because seed inherited leaves; winter false-start % back to DL level; **temperate early spring NOT fixed** (ENA −22.7, 40–50N −14.4, EAS −51) |
| dayllat (running, ends 10-21 04h) | autumn only: leaf-off threshold = 12.0 + 0.05(|lat|−40) h; spring = CTRL | offline prediction: 50–70N EOS +9.3→+5.9 d, TIB −31→+10.5 d |
| phasewfde5 (queued, ends 10-21 15h) | forcing rain/snow split from WFDE5 Snowf instead of converter's 0–2 °C ramp (ramp gives 1.2–1.5× more snow) | separates "forcing vs snow physics" for later snow work |

Seasonal 12-month LAI MAE vs GIMMS, DL→DLS5→DLH5: NEU .34/.30/.31, RFE .27/.23/.23, 40–50N .38/.47/.44,
EAS .49/.62/.54. Many boreal regions still have summer LAI too high (NWN, NEN, WSB MAE ≈ 0.8–1.1; peak LAI bias,
not timing).

Planned experiment matrix (user decision): autumn-only (dayllat) → spring-only (τ5 ± hold) → spring+autumn.
Judging metric decided earlier: not SOS days alone but FLUXCOM May–Jun GPP/NEE + LAI range across 3 products.

## 5. Open questions for you
1. Is the overall approach (one-parameter-at-a-time 1-year patch tests against 3 LAI products) sound for a
   paper and for an ESM improvement? What is missing for reviewers (multi-year, interannual variability,
   flux validation, coupled test, parameter-vs-structure argument)?
2. Temperate early leaf-out under τ5: how should spring be fixed? Options we see: latitude/species-limited τ5;
   τ depending on climate; GDD threshold scaled by chilling or photoperiod (e.g. spring day-length floor);
   keep 20-day for acer/temperate and τ5 only for boreal c3grass. What does the phenology-modelling literature
   (e.g. CLM, ORCHIDEE, JSBACH, Jolly GSI, Caffarra/Chuine) suggest and how to justify it physically?
3. Autumn: day-length rule with a latitude slope fitted to obs — is it defensible, or will reviewers call it
   curve-fitting? Better framing (e.g. photoperiod × temperature like Delpierre 2009 / CLM Birch, or GSI)?
4. Seed / 1-year design limits (Jan inherits seed leaves; snow inherits ramp). When should we move to a
   multi-year (e.g. 2001–2015) run, and with which final configuration?
5. Peak LAI too high in boreal (NWN/NEN/WSB) — separate problem (allocation, LMA, PPA) — in or out of scope?
6. Concretely: what should the paper's storyline and the next 3 experiments be?

## 6. Files you may read (read-only)
- `notes/findings.md` (verified numbers; latest entries ~lines 73–100)
- `lm4/LM4_SPINUP_NOTES.md` §13.69–13.70 and the last sections (from "봄 잎 나기 지연의 원인 진단" to the end)
- `lm4/patches/lm4P.phenology_*.diff` (actual code changes)
- `poster/2026_LM4p_LAI/data/daylspring5_2010.txt`, `lm4/data/winter_false_start_2010.txt`
- `paper/2026_LM4p_phenology/README.md`
