#!/bin/bash
# Build a test executable with update_atmos_model_state gated by do_atmos
# (lm4/patches/coupler_main.F90.atmos_state_gate.diff) WITHOUT touching the
# production tree: esm4p5-lm4p-offline/{src,exec} are only read.  The running
# lufix chain launches exec/fms_esm4.5_compile_v3_1007_fix.x every model year,
# so nothing may be rebuilt in place.
#
# Method: shadow source dir (symlinks to the original coupler sources + the one
# patched file), a copy of exec/coupler (objects), recompile coupler_main.o
# only, relink against the original libraries under a new name.
# Same flags as the production build: BLD_TYPE=PROD ISA=-march=core-avx2.
set -eu
E=/data2/ydkoh/lm4/esm4p5-lm4p-offline
B=/data2/ydkoh/lm4/build_stategate
X=fms_esm4.5_stategate.x

source $E/exec/env.sh
mkdir -p $B/src/coupler/full $B/src/coupler/shared
ln -sf $E/src/coupler/full/*   $B/src/coupler/full/
ln -sf $E/src/coupler/shared/* $B/src/coupler/shared/

# patched source: a real file replacing the symlink
rm -f $B/src/coupler/full/coupler_main.F90
cp $E/src/coupler/full/coupler_main.F90 $B/src/coupler/full/coupler_main.F90
n=$(grep -c '^ *call update_atmos_model_state( Atm )' $B/src/coupler/full/coupler_main.F90)
[ "$n" = 1 ] || { echo "ABORT: expected exactly one call site, found $n"; exit 1; }
sed -i 's/^\( *\)call update_atmos_model_state( Atm )/\1if (do_atmos) call update_atmos_model_state( Atm )/' \
    $B/src/coupler/full/coupler_main.F90
echo "--- source diff vs production:"
diff $E/src/coupler/full/coupler_main.F90 $B/src/coupler/full/coupler_main.F90 || true

# objects: copy, then rebuild only what is out of date (= coupler_main.o)
[ -d $B/coupler ] || cp -a $E/exec/coupler $B/coupler
cd $B/coupler
make SRCROOT=$B/src/ BUILDROOT=$E/exec/ MK_TEMPLATE=$E/exec/intel_tomo.mk \
     BLD_TYPE=PROD ISA="-march=core-avx2" libcoupler.a 2>&1 | tee $B/make_coupler.log | grep -E 'mpif90|rror' | cut -c1-160

cat > $B/link.mk <<EOF
MK_TEMPLATE = $E/exec/intel_tomo.mk
include \$(MK_TEMPLATE)
$X: FORCE
	\$(LD) $B/coupler/libcoupler.a $E/exec/atmos_drv/libatmos_drv.a $E/exec/sis2/libsis2.a $E/exec/atmos_dyn/libatmos_dyn.a $E/exec/atmos_phys/libatmos_phys.a $E/exec/lm4P/liblm4P.a $E/exec/mom6/libmom6.a $E/exec/fms/libfms.a \$(LDFLAGS) -o \$@ \$(STATIC_LIBS)
FORCE:
EOF
cd $B
make -f link.mk BLD_TYPE=PROD ISA="-march=core-avx2" $X 2>&1 | tail -3 | cut -c1-200
ls -l $B/$X $E/exec/fms_esm4.5_compile_v3_1007_fix.x
echo "--- production exe untouched if its date above is still 2026-07-20"
