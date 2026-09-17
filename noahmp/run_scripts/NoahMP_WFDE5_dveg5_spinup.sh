#!/bin/bash
#
# Noah-MP v5.2.1 (HRLDAS offline) -- dynamic-vegetation carbon spin-up on
# WFDE5 forcing, 1 deg, 6-hourly.  DVEG=5.
#
# Where this sits in the multi-LSM design (2026-09-17):
#   CLM5-BGC  prognostic LAI/carbon, PFT areas fixed (2000_ compset)   -> same tier
#   Noah-MP   prognostic LAI/carbon (Dickinson), veg type fixed, FVEG
#             fixed at its annual max                                  -> DVEG=5
#   LM4+      cohort demography + LUH2 transitions                      -> one tier up
# DVEG=5 rather than 2 because option 2 also makes the vegetated fraction a
# function of LAI (FVEG = 1-exp(-0.52(LAI+SAI))), a feedback CLM5 does not have;
# option 5 switches on the carbon/LAI prognostics and nothing else relative
# to the static run (DVEG=4).  NOAHMP_PORTING_NOTES 9d.
#
# What is reused and what starts from scratch:
#   physics  warm start from the GSWP3 static-veg spin-up (2 x 30 yr, 1 deg):
#            soil moisture/temperature and SWE are in equilibrium there
#            (notes 9b).  Seed = RESTART.2010122500_DOMAIN1, Times re-stamped
#            to the start date with redate_restart.py (the state is kept).
#   carbon   NOT spun up: DVEG=4 never ran the carbon module, so the seed
#            still carries the cold-start placeholders (RTMASS=WOOD=500,
#            FASTCP=1000, "all arbitrary" in NoahmpInitMainMod.F90; notes 9d).
#            Noah-MP has no accelerated-decomposition mode, so WOOD/STBLCP
#            equilibrate at their own pace: expect 4-10 cycles of 30 yr.
#   forcing  WFDE5 -> LDASIN by noahmp/scripts/wfde5_to_ldasin_1deg6h.py
#            (same files LM4+ and CLM5 read).  Six-hour MEANS stamped at the
#            window midpoint (03/09/15/21Z), so the run starts at 03Z and
#            every restart is written at 03Z.  Feb 29 inserted, ocean-fill
#            cells nearest-filled (18 of 22,003 land cells).
#
# Cycling: one PBS job = one 30-year pass over 1981-2010.  The next pass
# re-stamps the last restart to the start date and reads the same forcing
# again (no forcing re-generation), exactly as the static spin-up did.
# Convergence is judged on the carbon pools of non-ice land, cos(lat)
# weighted (notes 9c, memory lsm-spinup-ice-mask-convergence).
#
# Do NOT run this until the other experiments have finished (user, 2026-09-17):
# it takes climate01 for ~6 h per cycle.
#
# Usage (climate00):
#   bash NoahMP_WFDE5_dveg5_spinup.sh setup          # run dir, seed, namelist
#   qsub  ~/HRLDAS/forcing_WFDE5_1deg/spinup_dveg5/run_cycle.pbs        # cycle 1
#   bash NoahMP_WFDE5_dveg5_spinup.sh next           # stage cycle N+1, then qsub again
set -eu

HR=/home/ydkoh/HRLDAS
EXE_DIR=$HR/hrldas/run                          # hrldas.exe + tables (intel21 + intelmpi, notes 10)
FORC=$HR/forcing_WFDE5_1deg/LDASIN              # from wfde5_to_ldasin_1deg6h.py range 1979 2023
SETUP=$HR/forcing_GSWP3_1deg/init/HRLDAS_setup_GSWP3_1deg_d01.nc   # 1 deg, stride-2 of 0.5 deg
SEED=$HR/forcing_GSWP3_1deg/spinup/RESTART.2010122500_DOMAIN1       # static-veg spin-up, cycle 2 end
RUN=$HR/forcing_WFDE5_1deg/spinup_dveg5
ARCH=$HR/spinup_raw/noahmp_WFDE5_1deg_dveg5     # raw preservation, never --delete

Y0=1981; Y1=2010                                 # cycling block, same as GSWP3 and the LM4+/CLM5 spin-ups
START="${Y0}-01-01_03:00:00"                     # 03Z: first WFDE5 stamp of the day
KDAY=10957                                       # 1981-01-01 .. 2010-12-31 inclusive, real calendar (leap days included)

