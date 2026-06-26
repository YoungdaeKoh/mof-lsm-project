#!/bin/bash
CDO=/usr/local/cdo/1.9.3_gcc85/bin/cdo
SRC=/data2/ydkoh/WFDE5
OUT=/data2/ydkoh/WFDE5_6h
export CDO OUT
mkdir -p "$OUT"
do_zip() {
  local zip="$1"
  local T="/data2/ydkoh/wfde5_tmp_$(basename "$zip" .zip)"
  rm -rf "$T"; mkdir -p "$T"
  unzip -q "$zip" -d "$T"
  for nc in "$T"/*.nc; do
    base=$(basename "$nc" .nc); var=$(echo "$base" | cut -d_ -f1)
    mkdir -p "$OUT/$var"
    out="$OUT/$var/${base}_6h.nc"
    [ -s "$out" ] && continue
    $CDO -s timselmean,6 "$nc" "$out"
  done
  rm -rf "$T"
}
export -f do_zip
ls "$SRC"/*.zip | xargs -P 8 -I {} bash -c 'do_zip "$@"' _ {}
echo "ALL_DONE $(date '+%F %T')  6h_nc: $(find $OUT -name '*_6h.nc' | wc -l)"
