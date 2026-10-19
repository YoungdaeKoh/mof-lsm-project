# CAM6 (CESM2.1.5, FV dycore, f09) — 1 time step call trace

Source: `atmos/src/cam6/` (mirror of climate:~/CESM/components/cam/src, .F90 only). Line numbers verified by grep (2026-10-19).
Namelist (`atm_in`) NOT checked — scheme choices/defaults below are Fortran defaults + standard CAM6 config.

## 0. Actual order inside one coupling interval (`atm_run_mct`, cpl/atm_comp_mct.F90:332)
1. `atm_import` (:406 → cpl/atm_import_export.F90:8): coupler fluxes → `cam_in` (shf:56, cflx(:,1) evap:57, lhf:59, wsx:54, ts:65)
2. `cam_run2` (:433) → `cam_run3` (:437) → `cam_run4` (:441) → `advance_timestep` (:448) → `cam_run1` (:454)
3. `atm_export` (:460 → atm_import_export.F90:200): `cam_out` (tbot, netsw:238, precc:240, ...) → CLM/ocean

=> **[import] → tphysac (2nd half of previous step) → p_d_coupling → history/restart → clock+1 → dynamics → tphysbc (incl. radiation) → [export]**

## 1. Call tree (logical order)
### A. cam_run1 (control/cam_comp.F90:217)
1. `stepon_run1` (dynamics/fv/stepon.F90:261)
   - `dyn_run` (stepon:315 → dynamics/fv/dyn_comp.F90:687) — FV dynamics
     - sub-step dt = bdt/(nsplit*n2*nv) (:1435–1438)
     - `do iv=1,nv` (:1494) vertical-remap loop
       - `do n=1,n2` (:1762) tracer loop
         - `do it=1,nsplit` (:1816) → `cd_core` (:1862): C-grid half step `c_sw`, `geopk` (pressure gradient), D-grid momentum/mass/theta update on Lagrangian layers
         - `trac2d` (:2321): horizontal tracer advection with accumulated mass fluxes
       - `te_map` (:2635): remap Lagrangian layers → hybrid eta levels (+ total energy fix)
   - `d_p_coupling` (stepon:333 → dp_coupling.F90:72): D-grid wind → A-grid, block → physics chunks, `geopotential_t`, `set_state_pdry`
2. `phys_run1` (physpkg.F90:940): `check_energy_gmean` (:1001), `phys_timestep_init` (:1015; prescribed O3/GHG/aerosol/solar update)
   - `tphysbc` (:1634):
     a. `qneg3` (:1849) negative tracer fix
     b. `check_energy_fix` + update (:1873) — return energy lost by dycore as uniform heating
     c. `dadadj_tend` (:1905) dry adiabatic adjustment
     d. `convect_deep_tend` (:1918 → zm_conv_tend) — **ZM deep convection**
     e. `convect_shallow_tend` (:1963) — no-op in CAM6 (shallow handled by CLUBB)
     f. macmic loop `do macmic_it=1,cld_macmic_num_steps` (:2041):
        - **`clubb_tend_cam`** (:2083 → clubb_intr.F90:1012) — PBL turbulence + shallow Cu + cloud macrophysics (higher-order closure)
        - `microp_aero_run` (:2131) aerosol activation (CCN/IN)
        - **`microp_driver_tend`** (:2161 → micro_mg_tend2_0) — **MG2 2-moment microphysics**
     g. `aero_model_wetdep` (:2217) aerosol wet removal
     h. `convect_deep_tend_2` (:2234) convective tracer transport
     i. **`radiation_tend`** (:2272 → rrtmg/radiation.F90:680) — RRTMG SW (:1105)/LW (:1153) only when `radiation_do()`; otherwise reuse qrs/qrl (`radheat_tend` :1240). Fills `cam_out%netsw`, `flwds`.
     j. `cam_export` (:2291): lowest-level T/q/u/v, precip → `cam_out`

--- coupler: CLM/ocean/ice compute surface fluxes from `cam_out` → next `atm_import` ---

