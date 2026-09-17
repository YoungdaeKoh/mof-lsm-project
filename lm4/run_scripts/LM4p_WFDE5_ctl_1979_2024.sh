#!/bin/bash
#
# LM4p (LM4.2, offline "Route B") WFDE5 control run  lm4p_ctl_1979-2024
# ======================================================================
#
# One file that shows how the production run was actually configured, in the
# same spirit as cesm/run_scripts/F_f09_cam6clm5.csh.  The run itself was done
# in pieces (ctl_setup.sh, chain_lm4p_ctl.sh, run_lm4p_ctl.sh on climate00,
# 2026-08-11 .. 2026-09-07); this script reassembles them in order so that the
# whole configuration can be read top to bottom.  Running it again would stand
# up an identical case in a new directory -- it deletes nothing.
#
# What the experiment is
#   Land-only lm4P (the LM4.2 land of KIOST-ESM2 / GFDL ESM4.5) driven by WFDE5
#   v3.0 for 1979-2024 on the C96 cubed sphere, 48 PE on climate01.  It is the
#   LM4 leg of the multi-LSM diagnostic and the baseline ("ctl") for Phase 2
#   perturbation runs.  It ended at 2023 (45 years): LUH2 land-use transitions
#   stop at 2023-01-01 and land use is a land forcing that must not be invented
#   (LM4_SPINUP_NOTES 13.54).  The 2024 forcing file exists and is harmless.
#
# How the model is made to run without an atmosphere ("Route B", notes 13.10-11)
#   The full FMS coupler is used as built for KIOST-ESM2 AMIP.  coupler_nml
#   do_atmos=.false. skips the atmospheric time step, do_ocean=.false. removes
#   MOM6, do_ice=.true. keeps SIS2 with specified sea ice/SST (needed for the
#   exchange grid), and every forcing field LM4 needs is injected through the
#   fms_data_override hooks that already exist in atm_land_ice_flux_exchange
#   (data_table below).  Zero new Fortran; two small patches in the clone.
#
# Vegetation state
#   Warm start from a multi-tile, multi-cohort equilibrium (tile=13, cohort~60
#   per C96 cell) that came out of KIOST-ESM2's 400-year coupled spin-up, then
#   30 more years offline under WFDE5 1981-2010 ("cycle 1", RUN/lm4_spinup30,
#   preserved as archive_c1).  do_cohort_dynamics / do_patch_disturbance /
#   do_phenology are on; do_biogeography is OFF, so species composition is
#   prescribed (cover_type.nc) and only biomass, structure and LAI evolve
#   (notes 13.20, decision 2026-07-20).  vegn_to_use='uniform' is still in the
#   namelist but is only read on a COLD start; a warm start ignores it (13.20).
#
# Time axis
#   Calendar NOLEAP.  WFDE5 records sit at 03/09/15/21 UTC (6-h means at their
#   midpoints), so every segment starts at Jan 1 03:00 and runs days=365,
#   hours=0, ending at Jan 1 03:00 of the next year: December closes and the
#   next segment starts at exactly that instant (13.31, 13.36).  Each forcing
#   file carries the next year's first two records so that the last time step
#   is inside the file (append_boundary_1979_2024.py).
#
# Chunking
#   BATCH_SYSTEM cannot resubmit here, so a bash chain submits one PBS job per
#   model year, waits, checks, archives, hands RESTART/ to INPUT/, repeats.
#   The guards are the scars of two real incidents: a ~5000-iteration crash
#   loop on a stale restart, and 15 years written with 11 months each (13.31).
#
# Throughput  10.3-10.5 h / model-year at 48 PE (13.48, 13.51).
#
# Variant   LANDUSE=off bash LM4p_WFDE5_ctl_1979_2024.sh  freezes land use
#           (do_landuse_change=.FALSE., section 3) for a CLM5-like fixed-land-use
#           run; the ctl as actually run is LANDUSE=on (the default).
#
# ----------------------------------------------------------------------------
set -eu