case "${1:-}" in
# ------------------------------------------------------------------ setup ----
setup)
  [ -d "$RUN" ] && { echo "ABORT: $RUN exists -- 'next' to continue, or remove it deliberately"; exit 1; }
  [ -f "$SEED" ] || { echo "ABORT: seed restart missing: $SEED"; exit 1; }
  n=$(ls "$FORC" 2>/dev/null | wc -l)
  [ "$n" -ge 43800 ] || { echo "ABORT: only $n LDASIN files in $FORC (need >= 43800 for 1981-2010)"; exit 1; }
  for f in "$FORC/${Y0}010103.LDASIN_DOMAIN1" "$FORC/${Y1}123121.LDASIN_DOMAIN1"; do
    [ -f "$f" ] || { echo "ABORT: forcing endpoint missing: $f"; exit 1; }
  done
  mkdir -p "$RUN" "$ARCH"
  cd "$RUN"

  # executable and lookup tables: links, so a rebuild is picked up (setup_1deg_links.sh)
  for f in hrldas.exe NoahmpTable.TBL \
           snicar_drdt_bst_fit_60_c070416.nc snicar_optics_480bnd_c012422.nc snicar_optics_5bnd_c013122.nc \
           URBPARM.TBL URBPARM_LCZ.TBL URBPARM_UZE.TBL; do
    ln -sf "$EXE_DIR/$f" "$f"
  done

  # seed: physics from the static spin-up, Times re-stamped to the start date.
  # redate_restart.py copies the file and rewrites only the Times variable.
  /home/ydkoh/anaconda3/bin/python $HR/redate_restart.py "$SEED" "RESTART.${Y0}010103_DOMAIN1" "$START"
  echo "seed carbon pools (expect the cold-start placeholders, notes 9d):"
  /home/ydkoh/anaconda3/bin/python $HR/check_carbon.py "RESTART.${Y0}010103_DOMAIN1" || true

  # --- namelist: the static spin-up's namelist with five changes ------------
  #   DYNAMIC_VEG_OPTION 4 -> 5      carbon/LAI prognostic, FVEG = annual max
  #   INDIR                          WFDE5 LDASIN
  #   START_HOUR 00 -> 03            WFDE5 stamps are window midpoints
  #   FORCING_TIMESTEP 10800 -> 21600
  #   KDAY 10956 -> 10957            leap days are in the forcing (Feb 29 inserted)
  # Everything else is identical to forcing_GSWP3_1deg/spinup/namelist.hrldas.
  cat > namelist.hrldas << EOF
&NOAHLSM_OFFLINE
 HRLDAS_SETUP_FILE = "$SETUP"
 INDIR  = "$FORC"
 OUTDIR = "./"
 START_YEAR  = $Y0
 START_MONTH = 01
 START_DAY   = 01
 START_HOUR  = 03
 START_MIN   = 00
 KDAY = $KDAY
 SPINUP_LOOPS = 0
 RESTART_FILENAME_REQUESTED = "RESTART.${Y0}010103_DOMAIN1"
 FORCING_NAME_T = "T2D"
 FORCING_NAME_Q = "Q2D"
 FORCING_NAME_U = "U2D"
 FORCING_NAME_V = "V2D"
 FORCING_NAME_P = "PSFC"
 FORCING_NAME_LW = "LWDOWN"
 FORCING_NAME_SW = "SWDOWN"
 FORCING_NAME_PR = "RAINRATE"
 DYNAMIC_VEG_OPTION                = 5
 CANOPY_STOMATAL_RESISTANCE_OPTION = 1
 BTR_OPTION                        = 1
 SURFACE_RUNOFF_OPTION             = 3
 SUBSURFACE_RUNOFF_OPTION          = 3
 DVIC_INFILTRATION_OPTION          = 1
 SURFACE_DRAG_OPTION               = 1
 FROZEN_SOIL_OPTION                = 1
 SUPERCOOLED_WATER_OPTION          = 1
 RADIATIVE_TRANSFER_OPTION         = 3
 SNOW_ALBEDO_OPTION                = 1
 SNOW_COMPACTION_OPTION            = 2
 SNOW_COVER_OPTION                 = 1
 PCP_PARTITION_OPTION              = 1
 SNOW_THERMAL_CONDUCTIVITY         = 1
 TBOT_OPTION                       = 2
 TEMP_TIME_SCHEME_OPTION           = 3
 GLACIER_OPTION                    = 1
 SURFACE_RESISTANCE_OPTION         = 4
 SOIL_DATA_OPTION                  = 1
 PEDOTRANSFER_OPTION               = 1
 CROP_OPTION                       = 0
 IRRIGATION_OPTION                 = 0
 IRRIGATION_METHOD                 = 0
 TILE_DRAINAGE_OPTION              = 0
 WETLAND_OPTION                    = 0
 FORCING_TIMESTEP = 21600
 NOAH_TIMESTEP    = 1800
 OUTPUT_TIMESTEP  = 31536000
 RESTART_FREQUENCY_HOURS = 8760
 SPLIT_OUTPUT_COUNT = 1
 SKIP_FIRST_OUTPUT = .true.
 NSOIL=4
 soil_thick_input(1) = 0.10
 soil_thick_input(2) = 0.30
 soil_thick_input(3) = 0.60
 soil_thick_input(4) = 1.00
 ZLVL = 10.0
 SF_URBAN_PHYSICS = 0
 USE_WUDAPT_LCZ = 0
