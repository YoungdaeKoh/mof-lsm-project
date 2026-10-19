# GFDL AM4.5 (KIOST-ESM2 = ESM4.5) — 1 coupled atmos time step call trace

Source: `atmos/src/am45/` (mirror of climate:~/ESM4p5_KIOSTv2b/src). Line numbers verified by grep (2026-10-19).
Settings verified in `am45_input.nml.KIOST-ESM2` (copy of climate:~/KIOST-ESM2/input.nml).
Driver assumed: coupler/full + atmos_drivers/coupled + FV3 GFDL driver (build list not checked).

## Verified settings (input.nml line)
| item | value | line |
|---|---|---|
| dt_atmos / dt_cpld | 1800 s / 3600 s (ocean every 2 atmos steps) | 556–557 |
| grid | npx=97 (C96), npz=49 levels, hydrostatic=.T. | 817, 820, 836 |
| FV3 splitting | k_split=1, n_split=14 → acoustic sub-step 1800/14 = 128.6 s | 821–822 |
| radiation | rad_time_step=10800 s (full SW/LW every 3 h = 6 steps) | 1225 |
| PBL | Lock entrain=.true., stable_bl=.true., Mellor-Yamada=.false. | 1800–1804 |
| convection | UW (do_uw_conv=.true., do_deep=.true. → "double plume" deep+shallow), CMT on | 1152, 1668, 539 |
| microphysics | MG2 ('mg2'), 2-moment liquid+ice number; CLUBB off (do_clubb=0) | 1091, 1197–1199 |
| macrophysics | Tiedtke (code default, not overridden) | — |
| gravity-wave drag | cg_drag (non-orographic) + topo_drag (orographic); mg_drag off | 575–577 |

## Call tree (coupler/full/coupler_main.F90)
0. `do nc=1,num_cpld_calls` slow/ocean loop (:665); `do na=1,num_atmos_calls` fast loop (:783)
1. `sfc_boundary_layer` (:797 → atm_land_ice_flux_exchange.F90:682): Monin-Obukhov drag on exchange grid → explicit H,E,LW,τ **+ derivatives** dH/dTs, dE/dTs, dH/dTatm ...
2. `update_atmos_model_dynamics` (:831 → atmos_model.F90:1085 → atmosphere.F90:561 → fv_dynamics.F90:73) — adiabatic FV3
   - Rayleigh sponge (:383/388); `do n_map=1,k_split` (:447)
     - `dyn_core` (:486; dyn_core.F90:88) `do it=1,n_split` (:306): `c_sw` (:431) → `p_grad_c` (:561) → `d_sw` (:755) → `geopk` (:892) → `one_grad_p` (:1013, hydrostatic)
     - `tracer_2d` (:519): horizontal tracer transport
     - `Lagrangian_to_Eulerian` (:594 → fv_mapz.F90:63): remap to hybrid levels
   - `fv_subgrid_z` (atmosphere.F90:727): dry convective adjustment
3. `update_atmos_model_radiation` (:841 → atmos_model.F90:306 → radiation_driver.F90:1651): astronomy (:1949), gases (:1977), aerosol optics (:1988), cloud optics (:2011), `radiation_calc` (:2033) sea_esf SW (esfsw) / LW (sealw99). Full only on do_rad steps.
4. `update_atmos_model_down` (:851 → atmos_model.F90:461 → physics_driver_down, physics_driver.F90:1678)
   - `damping_driver` (:1934): Rayleigh, cg_drag, topo_drag
   - `vert_turb_driver` (:1959): Lock/stable_bl → K_m, K_h
   - `atmos_tracer_driver` (:1995)
   - `vert_diff_driver_down` (:2065 → vert_diff.F90:308): `uv_vert_diff` (:371), `compute_e` (:381), `vert_diff_down_2` (:431) → delta_t, dflux_t, dtmass (:441–447)
5. `flux_down_from_atmos` (:859 → atm_land_ice_flux_exchange.F90:2054): combine (:2364–2369) γ, e_t_n, f_t_delt_n; send SW/LW/precip + flux(ΔTs) coefficients
6. `update_land_model_fast` (:872, LM4) / `update_ice_model_fast` (:884, SIS2): implicit surface energy balance → ΔTs
7. `flux_up_to_atmos` (:895 → :2858): ΔT_N = f_t_delt_n + e_t_n·ΔTs (:3036)
8. `update_atmos_model_up` (:903 → atmos_model.F90:612 → physics_driver_up, physics_driver.F90:2248)
   - `vert_diff_driver_up` (:2475 → vert_diff.F90:1027): back-substitution dt(k) = e_k·dt(k+1) + f_k
   - `aerosol_driver` (:2546)
   - `moist_processes` (:2583 → moist_processes.F90:576): `convection_driver` (:708; uw_conv :1127, cu_mo_trans :1270), `lscloud_driver` (:712; Tiedtke macro :1088, MG2 micro :1153) → precip for next step's land
   - `cosp_driver` (:2722)
9. `flux_atmos_to_ocean` (:909)
10. `update_atmos_model_state` (:950 → atmosphere.F90:1088): `fv_update_phys` (:1152) applies accumulated u/v/t/q tendencies (pt += t_dt·dt·cp/cv, fv_update_phys.F90:385); time += 1800 s
11. after fast loop: `update_land_model_slow` (:964), `flux_land_to_ice` (:976), `update_ice_model_slow` (:1017), ocean MOM6 (:1058/1065)

## Implicit land–atmosphere coupling (split tridiagonal solve)
- Down sweep (atmos): ΔT_k = e_k·ΔT_{k+1} + f_k from top to bottom; hands over delta_t, dflux_t, dtmass
- Combine: γ = 1/(1 − dtmass·(dflux_t + dH/dTatm/cp)); e_t_n = dtmass·dH/dTs/cp·γ; f_t_delt_n = (delta_t + dtmass·H0/cp)·γ
- Land/ice solve linearised SEB (SW+LW−H−LE−G=0) with flux depending only on own ΔTs
- Up sweep: ΔT_N = f_t_delt_n + e_t_n·ΔTs, then back-substitute upward
- => fluxes and atmospheric column consistent; unconditionally stable (implicit Euler; Polcher et al. 1998, Best et al. 2004). LM4 must supply derivatives.

## Splitting
- Dynamics first (adiabatic), then all physics from post-dynamics state; tendencies accumulated and applied once at end (`fv_update_phys`).
- Exceptions applied directly: `fv_subgrid_z`; `fast_sat_adj` (if on).
- Precip reaching land in step 6 is from previous step's moist_processes (1-step lag, inferred from call order).

## Open
- LM4 inside `update_land_model_fast` not traced.
- Which of 3 atmos_model.F90 compiled not checked in build scripts.
