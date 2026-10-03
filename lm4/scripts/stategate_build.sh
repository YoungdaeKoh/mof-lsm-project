#!/bin/bash
# Build a patched test executable WITHOUT touching the production tree:
# esm4p5-lm4p-offline/{src,exec} are only read.  The running lufix chain
# launches exec/fms_esm4.5_compile_v3_1007_fix.x every model year, so nothing
# may be rebuilt in place.
#
# usage: bash stategate_build.sh <variant>      (gateB | gateBC)
#   gateB  : lm4/patches/coupler_main.F90.atmos_state_gate.diff
#            (update_atmos_model_state skipped when do_atmos=.false.; the
#            atmosphere clock and diag_send_complete are kept)
#   gateBC : lm4/patches/coupler.atmos_state_and_up_remap_gate.diff
#            (gateB + the exchange-grid -> atmosphere remaps of flux_up_to_atmos)
# The patched sources must already be in $B/patched/ (scp from the local repo).
#
# Method: shadow source dir (symlinks to the original coupler sources + the
# patched files), a copy of exec/coupler (objects), recompile what is out of
# date, relink against the original libraries under a new name.
# Same flags as the production build: BLD_TYPE=PROD ISA=-march=core-avx2.
set -eu
V=${1:?variant}
E=/data2/ydkoh/lm4/esm4p5-lm4p-offline
B=/data2/ydkoh/lm4/build_$V
X=fms_esm4.5_$V.x

source $E/exec/env.sh
mkdir -p $B/src/coupler/full $B/src/coupler/shared
ln -sf $E/src/coupler/full/*   $B/src/coupler/full/
ln -sf $E/src/coupler/shared/* $B/src/coupler/shared/
for p in $B/patched/*.F90; do
  f=$(basename $p)
  rm -f $B/src/coupler/full/$f
  cp $p $B/src/coupler/full/$f
  echo "--- $f vs production: $(diff $E/src/coupler/full/$f $B/src/coupler/full/$f | grep -c '^[<>]') changed lines"
done

[ -d $B/coupler ] || cp -a $E/exec/coupler $B/coupler
cd $B/coupler
make SRCROOT=$B/src/ BUILDROOT=$E/exec/ MK_TEMPLATE=$E/exec/intel_tomo.mk \
     BLD_TYPE=PROD ISA="-march=core-avx2" libcoupler.a > $B/make_coupler.log 2>&1 || { tail -20 $B/make_coupler.log; exit 1; }
echo "--- recompiled: $(grep mpif90 $B/make_coupler.log | grep -oE '[a-z_]+\.F90' | sort -u | tr '\n' ' ')"

cat > $B/link.mk <<EOF
MK_TEMPLATE = $E/exec/intel_tomo.mk
include \$(MK_TEMPLATE)
$X: FORCE
	\$(LD) $B/coupler/libcoupler.a $E/exec/atmos_drv/libatmos_drv.a $E/exec/sis2/libsis2.a $E/exec/atmos_dyn/libatmos_dyn.a $E/exec/atmos_phys/libatmos_phys.a $E/exec/lm4P/liblm4P.a $E/exec/mom6/libmom6.a $E/exec/fms/libfms.a \$(LDFLAGS) -o \$@ \$(STATIC_LIBS)
FORCE:
EOF
cd $B
make -f link.mk BLD_TYPE=PROD ISA="-march=core-avx2" $X > $B/link.log 2>&1 || { tail -20 $B/link.log; exit 1; }
ls -l $B/$X $E/exec/fms_esm4.5_compile_v3_1007_fix.x
echo "--- production exe untouched if its date above is still Jul 20"