### B. cam_run2 (cam_comp.F90:267)
3. `phys_run2` (physpkg.F90:1080) → `tphysac` (:1221):
   a. `chem_emissions` (:1373) surface emissions into `cam_in%cflx`
   b. `qneg4` (:1389) evaporation must not make lowest-level q negative
   c. **`vertical_diffusion_tend`** (:1434 → vertical_diffusion.F90:644): TMS (:930), Beljaars (:943); in CAM6 (eddy=CLUBB_SGS) shf/evap/stress set to 0 (:1098–1104) → only non-water tracer fluxes diffused (`compute_vdiff`)
   d. `rayleigh_friction_tend` (:1452), `aero_model_drydep` (:1467)
   e. **`gw_tend`** (:1498 → gw_drag.F90:1171): orographic / convective / frontal gravity wave drag
   f. **`physics_dme_adjust`** (:1603): readjust layer dp for water-vapour change (dry-mass conservation, FV only)
4. `stepon_run2` → **`p_d_coupling`** (dp_coupling.F90:698): u,v as tendencies (dudt/dvdt :846–847), T,q as updated state (:848)
### C. cam_run3 → `stepon_run3` (dynamics history)   ### D. cam_run4: history (:387), restart (:395)

## 2. Land (CLM) flux path — EXPLICIT coupling
- CLM computes fluxes from previous `cam_out` → arrives via `atm_import` into `cam_in`. Atmosphere treats them as fixed for the step.
- In CAM6, heat/moisture/momentum surface fluxes enter **CLUBB lower boundary** (clubb_intr.F90:1781–1783):
  `wpthlp_sfc = shf/(cp*rho)`, `wprtp_sfc = cflx(:,1)/rho`, `upwp_sfc = wsx/rho`
- Contrast GFDL: implicit (down/up sweep with dFlux/dT_surf) — lowest-level T and surface T solved together in one Δt.

## 3. Splitting & time steps
- Physics internal: **time-split (sequential update)** — `physics_update` (physics_types.F90:201) applies each tendency immediately (u :306, q :333, t :413). ZM → CLUBB → MG2 → radiation each sees the updated state.
- Dynamics ↔ physics: sequential (dynamics first, then physics; result passed back via p_d_coupling).
- dtime = 1800 s (ATM_NCPL=48; outside mirror)
- nsplit auto (`init_nsplit`, dyn_comp.F90:384): f09 → 8; nspltrac = 2; nspltvrm = 1 → 8 acoustic sub-steps ≈ 225 s, 1 remap per Δt
- iradsw/iradlw = −1 (radiation.F90:115,117) → full RRTMG every 1 h (2 steps)
- cld_macmic_num_steps: Fortran default 1 (phys_control.F90:79); CAM6 namelist default believed 3 (unverified)

### Verified in `cam6_atm_in.F_2000climo_f09` (copy of climate:~/CESM/cases/F_2000climo_f09/CaseDocs/atm_in; -phys cam6, 0.9x1.25, ATM_NCPL=48)
| item | value | line |
|---|---|---|
| deep / shallow / macro / micro / eddy | ZM / CLUBB_SGS / CLUBB_SGS / MG / CLUBB_SGS | 222–240 |
| radiation | rrtmg; iradsw/iradlw not set → default −1 → every 1 h | 239 |
| cld_macmic_num_steps | 3 → 600 s per macmic sub-step | 221 |
| clubb_timestep | 300 s → 2 CLUBB sub-steps per macmic | 144 |
| fv_nsplit | not set → auto: int(4·1800·382/(1800·191)+0.75) = 8 | — |
| fv_nspltvrm | 2 → in dyn_comp.F90:1436–1438: n2=(2+2−1)/2=1, nsplit=(8+2−1)/2=4, dt=1800/(4·1·2)=**225 s**; 8 acoustic sub-steps, **2 vertical remaps** per Δt | 159 |
| gravity waves | use_gw_rdg_beta=.true. (ridge orographic) only; convect/front/oro=.false. | 178, 242–246 |
| Beljaars / TMS | .true. / .false. | 13, 311 |

## 4. Schemes
ZM deep convection · CLUBB (PBL+shallow+macrophysics) · MG2 microphysics · MAM4 aerosol · RRTMG SW/LW · gravity wave drag (oro/conv/front) · TMS + Beljaars · dry adjustment · FV energy fixer · dme_adjust

## 5. Uncertainties
- Scheme strings, cld_macmic_num_steps=3, fv_nsplit, clubb_timestep come from `namelist_defaults_cam.xml` (not mirrored). Verify in a real run's `atm_in`: `fv_nsplit`, `cld_macmic_num_steps`, `iradsw`, `clubb_timestep`.
- `cam_export`, `time_manager`, `camsrfexch` (utils) not mirrored — only call sites verified.
- MCT cap assumed (CESM2.1.5 default).