# ============================================================================
# 0. Executable -- lm4P clone with two patches, built with the GFDL mkmf stack
# ============================================================================
# Clone of ~/ESM4p5_KIOSTv2b (the KIOST-ESM2 build); the original is untouched.
BASEDIR=/data2/ydkoh/lm4/esm4p5-lm4p-offline
EXE=$BASEDIR/exec/fms_esm4.5_compile_v3_1007_fix.x
#
# Patch 1  src/lm4P/shared/sphum.F90 (qscomp)          lm4/patches/sphum.F90.clamp.lm4P
#          Tc = min(max(T,173.16),372.16) fed to escomp.  Without it a canopy
#          temperature overshoot in dry, sunlit cells (Kalahari in January was
#          the first) overflows lookup_es and the run dies (notes 4, 5, 13.12).
# Patch 2  src/coupler/full/coupler_main.F90            lm4/patches/coupler_main.F90.radiation_gate.diff
#          "if (do_atmos .and. ...)" on the two update_atmos_model_radiation
#          calls.  The coupler gates every other atmospheric call on do_atmos
#          but forgot radiation, which was 56 % of the main loop for nothing
#          (13.15-13.16).  The data_override values overwrite its result anyway.
#
# Rebuild after patching (this is lm4p_offline_build_clamp.sh):
#   source /etc/profile.d/modules.sh; module purge
#   module load intel21/compiler-21 intel21/mkl intel21/hdf5-1.10.5 \
#               intel21/netcdf-4.6.1 intel21/mvapich2-2.3.4
#   cd $BASEDIR/exec
#   make BASEDIR=$BASEDIR SRCROOT=$BASEDIR/src/ BUILDROOT=$BASEDIR/exec/ \
#        MK_TEMPLATE=$BASEDIR/exec/intel_tomo.mk lm4P/liblm4P.a
#   make ... fms_esm4.5_compile_v3_1007_fix.x            (233 MB, 2026-07-20)
#
[ -x "$EXE" ] || { echo "ABORT: executable missing: $EXE"; exit 1; }
grep -q 'Tc = min' "$BASEDIR/src/lm4P/shared/sphum.F90" \
  || { echo "ABORT: qscomp clamp not in the source this exe was built from"; exit 1; }
grep -q 'do_atmos .and.' "$BASEDIR/src/coupler/full/coupler_main.F90" \
  || { echo "ABORT: radiation gate patch not in coupler_main.F90"; exit 1; }

# ============================================================================
# 1. Forcing -- WFDE5 in the form FMS data_override can read
# ============================================================================
# data_override is a plain reader (time/space interpolation, no derivation), so
# what CDEPS/DATM used to compute is precomputed once per year:
#   python /data2/ydkoh/lm4/wfde5_to_lm4p_atm.py YEAR
#     reads  /data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5/YEAR_wfde5.nc
#            (0.5 deg, 7 vars, 1460 x 6-h means, noleap; same files CLM5 uses)
#     writes /data2/ydkoh/lm4/forcing_WFDE5_lm4p/wfde5_atm_YEAR.nc with
#       - CF 1-D lat/lon (the CLM files only have 2-D LATIXY/LONGXY, which the
#         "bilinear" override cannot use)
#       - ocean cells filled with the nearest valid land value, periodic in
#         longitude, so the bilinear stencil never mixes in _FillValue at the
#         coast (8.5 % of land cells have a missing neighbour; East Asia above all)
#       - derived lprec/fprec (rain/snow split, ramp 273.15..275.15 K) and
#         coszen; u_bot = WIND, v_bot = 0
#   python /data2/ydkoh/lm4/append_boundary_1979_2024.py
#     appends the next year's first two records (day 365.125, 365.375) to every
#     file -> 1462 records, so a segment's last step (Jan 1 03:00) is in range.
#     2024, the true last year, wraps to 1979.
FORC=/data2/ydkoh/lm4/forcing_WFDE5_lm4p
for Y in $(seq 1979 2024); do
  [ -s "$FORC/wfde5_atm_$Y.nc" ] || { echo "ABORT: forcing missing $FORC/wfde5_atm_$Y.nc"; exit 1; }
done

