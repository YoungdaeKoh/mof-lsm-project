#!/bin/bash
# Test executable "B+C": update_atmos_model_state gated by do_atmos (B) AND the
# exchange-grid -> atmosphere remaps of flux_up_to_atmos skipped when
# do_atmos=.false. (C; dt_tr, dt_t, shflx, lhflx - read only by the skipped
# atmosphere physics).  Patch: lm4/patches/coupler.atmos_state_and_up_remap_gate.diff
# Same shadow-build method as stategate_build.sh: production src/exec read only.
# The two patched sources must already be in $B/patched/ (scp from local).
set -eu
E=/data2/ydkoh/lm4/esm4p5-lm4p-offline
B=/data2/ydkoh/lm4/build_stategateC
X=fms_esm4.5_stategateC.x

source $E/exec/env.sh
mkdir -p $B/src/coupler/full $B/src/coupler/shared
ln -sf $E/src/coupler/full/*   $B/src/coupler/full/
ln -sf $E/src/coupler/shared/* $B/src/coupler/shared/
for f in coupler_main.F90 atm_land_ice_flux_exchange.F90; do
  rm -f $B/src/coupler/full/$f
  cp $B/patched/$f $B/src/coupler/full/$f
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
