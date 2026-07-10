#!/bin/bash
#PBS -N nmp_jan1
#PBS -q workq
#PBS -l select=1:ncpus=48:mpiprocs=48:host=climate01
#PBS -l walltime=02:00:00
#PBS -j oe
#PBS -o /home/ydkoh/HRLDAS/forcing_GSWP3_1deg/jan1_snap/pbs.log
#
# Model-intercomparison snapshots on a FIXED calendar date (Jan-01), to match LM4.
#
# Why this is needed: RESTART_FREQUENCY_HOURS=8760 is a fixed 365-day stride, but the
# model runs a real Gregorian calendar (GSWP3 is noleap, so Feb-29 forcing was synthesised).
# Each leap year therefore slips the restart one calendar day earlier: 1981-01-01 -> 2010-12-25.
# LM4 is ALSO Gregorian, but its restarts fire on an FMS calendar-year alarm, so they land on
# Jan-01 every year regardless. The difference is the alarm type, not the calendar.
# Comparing LM4's Jan-01 state against Noah-MP's Dec-25 state is a 7-day seasonal offset.
#
# Each tail restarts from the drifted restart and integrates the remaining 1-7 days with the
# same forcing and the same physics options, so it reproduces the continuous trajectory exactly.
# RESTART_FREQUENCY_HOURS is set to 24*KDAY so a restart is written precisely at the tail end
# (HRLDAS does not write one at run termination -- that is why the Dec-25 files were the last).
set -u
source /etc/profile.d/modules.sh
module purge
module load intel21/compiler-21
module load intel21/intelmpi-21
module load intel21/netcdf-4.6.1
module load intel21/hdf5-1.10.5
ulimit -s unlimited

RUN=/home/ydkoh/HRLDAS/forcing_GSWP3_1deg/jan1_snap
SRC=/home/ydkoh/HRLDAS/spinup_raw/noahmp_GSWP3_1deg_staticveg_cyc2
OUT=$RUN/snapshots
cd "$RUN" || exit 1
mkdir -p "$OUT"

# "<restart date> <KDAY to next Jan-01>"; KDAY=0 entries are already on Jan-01 (copied verbatim).
TAILS="
1981010100 0
1982010100 0
1983010100 0
1984010100 0
1984123100 1
1985123100 1
1986123100 1
1987123100 1
1988123000 2
1989123000 2
1990123000 2
1991123000 2
1992122900 3
1993122900 3
1994122900 3
1995122900 3
1996122800 4
1997122800 4
1998122800 4
1999122800 4
2000122700 5
2001122700 5
2002122700 5
2003122700 5
2004122600 6
2005122600 6
2006122600 6
2007122600 6
2008122500 7
2009122500 7
2010122500 7
"

echo "=== START $(date) on $(hostname) ==="
ok=0; fail=0
while read -r RST K; do
  [ -z "${RST:-}" ] && continue
  Y=${RST:0:4}; M=${RST:4:2}; D=${RST:6:2}

  if [ "$K" -eq 0 ]; then
    cp "$SRC/RESTART.${RST}_DOMAIN1" "$OUT/JAN1.${Y}010100_DOMAIN1"
    echo "[$Y] already Jan-01 -> copied"
    ok=$((ok+1)); continue
  fi

  TGT=$((Y+1))
  cp -f "$SRC/RESTART.${RST}_DOMAIN1" "$RUN/RESTART.${RST}_DOMAIN1"
  cat > "$RUN/namelist.hrldas" <<EOF
&NOAHLSM_OFFLINE
 HRLDAS_SETUP_FILE = "/home/ydkoh/HRLDAS/forcing_GSWP3_1deg/init/HRLDAS_setup_GSWP3_1deg_d01.nc"
 INDIR  = "/home/ydkoh/HRLDAS/forcing_GSWP3_1deg/LDASIN"
 OUTDIR = "./"
 START_YEAR  = $Y
 START_MONTH = $M
 START_DAY   = $D
 START_HOUR  = 00
 START_MIN   = 00
 KDAY = $K
 SPINUP_LOOPS = 0
 RESTART_FILENAME_REQUESTED = "RESTART.${RST}_DOMAIN1"
 FORCING_NAME_T = "T2D"
 FORCING_NAME_Q = "Q2D"
 FORCING_NAME_U = "U2D"
 FORCING_NAME_V = "V2D"
 FORCING_NAME_P = "PSFC"
 FORCING_NAME_LW = "LWDOWN"
 FORCING_NAME_SW = "SWDOWN"
 FORCING_NAME_PR = "RAINRATE"
 DYNAMIC_VEG_OPTION                = 4
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
 FORCING_TIMESTEP = 10800
 NOAH_TIMESTEP    = 1800
 OUTPUT_TIMESTEP  = 31536000
 RESTART_FREQUENCY_HOURS = $((24*K))
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
  # </dev/null: mpirun otherwise consumes the here-string feeding this while-read loop,
  # which silently truncates the tail list after the first MPI launch.
  mpirun -np 48 ./hrldas.exe < /dev/null > "tail_${Y}.log" 2>&1
  NEW="$RUN/RESTART.${TGT}010100_DOMAIN1"
  if [ -f "$NEW" ]; then
    mv "$NEW" "$OUT/JAN1.${TGT}010100_DOMAIN1"
    echo "[$Y] +${K}d -> JAN1.${TGT}010100 OK"
    ok=$((ok+1))
  else
    echo "[$Y] +${K}d -> FAILED (no RESTART.${TGT}010100); see tail_${Y}.log"
    fail=$((fail+1))
  fi
  rm -f "$RUN/RESTART.${RST}_DOMAIN1"
done <<< "$TAILS"

echo "=== END $(date)  ok=$ok fail=$fail ==="
shopt -s nullglob
echo "snapshots: $(ls "$OUT"/JAN1.*_DOMAIN1 | wc -l)"