# ============================================================================
# 2. Run directory -- copied from cycle 1, never the other way round
# ============================================================================
SRC=/data2/ydkoh/lm4/RUN/lm4_spinup30          # cycle 1 (1981-2010), read only
T=/data2/ydkoh/lm4/RUN/lm4p_ctl_1979-2024

[ -e "$T" ] && { echo "ABORT: $T already exists (holds 45 years; not deleted)"; exit 1; }
mkdir -p "$T/RESTART" "$T/FORCING" "$T/archive"

# INPUT: 599 symlinks into ~/KIOST-ESM2_AMIP/INPUT (AM4 atmosphere data, grids,
# cover_type.nc, LUH2 states/transitions v20260127, CO2, AMIP SST/SIC ...) plus
# 121 real files = the restart set at the end of cycle 1 (2011-01-01).  That
# restart is the initial condition of this run; the clock is simply wound back
# to 1979 (force_date_from_namelist below), which is what a spin-up-then-
# transient protocol means.  -a keeps links as links.
cp -a "$SRC/INPUT" "$T/INPUT"

# Model configuration files, all inherited from the AMIP case via cycle 1.
# MOM_*/COBALT_* are read at init even though do_ocean=.false.
for f in data_table field_table diag_table MOM_input MOM_layout MOM_override \
         SIS_input SIS_layout SIS_override COBALT_input COBALT_override \
         input.nml.template; do
  cp -a "$SRC/$f" "$T/$f"
done
ln -sfn "$EXE" "$T/fms_esm4.5_compile_v3_1007_fix.x"

# --- 48 PE ---------------------------------------------------------------------
# atmos_npes must equal the total rank count (the "atmosphere" PE set hosts the
# land).  C96 = 96x96 per face -> layout 2,4 = 48x24 tiles; SIS 720x576 -> 6,8.
# 48 PE was 1.41x faster than 24 (job 8274 vs 8278, 70 % parallel efficiency).
sed -i -e "s/^        atmos_npes = .*/        atmos_npes = 48/" "$T/input.nml.template"
sed -i -e "/^ &fv_core_nml/,/^\// s/^        layout   = 2,2/        layout   = 2,4/" \
       -e "/^ &land_model_nml/,/^\// s/^       layout   = 2,2/       layout   = 2,4/" \
       "$T/input.nml.template"
sed -i -e "s/^LAYOUT    = 6,4/LAYOUT    = 6,8/" "$T/SIS_layout"
# land_model_nml npes_io_group = 48 (= all PEs): the land's unstructured grid
# ignores io_layout; with the KIOST default 8 the restarts AND the land
# diagnostics come out as .0001/.0002 pieces that the archive step below does
# not match and the cleanup step does (13.21, 13.48).  Set in the template
# already; asserted in section 3.

# --- land-use marker ------------------------------------------------------------
# landuse.res (one line) records when transitions were last applied; cycle 1
# left 2011.  land_transitions_init aborts if the start time is earlier.  Reset
# to 1979.  NOT re-seeding land use from states.v20260127.nc: that path is the
# cold-start "initial transition from all-natural state" and would apply the
# natural->crop conversion a second time on top of 2010 crop tiles (13.47).
# Accepted limitation: land-use AREA is 2010's plus 1979-2024 deltas -> do not
# use this run to evaluate land-use area itself.
printf '  1979     1     1     0     0     0        Time of previous landuse transition calculation\n' \
       > "$T/INPUT/landuse.res"

# --- AMIP sea-ice / SST boundary data extended past 2022-12 --------------------
# do_ice=.true. makes the coupler read AMIP SIC/SST; the PCMDI files end 2022-12
# and the run died at 2022-12-16.  These fields never reach the land (verified:
# land-received forcing == WFDE5, r=1.00000, 13.42), so they were extended with
# the 2013-2022 monthly climatology (lm4/scripts/extend_amip_bcs.py ->
# INPUT_amip_ext/*_ext2025.nc, 1872 records) and only the symlinks switched.
# Originals untouched (13.54).
EXT=/data2/ydkoh/lm4/INPUT_amip_ext
ln -sfn "$EXT/amipbc_sic_PCMDI-AMIP-1-1-10_ext2025.nc" "$T/INPUT/amipbc_sic_PCMDI-AMIP-1-1-10.nc"
ln -sfn "$EXT/amipbc_sst_PCMDI-AMIP-1-1-10_ext2025.nc" "$T/INPUT/amipbc_sst_PCMDI-AMIP-1-1-10.nc"

