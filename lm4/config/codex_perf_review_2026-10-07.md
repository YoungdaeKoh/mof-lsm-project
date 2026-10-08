**Prioritize tracer pruning and remaining diagnostic work. Do not interpret the 152 s “Flux land to ice” maximum as 152 s of removable work.** These are source-review recommendations, not verified speedups; no files were modified.

Paths below are relative to this folder.

1. **Prune unused tracers: strongest configuration-level candidate, but `sphum + co2` is not yet a certified minimum.**

   The exchange list contains atmospheric **prognostic** tracers matching land or ice, plus gas-exchange additions—not every field-table declaration (`src/atm_land_ice_flux_exchange.F90:359–408`). Removing land-only tracers reduces canopy work; removing matched tracers also reduces exchange work.

   | Path | Work repeated each fast step |
   |---|---|
   | `sfc_boundary_layer` | Atmospheric tracer overrides at `:895`; land overrides at `:968`; atmosphere→exchange remapping at `:997`; surface tracer remapping at `:1121`, `:1151`; derivatives at `:1288`; further tracer overrides at `:1360`, `:1515`. |
   | `flux_down_from_atmos` | Atmospheric tendency/derivative overrides at `:2154`; exchanged-tracer processing at `:2316`, `:2331`; two exchange→land remaps per matched tracer at `:2551`; land flux/derivative overrides at `:2590`. |
   | `flux_up_to_atmos` | Land tracer overrides at `:2915`; land→exchange remapping at `:2985`; updated fluxes/tendencies at `:3002`; exchange→atmosphere tendency remapping at `:3022`; diagnostic loops thereafter. |
   | `update_cana_tracers` | Generic-tracer loop at `src/land_tracer_driver.F90:940`; concentration and derivative diagnostics for **all `ntcana`** at `:1291`. |

   **Keep both humidity and CO₂.** Land directly indexes both for its implicit flux calculation (`src/land_model.F90:1648`) and uses canopy CO₂ for photosynthesis (`:1728`). Removing CO₂ or substituting a fixed concentration changes photosynthesis, stomatal conductance and consequently water/energy/carbon evolution.

   **What needs auditing before deletion:**

   - **Atmospheric initialization:** it still initializes the full atmosphere. Cloud/microphysics/aerosol modules may require tracer names even though they never step. Their implementations are absent.
   - **Dust:** `update_land_dust` is still called at `src/land_tracer_driver.F90:873`; its implementation is absent. Do not assume dust tracers are optional.
   - **Gas exchange/ice:** `input.nml:403–405` enables ocean nitrogen and NH₃ exchange. Audit these registrations and SIS2 requirements alongside tracer removal; `do_ocean=F` alone does not establish that their initialization is inactive.
   - **Forcing:** preserve `ATM co2_bot`, humidity, and all retained tracer overrides. CO₂ override conversion from dry VMR to moist MMR occurs at `src/atm_land_ice_flux_exchange.F90:895`. Deleted names stop receiving their `_bot`, `_surf`, `_flux`, `dfd*`, `delta_*`, `dflux_*` overrides. The supplied folder lacks `data_table`, so its compatibility cannot be certified.
   - **Diagnostics/restarts:** removed tracer diagnostics disappear. Canopy restart loading is name-based (`src/canopy_air.F90:318`), which helps, but atmosphere/ice restart compatibility remains unverified. Compare retained prognostic fields, not whole restart files with different schemas.

   Expected gain: potentially several percent, but unmeasured. The 207+94+209 s exchange maxima are **not** wholly tracer costs, and the 52 s land-tracer timer overlaps land-fast.

