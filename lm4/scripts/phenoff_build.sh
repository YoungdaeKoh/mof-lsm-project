#!/bin/bash
# Build the "autumn leaf-off by day length" test executable (LM4 notes 13.69)
# WITHOUT touching the production tree: esm4p5-lm4p-offline/{src,exec} are only read.
#
#   patch : lm4/patches/lm4P.phenology_autumn_daylength.diff
#           vegn_data.F90     new species params tc_crit_off, dayl_crit_off (default -1 = off)
#           vegn_dynamics.F90 vegn_phenology_ppa(tile, lat, doy): extra leaf-off rule
#           vegetation.F90    passes lnd%ug_lat(l), doy
#   base  : coupler from build_gateBC (B+C gate, land bit-identical to production)
#
# The patched sources must already be in $B/patched/ (scp from the local repo).
# Method: shadow lm4P source tree (symlinks + the 3 patched files), a copy of
# exec/lm4P (objects), recompile what is out of date, relink with the gateBC coupler.
# Same flags as the production build: BLD_TYPE=PROD ISA=-march=core-avx2.
set -eu
E=/data2/ydkoh/lm4/esm4p5-lm4p-offline
C=/data2/ydkoh/lm4/build_gateBC
B=${B:-/data2/ydkoh/lm4/build_phenoff}   # override for a separate variant build, e.g.
X=${X:-fms_esm4.5_phenoff.x}             # B=.../build_phenspring X=fms_esm4.5_phenspring.x (spring tau_pheno_on patch, 2026-10-14)

source $E/exec/env.sh
if [ ! -d $B/src/lm4P ]; then
  mkdir -p $B/src
  cp -as $E/src/lm4P $B/src/lm4P          # symlink tree
fi
ln -sfn $E/src/FMS $B/src/FMS             # lm4P Makefile also reads $(SRCROOT)FMS/include
for p in $B/patched/*.F90; do   # vegn_tile.F90 included for the spring patch
  f=$(basename $p)
  t=$B/src/lm4P/vegetation/$f
  rm -f $t
  cp $p $t
  echo "--- $f vs production: $(diff $E/src/lm4P/vegetation/$f $t | grep -c '^[<>]') changed lines"
done

[ -d $B/lm4P ] || cp -a $E/exec/lm4P $B/lm4P
cd $B/lm4P
make SRCROOT=$B/src/ BUILDROOT=$E/exec/ MK_TEMPLATE=$E/exec/intel_tomo.mk \
     BLD_TYPE=PROD ISA="-march=core-avx2" liblm4P.a > $B/make_lm4P.log 2>&1 || { tail -30 $B/make_lm4P.log; exit 1; }
echo "--- recompiled: $(grep mpif90 $B/make_lm4P.log | grep -oE '[A-Za-z_0-9]+\.F90' | sort -u | tr '\n' ' ')"

cat > $B/link.mk <<EOF
MK_TEMPLATE = $E/exec/intel_tomo.mk
include \$(MK_TEMPLATE)
$X: FORCE
	\$(LD) $C/coupler/libcoupler.a $E/exec/atmos_drv/libatmos_drv.a $E/exec/sis2/libsis2.a $E/exec/atmos_dyn/libatmos_dyn.a $E/exec/atmos_phys/libatmos_phys.a $B/lm4P/liblm4P.a $E/exec/mom6/libmom6.a $E/exec/fms/libfms.a \$(LDFLAGS) -o \$@ \$(STATIC_LIBS)
FORCE:
EOF
cd $B
make -f link.mk BLD_TYPE=PROD ISA="-march=core-avx2" $X > $B/link.log 2>&1 || { tail -20 $B/link.log; exit 1; }
ls -l $B/$X $C/fms_esm4.5_gateBC.x $E/exec/fms_esm4.5_compile_v3_1007_fix.x
echo "--- production exe untouched if its date above is still Jul 20"