# --- a second copy of the seed, outside the chain's reach ----------------------
mkdir -p "$T/SEED_2010"
cp -p "$T"/INPUT/*.res* "$T/SEED_2010"/
cp -p "$SRC/INPUT/landuse.res" "$T/SEED_2010/landuse.res.orig2011"

# ============================================================================
# 3. input.nml -- the settings that define this run (asserted, 1873-line file)
# ============================================================================
# The template is the AMIP input.nml with the Route B edits
# (lm4/config_offline/input.nml.diff_from_amip).  The chain fills in the three
# date lines per segment.  Everything that matters is checked here so that a
# silently reverted value cannot start a 45-year run.
need() {   # need <pattern>  : the template must contain this line
  grep -qE "$1" "$T/input.nml.template" || { echo "ABORT: input.nml.template lacks: $1"; exit 1; }
}
# coupler_nml -- land-only coupling
need '^ +calendar = .NOLEAP.'                  # 365-day years, matches WFDE5 files
need '^ +dt_atmos = 1800'                      # fast (land) step 30 min
need '^ +dt_cpld += 3600'                      # coupling step 1 h
need '^ +do_atmos = .false.'                   # atmosphere not time-stepped
need '^ +do_ocean = .false.'                   # MOM6 off
need '^ +ocean_npes = 0'
need '^ +do_ice += .true.'                     # SIS2 with specified ice (exchange grid)
need '^ +do_land += .true.'
need '^ +use_lag_fluxes = .false.'
need '^ +concurrent = .false.'
need '^ +atmos_npes = 48'                      # == total ranks
need '^ +force_date_from_namelist = .true.'    # clock from current_date, not coupler.res
# atmosphere leftovers that still cost time
need '^ +do_tropchem = .false.'                # tropospheric chemistry off (13.16)
need '^ +output_interval = 20000.0'            # diag_integral: > run length, < int32 day limit
need '^ +sst_degk = .false.'                   # tosbcs is degC (KIOST notes 12)
# land / vegetation
need '^ +layout += 2,4'                        # fv_core and land_model
need '^ +npes_io_group = 48'                   # combined land restarts+diags (13.48)
need '^ +use_static_veg = .FALSE.'             # dynamic vegetation
need '^ +do_cohort_dynamics += .TRUE.'
need '^ +do_patch_disturbance = .TRUE.'
need '^ +do_phenology += .TRUE.'
need '^ +do_biogeography += .FALSE.'           # species prescribed, decision 13.20
# --- land use: LUH2 transitions on (the ctl run) or frozen ---------------------
# landuse_nml do_landuse_change (lm4P/transitions/transitions.F90:136) is the
# single switch.  .TRUE. = LUH2 v20260127 transitions applied every Jan 1 (the
# ctl run; ends 2023 because the transitions file does).  .FALSE. =
# land_transitions_init returns at once (transitions.F90:293): tiles stay as the
# seed left them (2010 land-use areas), no landuse.res date check, no 2023
# limit -- the same "fixed land use" form as CLM5's 2000_ compset, a decade
# apart.  LANDUSE=off also removes the tile growth transitions cause, which is
# part (not the bulk: cohort count is, 13.17) of the 10 h/yr cost.
LANDUSE=${LANDUSE:-on}
if [ "$LANDUSE" = "off" ]; then
  sed -i 's/^\( *do_landuse_change *= *\)\.TRUE\./\1.FALSE./' "$T/input.nml.template"
  need '^ +do_landuse_change = .FALSE.'         # transitions frozen (LANDUSE=off)
else
  need '^ +do_landuse_change = .TRUE.'          # LUH2 transitions applied yearly (ctl)
fi
echo "land use: $LANDUSE"
need "^ +co2_to_use_for_photosynthesis ='interactive'"   # canopy-air CO2 drives photosynthesis
need "^ +soil_carbon_model_to_use = 'CENTURY-like'"      # nitrogen cycle OFF (inherited from KIOST)
need '^ +do_check_conservation = .FALSE.'      # lm4P: conservation check off (the LM4.1
                                               # carbon_cons_tol=1e-3 fix was for the UFS build)
need '^ +gust_min = 1.e-10'                    # lm4P gust comes from data_table (3.0 m/s), not here
# NOTE  vegn_to_use = 'uniform' is present.  Cold-start only; ignored on warm
#       start (this run: tile=13-16, cohort ~60 confirms the equilibrium
#       vegetation was read).  Change to 'multi-tile' before any cold start.
need "^ +vegn_to_use = 'uniform'"
echo "input.nml.template: all asserted settings present"

# ============================================================================
# 4. data_table -- WFDE5 injected at the atmosphere->land hooks
# ============================================================================
# Written out in full (48 lines, identical to lm4/config_offline/data_table.wfde5).
# LM4 builds incoming shortwave from the four *_down_* components only
# (land_model.F90:1264-1269, NIR = total - vis); the split just has to be
# self-consistent: dir/dif 50/50, vis/nir 50/50.
cat > "$T/data_table" << 'EOF'
# Route B: real WFDE5 forcing for offline lm4P via FMS data_override.
# Source file is the ATM-ready rewrite (CF 1D coords, ocean-filled, derived
# lprec/fprec/coszen) -- see wfde5_to_lm4p_atm.py.
#
# LM4 builds its incoming shortwave from the four *_down_* components only
# (land_model.F90:1264-1269, NIR = total - vis); Atm%flux_sw itself is never
# used by the land, so the split below just has to be self-consistent:
#   dir/dif = 50/50, vis/nir = 50/50  =>  total_dir=total_dif=0.5*FSDS,
#   vis_dir=vis_dif=0.25*FSDS, leaving NIR_dir=NIR_dif=0.25*FSDS.
#
"ATM", "t_bot"    , "t_bot"    , "./FORCING/wfde5_atm.nc", "bilinear", 1.0
"ATM", "sphum_bot", "sphum_bot", "./FORCING/wfde5_atm.nc", "bilinear", 1.0
"ATM", "p_surf"   , "p_surf"   , "./FORCING/wfde5_atm.nc", "bilinear", 1.0
"ATM", "p_bot"    , "p_surf"   , "./FORCING/wfde5_atm.nc", "bilinear", 1.0
"ATM", "u_bot"    , "u_bot"    , "./FORCING/wfde5_atm.nc", "bilinear", 1.0
"ATM", "flux_lw"  , "flux_lw"  , "./FORCING/wfde5_atm.nc", "bilinear", 1.0
"ATM", "coszen"   , "coszen"   , "./FORCING/wfde5_atm.nc", "bilinear", 1.0
"ATM", "lprec"    , "lprec"    , "./FORCING/wfde5_atm.nc", "bilinear", 1.0
"ATM", "fprec"    , "fprec"    , "./FORCING/wfde5_atm.nc", "bilinear", 1.0
#
# shortwave: one stored field, split by the factor column
#
"ATM", "flux_sw"               , "flux_sw", "./FORCING/wfde5_atm.nc", "bilinear", 1.0
"ATM", "flux_sw_down_total_dir", "flux_sw", "./FORCING/wfde5_atm.nc", "bilinear", 0.5
"ATM", "flux_sw_down_total_dif", "flux_sw", "./FORCING/wfde5_atm.nc", "bilinear", 0.5
"ATM", "flux_sw_down_vis_dir"  , "flux_sw", "./FORCING/wfde5_atm.nc", "bilinear", 0.25
"ATM", "flux_sw_down_vis_dif"  , "flux_sw", "./FORCING/wfde5_atm.nc", "bilinear", 0.25
"ATM", "flux_sw_dir"           , "flux_sw", "./FORCING/wfde5_atm.nc", "bilinear", 0.5
"ATM", "flux_sw_dif"           , "flux_sw", "./FORCING/wfde5_atm.nc", "bilinear", 0.5
"ATM", "flux_sw_vis"           , "flux_sw", "./FORCING/wfde5_atm.nc", "bilinear", 0.5
"ATM", "flux_sw_vis_dir"       , "flux_sw", "./FORCING/wfde5_atm.nc", "bilinear", 0.25
"ATM", "flux_sw_vis_dif"       , "flux_sw", "./FORCING/wfde5_atm.nc", "bilinear", 0.25
#
# constants: WFDE5 has scalar wind only, so v_bot=0 keeps |V| = WIND.
# z_bot 10 m = WFDE5 wind reference height (T/q are 2 m -- see notes).
# gust 3.0 matches the validated LM4 offline config (gust_const=3.0).
#
"ATM", "v_bot" , "", "", "none", 0.0
"ATM", "z_bot" , "", "", "none", 10.0
"ATM", "gust"  , "", "", "none", 3.0
"ATM", "slp"   , "", "", "none", 101325.0
#
# --- chemistry boundary conditions carried over from AMIP ---
#
"ATM", "o2_flux_pcair_atm", ""         , ""                             , "none" , 0.214
"ATM", "co2_dvmr_restore", "co2", "./INPUT/co2_gblannualdata.nc", "none", 1.0e-6
#
# --- specified ice/SST (do_ice=.true. still needs boundary data) ---
#
"ICE", "sic_obs", "siconcbcs", "./INPUT/amipbc_sic_PCMDI-AMIP-1-1-10.nc", "bilinear", 0.01
"ICE", "sit_obs", ""         , ""                                       , "none"    , 2.0
"ICE", "sst_obs", "tosbcs"   , "./INPUT/amipbc_sst_PCMDI-AMIP-1-1-10.nc", "bilinear", 1.0
EOF

# ============================================================================
# 5. diag_table and field_table
# ============================================================================
# diag_table: the AMIP table (3,713 lines) trimmed to the land streams by
# lm4/scripts/lm4p_offline_trim_diag_table.py (keeps land_* + grid_spec; drops
# 89 atmos/ocean/aerosol/ice streams that would otherwise be computed for a
# frozen atmosphere -- the 4.3 TB history incident's failure mode), then the
# land_forcing stream removed for production (8.4 GB/yr of echoed input;
# forcing delivery was already verified in 13.42).  1160 lines.
[ "$(grep -c land_forcing "$T/diag_table")" -eq 0 ] || { echo "ABORT: land_forcing still in diag_table"; exit 1; }
# field_table: the ORIGINAL AMIP table.  Removing the ~40 land chemistry
# tracers (dry deposition) saves ~7 % but the final measured config kept the
# original (13.19); co2 must stay in any case (interactive photosynthesis).

# ============================================================================
# 6. One model year = one PBS job (this is run_lm4p_ctl.sh)
# ============================================================================
cat > "$T/run_lm4p_ctl.sh" << 'EOF'
#!/bin/sh
### One model year of lm4p_ctl_1979-2024 at 48 PE.
### 48 ranks with npes_io_group=48: the io group has to span the whole PE set,
### otherwise the land's unstructured grid is written as .0001/.0002 pieces and
### the chain's archive pattern silently drops half of every diagnostic
### (LM4_SPINUP_NOTES 13.48).
#PBS -e lm4p_ctl.err
#PBS -o lm4p_ctl.log
#PBS -j oe
#PBS -V
#PBS -N lm4p_ctl
#PBS -q workq
#PBS -l select=1:ncpus=48:mpiprocs=48:host=climate01

source /etc/profile.d/modules.sh
module purge
module load intel21/compiler-21
module load intel21/mkl
module load intel21/hdf5-1.10.5
module load intel21/netcdf-4.6.1
module load intel21/mvapich2-2.3.4

ulimit -s unlimited

export work_dir=/data2/ydkoh/lm4/RUN/lm4p_ctl_1979-2024
cd $work_dir

export MV2_SMP_USE_CMA=1
export MV2_IBA_EAGER_THRESHOLD=131072
# mvapich2-2.3.4 hydra treats binding as oversubscription -> disable affinity
export MV2_ENABLE_AFFINITY=0

NP=`cat $PBS_NODEFILE | wc -l`
echo "=== lm4p_ctl launching on $NP ranks (atmos_npes must=48) $(date) ==="
# stdout to a file, never to the PBS stream: an undelivered PBS stdout is what
# filled climate01's root filesystem and stalled every job for four days (13.49)
mpirun -hostfile $PBS_NODEFILE -np $NP ./fms_esm4.5_compile_v3_1007_fix.x > esm4p5.log 2>&1
echo "=== END rc=$? $(date) ==="
EOF
chmod +x "$T/run_lm4p_ctl.sh"

# ============================================================================
# 7. The chain (lm4/scripts/chain_lm4p_ctl.sh, copied next to the run)
# ============================================================================
# Per year Y it does, in this order:
#   FORCING/wfde5_atm.nc -> wfde5_atm_Y.nc          (symlink switch)
#   input.nml <- template with days=365, hours=0, current_date=Y,1,1,3,0,0
#   rm previous year's history + RESTART/           (already archived)
#   qsub run_lm4p_ctl.sh ; poll qstat every 120 s
#   guard 1  no FATAL in esm4p5.log (FATAL_UNUSED_PARAMS excepted)
#   guard 2  >= 40 restart files in RESTART/
#   guard 3  RESTART/cana.res.tile1.nc newer than the INPUT one (no stale loop)
#   guard 4  Y0101.land_month.tile[1-6].nc all six combined, 12 time records
#   archive/yY <- RESTART/*.res*  (cp)  +  *.land_*.nc *.river_*.nc  (mv)
#   INPUT/    <- RESTART/*.res*   (next year's IC)
# Raw output is never deleted before it is archived; MAXSEG=50 caps the loop;
# a year whose archive/yY exists is skipped, so the chain can be relaunched.
# Reference copy: git lm4/scripts/chain_lm4p_ctl.sh (127 lines).  It hard-codes
# R=$T and F=$FORC, so it needs no arguments beyond the year range.
# TODO(confirm): path of the git checkout on climate00 -- until then, scp the
# file from the local repo into $T before submitting.
CHAIN=/data2/ydkoh/lm4/RUN/lm4p_ctl_1979-2024/chain_lm4p_ctl.sh     # the copy the run used
[ -f "$CHAIN" ] && cp -p "$CHAIN" "$T/chain_lm4p_ctl.sh" \
  || echo "NOTE: chain_lm4p_ctl.sh not found at $CHAIN -- scp lm4/scripts/chain_lm4p_ctl.sh into $T"

# ============================================================================
# 8. Checks, then how to submit
# ============================================================================
echo "--- checks ---"
grep -n "atmos_npes" "$T/input.nml.template"
grep -n -A2 "^ &fv_core_nml" "$T/input.nml.template" | head -3
grep -n -A2 "^ &land_model_nml" "$T/input.nml.template" | head -3
cat "$T/SIS_layout"
echo "landuse.res : $(cat "$T/INPUT/landuse.res")"
echo "sic/sst     : $(readlink "$T/INPUT/amipbc_sic_PCMDI-AMIP-1-1-10.nc")"
echo "exe         : $(readlink "$T/fms_esm4.5_compile_v3_1007_fix.x")"
echo "INPUT       : $(ls "$T/INPUT" | wc -l) entries, $(ls "$T"/INPUT/*.res* | wc -l) restart files (seed = end of cycle 1)"
echo "SEED_2010   : $(ls "$T/SEED_2010" | wc -l) files"
echo "archive     : $(ls "$T/archive" | wc -l) (must be 0)"
echo ""
echo "submit (login node; the chain only sleeps and qsubs):"
echo "  cd $T"
echo "  nohup bash chain_lm4p_ctl.sh 1979 2024 > chain_driver.out 2>&1 &"
echo "expect ~10.5 h per model year on climate01; it will stop at 2023 when"
echo "LUH2 transitions run out (13.54) -- that is the intended end."
echo "check:  tail chain.log ; ls archive | wc -l ; grep FATAL esm4p5.log"
echo "warm-start proof is the vegetation structure, not rc: tile>=13, cohort~60"
echo "in RESTART/vegn1.res.tile1.nc (cold start would show tile=1, cohort=1)."