2. **Remove unnecessary diagnostic computation inside land-fast: best code-level candidate.**

   The notable remaining opportunity is an **unconditional second tile traversal** at `src/land_model.F90:1342`. It computes vegetation, snow, soil/lake/glacier water stocks and heat before sending diagnostics (`:1351–1409`). Guard each expensive stock calculation by the complete set of diagnostics consuming it. With 1.37 M cohorts, avoiding vegetation stock/heat traversals could matter more than scalar micro-optimizations. Its cost is not separately timed.

   Further opportunities, ranked approximately:

   - **Residual deposition preparation:** even with every deposition method removed, `src/land_tracer_driver.F90:886–936` computes ground fractions, saturation humidity, vegetation wet/snow fractions and acid ratios. `get_tile_property` includes a cohort biomass sum (`:1351`). Skip preparation when neither active deposition nor requested diagnostics need it. **Do not skip the whole tracer update:** the concentration equation still operates without deposition (`:1168`). The measured 41.6 s deposition timer bounds this entire region, so savings here are below roughly 1% of total.
   - **Diagnostic buffers:** `src/land_tile_diag.F90:1076`, `:1109`, `:1142` allocate/free aggregation scratch arrays per field/selector dump. Reuse appropriately sized, thread-private storage while retaining zeroing and accumulation order. Dumps occur inside land-fast (`src/land_model.F90:1434`). Allocation savings are likely modest; traversal, reduction and output costs may dominate.
   - **Already guarded:** diagnostic `qscomp` at `src/land_model.F90:2616`; carbon totals at `:2669–2672`; conservation carbon totals at `:1653`, `:2474`. No additional saving when their IDs/checks are inactive. If both carbon diagnostics remain enabled, compute their shared total once.
   - **Small:** reuse `phot_co2_data` storage (`:1235`, `:1438`), cache immutable tracer names/override strings in the coupler, and reduce repeated watch-point calls (`:1607` onward). Expect small gains individually.

   **Do not cache evolving state as a constant.** Ground wet/frozen fractions, biomass, canopy wetness, temperatures and saturation humidity change. The physics `qscomp` calls at `:1778`, `:1833` are required. Canopy resistance also reads soil carbon (`src/canopy_air.F90:1086`); it is not merely a static property lookup.

3. **Avoid unused atmospheric tracer initialization: up to 130 s per job, about 3.0% here.**

   [`coupler_main.F90:1728`](/private/tmp/claude-501/-Volumes-data01-MOF-LSM-project/df7bcc93-200b-4d25-9727-518db5414f1b/scratchpad/codex_perf/src/coupler_main.F90:1728) calls `atmos_model_init` under `Atm%pe`, without a `do_atmos` guard. Thus the initialization timer is real despite zero atmospheric stepping.

   Pruning tracers and disabling their unused packages may reduce it. A proper minimal data-atmosphere initialization path could avoid more, but **simply skipping `atmos_model_init` is unsafe**: the coupler still needs atmospheric grids, arrays and boundary structures. The tracer-driver implementation is missing, so I cannot attribute the 130 s to particular reads/packages. `do_tropchem` is already false (`input.nml:1635`). This benefit amortizes over longer jobs.

4. **Trim atmosphere-return work selectively; retain the land boundary calculation.**

   Atmospheric tendency remaps at `src/atm_land_ice_flux_exchange.F90:3022`, `:3044` are candidates when their consumers are inactive. But `flux_up_to_atmos` also updates diagnostic fluxes, applies overrides and flushes land diagnostics before tiling changes (`:3264`); skipping the entire routine requires a dependency audit.

   Likewise, `sfc_boundary_layer` and `flux_down_from_atmos` supply land fluxes and derivatives. Data-atmosphere forcing does **not** make them redundant. Bypassing them without reproducing every land boundary value changes turbulent exchange and land physics.

   **Land→ice:** the unconditional slow-step call is at `src/coupler_main.F90:981`; its comment says it puts **runoff and surface pressure on the ice grid**. The actual routine lives in the unprovided `flux_exchange_mod`. Therefore I cannot establish its complete per-step operations, side effects, or whether specified SIS2 consumes those fields. `do_ocean=F` is insufficient justification for removing it.

   Crucially, slow-land’s spread is **147.94 s**, and the immediately following land→ice spread is **148.46 s**, with only **3.27 s minimum**. This strongly suggests transferred waiting time. It does not prove the exclusive cost is 3 s, but makes a 152 s wall-clock saving implausible without further timing.

5. **Layout tuning: worthwhile experiment, limited evidence for a large gain.**

   Fast-land max−mean is **93.6 s**, or **2.2% of total runtime**; max−min is 164.4 s. Neither is a guaranteed recoverable saving because these timers include diagnostics/communication.

   Current land `layout=2,2`, `io_layout=1,1` is at `input.nml:1056`. Try supported `1,4` and `4,1` decompositions at the same rank count, measuring cohort counts and compute time per rank. These alter geographic partitioning, not necessarily cohort balance.

   `mask_table` removes all-ocean regions (`src/land_model.F90:181–201`); it is not cohort-weighted balancing. `io_layout` targets I/O, not vegetation compute. Actual unstructured partition behavior is in the missing `land_data_init` implementation (`:389`). Changed decomposition can also change reduction order, so bit identity must be tested.

**What is still missing:** exclusive timings within land-fast—especially vegetation steps at `src/land_model.F90:1735`, `:2261`, `:2401`, boundary-property updates, and diagnostic dumps. The supplied clocks cannot establish which dominates. Validate candidates individually against retained land state and outputs over restart boundaries and vegetation/tiling transitions; avoid claiming bit identity from an inactive-atmosphere argument alone.
