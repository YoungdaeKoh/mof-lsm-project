#!/bin/bash
#
# Noah-MP v5.2.1 (HRLDAS offline) -- production run 1979-2023, WFDE5 forcing,
# 1 deg / 6-hourly, DVEG=5.
#
# The Noah-MP leg of the three-model comparison: same forcing, period and
# fixed-vegetation-type form as CLM5 clm5_prod_1979_2023 (2000 land use) and
# LM4+ lm4p_ctl (2010 land use frozen); Noah-MP has no land-use concept.
#
# Initial condition
#   cycle 6 of the DVEG=5 carbon spin-up on WFDE5 1981-2010
#   (spinup_raw/noahmp_WFDE5_1deg_dveg5/cycle06/RESTART.2011010103_DOMAIN1),
#   Times re-stamped to 1979-01-01 03Z.  Physics, LAI and WOOD converged
#   (98 % of cells within 1 %/cycle); STBLCP still rising, which feeds back on
#   nothing but soil respiration -- flag it when NEE is diagnosed (notes 11).
#
# Output
#   HRLDAS writes instantaneous snapshots (accumulated runoff/snow excepted)
#   and has no averaging, so the run writes every 6 h at the forcing stamps
#   03/09/15/21Z and the daily/monthly means are formed afterwards
#   (postprocess step, then the 6-h files are deleted).  95 variables, 31 MB
#   per file, 65,744 files, ~2 TB -- disk guard below.  Yearly restarts land
#   on Jan 1 03Z exactly (yearly segments, notes 10).
#
# Layout: same as the spin-up script.  One PBS job runs all 45 yearly
# segments back to back (~11 min each, ~8.5 h) and resumes from the last
# finished year if resubmitted.
#
# Usage (climate00):
#   bash NoahMP_WFDE5_prod_1979_2023.sh setup
#   qsub ~/HRLDAS/forcing_WFDE5_1deg/prod_1979_2023/run_prod.pbs
set -eu

HR=/home/ydkoh/HRLDAS
EXE_DIR=$HR/hrldas/run
FORC=$HR/forcing_WFDE5_1deg/LDASIN                          # 1979-2023, 65,744 files
SETUP=$HR/forcing_GSWP3_1deg/init/HRLDAS_setup_GSWP3_1deg_d01.nc
IC=$HR/spinup_raw/noahmp_WFDE5_1deg_dveg5/cycle06/RESTART.2011010103_DOMAIN1
RUN=$HR/forcing_WFDE5_1deg/prod_1979_2023
NODE=${NODE:-climate02}

Y0=1979; Y1=2023
START="${Y0}-01-01_03:00:00"
OUT_SEC=21600                                                # 6-hourly snapshots
MIN_FREE_TB=3                                                # /home free space needed before start

case "${1:-}" in
setup)
  [ -d "$RUN" ] && { echo "ABORT: $RUN exists -- production output lives here, not deleted automatically"; exit 1; }
  [ -f "$IC" ] || { echo "ABORT: IC missing: $IC"; exit 1; }
  for f in "$FORC/${Y0}010103.LDASIN_DOMAIN1" "$FORC/${Y1}123121.LDASIN_DOMAIN1"; do
    [ -f "$f" ] || { echo "ABORT: forcing endpoint missing: $f"; exit 1; }
  done
  n=$(ls "$FORC" | wc -l)
  [ "$n" -ge 65744 ] || { echo "ABORT: $n LDASIN files, need 65744"; exit 1; }
  free_tb=$(df -BT "$HR" | awk 'NR==2 {gsub("T","",$4); print $4}')
  [ "${free_tb%.*}" -ge "$MIN_FREE_TB" ] || { echo "ABORT: only ${free_tb} TB free on /home, need $MIN_FREE_TB"; exit 1; }

  mkdir -p "$RUN"
  cd "$RUN"
  for f in hrldas.exe NoahmpTable.TBL \
           snicar_drdt_bst_fit_60_c070416.nc snicar_optics_480bnd_c012422.nc snicar_optics_5bnd_c013122.nc \
           URBPARM.TBL URBPARM_LCZ.TBL URBPARM_UZE.TBL; do
    ln -sf "$EXE_DIR/$f" "$f"
  done

  /home/ydkoh/anaconda3/bin/python $HR/redate_restart.py "$IC" "RESTART.${Y0}010103_DOMAIN1" "$START"
  echo "IC carbon pools (cycle 6 end):"
  /home/ydkoh/anaconda3/bin/python $HR/check_carbon.py "RESTART.${Y0}010103_DOMAIN1" 2>/dev/null | grep -E "WOOD|FASTCP|STBLCP|LAI" || true

  # --- namelist: the spin-up template with OUTPUT_TIMESTEP = 6 h -----------
  # (physics options identical to forcing_GSWP3_1deg/spinup and spinup_dveg5)
  cat > namelist.template << EOF
