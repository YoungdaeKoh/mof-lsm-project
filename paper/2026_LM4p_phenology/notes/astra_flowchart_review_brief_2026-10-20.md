# Review request: is this leaf-on/leaf-off flow chart faithful to the (patched) LM4.1 code?

Read (read-only): `lm4/patches/phenoff_work/vegn_dynamics.F90` (subroutine vegn_phenology_ppa, ~lines 2066–2259) and
`lm4/patches/phenoff_work/vegetation.F90` (update_vegn_slow, ~lines 2600–2850). Facts verified on the server source that
are not in these files: `tc_daily` and `daily_T_min/max` are accumulated from canopy-AIR temperature `cana_T`
(vegetation.F90:2265; vegn_tile.F90:396–398 comments "daily canopy air temperature").
Also see `paper/2026_LM4p_phenology/figures/f2a_rule_box.png` (current equation box for the paper).

## Flow chart to check
```
[every 30 min] accumulate canopy-air T -> daily mean tc_daily, daily Tmin/Tmax (per tile)
[once a day, update_vegn_slow]
  GDD(per cohort) += [max(Tmin-0C,0) + max(Tmax-0C,0)]/2            :2659
  (tau5 patch) tc_pheno_on = 5-day smoothed tc_daily (per tile)      :2667
  tc_pheno = 0.95 tc_pheno + 0.05 tc_daily  (~20-day, per tile)      :2671
  growth (vegn_growth; leaves grow toward bl_max if ON)              :2777
  starvation check                                                   :2781
  vegn_phenology_ppa (loop over cohorts)                             :2783
    evergreen -> always ON
    drought = root-zone soil moisture < threshold
    if OFF: ON when GDD > gdd_crit AND tc_on >= tc_crit (tc_on = tau5 or 20-day)
            AND not drought AND NOT[dayl < dayl_crit_on AND tc_pheno < tc_crit_off]   (winter hold)
            (grass: reset bl_max at onset)
    if ON:  OFF + GDD=0 when (tc_pheno < tc_crit [only on shortening days if tau5 on])
            OR (shortening AND dayl < dayl_crit_off + slope(|lat|-lat0) AND tc_pheno < tc_crit_off)
            OFF without GDD reset when drought
    if OFF and leaves remain: trees lose 7.5 %/day of leaf C; grasses reset to seedling size, excess leaves dropped
            at once; all leaves dropped if LAI < min_lai_pheno -> litter to soil
    relayer + merge cohorts
[next 30 min] LAI = bl / LMA / crown area -> absorbed shortwave -> photosynthesis
```
## Claimed differences between f2a (paper box) and code
1. f2a GDD uses daily mean T; code uses (Tmin-term + Tmax-term)/2 — differs when Tmin < 0 < Tmax.
2. f2a does not say T is canopy-air temperature.
3. f2a omits the drought condition in leaf-on and the drought leaf-off (no GDD reset).
4. f2a shows constant L_crit; code supports latitude-dependent threshold (slope 0 in the DL run).
5. f2a omits tau5 (spring smoothing) — intended (paper scope is autumn-centred).
Minor: f2a uses ">" for leaf-on T test, code uses ">=".

## Questions
1. Is the flow chart correct and complete? Any path missing (e.g. order effects: phenology after growth on the same
   day, cohort merging changing status/GDD, grass height reset, first-day initialisation of tc_pheno_on, restart)?
2. Are the 5 claimed differences right? Any other mismatch between f2a and code?
3. For a paper figure, what is the minimal faithful rule box (which conditions must be shown, which can go to SI)?
Answer in Korean, technical terms in English, cite file:line.
