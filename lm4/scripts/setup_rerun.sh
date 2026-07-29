#!/bin/bash
# Build two worker directories for the LM4 December re-run (1990-1996).
# Each worker runs one year at a time from the archived restart of the previous
# year, with days=365/hours=0 so December's monthly window (which closes at
# Jan 1 03:00) actually completes.
set -e
S=/data2/ydkoh/lm4/RUN/lm4_spinup30
for W in wA wB; do
  R=/data2/ydkoh/lm4/RERUN/$W
  mkdir -p "$R/INPUT" "$R/RESTART" "$R/archive"
  for f in "$S"/*.x "$S"/data_table "$S"/diag_table "$S"/field_table \
           "$S"/input.nml.template "$S"/COBALT_input "$S"/COBALT_override \
           "$S"/MOM_input "$S"/MOM_layout "$S"/MOM_override \
           "$S"/SIS_input "$S"/SIS_layout "$S"/SIS_override; do
    [ -e "$f" ] && cp -p "$f" "$R"/
  done
  # FORCING is a tree of links; reuse it instead of duplicating
  [ -e "$R/FORCING" ] || ln -s "$S/FORCING" "$R/FORCING"
  # INPUT statics only - per-year restarts are swapped in by the worker
  rsync -a --exclude '*.res*.nc' "$S/INPUT/" "$R/INPUT/"
done
echo SETUP_OK
du -sh /data2/ydkoh/lm4/RERUN/wA /data2/ydkoh/lm4/RERUN/wB
ls /data2/ydkoh/lm4/RERUN/wA | head -20