&NOAHLSM_OFFLINE
 HRLDAS_SETUP_FILE = "$SETUP"
 INDIR  = "$FORC"
 OUTDIR = "./"
 START_YEAR  = __YEAR__
 START_MONTH = 01
 START_DAY   = 01
 START_HOUR  = 03
 START_MIN   = 00
 KDAY = __KDAY__
 SPINUP_LOOPS = 0
 RESTART_FILENAME_REQUESTED = "__RESTART__"
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
 OUTPUT_TIMESTEP  = $OUT_SEC
 RESTART_FREQUENCY_HOURS = __FREQ__
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

  # --- PBS: 45 yearly segments in one job, resumable ----------------------
  cat > run_prod.pbs << EOF
#!/bin/bash
#PBS -N nmp_prod
#PBS -q workq
#PBS -l select=1:ncpus=48:mpiprocs=48:host=$NODE
#PBS -l walltime=14:00:00
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
echo "=== (re)start \$(date) on \$(hostname) np48 (WFDE5 1deg/6h DVEG=5 production $Y0-$Y1, 6h output) ===" | tee -a run.log
for y in \$(seq $Y0 $Y1); do
  if [ \$((y % 4)) -eq 0 ] && { [ \$((y % 100)) -ne 0 ] || [ \$((y % 400)) -eq 0 ]; }; then nd=366; else nd=365; fi
  seed=RESTART.\${y}010103_DOMAIN1
  next=RESTART.\$((y + 1))010103_DOMAIN1
  if [ -f "\$next" ]; then echo "=== \$y already done, skipping ===" | tee -a run.log; continue; fi
  [ -f "\$seed" ] || { echo "ABORT: seed \$seed missing before \$y" | tee -a run.log; exit 1; }
  # disk guard per year: 1460 files x 31 MB = 45 GB
  free_gb=\$(df -BG $HR | awk 'NR==2 {gsub("G","",\$4); print \$4}')
  [ "\$free_gb" -ge 200 ] || { echo "ABORT: \$free_gb GB free before \$y" | tee -a run.log; exit 1; }
  sed -e "s/__YEAR__/\$y/" -e "s/__KDAY__/\$nd/" -e "s/__RESTART__/\$seed/" -e "s/__FREQ__/\$((nd * 24))/" \\
      namelist.template > namelist.hrldas
  echo "=== \$y (\$nd d) start \$(date) ===" | tee -a run.log
  mpirun -np 48 ./hrldas.exe 2>&1 | grep --line-buffered -vE 'Timing:|GLACIER HAS MELTED|ARE YOU SURE THIS SHOULD BE A GLACIER' >> hrldas.log
  rc=\${PIPESTATUS[0]}
  [ -f "\$next" ] || { echo "ABORT: \$y ended (rc=\$rc) without \$next" | tee -a run.log; exit 1; }
  nout=\$(ls \${y}*.LDASOUT_DOMAIN1 | wc -l)
  echo "=== \$y done rc=\$rc -> \$next, \$nout LDASOUT (expect \$((nd * 4))) \$(date) ===" | tee -a run.log
done
echo "=== END \$(date) ===" | tee -a run.log
EOF
  echo "set up in $RUN.  submit with:  qsub $RUN/run_prod.pbs"
  ;;
*)
  echo "usage: $0 setup"; exit 1 ;;
esac