/
EOF

  # --- PBS job: one 30-year cycle, 48 ranks on climate01 --------------------
  # Same module set and mpirun form as the static spin-up (run_cyc2b_c01.sh).
  # exit=255 at the end is the Intel-MPI teardown artefact (notes 8d): judge
  # success by the last RESTART date, not by rc.
  cat > run_cycle.pbs << EOF
#!/bin/bash
#PBS -N nmp_wfde5_dveg5
#PBS -q workq
#PBS -l select=1:ncpus=48:mpiprocs=48:host=climate01
#PBS -l walltime=12:00:00
#PBS -j oe
#PBS -o $RUN/pbs.log
source /etc/profile.d/modules.sh
module purge
module load intel21/compiler-21
module load intel21/intelmpi-21
module load intel21/netcdf-4.6.1
module load intel21/hdf5-1.10.5
ulimit -s unlimited
cd $RUN || exit 1
echo "=== START \$(date) on \$(hostname) np48 (WFDE5 1deg/6h DVEG=5, cycle \$(cat cycle.txt 2>/dev/null || echo 1)) ==="
mpirun -np 48 ./hrldas.exe 2>&1 | grep --line-buffered -vE 'Timing:' > spinup.log
rc=\${PIPESTATUS[0]}
echo "=== END exit=\$rc \$(date) ==="
ls -t RESTART.*_DOMAIN1 | head -1
# raw preservation into a per-cycle folder, no --delete
C=\$(cat cycle.txt 2>/dev/null || echo 1)
A=$ARCH/cycle\$(printf %02d \$C)
mkdir -p "\$A"
shopt -s nullglob
rsync -a RESTART.*_DOMAIN1 *.LDASOUT_DOMAIN1 namelist.hrldas spinup.log "\$A/"
shopt -u nullglob
echo "=== archived -> \$A (\$(ls \$A/RESTART.*_DOMAIN1 | wc -l) restarts) \$(date) ==="
EOF
  echo 1 > cycle.txt
  echo "set up in $RUN.  submit with:  qsub $RUN/run_cycle.pbs"
  ;;

# ------------------------------------------------------------------- next ----
# Stage cycle N+1: last restart of cycle N -> re-stamped seed for 1981-01-01 03Z.
# The last restart is dated 12-25 (RESTART_FREQUENCY_HOURS=8760 = 365 d drifts
# one day per leap year; notes 9a) -- the missing six days are harmless for a
# spin-up seed.  Previous cycle's outputs are already in $ARCH (checked here).
next)
  cd "$RUN"
  C=$(cat cycle.txt)
  last=$(ls -t RESTART.*_DOMAIN1 | grep -v "RESTART.${Y0}010103_DOMAIN1" | head -1)
  [ -n "$last" ] || { echo "ABORT: no restart from cycle $C in $RUN"; exit 1; }
  A=$ARCH/cycle$(printf %02d "$C")
  [ -f "$A/$last" ] || { echo "ABORT: $last not archived in $A -- archive first"; exit 1; }
  echo "cycle $C ended at $last"
  /home/ydkoh/anaconda3/bin/python $HR/redate_restart.py "$last" "RESTART.${Y0}010103_DOMAIN1" "$START"
  for f in RESTART.*_DOMAIN1; do
    [ "$f" = "RESTART.${Y0}010103_DOMAIN1" ] || rm -f "$f"
  done
  rm -f ./*.LDASOUT_DOMAIN1 spinup.log pbs.log
  echo $((C + 1)) > cycle.txt
  echo "staged cycle $((C + 1)).  submit with:  qsub $RUN/run_cycle.pbs"
  ;;

*)
  echo "usage: $0 setup | next"; exit 1 ;;
esac
