#!/bin/bash
# Route B step 1 probe: land-only (data-atmosphere) run dir from AMIP config.
# Original ~/KIOST-ESM2_AMIP is NOT modified; INPUT and exe are symlinked.
set -e

R=/data2/ydkoh/lm4/RUN/lm4_offline_probe
A=$HOME/KIOST-ESM2_AMIP

mkdir -p "$R/RESTART"
cd "$A"

cp -p input.nml data_table diag_table field_table "$R"/
cp -p MOM_input MOM_layout MOM_override "$R"/
cp -p SIS_input SIS_layout SIS_override "$R"/
cp -p COBALT_input COBALT_override "$R"/

ln -sfn "$A/INPUT" "$R/INPUT"
ln -sfn "$HOME/ESM4p5_KIOSTv2b/exec/fms_esm4.5_compile_v3_1007_fix.x" "$R/fms_esm4.5_compile_v3_1007_fix.x"

echo "=== run dir ==="
ls -la "$R"
echo "=== INPUT reachable: $(ls "$R"/INPUT/ | wc -l) entries ==="
echo "=== current coupler_nml ==="
sed -n '/&coupler_nml/,/^ *\//p' "$R/input.nml"
